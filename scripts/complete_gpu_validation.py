#!/usr/bin/env python3
"""Complete deferred native VPR checking on the CPU host, preserving GPU records."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from prepare import sha256, write_json


def complete(run, output):
    root=Path(__file__).resolve().parents[1]
    run=Path(run).resolve();output=Path(output).resolve()
    gpu=json.loads((run/'validation.json').read_text())
    if not gpu.get('gpu_execution_passed'):
        raise ValueError('GPU execution has not passed; cannot complete FULL verification')
    matrix_path=run/'matrix/summary.json'
    if sha256(matrix_path)!=gpu['matrix_sha256']:
        raise ValueError('GPU matrix changed after execution')
    matrix=json.loads(matrix_path.read_text())
    case=Path(gpu['case'])
    reference=root.parent/'FPGA_accelerate_FPGA/G_3d_routing'
    output.mkdir(parents=True,exist_ok=False)
    report={'status':'running','gpu_run':str(run),'gpu_report_sha256':sha256(run/'validation.json'),
            'vpr_full_check_passed':False,'checks':[],'runs':[],
            'matrix_summary':matrix['summary'],'cuda_comparison':matrix.get('cuda_comparison',[])}
    write_json(output/'summary.json',report)
    by_fingerprint={}
    try:
        if not matrix['runs']:
            raise ValueError('Empty GPU benchmark')
        for row in matrix['runs']:
            if not row.get('success') or not row.get('audit',{}).get('legal_in_projection'):
                raise ValueError('Unsuccessful benchmark row')
            stem=f'{row["variant"]}_{row["repeat"]}'
            if not re.fullmatch(r'[a-z_]+_[0-9]+',stem):
                raise ValueError('Invalid benchmark result name')
            result=run/'matrix'/f'{stem}.json'
            if sha256(result)!=row['audit']['result_sha256']:
                raise ValueError('Routing result changed after GPU audit')
            data=json.loads(result.read_text())
            fingerprint=hashlib.sha256(json.dumps(data['routes'],sort_keys=True).encode()).hexdigest()
            if fingerprint!=row['route_fingerprint']:
                raise ValueError('Route fingerprint mismatch')
            if fingerprint not in by_fingerprint:
                dest=output/stem
                command=[sys.executable,str(root/'scripts/vpr_validate.py'),'--case',str(case),
                         '--result',str(result),'--vpr-case',str(reference/'data/raw/ex5p_balanced.json'),
                         '--vpr-lock',str(reference/'configs/vpr.lock.json'),'--output',str(dest)]
                with (output/f'{stem}.log').open('w') as log:
                    proc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=300)
                if proc.returncode:
                    raise RuntimeError(f'VPR validation failed for {stem}; inspect {dest}/vpr.log')
                check=json.loads((dest/'validation.json').read_text())
                if not check['vpr_full_check'] or check['source_result_sha256']!=row['audit']['result_sha256']:
                    raise ValueError('VPR FULL check did not verify the requested result')
                wire=re.search(r'Total wirelength:\s*(\d+)',(dest/'vpr.log').read_text())
                by_fingerprint[fingerprint]={'path':str(dest/'validation.json'),
                    'critical_path_ns':check['critical_path_ns'],'wirelength':int(wire[1]) if wire else None,
                    'vpr_full_check':True,'route_fingerprint':fingerprint}
                report['checks'].append(by_fingerprint[fingerprint])
            report['runs'].append({'variant':row['variant'],'repeat':row['repeat'],
                'process_seconds':row['process_seconds'],**by_fingerprint[fingerprint]})
            write_json(output/'summary.json',report)
        report.update(status='passed',vpr_full_check_passed=True)
    except (OSError,ValueError,KeyError,RuntimeError,subprocess.TimeoutExpired) as exc:
        report.update(status='failed',error=str(exc))
    write_json(output/'summary.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=complete(args.run,args.output)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
