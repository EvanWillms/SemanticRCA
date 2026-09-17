"""Offline contract checks for the live submission seam."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from rca.contracts import Solution
from rca.model_client import AllModelsUnavailable, FeatherlessClient


class _Response:
    status = 200

    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def read(self):
        return self.payload


class _Transport:
    def __init__(self):
        self.requests = []
        self.responses = [
            _Response({"error": {"message": "busy", "type": "server_error"}}),
            _Response({"choices": [{"message": {"content": '{"candidate_ids":[1]}'}}],
                       "usage": {"prompt_tokens": 4, "completion_tokens": 3}}),
        ]

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        return self.responses.pop(0)


class _FakeAgentClient:
    def __init__(self, **kwargs):
        self.usage = {"zai-org/GLM-5.2": {"prompt_tokens": 8, "completion_tokens": 4, "calls": 1}}
        self.failures = []
        self.calls = 0

    def ask(self, models, prompt, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return '{"candidate_ids":[1]}'
        return ('{"answers":[{"candidate_id":1,"component":"shippingservice-1",'
                '"reason":"container read I/O load","datetime":"2022-03-20 09:09:06"}],'
                '"confidence":"medium","why":"The changed read series is the earliest recorded departure."}')


class _UnavailableAgentClient:
    def __init__(self, **kwargs):
        self.usage = {}
        self.failures = []

    def ask(self, models, prompt, **kwargs):
        self.failures.append("ModelClientError")
        raise AllModelsUnavailable("provider detail with secret")


class SubmissionAgentTests(unittest.TestCase):
    def test_client_checks_200_error_body_then_falls_back(self):
        transport = _Transport()
        client = FeatherlessClient(api_key="test-key", base_url="https://example.test/v1",
                                   attempts=1, transport=transport)
        text = client.ask(("zai-org/GLM-4.7-Flash", "zai-org/GLM-5.3-Flash"), "hello")
        self.assertEqual(text, '{"candidate_ids":[1]}')
        self.assertEqual(len(transport.requests), 2)
        self.assertEqual(transport.requests[0][0].full_url, "https://example.test/v1/chat/completions")
        self.assertEqual(transport.requests[0][0].get_header("User-agent"), "semanticrca/1.0 (Python urllib)")

    def test_solve_emits_requested_projection_and_validated_reason(self):
        from agents import routed

        sidecar = {
            "interpretation": {"status": "interpreted", "scope": {
                "deployment": "cloudbed-8", "window_start": "2022-03-20T09:00:00+08:00",
                "window_end": "2022-03-20T09:30:00+08:00", "failure_count": 1,
                "requested_fields": ["datetime", "component", "reason"],
            }},
            "findings": {"status": "completed", "stop_reason": None, "candidates": [{
                "family": "metric_container", "resource": "node-3.shippingservice-1",
                "kpi": "container_read_bytes", "timestamp": 1647738546,
                "value": 47, "reference_median": 2.1, "signed_difference": 44.9,
                "locator": {"path": "telemetry/2022_03_20/metric/metric_container.csv", "record": 9},
            }], "source_snapshot": {"sources": [{
                "family": "metric_container", "resources": ["node-3.shippingservice-1"]
            }]}},
            "operations": [],
        }
        base = Solution(prediction="", evidence="## Evidence\nObserved source row.\n\n## Ruled out\nNone.\n",
                        discovery=sidecar)
        with patch.object(routed.discovery_agent, "solve", return_value=base), \
             patch.object(routed, "ModelClient", _FakeAgentClient):
            result = routed.solve("query", Path("/tmp/data"), {"row_id": 4})
        self.assertIsNone(result.discovery)
        self.assertIn('"root cause occurrence datetime"', result.prediction)
        self.assertIn('"root cause component"', result.prediction)
        self.assertIn('"root cause reason"', result.prediction)
        self.assertLess(result.prediction.index("root cause occurrence datetime"),
                        result.prediction.index("root cause component"))
        self.assertLess(result.prediction.index("root cause component"),
                        result.prediction.index("root cause reason"))
        self.assertIn("container read I/O load", result.prediction)
        self.assertEqual(result.evidence.count("## Answer"), 1)
        self.assertIn("Qualified model hypothesis (not a validated fact)", result.evidence)

    def test_solve_returns_unknown_fields_when_all_models_are_unavailable(self):
        from agents import routed

        sidecar = {
            "interpretation": {"status": "interpreted", "scope": {
                "deployment": "cloudbed-8", "window_start": "2022-03-20T09:00:00+08:00",
                "window_end": "2022-03-20T09:30:00+08:00", "failure_count": 1,
                "requested_fields": ["datetime", "component", "reason"],
            }},
            "findings": {"status": "completed", "stop_reason": None, "candidates": [{
                "family": "metric_container", "resource": "node-3.shippingservice-1",
                "kpi": "container_cpu_usage", "timestamp": 1647738546,
                "value": 47, "reference_median": 2.1, "signed_difference": 44.9,
                "locator": {"path": "telemetry/2022_03_20/metric/metric_container.csv", "record": 9},
            }], "source_snapshot": {"sources": [{
                "family": "metric_container", "resources": ["node-3.shippingservice-1"]
            }]}},
            "operations": [],
        }
        base = Solution(prediction="", evidence="## Evidence\nObserved source row.\n\n## Ruled out\nNone.\n",
                        discovery=sidecar)
        with patch.object(routed.discovery_agent, "solve", return_value=base), \
             patch.object(routed, "ModelClient", _UnavailableAgentClient):
            result = routed.solve("query", Path("/tmp/data"), {"row_id": 4})

        class MalformedClient(_UnavailableAgentClient):
            def ask(self, models, prompt, **kwargs):
                return '{"candidate_ids":null,"answers":[{"candidate_id":{},"component":{},"reason":"container CPU load"}],"confidence":"high"}'

        with patch.object(routed.discovery_agent, "solve", return_value=base), \
             patch.object(routed, "ModelClient", MalformedClient):
            malformed = routed.solve("query", Path("/tmp/data"), {"row_id": 4})
        self.assertEqual(json.loads(malformed.prediction), json.loads(result.prediction))
        self.assertIn("Low.", malformed.evidence)

        prediction = json.loads(result.prediction)
        self.assertEqual(prediction["1"], {
            "root cause occurrence datetime": "I don't know",
            "root cause component": "I don't know",
            "root cause reason": "I don't know",
        })
        self.assertIn("requested fields are unknown", result.evidence)
        self.assertNotIn("container CPU load", result.prediction)


if __name__ == "__main__":
    unittest.main()
