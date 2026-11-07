"""Same-worker four-core original/CPU/guard/joint confirmation, then elliptic."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from prepare import sha256,write_json
from scaling_common import run_process


VARIANTS=['original_parallel','native_parallel','guard','batch']


def legal_quality(summary):
    rows=summary['measurements'];original=next(r for r in rows if r['variant']=='original_parallel')
    if not original['success']:return False
    return all(r['success'] and r['critical_path_ns']<=1.05*original['critical_path_ns'] and
               r['wirelength']<=1.05*original['wirelength'] and not r.get('hybrid',{}).get('errors',0) for r in rows)


def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--suite',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    bundle=args.bundle.resolve();out=args.output.resolve();out.mkdir(exist_ok=False)
    env={k:v for k,v in os.environ.items() if not k.startswith(('VPR_HYBRID_','H3D_GPU_'))};env['PYTHONDONTWRITEBYTECODE']='1'
    record={'status':'running','scope':'Joint end-to-end comparison against original parallel VPR under equal four-core CPU affinity; GPU incremental gain is attribution, not an acceptance prerequisite.',
            'bundle':str(bundle),'variants':VARIANTS,'gemm_repeats':3,'elliptic_initial_repeats':1,'steps':[],
            'device':subprocess.check_output(['nvidia-smi'],text=True),'hostname':subprocess.check_output(['hostname'],text=True).strip()}
    write_json(out/'summary.json',record)
    def run(name,command,timeout):
        result=run_process(command,out,env,timeout,name+'.log');record['steps'].append({'name':name,**result});write_json(out/'summary.json',record)
        if result['returncode']:raise RuntimeError(name+' failed; see '+name+'.log')
    try:
        run('library_oracle',[sys.executable,'-B',str(bundle/'scripts/run_native_replay.py'),'--source',str(bundle/'native'),'--resident','--cooperative-blocks','64','--capture',str(bundle/'legacy_oracle'),'--output',str(out/'library')],600)
        library=out/'library/libh3d_native_gpu.so'
        def matrix(name,case,repeats,start=0):
            command=[sys.executable,'-B',str(bundle/'scripts/run_native_hybrid.py'),'--binary',str(bundle/'vpr'),'--library',str(library),
                     '--suite',str(args.suite),'--runtime',str(bundle/'runtime/runtime.json'),'--vpr-lock',str(bundle/'vpr.lock.json'),
                     '--output',str(out/name),'--cases',case,'--variants',','.join(VARIANTS),'--budget','2048','--workers','4',
                     '--batch-size','4','--batch-wait-us','50','--cooperative-blocks','64','--cpu-cores','4','--prewarm-inputs',
                     '--overuse-report','--repeats',str(repeats),'--repeat-start',str(start),'--timeout','900']
            run(name,command,9000 if case=='gemm' else 4500)
            result=json.loads((out/name/'summary.json').read_text())
            if result['status']!='completed' or len(result['measurements'])!=4*repeats:raise RuntimeError('Incomplete native matrix')
            for row in result['measurements']:
                if row['diagnostic'] or row['execution_settings']['gpu_timing']!='0' or row['execution_settings']['diagnostics']!='0' or row['execution_settings']['capture']:raise RuntimeError('Diagnostic configuration leaked into confirmation')
                if not row.get('cpu_budget_audit',{}).get('verified'):raise RuntimeError('CPU affinity audit failed')
                if row.get('independent_check') and not row['independent_check']['cpu_budget_audit']['verified']:raise RuntimeError('Readback CPU affinity audit failed')
                if row.get('hybrid',{}).get('diagnostic'):raise RuntimeError('Native runtime reports diagnostics enabled')
            return result
        matrix('gemm','gemm',3)
        elliptic=matrix('elliptic_initial','elliptic',1)
        record['elliptic_initial_quality_passed']=legal_quality(elliptic);write_json(out/'summary.json',record)
        if record['elliptic_initial_quality_passed']:
            matrix('elliptic_repeats','elliptic',2,1)
        else:
            record['elliptic_followup']='Initial quality/convergence failure retained; analyze overuse reports and controls before further performance repeats.'
        frozen=json.loads((bundle/'bindings.json').read_text())
        if any(sha256(bundle/k)!=v for k,v in frozen['files'].items()):raise RuntimeError('Frozen bundle changed')
        record['status']='completed'
    except Exception as e:record.update(status='failed',error=repr(e));raise
    finally:write_json(out/'summary.json',record)


if __name__=='__main__':main()
