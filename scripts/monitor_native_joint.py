"""One bounded, read-only observation of a known joint experiment job."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from prepare import write_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--fresh',action='store_true');args=p.parse_args()
    pointer=json.loads(args.record.read_text());base=args.record.parent;receipt=Path(pointer['receipt']);status_path=receipt/'status.json'
    status_error=None
    if args.fresh or not status_path.exists() or time.time()-status_path.stat().st_mtime>300:
        helper='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/skills/inspire-gpu-submit/scripts/inspire_gpu.py'
        result=subprocess.run(['python3',helper,'status',pointer['job_id']],capture_output=True,text=True,timeout=45)
        if result.returncode==0:
            state=json.loads(result.stdout);write_json(status_path,state)
        else:status_error=result.stderr.strip()
    status=json.loads(status_path.read_text())['Result'] if status_path.exists() else {}
    out=Path(pointer['output']);observation={'observed_utc':datetime.now(timezone.utc).isoformat(),'job_id':pointer['job_id'],
        'platform_status':status.get('status'),'status_age_seconds':round(time.time()-status_path.stat().st_mtime,1) if status_path.exists() else None,'status_query_error':status_error,'completed':[],'active':[]}
    for name in ['elliptic_initial','elliptic_repeats','gemm','gemm_cpu_control']:
        path=out/'live'/name/'summary.json'
        if not path.exists():continue
        try:data=json.loads(path.read_text())
        except json.JSONDecodeError:continue
        for row in data['measurements']:
            item={k:row.get(k) for k in ['case','repeat','variant','success','native_process_seconds','workflow_seconds','critical_path_ns','wirelength']}
            if row.get('workflow_seconds') is not None:
                item['affinity_verified']=row.get('cpu_budget_audit',{}).get('verified');observation['completed'].append(item)
            else:
                directory=path.parent/Path(row['directory']).name
                logs=[f for f in [directory/'process.log',directory/'independent_check.log'] if f.exists()]
                if logs:
                    log=logs[-1];payload=log.read_bytes();text=payload.decode(errors='replace')
                    item.update(log=log.name,mirror_age_seconds=round(time.time()-log.stat().st_mtime,1),
                                content_sha256=hashlib.sha256(payload).hexdigest(),tail=text[-350:])
                    item['freshness_note']='mtime is the live mirror write time, not solver progress; compare content and iterations.'
                    stages=re.findall(r'^.*(?:took|Routing failed|VPR succeeded).*$',text,re.M)
                    item['last_timing_line']=stages[-1] if stages else None
                    iterations=re.findall(r'^\s*(\d+)\s+[\d.]+\s+[\d.eE+-]+\s+\d+\s+[\d.eE+]+\s+\d+\s+\d+\s+(\d+)\s+\(',text,re.M)
                    if iterations and log.name=='process.log':
                        item['last_timing_line']=(item['last_timing_line'] or '')+f' [latest routing iteration {iterations[-1][0]}, overused {iterations[-1][1]}]'
                observation['active'].append(item)
    bootstrap=out/'bootstrap.json'
    if bootstrap.exists():
        try:observation['bootstrap']=json.loads(bootstrap.read_text())['status']
        except json.JSONDecodeError:pass
    write_json(base/'live_status.json',observation)
    with (base/'progress.jsonl').open('a') as f:f.write(json.dumps(observation)+'\n')
    print(json.dumps(observation))


if __name__=='__main__':main()
