"""Model eligibility is checked before any inference leaves the process."""
import unittest
from unittest.mock import Mock, patch

from rca.model_client import FeatherlessClient
from rca.model_policy import ALLOWED_MODELS
from experiments.semantic_encoding_v1.featherless_p01 import request
from experiments.semantic_encoding_v1.run_s09_live import call_provider


class ModelPolicyTests(unittest.TestCase):
    def test_all_official_models_can_reach_transport(self):
        for model in ALLOWED_MODELS:
            with self.subTest(model=model):
                response = Mock(status=200)
                response.read.return_value = b'{"choices":[{"message":{"content":"ok"}}]}'
                transport = Mock(return_value=response)
                self.assertEqual(FeatherlessClient(api_key="test", transport=transport).ask(model, "hello"), "ok")
                transport.assert_called_once()

    def test_entire_fallback_list_is_validated_before_transport(self):
        for model in ("gpt-5.6-luna", "zai-org/GLM-4.5", "zai-org/GLM-5.3", "other/GLM-5.2"):
            with self.subTest(model=model):
                transport = Mock()
                client = FeatherlessClient(api_key="test", transport=transport)
                with self.assertRaises(ValueError):
                    client.ask(["zai-org/GLM-4.7-Flash", model], "hello")
                transport.assert_not_called()
                self.assertEqual(client.failures, [])

    def test_semantic_studies_reject_unlisted_and_missing_models(self):
        for payload in ({"model": "zai-org/GLM-5.3"}, {}):
            with self.subTest(payload=payload), patch("urllib.request.build_opener") as opener:
                with self.assertRaises(ValueError):
                    request("test", "https://example.test/v1", "/chat/completions", payload)
                opener.assert_not_called()
                with self.assertRaises(ValueError):
                    call_provider("https://example.test/v1/chat/completions", "test", payload)
