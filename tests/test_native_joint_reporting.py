from copy import deepcopy
from pathlib import Path
import sys
import json
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from report_native_joint import compare,repeated_claim,log_evidence


def row(variant,seconds=10,repeat=0):
    return {'case':'gemm','repeat':repeat,'variant':variant,'success':True,'diagnostic':False,
            'execution_settings':{'gpu_timing':'0','diagnostics':'0','capture':False,'cpu_affinity':[0,1,2,3]},
            'command':['vpr','--num_workers','4','--router_algorithm','parallel'],
            'cpu_budget_audit':{'permitted_cpu_set':[0,1,2,3],'verified':True,'affinity_violations':[]},
            'full_check':True,'independent_metrics':{'full_check':True},'independent_check':{'cpu_budget_audit':{'verified':True}},
            'hybrid':{'gpu_initialized':variant=='batch','committed':10 if variant=='batch' else 0},
            'native_process_seconds':seconds,'workflow_seconds':seconds+2,'critical_path_ns':10,'wirelength':100}


class JointReporting(unittest.TestCase):
    def test_joint_gain_does_not_require_guard_or_gpu_incremental_win(self):
        values=[]
        for repeat in range(3):
            original=row('original_parallel',10,repeat);cpu=row('native_parallel',7,repeat);gpu=row('batch',8,repeat)
            values.extend([compare(original,gpu),compare(cpu,gpu)])
        self.assertTrue(repeated_claim(values)['positive_joint_candidate'])
    def test_single_thread_baseline_rejected(self):
        original=row('original_parallel');original['command'][2]='1'
        self.assertFalse(compare(original,row('batch',8))['eligible'])
    def test_cpu_affinity_difference_rejected(self):
        gpu=row('batch',8);gpu['cpu_budget_audit']['permitted_cpu_set']=[4,5,6,7];gpu['execution_settings']['cpu_affinity']=[4,5,6,7]
        self.assertIn('different_cpu_sets',compare(row('original_parallel'),gpu)['reasons'])
    def test_failed_diagnostic_and_no_gpu_results_rejected(self):
        for key,value in [('success',False),('diagnostic',True),('hybrid',{'gpu_initialized':True,'committed':0})]:
            gpu=row('batch',8);gpu[key]=value;self.assertFalse(compare(row('original_parallel'),gpu)['eligible'])
    def test_quality_failure_not_eligible(self):
        gpu=row('batch',8);gpu['wirelength']=106
        self.assertFalse(compare(row('original_parallel'),gpu)['eligible'])
    def test_faster_readback_alone_does_not_pass(self):
        values=[]
        for repeat in range(3):
            gpu=row('batch',11,repeat);gpu['workflow_seconds']=11
            values.append(compare(row('original_parallel',10,repeat),gpu))
        self.assertFalse(repeated_claim(values)['positive_joint_candidate'])
    def test_missing_or_duplicate_repeats_not_confirmation(self):
        value=compare(row('original_parallel'),row('batch',8))
        self.assertFalse(repeated_claim([value])['positive_joint_candidate'])
        self.assertFalse(repeated_claim([value,deepcopy(value),deepcopy(value)])['positive_joint_candidate'])
    def test_crash_last_iteration_is_not_a_final_congestion_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)
            (path/'process.log').write_text('  63    1.6  1000.0    0 3583325      61     204      30 ( 0.011%)\n')
            (path/'measurement.json').write_text(json.dumps({'status':'failed','returncode':-11,'routing_success':False}))
            evidence=log_evidence(path)
            self.assertEqual(evidence['last_observed_overused_nodes'],30)
            self.assertIsNone(evidence['final_overused_nodes'])
            self.assertIsNone(evidence['overuse_report'])
    def test_successful_zero_overuse_remains_final(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)
            (path/'process.log').write_text('  14    0.7  11.6    0 3583325      13     51      0 ( 0.000%)\n')
            (path/'measurement.json').write_text(json.dumps({'status':'completed','returncode':0,'routing_success':True}))
            self.assertEqual(log_evidence(path)['final_overused_nodes'],0)


if __name__=='__main__':unittest.main()
