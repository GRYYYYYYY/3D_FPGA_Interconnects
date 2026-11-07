"""Prevent invalid experimental evidence from becoming a speedup claim."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from report_native_cpu_study import compare, top_level_timings


class ComparisonEligibility(unittest.TestCase):
    def setUp(self):
        self.base = {'key': 'control', 'success': True, 'case': 'gemm', 'workers': 4,
                     'cache_mode': 'reuse', 'repeat': 0, 'lane': 'same_block', 'hostname': 'same_host',
                     'cpu_budget': {'cpu_set': [0, 1, 2, 3]}, 'inputs': {'rr_graph': {'sha256': 'rr'}},
                     'lookahead_cache_sha256': 'common', 'log_evidence': {'final_overused_nodes': 0},
                     'critical_path_ns': 10, 'wirelength': 1000, 'native_process_seconds': 100,
                     'workflow_seconds': 200, 'routing_seconds': 20, 'route_body_sha256': 'route'}
        self.candidate = copy.deepcopy(self.base)
        self.candidate.update(key='candidate', native_process_seconds=50)

    def test_matched_quality_preserving_pair(self):
        result = compare(self.base, self.candidate)
        self.assertTrue(result['eligible'] and result['quality_pass'])
        self.assertEqual(result['process_speedup'], 2)

    def test_fast_failed_or_overused_route_is_not_speedup(self):
        for change in [{'success': False}, {'log_evidence': {'final_overused_nodes': 1}},
                       {'log_evidence': {'final_overused_nodes': None}}]:
            with self.subTest(change=change):
                result = compare(self.base, self.candidate | change)
                self.assertFalse(result['eligible'])
                self.assertNotIn('process_speedup', result)

    def test_hardware_and_input_mismatches_are_rejected(self):
        for change in [{'workers': 8}, {'hostname': 'other'}, {'cache_mode': 'rebuild'},
                       {'cpu_budget': {'cpu_set': [4, 5, 6, 7]}}, {'lookahead_cache_sha256': 'different'},
                       {'inputs': {'rr_graph': {'sha256': 'modified'}}}]:
            with self.subTest(change=change):
                self.assertFalse(compare(self.base, self.candidate | change)['eligible'])

    def test_quality_regression_cannot_enter_accepted_geomean(self):
        result = compare(self.base, self.candidate | {'critical_path_ns': 10.6})
        self.assertTrue(result['eligible'])
        self.assertFalse(result['quality_pass'])

    def test_nested_graph_timer_is_not_double_counted(self):
        log = '# Create Device took 60.0 seconds\n## Loading routing resource graph took 55.0 seconds\n# Routing took 20.0 seconds\n'
        timing = top_level_timings(log, 100)
        self.assertEqual(timing['top_level_seconds'], {'Create Device': 60, 'Routing': 20})
        self.assertEqual(timing['unscoped_seconds'], 20)

    def test_inconsistent_timer_remainder_is_not_hidden(self):
        timing = top_level_timings('# Routing took 20.0 seconds\n', 10)
        self.assertEqual(timing['unscoped_seconds'], -10)
        self.assertTrue(timing['rounding_or_overlap_warning'])


if __name__ == '__main__':
    unittest.main()
