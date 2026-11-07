"""Wait for the sole diagnostic owner, then audit outputs; never submit solvers."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from prepare import sha256, write_json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_cpu_large_diagnostic_20261103'


def main():
    with (OUT/'audit_owner.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUT/'audit_supervisor.json').exists():raise RuntimeError('Existing auditor; inspect it')
        script=ROOT/'scripts/audit_native_cpu_large_diagnostic.py';expected=sha256(script)
        state=dict(status='waiting',pid=os.getpid(),solver_submission_owner=False,auditor_sha256=expected)
        write_json(OUT/'audit_supervisor.json',state)
        try:
            while True:
                try:summary=json.loads((OUT/'summary.json').read_text())
                except json.JSONDecodeError:time.sleep(5);continue
                if summary['status']!='running':break
                status=Path('/proc')/str(summary['pid'])/'stat'
                if not status.exists() or status.read_text().split(') ',1)[1].split()[0]=='Z':
                    raise RuntimeError('Diagnostic owner lost; no automatic recovery')
                time.sleep(15)
            if summary['status']!='completed':raise RuntimeError('Diagnostic chain requires review')
            assert sha256(script)==expected, 'Auditor source changed while waiting'
            state['status']='auditing';write_json(OUT/'audit_supervisor.json',state)
            with (OUT/'audit.log').open('x') as log:
                rc=subprocess.run([sys.executable,str(script)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT).returncode
            state.update(status='complete' if rc==0 else 'audit_failed_requires_review',returncode=rc)
        except Exception as exc:state.update(status='stopped_for_review',error=repr(exc));raise
        finally:write_json(OUT/'audit_supervisor.json',state)


if __name__=='__main__':main()
