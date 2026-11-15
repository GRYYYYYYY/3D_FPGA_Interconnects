#!/usr/bin/env python3
"""Verify protected refs, fixed base and changes restricted to this candidate."""
import json,subprocess,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];RAW=ROOT/'results/fpga_cpu_primary_20261115'
m=json.loads((RAW/'protection.json').read_text())
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
for ref,want in m['protected_refs'].items():assert git('rev-parse',ref)==want,ref
subprocess.run(['git','merge-base','--is-ancestor',m['base'],'HEAD'],cwd=ROOT,check=True)
guide=ROOT/'docs/CODEX_FPGA_CPU_PRIMARY_AFTER_3C7F96E.md';assert hashlib.sha256(guide.read_bytes()).hexdigest()==m['guide_sha256']
changed=set(git('diff',m['base'],'--name-only').splitlines())
changed.update(git('ls-files','--others','--exclude-standard').splitlines());changed.discard('')
allowed=lambda f:f.startswith('accel/lookahead/fpga_cpu_primary/') or f.startswith('results/fpga_cpu_primary_20261115/') or f.startswith('docs/lookahead_fpga_cpu_primary') or f=='docs/CODEX_FPGA_CPU_PRIMARY_AFTER_3C7F96E.md'
assert all(allowed(f) for f in changed),sorted(f for f in changed if not allowed(f))
r={'status':'PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base':m['base'],'head_at_check':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'protected_refs_unchanged':len(m['protected_refs']),'changed_paths':sorted(changed),'guide_sha256':m['guide_sha256']}
(RAW/'protection_verification.json').write_text(json.dumps(r,indent=2)+'\n');print('PROTECTION_PASS',len(m['protected_refs']),'refs;',len(changed),'candidate-only paths')
