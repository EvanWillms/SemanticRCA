"""Frozen-input and failure-oriented contracts, no network."""
import copy
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from .score_p01 import score, parse_json
from .run_p01 import usage_cost, build_request, admit, create_run_dir, token_count, verify_freeze, digest
from .featherless_p01 import credentials, request

ROOT=Path(__file__).resolve().parents[2]
DESIGN=ROOT/'specs/008-featherless-trace-semantics'

class P01Tests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((DESIGN/'design-fixtures/p01/q9.symbolic.json').read_text())
        self.source=json.loads((ROOT/'experiments/semantic_encoding_v1/fixtures/T2.json').read_text())
        self.book=json.loads((ROOT/'experiments/semantic_encoding_v1/fixtures/codebook.json').read_text())
        self.answer={k:copy.deepcopy(self.data[k]) for k in ['packet_id','trace_id','context','entities']}
        self.answer.update(schema_version='p01.v1',occurrences=copy.deepcopy(self.data['records']),unknowns={k:'unknown' for k in ['status_interpretation','business_outcome','interaction_role','backend_target','instrumentation_completeness']})
    def check(self,a):return score(a,'q9',self.source,self.book)
    def test_correct_and_reordered(self):
        self.assertTrue(self.check(self.answer)['passed'])
        self.answer['occurrences'].reverse()
        self.assertTrue(self.check(self.answer)['passed'])
    def test_mutations_rejected(self):
        edits=[lambda a:a['occurrences'].pop(),lambda a:a['occurrences'][0].__setitem__(2,'e0'),lambda a:a['occurrences'][0].__setitem__(3,'bogus'),lambda a:a['occurrences'][0].__setitem__(9,'bogus'),lambda a:a['unknowns'].__setitem__('business_outcome','success'),lambda a:a.__setitem__('cause','network')]
        for edit in edits:
            a=copy.deepcopy(self.answer);edit(a);self.assertFalse(self.check(a)['passed'])
    def test_context_comparison_is_json_type_strict(self):
        self.source['context']['numeric_marker'] = 1
        self.answer['context']['numeric_marker'] = True
        result = self.check(self.answer)
        self.assertFalse(result['passed'])
        self.assertIn('context', result['errors'])
    def test_duplicate_occurrence_and_bad_type(self):
        self.answer['occurrences'].append(self.answer['occurrences'][0]);self.assertFalse(self.check(self.answer)['passed'])
        self.answer['occurrences']={};self.assertFalse(self.check(self.answer)['passed'])
    def test_no_extra_json_or_duplicate_keys(self):
        for raw in ['{} {}','```json\n{}\n```','{"a":1,"a":2}']:
            with self.assertRaises(ValueError):parse_json(raw)
    def test_builder_only_prompt_and_input(self):
        req=build_request('frozen',self.data)
        self.assertEqual(req['messages'],[{'role':'system','content':'frozen'},{'role':'user','content':json.dumps(self.data,sort_keys=True,separators=(',',':'),ensure_ascii=False)}])
        self.assertNotIn('cache_control',req)
    def test_usage_unknown_and_cached(self):
        rates={'fresh':.15,'cached':.03,'output':.5}
        u=usage_cost({'prompt_tokens':1000,'completion_tokens':100},rates)
        self.assertIsNone(u['cached_input_tokens']);self.assertIsNone(u['estimated_cost_usd'])
        self.assertAlmostEqual(u['uncached_estimate_usd'],.0002)
        u=usage_cost({'prompt_tokens':1000,'completion_tokens':100,'prompt_tokens_details':{'cached_tokens':800}},rates)
        self.assertAlmostEqual(u['estimated_cost_usd'],.000104)
        self.assertIsNone(usage_cost({},rates)['uncached_estimate_usd'])
        self.assertIsNone(usage_cost({'prompt_tokens':10,'completion_tokens':1,'prompt_tokens_details':{'cached_tokens':11}},rates)['cached_input_tokens'])
    def test_provider_top_level_cache_and_conflict(self):
        u=usage_cost({'prompt_tokens':1000,'completion_tokens':100,'cached_tokens':800})
        self.assertEqual(u['cached_input_tokens'],800)
        self.assertAlmostEqual(u['estimated_cost_usd'],.000104)
        u=usage_cost({'prompt_tokens':1000,'completion_tokens':100,'cached_tokens':800,'prompt_tokens_details':{'cached_tokens':400}})
        self.assertTrue(u['invalid_cache_counter']);self.assertIsNone(u['estimated_cost_usd'])
    def test_admission(self):
        self.assertTrue(admit(0,0,0,1000,0.0033))
        for args in [(18,0,0,1000,.0033),(0,1,0,1000,.0033),(0,0,1150,1000,.0033),(0,0,0,8193,.0033)]:self.assertFalse(admit(*args))
    def test_reused_run_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            create_run_dir(Path(d),'first')
            with self.assertRaises(FileExistsError):create_run_dir(Path(d),'first')
            with self.assertRaises(ValueError):create_run_dir(Path(d),'../elsewhere')
    def test_token_count_variants(self):
        self.assertEqual(token_count({'status':200,'json':{'count':626,'model':'zai-org/GLM-5.3-Flash'}}),626)
        self.assertEqual(token_count({'status':200,'json':{'tokens':[1,2]}}),2)
        self.assertIsNone(token_count({'status':200,'json':{'count':True}}))
        self.assertIsNone(token_count({'status':200,'json':{'count':626,'model':'other'}}))
    def test_transport_failure_no_retry(self):
        opener=MagicMock();opener.open.side_effect=TimeoutError('credential-must-not-appear')
        with patch('urllib.request.build_opener',return_value=opener):
            result=request('credential-must-not-appear','https://api.featherless.ai/v1','/chat/completions',{'model': 'zai-org/GLM-5.3-Flash'})
        self.assertEqual(opener.open.call_count,1)
        self.assertEqual(result['error_type'],'TimeoutError')
        self.assertNotIn('credential-must-not-appear',json.dumps(result))
    def test_http_error_body_read_failure_is_recorded_without_exception_or_secret(self):
        error = urllib.error.HTTPError('https://api.featherless.ai/v1/chat/completions', 503, 'unavailable', {}, None)
        error.read = Mock(side_effect=TimeoutError('credential-must-not-appear'))
        opener = MagicMock(); opener.open.side_effect = error
        with patch('urllib.request.build_opener', return_value=opener):
            result = request('credential-must-not-appear', 'https://api.featherless.ai/v1', '/chat/completions', {'model': 'zai-org/GLM-5.3-Flash'})
        self.assertEqual(result['status'], 503)
        self.assertEqual(result['error_type'], 'TimeoutError')
        self.assertIsNone(result['raw_body'])
        self.assertNotIn('credential-must-not-appear', json.dumps(result))

    def test_request_rejects_expired_total_deadline_before_open(self):
        opener = MagicMock()
        with patch('urllib.request.build_opener', return_value=opener), patch(
            'experiments.semantic_encoding_v1.featherless_p01.time.monotonic', return_value=100.0
        ):
            result = request('credential', 'https://api.featherless.ai/v1', '/chat/completions', {'model': 'zai-org/GLM-5.3-Flash'}, deadline=99.0)
        self.assertEqual(result['error_type'], 'DeadlineExceeded')
        opener.open.assert_not_called()

    def test_request_records_deadline_during_body_read(self):
        class Response:
            status = 200

            def __init__(self):
                self.chunks = [b'{"ok":', b'true}']

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self, _):
                return self.chunks.pop(0) if self.chunks else b''

        opener = MagicMock(); opener.open.return_value = Response()
        clock = iter([100.0, 100.0, 109.0, 111.0, 111.0])
        with patch('urllib.request.build_opener', return_value=opener), patch(
            'experiments.semantic_encoding_v1.featherless_p01.time.monotonic', side_effect=clock
        ):
            result = request('credential', 'https://api.featherless.ai/v1', '/chat/completions', {'model': 'zai-org/GLM-5.3-Flash'}, deadline=110.0)
        self.assertEqual(result['status'], 200)
        self.assertEqual(result['error_type'], 'DeadlineExceeded')

    def test_verify_freeze_rejects_mutated_snapshot_without_live_code_check(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            (path / 'code').mkdir()
            (path / 'code' / 'run_p01.py').write_text('frozen code')
            (path / 'prompt.txt').write_text('frozen prompt')
            (path / 'design-manifest.json').write_text('{}')
            freeze = {
                'file_sha256': {'code/run_p01.py': digest((path / 'code' / 'run_p01.py').read_bytes())},
                'prompt_sha256': digest((path / 'prompt.txt').read_bytes()),
                'design_manifest_sha256': digest((path / 'design-manifest.json').read_bytes()),
            }
            (path / 'freeze.json').write_text(json.dumps(freeze))
            self.assertEqual(verify_freeze(path, check_live_code=False), freeze)
            (path / 'code' / 'run_p01.py').write_text('mutated code')
            with self.assertRaisesRegex(ValueError, 'snapshot changed'):
                verify_freeze(path)
    def test_env_not_executed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'.env';p.write_text('FEATHERLESS_API_KEY="literal-$(not-a-command)"\n')
            key,base=credentials(p);self.assertEqual(key,'literal-$(not-a-command)')

if __name__=='__main__':unittest.main()
