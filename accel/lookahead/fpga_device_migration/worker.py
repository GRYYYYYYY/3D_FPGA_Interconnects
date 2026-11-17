#!/usr/bin/env python3
import json,pathlib,subprocess,sys,hashlib,time
r=pathlib.Path(sys.argv[1]).resolve();b=json.loads((r/'flow_binding.json').read_text())
assert time.time()<json.loads((r/'budget.json').read_text())['compute_deadline_epoch']
for name,sha in b['files'].items(): assert hashlib.sha256((r/name).read_bytes()).hexdigest()==sha,name
for s in json.loads((r/'source_binding.json').read_text())['sources']: assert hashlib.sha256((r/'source'/pathlib.Path(s['path']).name).read_bytes()).hexdigest()==s['sha256']
p=subprocess.Popen(b['command'],cwd=r)
while True:
 try: rc=p.wait();break
 except KeyboardInterrupt: continue # SIGINT reaches whole owned process group; await actual exit.
(r/'vivado_exit.json').write_text(json.dumps({'returncode':rc,'utc':time.time()}))
sys.exit(rc)
