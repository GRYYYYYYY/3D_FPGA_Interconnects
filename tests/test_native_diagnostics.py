import csv
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from report_native_diagnostics import batch_observation,summarize,replay_comparison


def write(path,items):
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)


class Diagnostics(unittest.TestCase):
    def test_shared_batch_cost_counted_once(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);q={'batch_id':1,'mode':'batch','ran':1,'failed':0,'state_prepare_ns':100}
            write(d/'hybrid.json.queries.csv',[q,q])
            write(d/'hybrid.json.batches.csv',[{'batch_id':1,'size':2,'search_kernel_event_ns':1000,'execute_call_ns':2000}])
            r=summarize(d)
            self.assertEqual(r['unique_batch_seconds']['search_kernel_event_ns'],1e-6)
            self.assertEqual(r['query_host_seconds']['state_prepare_ns'],2e-7)
            self.assertEqual(r['batch_observation_counts'],{'multiple_ready_queries':1})
    def test_truncated_csv_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);(d/'hybrid.json.batches.csv').write_text('batch_id,size,execute_call_ns\n1,1\n')
            with self.assertRaisesRegex(ValueError,'incomplete CSV'):summarize(d)
    def test_duplicate_batch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);b={'batch_id':1,'size':1};write(d/'hybrid.json.batches.csv',[b,b])
            with self.assertRaisesRegex(ValueError,'duplicate'):summarize(d)
    def test_missing_queries_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);write(d/'hybrid.json.batches.csv',[{'batch_id':1,'size':2}])
            with self.assertRaisesRegex(ValueError,'membership'):summarize(d)
    def test_mixed_scheduler_evidence_not_one_invented_cause(self):
        b={'size':1,'active_partitions':1,'queued_partitions':0,'branch_parents':1,'lease_waiters':2}
        self.assertEqual(batch_observation(b),['single_parent_partition_with_children_unreleased','ownership_waiters_present'])
    def test_singleton_does_not_prove_dependencies(self):
        self.assertEqual(batch_observation({'size':1}),['insufficient_ready_queries_at_deadline_unresolved'])
    def test_replay_cannot_hide_missing_or_duplicate_repetitions(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);write(d/'takeover_0.native.csv',[{'repeat':i} for i in range(3)])
            for repeats in [[-1,0,1],[-1,0,0,2]]:
                data=[{'repeat':str(i),'sequence':'0','valid':'1'} for i in repeats]
                with self.assertRaisesRegex(ValueError,'GPU repetitions'):replay_comparison(d,data)
    def test_replay_must_cover_all_native_snapshots(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);write(d/'takeover_0.native.csv',[{'repeat':0}]);write(d/'takeover_1.native.csv',[{'repeat':0}])
            with self.assertRaisesRegex(ValueError,'coverage'):replay_comparison(d,[{'sequence':'0'}])


if __name__=='__main__':unittest.main()
