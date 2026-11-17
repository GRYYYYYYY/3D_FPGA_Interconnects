"""Read-only snapshot of the FPGA group and its pause manager."""
import datetime
import hashlib
import json
import sys
import time
from pathlib import Path

base = Path(__file__).resolve().parents[4]
raw = base / '3D_FPGA_Interconnects_DEVICE_MIGRATION/results/fpga_device_migration_20261117/migration_a'
beat = json.loads((raw / 'pause_heartbeat.json').read_text())
budget = (raw / 'budget.json').read_bytes()
boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
def identity(record):
    p = Path('/proc') / str(record['pid'])
    fields = (p/'stat').read_text().rsplit(') ', 1)[1].split()
    assert int(fields[19]) == record['start_ticks'] and int(fields[2]) == record['pgid']
    return dict(pid=record['pid'], start_ticks=int(fields[19]), pgid=int(fields[2]), state=fields[0],
                threads=[(task/'stat').read_text().rsplit(') ',1)[1][0] for task in (p/'task').iterdir()])
status = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), heartbeat=beat['utc'],
              budget_sha256=hashlib.sha256(budget).hexdigest(), boot_id=boot)
try:
    assert boot == beat['observer']['boot_id'] == json.loads(budget)['boot_id']
    assert time.time()-datetime.datetime.fromisoformat(beat['utc']).timestamp() < 100
    assert not any(beat[k] for k in ('auto_resume_allowed','terminal_publication_allowed','budget_signals_allowed'))
    members=[identity(m) for m in beat['snapshot']['members']]
    assert all(set(m['threads'])=={'T'} for m in members)
    observer=identity(beat['observer'])
    locks=[s for s in Path('/proc/locks').read_text().splitlines() if len(s.split())>4 and s.split()[4]==str(observer['pid'])]
    assert len(locks)>=2 and beat['state'].startswith('PAUSED_BY_USER')
    status.update(state=beat['state'], members=members, manager=observer, locks=locks)
except (AssertionError,OSError,KeyError) as exc:
    status.update(state='UNKNOWN', reason=repr(exc))
with Path(sys.argv[1]).open('x') as output:
    json.dump(status,output,indent=2)
print(status['state'], status['heartbeat'])

