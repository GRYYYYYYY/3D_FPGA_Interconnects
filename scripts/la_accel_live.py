"""Execute a real backend inside the complete native builder, including cold setup."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from prepare import sha256
import run_native_flat_baseline as base

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--binary', type=Path, required=True)
    p.add_argument('--library', type=Path, required=True)
    p.add_argument('--case', choices=['tseng_2d', 'bnn', 'dla_like.medium'], default='tseng_2d')
    p.add_argument('--workers', type=int, default=8)
    p.add_argument('--contexts', type=int, default=8)
    p.add_argument('--repeats', type=int, default=3)
    a = p.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    frozen = ROOT / 'results/native_flat_baseline_20261105'
    entry = json.loads((frozen / 'summary.json').read_text())['cases'][a.case]
    plan = json.loads((frozen / 'plan.json').read_text())
    case = json.loads(Path(entry['case']['path']).read_text())
    records = []
    for repeat in range(a.repeats):
        d = out / str(repeat)
        d.mkdir()
        for name, target in [('packed_netlist', 'packed.net'), ('placement', 'fixed.place')]:
            shutil.copyfile(case['inputs'][name]['path'], d / target)
        cmd = base.cpu_command(str(a.binary.resolve()), case, d, {'router': 'parallel'}, a.workers, iterations=1)
        base.set_option(cmd, '--write_router_lookahead', d / 'wire_map.bin')
        base.set_option(cmd, '--generate_rr_node_overuse_report', 'off')
        cmd.remove('--analysis')
        env = base.environment(plan, 'flat', d, False)
        for name in ['VPR_LA_EXPORT', 'VPR_LA_IMPORT', 'VPR_LA_WORKLOAD', 'OMP_PROC_BIND', 'OMP_PLACES']:
            env.pop(name, None)
        env.update(VPR_LA_BACKEND=str(a.library.resolve()), VPR_LA_CONTEXTS=str(a.contexts))
        rec = dict(command=cmd, repeat=repeat, affinity=sorted(os.sched_getaffinity(0)),
                   binary_sha256=sha256(a.binary), library_sha256=sha256(a.library),
                   case=a.case, contexts=a.contexts, workers=a.workers,
                   timing_scope='complete_native_builder_including_cold_backend_service',
                   route_success=False, gpu_warmup=False)
        (d / 'invocation.json').write_text(json.dumps(rec, indent=2))
        start = time.time()
        with (d / 'stdout.log').open('w') as log:
            proc = subprocess.run(cmd, cwd=d, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        text = (d / 'stdout.log').read_text()
        live = re.findall(r'LA_LIVE ([^\n]+)', text)
        metrics = dict(re.findall(r'(\w+)=([^ ]+)', live[0])) if len(live) == 1 else {}
        rec.update(returncode=proc.returncode, process_elapsed_s=time.time()-start,
                   live_metrics={k: float(v) for k, v in metrics.items()})
        # Keep complete original timing lines and their precision in the report.
        rec['native_timer_lines'] = [s for s in text.splitlines() if 'lookahead' in s.lower() and ('took' in s or 'sec' in s)]
        wire = d / 'wire_map.bin'
        rec['wire_map_sha256'] = sha256(wire) if wire.exists() else None
        rec['wire_map_matches_frozen_reference'] = rec['wire_map_sha256'] == entry['reference_map']['sha256']
        rec['status'] = 'passed' if (proc.returncode in [0, 2] and rec['wire_map_matches_frozen_reference']
                                   and metrics.get('cold_service') == '1') else 'failed'
        (d / 'result.json').write_text(json.dumps(rec, indent=2))
        records.append(rec)
        (out / 'runs.json').write_text(json.dumps(records, indent=2))
        if rec['status'] != 'passed':
            return 1
    print(json.dumps(dict(status='passed', repeats=len(records), final_wire_maps_match=True)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
