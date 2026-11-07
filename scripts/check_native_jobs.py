"""Bounded observation of submitted native experiments; never submits/restarts.

Terminal platform receipts are retained. A missing or incomplete summary is not
treated as job termination. Invoke periodically rather than running a busy loop.
"""
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

from prepare import write_json


def main():
    root=Path(__file__).resolve().parents[1]
    helper=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/skills/inspire-gpu-submit/scripts/inspire_gpu.py')
    terminal={'job_succeeded','job_failed','job_stopped','job_deleted'}
    rows=[]
    for receipt in sorted((root/'results/inspire').glob('h3d-native-*')):
        submitted=receipt/'submit.json'
        if not submitted.exists():continue
        response=json.loads(submitted.read_text())
        job=response.get('submission',{}).get('Result',{}).get('job_id')
        if not job:continue
        status_path=receipt/'status.json'
        cached=json.loads(status_path.read_text()) if status_path.exists() else {}
        state=cached.get('Result',{}).get('status')
        observation_error=None
        if state not in terminal:
            result=subprocess.run(['python3',str(helper),'status',job],capture_output=True,text=True,timeout=45)
            if result.returncode:
                observation_error=result.stderr[:500]
            else:
                current=json.loads(result.stdout);state=current['Result']['status'];status_path.write_text(result.stdout)
        row={'name':receipt.name,'job_id':job,'platform_status':state,'observation_error':observation_error,
             'status_receipt':str(status_path),'terminal':state in terminal}
        summary=root/'results'/receipt.name/'summary.json'
        if summary.exists():
            data=json.loads(summary.read_text());row.update(summary=str(summary),experiment_status=data['status'],error=data.get('error'))
            if 'measurements' in data:
                row['measurements']=[{key:item.get(key) for key in ['case','variant','success','status','native_process_seconds','diagnostic']} for item in data['measurements']]
            if not row['terminal']:print(receipt.name,state,data['status'],row.get('measurements',[])[-1:] if row.get('measurements') else '',flush=True)
        rows.append(row)
    write_json(root/'results/native_job_registry.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'jobs':rows})


if __name__=='__main__':main()
