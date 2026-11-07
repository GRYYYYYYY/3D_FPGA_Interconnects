"""A good median must never hide a failed repeat in a confirmation claim."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_target_confirmation import evaluate


class ConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.protocol = dict(case='example', repeats=3, epochs=2,
                             refine_threshold=700, refine_connections=2048,
                             bootstrap_congestion_mode='full', refine_mode='negotiate',
                             all_pairs_must_pass=True, quality_budget_percent=5,
                             workflow_speedup_required=True,
                             variant_order='rotate vpr,target each repeat')
        self.summary = dict(status='completed', cases=[{'id': 'example'}],
                            protocol=dict(repeats=3, epochs=2, refine_threshold=700,
                                          refine_connections=2048, congestion_mode='full',
                                          refine_mode='negotiate', incremental_target=True), rows=[])
        for repeat in range(3):
            for variant in (['vpr', 'target'] if repeat % 2 == 0 else ['target', 'vpr']):
                self.summary['rows'].append(dict(case='example', variant=variant, repeat=repeat,
                    success=True, full_check=True, workflow_seconds=100 if variant == 'vpr' else 70,
                    critical_path_ns=10, wirelength=100))

    def test_every_pair_passes(self):
        result = evaluate(self.summary, self.protocol)
        self.assertEqual(result['status'], 'passed')
        self.assertTrue(result['not_a_scaling_crossover_claim'])

    def test_one_slow_repeat_rejects_good_median(self):
        self.summary['rows'][-1]['workflow_seconds'] = 101
        result = evaluate(self.summary, self.protocol)
        self.assertGreater(result['median_paired_workflow_speedup'], 1)
        self.assertEqual(result['status'], 'failed')

    def test_quality_limits_apply_to_each_metric_and_repeat(self):
        for key, value in [('critical_path_ns', 10.501), ('wirelength', 106)]:
            with self.subTest(metric=key):
                summary = copy.deepcopy(self.summary)
                summary['rows'][-1][key] = value
                self.assertEqual(evaluate(summary, self.protocol)['status'], 'failed')

    def test_failed_or_unchecked_attempt_is_retained(self):
        for key in ['success', 'full_check']:
            with self.subTest(flag=key):
                summary = copy.deepcopy(self.summary)
                summary['rows'][-1][key] = False
                result = evaluate(summary, self.protocol)
                self.assertEqual(result['status'], 'failed')
                self.assertEqual(len(result['pairs']), 3)

    def test_incomplete_reordered_or_nonfinite_records_are_rejected(self):
        mutations = [lambda s: s.update(status='running'),
                     lambda s: s['rows'].reverse(),
                     lambda s: s['rows'].pop(),
                     lambda s: s['rows'][-1].update(workflow_seconds=float('nan')),
                     lambda s: s['protocol'].update(congestion_mode='subtree')]
        for mutate in mutations:
            summary = copy.deepcopy(self.summary)
            mutate(summary)
            with self.assertRaises(ValueError):
                evaluate(summary, self.protocol)


if __name__ == '__main__':
    unittest.main()
