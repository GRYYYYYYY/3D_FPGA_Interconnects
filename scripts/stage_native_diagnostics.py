"""Stage only diagnostic inputs in the platform-reported job work directory.

Does not submit a job. Originals are read-only. Every copy is SHA256 verified;
records preparation time separately from all VPR/GPU measurements.
"""
import argparse
import gzip
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from prepare import sha256,write_json
from scaling_common import verified


def main():
    p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True)
    p.add_argument('--reuse-inputs',type=Path,help='Hard-link verified immutable inputs from an existing frozen bundle on the same filesystem')
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1];dest=args.destination.resolve();dest.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter();copies=[];copied={}
    def copy(source,target,expected=None):
        source=Path(source).resolve();target=dest/target;target.parent.mkdir(parents=True,exist_ok=True)
        expected=expected or sha256(source);shutil.copyfile(source,target)
        if sha256(target)!=expected:raise RuntimeError('staging hash mismatch: '+str(source))
        copies.append({'source':str(source),'destination':str(target),'sha256':expected,'bytes':source.stat().st_size});copied[str(source)]=target
        return target
    for sub in ['native','scripts']:
        for f in sorted((root/sub).glob('*')):
            if f.is_file():copy(f,Path(sub)/f.name)
    copy(root/'build_native/vpr/vpr','vpr').chmod(0o755)
    vendor=root/'vendor/vtr_hybrid';(dest/'vpr.patch').write_bytes(subprocess.check_output(['git','-C',str(vendor),'diff','--binary','HEAD']))
    for rel in subprocess.check_output(['git','-C',str(vendor),'ls-files','--others','--exclude-standard'],text=True).splitlines():copy(vendor/rel,Path('vendor_extra')/rel)
    lock=json.loads((root.parent/'FPGA_accelerate_FPGA/G_3d_routing/configs/vpr.lock.json').read_text());b=lock['binary'];target=copy(verified(b),'baseline/vpr',b['sha256']);target.chmod(0o755);b['path']=str(target);write_json(dest/'vpr.lock.json',lock)
    runtime=json.loads((root/'data/vpr_runtime_20261025/runtime.json').read_text())
    for lib in runtime['libraries']:lib['path']=str(copy(verified(lib),Path('runtime')/Path(lib['path']).name,lib['sha256']))
    runtime['library_directory']=str(dest/'runtime');write_json(dest/'runtime/runtime.json',runtime)
    suite=json.loads((root/'jobs/target_suite_20261027.json').read_text());cases=[]
    for name in ['elliptic','gemm']:
        item=next(c for c in suite['cases'] if c['id']==name);case=json.loads(Path(item['vpr_case']).read_text())
        previous=json.loads((args.reuse_inputs/'inputs'/name/'vpr_case.json').read_text()) if args.reuse_inputs else None
        for role,r in case['inputs'].items():
            src=verified(r);relative=Path('inputs')/name/(role+'_'+src.name)
            if previous:
                old=previous['inputs'][role]
                if old['sha256']!=r['sha256']:raise RuntimeError('Reused input differs from frozen source')
                compressed='compressed_path' in old
                source=Path(old['compressed_path'] if compressed else old['path'])
                expected=old['compressed_sha256'] if compressed else old['sha256']
                if sha256(source)!=expected:raise RuntimeError('Reused input checksum mismatch')
                target=dest/(str(relative)+'.gz' if compressed else relative);target.parent.mkdir(parents=True,exist_ok=True)
                os.link(source,target)
                r['path']=str(dest/relative)
                if compressed:r.update(compressed_path=str(target),compressed_sha256=expected)
                copies.append({'source':str(src),'destination':str(target),'sha256':r['sha256'],'bytes':src.stat().st_size,
                               'stored_bytes':target.stat().st_size,'hardlinked_from':str(source),'stored_sha256':expected})
                continue
            if src.stat().st_size>64*1024*1024:
                target=dest/(str(relative)+'.gz');target.parent.mkdir(parents=True,exist_ok=True)
                with src.open('rb') as inp,gzip.open(target,'wb',compresslevel=1) as output:shutil.copyfileobj(inp,output,8*1024*1024)
                r.update(path=str(dest/relative),compressed_path=str(target),compressed_sha256=sha256(target))
                copies.append({'source':str(src),'destination':str(target),'sha256':r['sha256'],'compressed_sha256':r['compressed_sha256'],'bytes':src.stat().st_size,'stored_bytes':target.stat().st_size})
            else:r['path']=str(copied.get(str(src)) or copy(src,relative,r['sha256']))
        case_path=dest/'inputs'/name/'vpr_case.json';write_json(case_path,case);cases.append({'id':name,'vpr_case':str(case_path)})
    write_json(dest/'suite.json',{'cases':cases})
    for source,sub in [(root/'results/hybrid_native_state_capture_20261027/ex5p/queries','legacy_oracle'),(root/'results/native_diagnostics_20261029/cpu_capture_v2/ex5p_0_capture/takeovers','takeover_oracle')]:
        for f in sorted(source.iterdir()):
            if f.is_file():copy(f,Path(sub)/f.name)
    write_json(dest/'staging.json',{'created_at':datetime.now(timezone.utc).isoformat(),'seconds':time.perf_counter()-tick,'bytes':sum(c['bytes'] for c in copies),'copies':copies,'purpose':'GPU worker cannot see global_user; selective verified copies only; not an SSD experiment'})
    files={str(f.relative_to(dest)):sha256(f) for f in dest.rglob('*') if f.is_file()}
    write_json(dest/'bindings.json',{'base_commit':'0b912334fdd83bb754b302146ac0d1ec9edc9a0e','files':files})
    print(json.dumps({'bundle':str(dest),'files':len(files),'staging_seconds':time.perf_counter()-tick}),flush=True)


if __name__=='__main__':main()
