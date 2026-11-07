"""Freeze and submit one native CPU/GPU routing experiment; never retry CreateJob."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shlex
import shutil
import subprocess
from prepare import sha256


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--binary',type=Path,default=Path('build_native/vpr/vpr'))
    p.add_argument('--library',type=Path,required=True)
    p.add_argument('--cases',default='ex5p')
    p.add_argument('--variants',default='original_vpr,native_cpu,pair,hybrid')
    p.add_argument('--budget',type=int,default=2048)
    p.add_argument('--max-offloads',type=int)
    p.add_argument('--pair-limit',type=int)
    p.add_argument('--pair-stride',type=int,default=1)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--batch-size',type=int,default=4)
    p.add_argument('--batch-wait-us',type=int,default=50)
    p.add_argument('--cooperative-blocks',type=int,default=0)
    p.add_argument('--verify-state',action='store_true')
    p.add_argument('--diagnostics',action='store_true')
    p.add_argument('--capture-limit',type=int,default=0)
    p.add_argument('--capture-stride',type=int,default=5)
    p.add_argument('--native-repeats',type=int,default=3)
    p.add_argument('--timeout',type=float,default=900)
    p.add_argument('--repeats',type=int,default=1)
    p.add_argument('--minutes',type=int,default=30)
    args=p.parse_args();root=Path(__file__).resolve().parents[1]
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S');name='h3d-native-hybrid-'+stamp
    frozen=root/'results'/('native_hybrid_source_'+stamp);frozen.mkdir();receipt=root/'results/inspire'/name;receipt.mkdir(parents=True)
    for sub in ['scripts','native']:shutil.copytree(root/sub,frozen/sub,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copyfile(args.binary.resolve(),frozen/'vpr');(frozen/'vpr').chmod(0o755)
    shutil.copyfile(args.library.resolve(),frozen/'libh3d_native_gpu.so')
    # The supplied CUDA library may deliberately be an earlier engine. Preserve
    # its actual build inputs separately from current native host headers/code.
    library_summary=args.library.resolve().parent/'summary.json'
    if not library_summary.exists():raise RuntimeError('CUDA library requires its completed replay build summary')
    provenance=json.loads(library_summary.read_text())
    if provenance.get('status')!='completed':raise RuntimeError('CUDA replay validation has not completed')
    for original,expected in provenance['source'].items():
        path=Path(original)
        if sha256(path)!=expected:raise RuntimeError('CUDA build source changed')
        destination=frozen/'library_source'/path.name;destination.parent.mkdir(exist_ok=True);shutil.copyfile(path,destination)
    (frozen/'library_provenance.json').write_text(json.dumps({
        'summary':str(library_summary),'summary_sha256':sha256(library_summary),
        'library_sha256':sha256(args.library.resolve()),'build_source':provenance['source'],
        'compile':provenance['compile'],'validated_cases':provenance['cases']},indent=2)+'\n')
    vendor=root/'vendor/vtr_hybrid'
    patch=subprocess.check_output(['git','-C',str(vendor),'diff','--binary','HEAD'])
    (frozen/'vpr.patch').write_bytes(patch)
    files=subprocess.check_output(['git','-C',str(vendor),'ls-files','--others','--exclude-standard'],text=True).splitlines()
    for rel in files:
        destination=frozen/'vendor_extra'/rel;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(vendor/rel,destination)
    bindings={str(f.relative_to(frozen)):sha256(f) for f in frozen.rglob('*') if f.is_file()}
    (frozen/'bindings.json').write_text(json.dumps({'base_commit':'0b912334fdd83bb754b302146ac0d1ec9edc9a0e','files':bindings},indent=2)+'\n')
    manifest=json.loads((root/'jobs/h100_target_confirm_subtree_20261027-221003.json').read_text())
    helper='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/skills/inspire-gpu-submit/scripts/inspire_gpu.py'
    with (receipt/'resources.json').open('w') as out:
        subprocess.run(['python3',helper,'resources','--workspace-id',manifest['workspace_id'],'--project-id',manifest['project_id'],
                        '--logic-compute-group-id',manifest['logic_compute_group_id'],'--images'],stdout=out,check=True)
    command=['python3',str(frozen/'scripts/run_native_hybrid.py'),'--binary',str(frozen/'vpr'),'--library',str(frozen/'libh3d_native_gpu.so'),
             '--suite',str(root/'jobs/target_suite_20261027.json'),'--runtime',str(root/'data/vpr_runtime_20261025/runtime.json'),
             '--vpr-lock',str(root.parent/'FPGA_accelerate_FPGA/G_3d_routing/configs/vpr.lock.json'),'--output',str(root/'results'/name),
             '--cases',args.cases,'--variants',args.variants,'--budget',str(args.budget),'--repeats',str(args.repeats),
             '--workers',str(args.workers),'--batch-size',str(args.batch_size),'--batch-wait-us',str(args.batch_wait_us),'--timeout',str(args.timeout),'--pair-stride',str(args.pair_stride),'--cooperative-blocks',str(args.cooperative_blocks)]
    if args.max_offloads is not None:command+=['--max-offloads',str(args.max_offloads)]
    if args.pair_limit is not None:command+=['--pair-limit',str(args.pair_limit)]
    if args.verify_state:command+=['--verify-state']
    if args.diagnostics:command+=['--diagnostics']
    command+=['--capture-limit',str(args.capture_limit),'--capture-stride',str(args.capture_stride),'--native-repeats',str(args.native_repeats)]
    manifest.update(name=name,command=shlex.join(command),max_running_time_ms=str(args.minutes*60000),
        description='VPR-native hybrid pilot. Original VPR/native CPU/paired native snapshots/selective GPU. Native timing, tree commit and FULL checks retained; independent locked-original readback for all variants. Single H100. Frozen source and binaries.')
    path=root/'jobs'/(name+'.json');path.write_text(json.dumps(manifest,indent=2)+'\n')
    pointer={'name':name,'source':str(frozen),'manifest':str(path),'receipt':str(receipt),'output':str(root/'results'/name),'status':'prepared'}
    pointer_file=root/'results/native_hybrid_run.json'
    if pointer_file.exists():shutil.copyfile(pointer_file,receipt/'previous_run.json')
    pointer_file.write_text(json.dumps(pointer,indent=2)+'\n')
    with (receipt/'validate.json').open('w') as out:subprocess.run(['python3',helper,'validate',str(path)],stdout=out,check=True)
    with (receipt/'submit.json').open('w') as out,(receipt/'submit.stderr').open('w') as err:
        result=subprocess.run(['python3',helper,'submit',str(path),'--confirm'],stdout=out,stderr=err)
    if result.returncode:raise RuntimeError(f'Submission outcome requires reconciliation by unique name {name}; do not retry automatically')
    response=json.loads((receipt/'submit.json').read_text());pointer['job_id']=response['submission']['Result']['job_id'];pointer['status']='submitted'
    pointer_file.write_text(json.dumps(pointer,indent=2)+'\n');print(json.dumps(pointer),flush=True)
    with (receipt/'status.json').open('w') as out:subprocess.run(['python3',helper,'status',pointer['job_id']],stdout=out,check=True)


if __name__=='__main__':main()
