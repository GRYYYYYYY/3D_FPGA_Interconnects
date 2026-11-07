"""Decompress verified inputs on the worker; archive all outcomes back to GPFS.

The original and candidate use identical worker-local input paths. Storage is
recorded, without claiming SSD/NVMe. Live small logs survive a process failure.
"""
import argparse
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from prepare import sha256,write_json


def mirror_small_files(run,output):
    """Telemetry failures must not terminate the active experiment."""
    errors=[]
    try:files=list(run.rglob('*')) if run.exists() else []
    except OSError as e:return [{'path':str(run),'error':repr(e)}]
    for f in files:
        temporary=None
        try:
            if not f.is_file() or f.stat().st_size>8*1024*1024 or f.suffix not in ['.json','.csv','.log','.rpt']:continue
            dest=output/'live'/f.relative_to(run);dest.parent.mkdir(parents=True,exist_ok=True)
            temporary=dest.with_name(dest.name+'.mirror_tmp');shutil.copyfile(f,temporary);temporary.replace(dest)
        except OSError as e:
            errors.append({'path':str(f),'error':repr(e)})
            if temporary is not None:
                try:temporary.unlink(missing_ok=True)
                except OSError:pass
    return errors


def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cases',default='elliptic,gemm');p.add_argument('--variants',default='original_vpr,pair,batch')
    p.add_argument('--pair-stride',type=int,default=1);p.add_argument('--capture-limit',type=int,default=32);p.add_argument('--capture-stride',type=int,default=5)
    p.add_argument('--joint-confirmation',action='store_true')
    p.add_argument('--repair-validation',action='store_true')
    p.add_argument('--lookahead-confirmation',action='store_true')
    p.add_argument('--output-reserve-mib',type=int)
    args=p.parse_args()
    bundle=args.bundle.resolve();out=args.output.resolve();out.mkdir(exist_ok=False)
    local=Path(tempfile.mkdtemp(prefix='h3d_native_diagnostics_'));run=local/'run';record={'status':'preparing','local_directory':str(local),'bundle':str(bundle)}
    write_json(out/'bootstrap.json',record);start=time.perf_counter()
    reserve=out/'.archive-reserve';emergency=out/'.metadata-reserve'
    def mirror():
        errors=mirror_small_files(run,out)
        if errors:
            record['mirror_error_count']=record.get('mirror_error_count',0)+len(errors)
            record['last_mirror_errors']=errors[:10]
            print('Live mirror errors; solver continues: '+json.dumps(errors[:2]),flush=True)
    try:
        reserve_mib=args.output_reserve_mib if args.output_reserve_mib is not None else (1024 if args.joint_confirmation else 0)
        if reserve_mib:
            with reserve.open('wb') as f:os.posix_fallocate(f.fileno(),0,reserve_mib*1024*1024)
            with emergency.open('wb') as f:os.posix_fallocate(f.fileno(),0,64*1024)
            record['reserved_archive_bytes']=reserve_mib*1024*1024
        frozen=json.loads((bundle/'bindings.json').read_text())
        if any(sha256(bundle/k)!=v for k,v in frozen['files'].items()):raise RuntimeError('frozen input/source checksum mismatch')
        suite=json.loads((bundle/'suite.json').read_text())
        suite['cases']=[c for c in suite['cases'] if c['id'] in args.cases.split(',')]
        for c in suite['cases']:
            case=json.loads(Path(c['vpr_case']).read_text());directory=local/'inputs'/c['id'];directory.mkdir(parents=True)
            for role,r in case['inputs'].items():
                # All actual inputs are local for both CPU baseline and hybrid.
                dest=directory/Path(r['path']).name
                if 'compressed_path' in r:
                    with gzip.open(r['compressed_path'],'rb') as inp,dest.open('wb') as f:shutil.copyfileobj(inp,f,8*1024*1024)
                else:shutil.copyfile(r['path'],dest)
                if sha256(dest)!=r['sha256']:raise RuntimeError('unpacked input hash mismatch')
                r['path']=str(dest)
            c['vpr_case']=str(directory/'vpr_case.json');write_json(Path(c['vpr_case']),case)
        write_json(local/'suite.json',suite)
        record.update(status='running',input_prepare_seconds=time.perf_counter()-start,storage=subprocess.check_output(['findmnt','-T',str(local)],text=True))
        write_json(out/'bootstrap.json',record)
        command=[sys.executable,str(bundle/'scripts/run_native_diagnostics.py'),'--bundle',str(bundle),'--suite',str(local/'suite.json'),'--output',str(run),'--cases',args.cases,'--variants',args.variants,'--pair-stride',str(args.pair_stride),'--capture-limit',str(args.capture_limit),'--capture-stride',str(args.capture_stride)]
        if args.joint_confirmation:
            command=[sys.executable,'-B',str(bundle/'scripts/run_native_joint_confirmation.py'),'--bundle',str(bundle),'--suite',str(local/'suite.json'),'--output',str(run)]
        if args.repair_validation:
            command=[sys.executable,'-B',str(bundle/'scripts/run_native_repair_validation.py'),'--bundle',str(bundle),'--suite',str(local/'suite.json'),'--output',str(run)]
        if args.lookahead_confirmation:
            command=[sys.executable,'-B',str(bundle/'scripts/run_native_lookahead_confirmation.py'),'--bundle',str(bundle),'--suite',str(local/'suite.json'),'--output',str(run)]
        with (out/'worker.log').open('w') as log:
            proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
            while True:
                try:rc=proc.wait(timeout=30);break
                except subprocess.TimeoutExpired:mirror()
        record['returncode']=rc;record['status']='completed' if rc==0 else 'failed'
    except Exception as e:record.update(status='failed',error=repr(e));raise
    finally:
        mirror()
        reserve.unlink(missing_ok=True)
        if run.exists():
            archive=out/'artifacts.tar.gz';partial=out/'artifacts.tar.gz.partial';tick=time.perf_counter()
            try:
                with tarfile.open(partial,'w:gz',compresslevel=1) as tar:tar.add(run,arcname='run')
                partial.replace(archive)
                record.update(archive=str(archive),archive_sha256=sha256(archive),archive_seconds=time.perf_counter()-tick)
            except OSError as e:
                record.update(status='failed',archive_error=repr(e),partial_archive=str(partial));print('Archive failed: '+repr(e),flush=True)
        emergency.unlink(missing_ok=True)
        record['elapsed_seconds']=time.perf_counter()-start;write_json(out/'bootstrap.json',record)
    if record.get('returncode',1) or record['status']!='completed':raise SystemExit(record.get('returncode') or 1)


if __name__=='__main__':main()
