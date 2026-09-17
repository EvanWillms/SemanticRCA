"""Offline transport and accounting tests for the submission model client."""

from __future__ import annotations

import json
import time
import unittest
from unittest.mock import patch
from urllib.request import Request

from rca import model_client


class _Response:
    def __init__(self, payload, status=200):
        self.status = status
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._raw


class _SequenceTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request, timeout))
        return self.responses.pop(0)


def _sleeping_worker(url, body, authorization, timeout, result_queue):
    del url, body, authorization, timeout, result_queue
    time.sleep(2)


def _large_response_worker(url, body, authorization, timeout, result_queue):
    del url, body, authorization, timeout
    result_queue.put(("response", 200, b"x" * 100_000))


class ModelClientTests(unittest.TestCase):
    def test_http_200_error_body_falls_back_before_choices_access(self):
        transport = _SequenceTransport([
            _Response({"error": {"message": "busy", "type": "server_error"}}),
            _Response({"choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 2, "completion_tokens": 1}}),
        ])
        client = model_client.FeatherlessClient(api_key="test", attempts=1, transport=transport)
        self.assertEqual(client.ask(("zai-org/GLM-4.7-Flash", "zai-org/GLM-5.3-Flash"), "fact"), "ok")
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(client.usage["zai-org/GLM-5.3-Flash"]["calls"], 1)

    def test_billable_empty_content_still_records_usage(self):
        transport = _SequenceTransport([
            _Response({"choices": [{"message": {"content": ""}}], "usage": {"prompt_tokens": 7, "completion_tokens": 4}}),
        ])
        client = model_client.FeatherlessClient(api_key="test", attempts=1, transport=transport)
        with self.assertRaises(model_client.AllModelsUnavailable):
            client.ask("zai-org/GLM-4.7-Flash", "fact")
        self.assertEqual(client.usage["zai-org/GLM-4.7-Flash"], {
            "calls": 1, "prompt_tokens": 7, "completion_tokens": 4,
        })

    def test_sdk_transport_terminates_stuck_worker(self):
        request = Request("https://example.test/v1/chat/completions", data=b"{}", headers={"Authorization": "Bearer test"}, method="POST")
        with patch.object(model_client, "_sdk_worker", _sleeping_worker):
            started = time.monotonic()
            with self.assertRaises(model_client.ModelClientError):
                model_client._sdk_transport(request, 0.05)
            self.assertLess(time.monotonic() - started, 1.2)

    def test_sdk_transport_reads_large_response_before_joining_worker(self):
        request = Request("https://example.test/v1/chat/completions", data=b"{}", headers={"Authorization": "Bearer test"}, method="POST")
        with patch.object(model_client, "_sdk_worker", _large_response_worker):
            response = model_client._sdk_transport(request, 1.0)
        self.assertEqual(len(response.read()), 100_000)

    def test_request_payload_keeps_low_reasoning_and_output_cap(self):
        transport = _SequenceTransport([
            _Response({"choices": [{"message": {"content": "ok"}}], "usage": {}}),
        ])
        client = model_client.FeatherlessClient(api_key="test", attempts=1, transport=transport)
        client.ask("zai-org/GLM-4.7-Flash", "fact", max_tokens=5000)
        payload = json.loads(transport.calls[0][0].data)
        self.assertEqual(payload["reasoning_effort"], "low")
        self.assertEqual(payload["max_tokens"], 2048)


if __name__ == "__main__":
    unittest.main()
