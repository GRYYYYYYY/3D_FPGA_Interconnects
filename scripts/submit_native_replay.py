"""One explicit submission, with frozen source and live resource validation.

Never retries CreateJob. A nonzero/ambiguous response must be reconciled using
the unique job name before any subsequent submission.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import shutil
import subprocess


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--capture',type=Path,action='append',required=True)
    parser.add_argument('--resident',action='store_true')
    parser.add_argument('--cooperative-blocks',type=int,default=0)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    helper=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/skills/inspire-gpu-submit/scripts/inspire_gpu.py')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S');name='h3d-native-replay-'+stamp
    frozen=root/'results'/('hybrid_replay_source_'+stamp);frozen.mkdir()
    for sub in ['native','scripts']:shutil.copytree(root/sub,frozen/sub,ignore=shutil.ignore_patterns('__pycache__'))
    receipt=root/'results/inspire'/name;receipt.mkdir(parents=True)
    manifest=json.loads((root/'jobs/h100_target_confirm_subtree_20261027-221003.json').read_text())
    with (receipt/'resources.json').open('w') as out:
        subprocess.run(['python3',str(helper),'resources','--workspace-id',manifest['workspace_id'],'--project-id',manifest['project_id'],
                        '--logic-compute-group-id',manifest['logic_compute_group_id'],'--images'],stdout=out,check=True)
    command=['python3',str(frozen/'scripts/run_native_replay.py'),'--source',str(frozen/'native')]
    if args.resident:command+=['--resident']
    if args.cooperative_blocks:command+=['--cooperative-blocks',str(args.cooperative_blocks)]
    for capture in args.capture:
        capture=capture.resolve()
        if not (capture/'graph.bin').exists() or not list(capture.glob('query_*.bin')):raise RuntimeError('incomplete capture')
        command+=['--capture',str(capture)]
    command+=['--output',str(root/'results'/name)]
    manifest.update(name=name,command=shlex.join(command),max_running_time_ms='1200000',
                    description='Native VPR query replay diagnostics; CPU/CUDA same snapshots, batch1/8, 3 repetitions, path/cost validation; no end-to-end speedup claim. One H100, maximum20min.')
    if args.resident:manifest['description']='Resident native-cost CUDA engine oracle: sparse state transitions, lazy labels, native lookahead; 1/4 duplicate-slot isolation checks, 3 repetitions, native path/cost validation. Not a routing speedup benchmark. 1H100 maximum20min.'
    path=root/'jobs'/(name+'.json');path.write_text(json.dumps(manifest,indent=2)+'\n')
    pointer={'name':name,'manifest':str(path),'source':str(frozen),'output':str(root/'results'/name),'receipt':str(receipt),'status':'prepared'}
    pointer_path=root/'results/hybrid_replay_run.json'
    if pointer_path.exists():shutil.copyfile(pointer_path,receipt/'previous_run.json')
    pointer_path.write_text(json.dumps(pointer,indent=2)+'\n')
    with (receipt/'validate.json').open('w') as out:
        subprocess.run(['python3',str(helper),'validate',str(path)],stdout=out,check=True)
    with (receipt/'submit.json').open('w') as out,(receipt/'submit.stderr').open('w') as err:
        submitted=subprocess.run(['python3',str(helper),'submit',str(path),'--confirm'],stdout=out,stderr=err)
    if submitted.returncode:raise RuntimeError(f'Submission outcome requires reconciliation: {name}; do not retry automatically')
    response=json.loads((receipt/'submit.json').read_text())
    pointer['job_id']=response['submission']['Result']['job_id'];pointer['status']='submitted'
    pointer_path.write_text(json.dumps(pointer,indent=2)+'\n')
    print(json.dumps(pointer),flush=True)
    with (receipt/'status.json').open('w') as out:
        subprocess.run(['python3',str(helper),'status',pointer['job_id']],stdout=out,check=True)


if __name__=='__main__':main()
