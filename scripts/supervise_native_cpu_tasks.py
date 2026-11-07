"""Own one frozen multi-lane experiment and retain each child exit receipt."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

from prepare import sha256, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    plan_path = args.plan.resolve()
    plan = json.loads(plan_path.read_text())
    root = Path(plan['output'])
    root.mkdir(exist_ok=False)
    receipt = {'plan': str(plan_path), 'plan_sha256': sha256(plan_path),
               'status': 'running', 'started_utc': datetime.now(timezone.utc).isoformat(), 'lanes': {}}
    children = {}
    for name in plan['lanes']:
        log = (root / (name + '.log')).open('w')
        command = [sys.executable, str(Path(__file__).with_name('run_native_cpu_tasks.py')),
                   '--plan', str(plan_path), '--lane', name]
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        children[name] = (child, log)
        receipt['lanes'][name] = {'pid': child.pid, 'command': command, 'status': 'running'}
    while True:
        active = 0
        for name, (child, log) in children.items():
            item = receipt['lanes'][name]
            rc = child.poll()
            if rc is None:
                active += 1
            elif item['status'] == 'running':
                log.close()
                item.update(status='completed' if rc == 0 else 'failed', returncode=rc,
                            finished_utc=datetime.now(timezone.utc).isoformat())
                print(json.dumps({'lane': name, 'returncode': rc}), flush=True)
        receipt['observed_utc'] = datetime.now(timezone.utc).isoformat()
        if not active:
            receipt['status'] = 'completed' if all(x['returncode'] == 0 for x in receipt['lanes'].values()) else 'failed'
        write_json(root / 'supervisor.json', receipt)
        if not active:
            break
        time.sleep(30)


if __name__ == '__main__':
    main()
