#!/usr/bin/env python3
import subprocess,json,hashlib,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/'results/fpga_device_migration_20261117/migration_a'
def git(root,*args): return subprocess.check_output(['git','-C',str(root),*args]).decode().strip()
def snapshot():
 refs={x:git(ROOT,'rev-parse',x) for x in git(ROOT,'for-each-ref','--format=%(refname)','refs/heads').splitlines() if 'device-migration' not in x}
 trees={r:git(ROOT,'rev-parse',v+'^{tree}') for r,v in refs.items()}
 roots=[ROOT.parent/'3D_FPGA_Interconnects',ROOT.parent/'3D_FPGA_Interconnects_CPU_PRIMARY',ROOT.parent/'3D_FPGA_Interconnects_PAPER_DEPENDENCY']
 guides={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for r in roots for p in r.glob('docs/CODEX*') if p.is_file()}
 return {'refs':refs,'tree_hashes':trees,'guides':guides,'tracked_diffs':{str(r):git(r,'diff','HEAD','--binary') for r in roots},'scope':'All tracked historical content protected by immutable Git trees and live tracked diffs; untracked guidance byte hashes. No writes outside new paths.'}
a=snapshot()
if sys.argv[1]=='baseline':
 with (OUT/'protection_before.json').open('x') as f: json.dump(a,f,indent=2)
else:
 old=json.loads((OUT/'protection_before.json').read_text()); assert old==a,'protected state changed'
 changed=git(ROOT,'diff','706feba1cbefcf828d998560440c488cd081ba07','--name-only').splitlines()
 assert all(p.startswith(('accel/lookahead/fpga_device_migration/','docs/lookahead_fpga_bounded_device_migration_')) for p in changed),changed
 (OUT/'protection_after.json').write_text(json.dumps({'pass':True,'snapshot':a},indent=2))
print('PROTECTION',sys.argv[1],len(a['refs']))
