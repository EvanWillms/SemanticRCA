"""Narrow, no-retry HTTP boundary for the frozen P01 experiment."""
from __future__ import annotations
import json
import os
import shlex
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from rca.model_policy import require_allowed_model

MODEL = 'zai-org/GLM-5.3-Flash'


def credentials(env_file: Path) -> tuple[str, str]:
    values = {}
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('export '):
                line = line[7:]
            name, sep, value = line.partition('=')
            if sep and name.strip() in {'FEATHERLESS_API_KEY', 'FEATHERLESS_BASE_URL'}:
                parts = shlex.split(value, comments=True)
                if len(parts) != 1:
                    raise ValueError('Malformed Featherless environment assignment')
                values[name.strip()] = parts[0]
    key = os.environ.get('FEATHERLESS_API_KEY', values.get('FEATHERLESS_API_KEY', ''))
    base = os.environ.get('FEATHERLESS_BASE_URL', values.get('FEATHERLESS_BASE_URL', 'https://api.featherless.ai/v1')).rstrip('/')
    parsed = urlsplit(base)
    if not key or parsed.scheme != 'https' or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Missing credential or invalid HTTPS API base')
    return key, base


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class DeadlineExceeded(Exception):
    """The absolute study deadline elapsed during transport."""


def _set_response_timeout(response, seconds):
    """Tighten the underlying socket timeout to the remaining wall budget."""
    holders = [response, getattr(response, 'fp', None)]
    fp = holders[-1]
    holders.append(getattr(fp, 'raw', None))
    for holder in holders:
        sock = getattr(holder, '_sock', None)
        setter = getattr(sock, 'settimeout', None)
        if callable(setter):
            setter(seconds)
            return


def _read_body(response, max_bytes, timeout=None, deadline=None):
    raw = bytearray()
    read1 = getattr(type(response), 'read1', None)
    reader = response.read1 if callable(read1) else response.read
    while len(raw) <= max_bytes:
        allowed = timeout
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise DeadlineExceeded()
            allowed = remaining if allowed is None else min(allowed, remaining)
        if allowed is not None:
            _set_response_timeout(response, allowed)
        chunk = reader(min(64 * 1024, max_bytes + 1 - len(raw)))
        if not chunk:
            break
        raw.extend(chunk)
    if deadline is not None and time.monotonic() > deadline:
        raise DeadlineExceeded()
    return bytes(raw)


def _failure(status, error_type, start):
    return {'status': status, 'error_type': error_type,
            'wall_seconds': time.monotonic() - start,
            'raw_body': None, 'json': None}


def request(key: str, base: str, endpoint: str, payload=None, timeout=60,
            max_bytes=4_000_000, deadline=None) -> dict:
    """Return sanitized raw body, never request headers or exception messages."""
    if payload is not None or endpoint.rstrip("/").endswith(("/chat/completions", "/tokenize")):
        require_allowed_model((payload or {}).get("model"))
    body = None if payload is None else json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode()
    req = urllib.request.Request(base + endpoint, data=body, headers={
        'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'User-Agent': 'SymbolicRCA-P01/1'})
    start = time.monotonic()
    if deadline is not None and deadline <= start:
        return _failure(None, 'DeadlineExceeded', start)
    open_timeout = timeout if deadline is None else min(timeout, deadline - start)
    status = None
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=open_timeout) as response:
            status = response.status
            raw = _read_body(response, max_bytes, timeout, deadline)
    except urllib.error.HTTPError as exc:
        status = exc.code
        try:
            raw = _read_body(exc, max_bytes, timeout, deadline)
        except Exception as body_error:
            return _failure(status, type(body_error).__name__, start)
        finally:
            close = getattr(exc, 'close', None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
    except Exception as exc:
        return _failure(status, type(exc).__name__, start)
    text = raw.decode('utf-8', errors='replace').replace(key, '[REDACTED]')
    if len(raw) > max_bytes:
        return {'status': status, 'error_type': 'ResponseTooLarge', 'wall_seconds': time.monotonic()-start, 'raw_body': None, 'json': None}
    try:
        parsed = json.loads(text)
    except ValueError:
        parsed = None
    return {'status': status, 'error_type': None, 'wall_seconds': time.monotonic()-start, 'raw_body': text, 'json': parsed}
