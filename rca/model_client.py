"""Small, bounded OpenAI compatible client for the Track 1 submission.

The submission image is deliberately able to run with only the Python standard
library.  Featherless speaks the OpenAI chat-completions wire format, so this
module keeps the transport narrow and makes provider failures ordinary routing
outcomes rather than process failures.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://api.featherless.ai/v1"
DEFAULT_TIMEOUT = 8.0
MAX_ATTEMPTS_PER_MODEL = 2
MAX_OUTPUT_TOKENS = 1500


def _sdk_transport(request, timeout):
    from openai import OpenAI, DefaultHttpxClient
    from types import SimpleNamespace
    payload = json.loads(request.data)
    endpoint = request.full_url.removesuffix('/chat/completions')
    key = request.get_header('Authorization').removeprefix('Bearer ')
    with OpenAI(api_key=key, base_url=endpoint, timeout=timeout, max_retries=0,
                http_client=DefaultHttpxClient(follow_redirects=False)) as client:
        result = client.chat.completions.create(**payload)
    raw = result.model_dump_json().encode()
    return SimpleNamespace(status=200, read=lambda: raw)


class ModelClientError(RuntimeError):
    """A provider, transport, or response-shape failure."""


class AllModelsUnavailable(ModelClientError):
    """No offered model produced a usable completion."""


def _message_text(messages: str | Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]
    return [dict(message) for message in messages]


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


class FeatherlessClient:
    """Bounded chat client.

    ``transport`` is injectable for an offline test.  It receives a prepared
    ``Request`` and timeout and must return an object with ``status`` and
    ``read()`` attributes, matching ``urllib`` responses.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        deadline: float | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        attempts: int = MAX_ATTEMPTS_PER_MODEL,
        transport: Callable[[Request, float], Any] | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("FEATHERLESS_API_KEY")
        self.base_url = (base_url or os.environ.get("FEATHERLESS_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.deadline = deadline
        self.timeout = max(0.1, float(timeout))
        self.attempts = max(1, int(attempts))
        self.transport = transport or _sdk_transport
        self.usage: dict[str, dict[str, int]] = {}
        self.failures: list[str] = []

    def ask(
        self,
        models: str | Sequence[str],
        messages: str | Sequence[Mapping[str, Any]],
        *,
        max_tokens: int = MAX_OUTPUT_TOKENS,
        temperature: float = 0.0,
    ) -> str:
        """Ask models in preference order, retrying each at most twice."""
        offered = [models] if isinstance(models, str) else [str(item) for item in models]
        if not offered:
            raise ValueError("at least one model is required")
        payload = {
            "model": "",  # filled for each preference, keeping the prompt identical
            "messages": _message_text(messages),
            "temperature": temperature,
            "max_tokens": min(MAX_OUTPUT_TOKENS, max(1, int(max_tokens))),
            "stream": False,
        }
        for model in offered:
            for attempt in range(self.attempts):
                try:
                    remaining = self._remaining()
                    if remaining <= 0:
                        raise ModelClientError("case deadline reached")
                    payload["model"] = model
                    return self._once(model, payload, min(self.timeout, remaining))
                except Exception as exc:  # provider failures must trigger fallback
                    if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                        raise
                    self.failures.append(f"{model}: {self._safe_error(exc)}")
                    if attempt + 1 < self.attempts:
                        remaining = self._remaining()
                        if remaining <= 0:
                            break
                        # A short bounded pause helps transient capacity errors,
                        # while ensuring retry policy cannot consume the case.
                        time.sleep(min(0.15 * (2**attempt), max(0.0, remaining - 0.05)))
                    else:
                        break
        detail = "; ".join(self.failures[-4:])
        raise AllModelsUnavailable(detail or "no model completed")

    def _remaining(self) -> float:
        if self.deadline is None:
            return self.timeout
        return self.deadline - time.monotonic()

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        # Provider bodies can contain account or request details.  Keep only a
        # short type label in state and evidence; never expose headers or keys.
        if isinstance(exc, HTTPError):
            return f"HTTP {exc.code}"
        if isinstance(exc, URLError):
            return "transport error"
        return type(exc).__name__

    def _once(self, model: str, payload: dict[str, Any], timeout: float) -> str:
        if not self.api_key:
            raise ModelClientError("FEATHERLESS_API_KEY is not set")
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                # Some hosted edge proxies reject urllib's default user agent.
                "User-Agent": "semanticrca/1.0 (Python urllib)",
            },
            method="POST",
        )
        try:
            response = self.transport(request, timeout=timeout)
            raw = response.read()
            status = int(getattr(response, "status", 200))
        except HTTPError as exc:
            # HTTPError is also a response; consume no secret-bearing headers.
            try:
                raw = exc.read()
            except OSError:
                raw = b""
            raise ModelClientError(f"HTTP {exc.code}") from None
        except (URLError, TimeoutError, OSError) as exc:
            raise ModelClientError(type(exc).__name__) from None
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ModelClientError("invalid JSON response") from exc
        # Featherless can return status 200 with an error object.  Inspect it
        # before touching choices, as required by the provider contract.
        if status < 200 or status >= 300 or isinstance(decoded, Mapping) and decoded.get("error"):
            raise ModelClientError(f"HTTP {status}" if status != 200 else "provider error")
        choices = decoded.get("choices") if isinstance(decoded, Mapping) else None
        if not isinstance(choices, Sequence) or not choices:
            raise ModelClientError("response has no choices")
        message = _value(choices[0], "message", {})
        text = _value(message, "content", "")
        if isinstance(text, list):
            text = "".join(str(part.get("text", "")) if isinstance(part, Mapping) else str(part) for part in text)
        if not isinstance(text, str) or not text.strip():
            raise ModelClientError("response has empty content")
        usage = decoded.get("usage", {}) if isinstance(decoded, Mapping) else {}
        counters = self.usage.setdefault(model, {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0})
        counters["calls"] += 1
        counters["prompt_tokens"] += int(_value(usage, "prompt_tokens", 0) or 0)
        counters["completion_tokens"] += int(_value(usage, "completion_tokens", 0) or 0)
        return text.strip()


# Short alias for callers and test doubles.
ModelClient = FeatherlessClient

__all__ = [
    "AllModelsUnavailable",
    "DEFAULT_BASE_URL",
    "FeatherlessClient",
    "MAX_OUTPUT_TOKENS",
    "ModelClient",
    "ModelClientError",
]
