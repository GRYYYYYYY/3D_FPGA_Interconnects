"""Submit one frozen joint confirmation job; preserve unique receipts, no retry."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shlex
import subprocess
from prepare import sha256,write_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--record',type=Path,required=True);p.add_argument('--minutes',type=int,default=180);args=p.parse_args()
    root=Path(__file__).resolve().parents[1];bundle=args.bundle.resolve();frozen=json.loads((bundle/'bindings.json').read_text())
    if any(sha256(bundle/k)!=v for k,v in frozen['files'].items()):raise RuntimeError('Bundle checksum mismatch')
    name='h3d-native-joint-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S');receipt=root/'results/inspire'/name;receipt.mkdir(parents=True)
    output=bundle.parent/(name+'-output');helper='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/skills/inspire-gpu-submit/scripts/inspire_gpu.py'
    manifest=json.loads((root/'jobs/h100_target_confirm_subtree_20261027-221003.json').read_text())
    with (receipt/'resources.json').open('w') as f:subprocess.run(['python3',helper,'resources','--workspace-id',manifest['workspace_id'],'--project-id',manifest['project_id'],'--logic-compute-group-id',manifest['logic_compute_group_id'],'--images'],stdout=f,check=True)
    manifest.update(name=name,command=shlex.join(['python3','-B',str(bundle/'scripts/bootstrap_native_diagnostics.py'),'--bundle',str(bundle),'--output',str(output),'--joint-confirmation']),
                    max_running_time_ms=str(args.minutes*60000),description='Native joint confirmation: 1 H100, same four physical CPU cores for original_parallel/native_parallel/guard/batch including GPU service threads; GEMM 3 rotated repetitions, elliptic 1 qualification then 2 if all legal and within 5%. Diagnostic events/capture/replay disabled. Preserve all failures.')
    path=root/'jobs'/(name+'.json');write_json(path,manifest)
    pointer={'name':name,'manifest':str(path),'bundle':str(bundle),'bundle_bindings_sha256':sha256(bundle/'bindings.json'),'output':str(output),'receipt':str(receipt),'status':'prepared'}
    write_json(args.record,pointer);write_json(receipt/'run.json',pointer)
    with (receipt/'validate.json').open('w') as f:subprocess.run(['python3',helper,'validate',str(path)],stdout=f,check=True)
    with (receipt/'submit.json').open('w') as f,(receipt/'submit.stderr').open('w') as e:r=subprocess.run(['python3',helper,'submit',str(path),'--confirm'],stdout=f,stderr=e)
    if r.returncode:raise RuntimeError('Submission outcome uncertain; reconcile unique name '+name+' before any further CreateJob')
    pointer.update(job_id=json.loads((receipt/'submit.json').read_text())['submission']['Result']['job_id'],status='submitted')
    write_json(args.record,pointer);write_json(receipt/'run.json',pointer);print(json.dumps(pointer),flush=True)
    with (receipt/'status.json').open('w') as f:subprocess.run(['python3',helper,'status',pointer['job_id']],stdout=f,check=True)


if __name__=='__main__':main()
