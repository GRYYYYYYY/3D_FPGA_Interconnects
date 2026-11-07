"""Observe the existing owners and render terminal evidence; never submit solvers."""
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from prepare import sha256, write_json
from scaling_common import verified

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/native_cpu_large_20261102'


def read(path):
    return json.loads(path.read_text())


def alive(pid):
    p=Path('/proc')/str(pid)/'stat'
    try: return p.read_text().split(') ',1)[1].split()[0] != 'Z'
    except FileNotFoundError:return False


def main():
    with (OUT/'observer.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUT/'observer.json').exists():raise RuntimeError('Observer already recorded; inspect before starting another')
        reporter=ROOT/'scripts/report_native_cpu_large.py'
        report_binding={'path':str(reporter),'sha256':sha256(reporter)}
        state=dict(status='observing',pid=os.getpid(),solver_submission_owner=False,
                   policy='Read existing owner receipts every 15 seconds; no retries, no solver submission, report only terminal results.',
                   report_binding=report_binding,started_utc=datetime.now(timezone.utc).isoformat())
        write_json(OUT/'observer.json',state)
        try:
            while True:
                try:
                    continuation=read(OUT/'continuation.json')
                    original=read(OUT/'supervisor.json')
                except json.JSONDecodeError:time.sleep(5);continue
                current=continuation['status']
                if current not in ['running','waiting_original_preparation']:
                    break
                monitored=original if current=='waiting_original_preparation' and original['status']=='running' else continuation
                if not alive(monitored['pid']):
                    state.update(status='owner_lost_requires_review',last_continuation=continuation,last_original=original)
                    return
                state.update(last_checked_utc=datetime.now(timezone.utc).isoformat(),chain_status=current,
                             phase=continuation.get('current') if current=='running' else original.get('current'),
                             case=original.get('current_case') if current=='waiting_original_preparation' else None)
                write_json(OUT/'observer.json',state)
                time.sleep(15)
            verified(report_binding)
            with (OUT/'terminal_report.log').open('x') as log:
                rc=subprocess.run([sys.executable,str(reporter)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT).returncode
            state.update(status='terminal_report_ready' if rc==0 else 'report_failed_requires_review',
                         chain_terminal_status=current,report_returncode=rc,report=str(OUT/'report.md'))
        except Exception as exc:
            state.update(status='observer_failed_requires_review',error=repr(exc));raise
        finally:
            state['finished_utc']=datetime.now(timezone.utc).isoformat()
            write_json(OUT/'observer.json',state)


if __name__=='__main__':main()
