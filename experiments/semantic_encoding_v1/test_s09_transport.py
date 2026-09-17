"""Exercise the real SDK boundary without making network requests."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import httpx2
import openai

from . import run_s09_live as s09


class S09TransportTests(unittest.TestCase):
    def sdk_transport(self, handler):
        real_client = openai.OpenAI
        return patch.object(openai, "OpenAI", side_effect=lambda **kwargs: real_client(
            **kwargs, http_client=httpx2.Client(transport=httpx2.MockTransport(handler))))

    def block_legacy_transport(self):
        # Prevent the pre-fix implementation from making a real request.
        error = HTTPError("https://api.featherless.ai/v1/chat/completions", 403,
                          "Forbidden", {}, io.BytesIO(b'{"error_code":1010}'))
        return patch.object(s09, "urlopen", side_effect=error, create=True)

    def test_sdk_preserves_request_response_and_usage(self):
        requests = []
        body = s09.request_body(s09.make_case("unmapped_14", "normalized_json")[0])
        payload = {"model": s09.MODEL, "choices": [{"message": {"content": "{}"}}],
                   "usage": {"prompt_tokens": 21, "completion_tokens": 10, "cached_tokens": 0}}

        def handler(request):
            requests.append(request)
            self.assertEqual(str(request.url), "https://api.featherless.ai/v1/chat/completions")
            self.assertEqual(json.loads(request.content), body)
            self.assertEqual(request.headers["authorization"], "Bearer test-secret")
            return httpx2.Response(200, json=payload, headers={"cf-ray": "test-ray"})

        with self.sdk_transport(handler), self.block_legacy_transport():
            result = s09.call_provider(s09.endpoint_from(""), "test-secret", body)
        self.assertEqual(result["transport"], "success")
        self.assertEqual(result["response"], payload)
        self.assertEqual(result["headers"]["cf-ray"], "test-ray")
        self.assertEqual(len(requests), 1)

    def test_sdk_does_not_retry_rate_limit(self):
        requests = []

        def handler(request):
            requests.append(request)
            return httpx2.Response(429, json={"error": {"message": "Rate limit"}})

        with self.sdk_transport(handler), self.block_legacy_transport():
            result = s09.call_provider(s09.endpoint_from(""), "test-secret", {
                "model": s09.MODEL, "messages": [{"role": "user", "content": "Hello"}]})
        self.assertEqual(result["http_status"], 429)
        self.assertEqual(len(requests), 1)

    def test_access_denial_stops_schedule_and_retains_evidence(self):
        requests = []

        def handler(request):
            requests.append(request)
            return httpx2.Response(403, json={
                "error_code": 1010, "error_name": "browser_signature_banned",
                "retryable": False, "owner_action_required": True,
                "detail": "test-secret", "ray_id": "test-ray",
            }, headers={"cf-ray": "test-ray"})

        with tempfile.TemporaryDirectory() as temp, self.sdk_transport(handler), \
                self.block_legacy_transport(), patch.object(s09, "OUT_ROOT", Path(temp)), \
                patch.object(s09, "read_dotenv", return_value={}), \
                patch.object(s09, "env_value", side_effect=lambda _, name:
                             "test-secret" if name == "FEATHERLESS_API_KEY" else ""), \
                redirect_stdout(io.StringIO()):
            code = s09.run(["--run-id", "denied"])
            out = Path(temp) / "denied"
            result = json.loads((out / "result.json").read_text())
            response = json.loads((out / "responses/01.json").read_text())
            self.assertEqual(code, 1)
            self.assertEqual(result["status"], "inconclusive")
            self.assertEqual(result["calls_completed"], 1)
            self.assertEqual(result["calls_not_started"], 5)
            self.assertEqual(result["stop_reason"], "non_retryable_http_403")
            self.assertEqual(result["token_comparison_status"], "unavailable_missing_provider_usage")
            self.assertEqual(len(list((out / "requests").glob("*.json"))), 6)
            self.assertEqual(response["headers"]["cf-ray"], "test-ray")
            self.assertIn("[REDACTED]", response["error_body"])
            self.assertNotIn("test-secret", "".join(p.read_text() for p in out.rglob("*") if p.is_file()))
        self.assertEqual(len(requests), 1)


if __name__ == "__main__":
    unittest.main()
