"""Advance already-authorized stages only after native gates pass; never retry."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

from prepare import write_json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_cpu_slices_20261101'


def now():
    return datetime.now(timezone.utc).isoformat()


def live_json(path):
    """The frozen legacy writer is non-atomic; retry a partial live read."""
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def wait_stage(stage):
    plan=json.loads((OUT/(stage+'_plan.json')).read_text())
    while True:
        complete=True
        for lane in plan['lanes']:
            path=Path(plan['output'])/lane/'summary.json'
            state=live_json(path)
            if state is None:complete=False;continue
            if state['status']=='failed':raise RuntimeError('Stage failed: '+stage+'/'+lane)
            if state['status']!='completed':complete=False;continue
            if not state.get('all_routes_successful'):raise RuntimeError('Native legality gate failed: '+stage+'/'+lane)
        supervisor=Path(plan['output'])/'supervisor.json'
        supervisor_state=live_json(supervisor)
        if supervisor_state is not None:
            status=supervisor_state['status']
            if status=='failed':raise RuntimeError('Supervisor failed: '+stage)
            complete &= status=='completed'
        else:complete=False
        if complete:return
        time.sleep(30)


def main():
    lock=OUT/'continuation.owner'
    with lock.open('x') as file:
        import os
        file.write(json.dumps({'pid':os.getpid(),'started_utc':now()})+'\n')
    receipt={'status':'running','started_utc':now(),'steps':[]}
    def save():
        receipt['observed_utc']=now();write_json(OUT/'continuation.json',receipt)
    def step(name,command):
        receipt['current']=name;save()
        print(json.dumps({'step':name,'command':command}),flush=True)
        result=subprocess.run(command,cwd=ROOT)
        receipt['steps'].append({'name':name,'command':command,'returncode':result.returncode,'finished_utc':now()});save()
        result.check_returncode()
    try:
        receipt['current']='wait_diagnostic_and_slice_gate';save()
        wait_stage('diagnostic');wait_stage('slice_gate')
        step('freeze_memory_config',[sys.executable,'scripts/report_native_cpu_slices.py','--partial','--memory-config'])
        for stage in ['storage_gate','confirmation']:
            step('freeze_'+stage,[sys.executable,'scripts/plan_native_cpu_slices.py',stage,'--binary',str(OUT/'bin/vpr_compact')])
            step('run_'+stage,[sys.executable,'scripts/supervise_native_cpu_slices.py','--plan',str(OUT/(stage+'_plan.json'))])
            wait_stage(stage)
            if stage=='storage_gate':
                step('small_regression',[sys.executable,'vendor/vtr_cpu_slices/vtr_flow/tasks/regression_tests/vtr_reg_strong/strong_native_lookahead_slices/check_native_results.py',str(OUT/'storage_gate/small')])
        step('final_analysis',[sys.executable,'scripts/report_native_cpu_slices.py'])
        receipt['status']='completed';receipt['current']='await_review_of_results';save()
    except Exception as error:
        receipt.update(status='needs_attention',error=str(error));save();raise


if __name__=='__main__':
    main()
