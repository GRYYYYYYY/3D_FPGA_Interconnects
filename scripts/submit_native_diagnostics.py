"""Submit one staged diagnostic job, with fresh resources and no retries."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shlex
import subprocess
from prepare import sha256,write_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--minutes',type=int,default=75)
    p.add_argument('--cases',default='elliptic,gemm');p.add_argument('--variants',default='original_vpr,pair,batch')
    p.add_argument('--pair-stride',type=int,default=1);p.add_argument('--capture-limit',type=int,default=32);p.add_argument('--capture-stride',type=int,default=5)
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1];bundle=args.bundle.resolve();bindings=json.loads((bundle/'bindings.json').read_text())
    if any(sha256(bundle/k)!=v for k,v in bindings['files'].items()):raise RuntimeError('bundle changed before submission')
    name='h3d-native-diagnostics-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    receipt=root/'results/inspire'/name;receipt.mkdir(parents=True);output=bundle.parent/(name+'-output')
    helper='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/skills/inspire-gpu-submit/scripts/inspire_gpu.py'
    manifest=json.loads((root/'jobs/h100_target_confirm_subtree_20261027-221003.json').read_text())
    with (receipt/'resources.json').open('w') as f:subprocess.run(['python3',helper,'resources','--workspace-id',manifest['workspace_id'],'--project-id',manifest['project_id'],'--logic-compute-group-id',manifest['logic_compute_group_id'],'--images'],stdout=f,check=True)
    manifest.update(name=name,command=shlex.join(['python3','-B',str(bundle/'scripts/bootstrap_native_diagnostics.py'),'--bundle',str(bundle),'--output',str(output),'--cases',args.cases,'--variants',args.variants,'--pair-stride',str(args.pair_stride),'--capture-limit',str(args.capture_limit),'--capture-stride',str(args.capture_stride)]),
                    max_running_time_ms=str(args.minutes*60000),description=f'Native CPU/GPU diagnostics only. Cases={args.cases}; variants={args.variants}; pair_stride={args.pair_stride}; capture_limit={args.capture_limit}; fixed pre-outcome sampling. 1 H100. Same-state native CPU repeats, real GPU takeover replay and path checks; archive all failures. No cross-job speed ratios.')
    path=root/'jobs'/(name+'.json');write_json(path,manifest)
    pointer={'cases':args.cases,'variants':args.variants,'pair_stride':args.pair_stride,'capture_limit':args.capture_limit,'capture_stride':args.capture_stride,'name':name,'manifest':str(path),'bundle':str(bundle),'bundle_bindings_sha256':sha256(bundle/'bindings.json'),'output':str(output),'receipt':str(receipt),'status':'prepared'}
    write_json(receipt/'run.json',pointer);write_json(root/'results/native_diagnostics_20261029/run.json',pointer)
    with (receipt/'validate.json').open('w') as f:subprocess.run(['python3',helper,'validate',str(path)],stdout=f,check=True)
    with (receipt/'submit.json').open('w') as f,(receipt/'submit.stderr').open('w') as e:r=subprocess.run(['python3',helper,'submit',str(path),'--confirm'],stdout=f,stderr=e)
    if r.returncode:raise RuntimeError('Submission outcome uncertain; reconcile unique name '+name+'; do not retry CreateJob')
    pointer.update(job_id=json.loads((receipt/'submit.json').read_text())['submission']['Result']['job_id'],status='submitted')
    write_json(receipt/'run.json',pointer);write_json(root/'results/native_diagnostics_20261029/run.json',pointer);print(json.dumps(pointer),flush=True)
    with (receipt/'status.json').open('w') as f:subprocess.run(['python3',helper,'status',pointer['job_id']],stdout=f,check=True)


if __name__=='__main__':main()
