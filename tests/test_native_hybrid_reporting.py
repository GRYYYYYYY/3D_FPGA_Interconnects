import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('native_reporting', ROOT / 'scripts/report_native_hybrid.py')
reporting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reporting)


def row(variant, seconds, cpd=10, success=True, repeat=0):
    return dict(case='c', repeat=repeat, variant=variant, success=success,
                diagnostic=variant=='pair', directory='unused', native_process_seconds=seconds,
                workflow_seconds=seconds+1, routing_seconds=seconds-.1, critical_path_ns=cpd, wirelength=100)


class NativeReporting(unittest.TestCase):
    def test_faster_external_verification_is_not_gpu_gain(self):
        baseline = row('original_vpr', 10)
        baseline['workflow_seconds'] = 20
        gpu = row('hybrid', 11)
        gpu['workflow_seconds'] = 19
        gpu['hybrid'] = {'offload_attempts': 10, 'errors': 0}
        result = reporting.comparisons(dict(measurements=[baseline, gpu]))[0]
        self.assertTrue(result['positive_single_run'])
        self.assertFalse(result['positive_gpu_candidate'])

    def test_failed_guard_is_not_speedup_denominator(self):
        gpu = row('batch', 2)
        gpu['hybrid'] = {'offload_attempts': 10, 'errors': 0}
        data = dict(measurements=[row('original_parallel', 10),
                                  row('guard', 20, success=False), gpu])
        results = [r for r in reporting.comparisons(data) if r['variant'] == 'batch']
        self.assertFalse(any(r['positive_gpu_candidate'] for r in results))
        guarded = next(r for r in results if r['reference'] == 'guard')
        self.assertNotIn('process_speedup', guarded)

    def test_signal_is_not_reported_as_infeasibility(self):
        failed = row('original_parallel', 20, success=False)
        failed.update(status='failed', returncode=-9)
        result = reporting.measurement_outcome(failed)
        self.assertEqual(result['outcome'], 'terminated_by_signal')
        self.assertEqual(result['signal'], 'SIGKILL')
        failed.update(status='timeout', returncode=-15)
        self.assertEqual(reporting.measurement_outcome(failed)['outcome'], 'timeout')

    def test_parallel_search_timer_is_not_last_worker(self):
        parsed=reporting.metrics('Time spent on path search: 9.5 seconds.\nTime spent on path search: 0.1 seconds.\n')
        self.assertEqual(parsed['search_seconds'],9.6)
        self.assertEqual(parsed['search_timer_seconds'],[9.5,.1])

    def test_diagnostic_and_quality_rejection(self):
        data = dict(measurements=[row('original_vpr', 10), row('pair', 1), row('hybrid', 2, cpd=11)])
        result = reporting.comparisons(data)
        self.assertEqual(len(result), 1)
        self.assertGreater(result[0]['workflow_speedup'], 1)
        self.assertFalse(result[0]['positive_single_run'])

    def test_failed_runs_retained_and_no_cross_repeat_ratio(self):
        data = dict(measurements=[row('original_vpr', 10), row('hybrid', 100, success=False), row('batch', 1, repeat=1)])
        result = reporting.comparisons(data)
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]['success'])
        self.assertNotIn('workflow_speedup', result[0])

    def test_limited_smoke_is_not_production_speedup(self):
        data = dict(max_offloads=32, measurements=[row('original_vpr',10), row('hybrid',1)])
        result = reporting.comparisons(data)[0]
        self.assertTrue(result['limited_offload_smoke'])
        self.assertFalse(result['positive_single_run'])

    def test_no_offload_speedup_cannot_be_attributed_to_gpu(self):
        data = dict(measurements=[row('original_parallel',10), row('batch',8)])
        result = reporting.comparisons(data)[0]
        self.assertTrue(result['positive_single_run'])
        self.assertFalse(result['gpu_executed'])
        self.assertFalse(result['positive_gpu_candidate'])


if __name__ == '__main__':
    unittest.main()
