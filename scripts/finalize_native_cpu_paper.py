"""Wait for frozen studies, then regenerate and audit all terminal evidence.

This does not launch, change or terminate experiments. The caller still reviews
the report and figures before recording final acceptance and handoff.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from prepare import write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    scripts = Path(__file__).resolve().parent
    studies = [
        ('plan.json', 'analysis.json'),
        ('architecture_plan.json', 'architecture_analysis.json'),
        ('tasks_plan.json', 'tasks_analysis.json'),
        ('tasks_extension_plan.json', 'tasks_extension_analysis.json'),
        ('clstm_quality_plan.json', 'clstm_quality_analysis.json'),
        ('multiqueue_plan.json', 'multiqueue_analysis.json'),
        ('tasks_attribution_plan.json', 'tasks_attribution_analysis.json'),
    ]
    plans = [root / name for name, _ in studies] + [root / 'smoke_v2_plan.json', root / 'tasks_smoke_plan.json']
    previous = None
    while True:
        states = []
        for plan_path in plans:
            plan = json.loads(plan_path.read_text())
            for name in plan['lanes']:
                summary = json.loads((Path(plan['output']) / name / 'summary.json').read_text())
                done = [x for x in summary['measurements'] if x.get('finished_utc')]
                states.append({'plan': plan_path.name, 'lane': name, 'status': summary['status'],
                               'attempted': len(done), 'successful': sum(x['success'] for x in done),
                               'skipped': len(summary['skipped'])})
        receipt = {'status': 'waiting', 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'lanes': states, 'attempted': sum(x['attempted'] for x in states),
                   'successful': sum(x['successful'] for x in states)}
        write_json(root / 'finalization_progress.json', receipt)
        if states != previous:
            print(json.dumps(receipt, ensure_ascii=False), flush=True)
            previous = states
        if any(x['status'] == 'failed' for x in states):
            raise RuntimeError('A study lane failed; inspect its retained evidence before finalizing.')
        if all(x['status'] == 'completed' for x in states):
            break
        time.sleep(30)

    def run(script, arguments, logfile, env=None):
        with (root / logfile).open('w') as output:
            subprocess.run([sys.executable, str(scripts / script), *map(str, arguments)],
                           stdout=output, stderr=subprocess.STDOUT, check=True, env=env)

    for name, output in studies:
        run('report_native_cpu_study.py', ['--plan', root / name, '--output', root / output], output + '.log')
    audit_args = [arg for path in plans for arg in ['--plan', path]] + ['--output', root / 'evidence_verification.json']
    run('verify_native_cpu_study.py', audit_args, 'evidence_verification.log')
    env = os.environ.copy()
    env.update(PYTHONPATH=str(root / 'plot_packages'), OPENBLAS_NUM_THREADS='1', MPLCONFIGDIR=str(root / 'plot_config'))
    run('plot_native_cpu_study.py', ['--root', root], 'plot.log', env=env)
    run('summarize_native_cpu_paper.py', ['--root', root], 'summarize.log')
    receipt.update(status='artifacts_ready_for_review', updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    write_json(root / 'finalization_progress.json', receipt)
    print('Terminal reports, audit and figures ready for review.', flush=True)


if __name__ == '__main__':
    main()
