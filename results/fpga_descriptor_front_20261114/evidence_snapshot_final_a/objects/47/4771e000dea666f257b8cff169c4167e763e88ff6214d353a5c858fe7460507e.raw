#!/usr/bin/env python3
"""Reproduce source-bound finite services checks in a NEW result directory."""
import argparse,datetime,hashlib,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args()
src=Path(__file__).resolve().parent;root=src.parents[3];out=Path(a.output).resolve()
if out.exists():raise SystemExit('Use a NEW output directory; never overwrite an experiment')
out.mkdir(parents=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=[p for p in src.iterdir() if p.is_file() and p.suffix in ('.hpp','.cpp','.sv','.py','.tcl')]
binding={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':{str(p.relative_to(root)):sha(p) for p in source},'pid':os.getpid(),'argv':os.sys.argv}
(out/'source').mkdir()
for p in source:(out/'source'/p.name).write_bytes(p.read_bytes())
(out/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
cases=['directory','network','candidate','min','min_collect'];commands=[]
def run(cmd,log,env=None):
 commands.append(cmd)
 with (out/log).open('w') as f:r=subprocess.run(cmd,cwd=out,stdout=f,stderr=subprocess.STDOUT,env=env)
 (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if r.returncode:raise RuntimeError(f'{log}: rc={r.returncode}')
try:
 for c in cases:
  run(['g++','-std=c++17','-O2','-Wall','-Wextra',str(src/f'test_{c}.cpp'),'-o',str(out/f'test_{c}')],f'{c}_compile.log')
  run([str(out/f'test_{c}'),str(out/f'{c}.vec')],f'{c}_model.log')
 tcl=['create_project services [file join [pwd] project] -part xcu280-fsvh2892-2L-e']
 for p in sorted(src.glob('df_*.sv')):tcl.append(f'add_files {{{p}}}')
 for c in cases:
  fs=f'sim_{c}';tcl.extend([f'create_fileset -simset {fs}',f'add_files -fileset {fs} {{{src/f"tb_{c}.sv"}}}',f'set_property top tb_{c} [get_filesets {fs}]',f'set_property xsim.simulate.runtime all [get_filesets {fs}]',f'set_property -name xsim.simulate.xsim.more_options -value {{-testplusarg VECTORS={out/f"{c}.vec"}}} -objects [get_filesets {fs}]',f'current_fileset -simset {fs}',f'update_compile_order -fileset {fs}',f'launch_simulation -simset {fs}','close_sim'])
 (out/'run.tcl').write_text('\n'.join(tcl)+'\nexit\n')
 env=dict(os.environ);env['LD_PRELOAD']='/lib/x86_64-linux-gnu/libudev.so.1'
 run(['/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin/vivado','-mode','batch','-source',str(out/'run.tcl')], 'vivado_console.log',env)
 transcripts={}
 for c in cases:
  log=out/f'project/services.sim/sim_{c}/behav/xsim/simulate.log';text=log.read_text()
  assert 'TEST_PASS' in text and 'Fatal:' not in text and 'ERROR:' not in text,c
  transcripts[c]={'transcript':str(log.relative_to(out)),'sha256':sha(log),'vectors_sha256':sha(out/f'{c}.vec'),'binary_sha256':sha(out/f'test_{c}')}
 (out/'terminal.json').write_text(json.dumps({'status':'PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':transcripts,'scope':'local services, no complete kernel clock/fit qualification','board_measured':False},indent=2)+'\n')
 print('SERVICES_PASS',out)
except BaseException as e:
 (out/'terminal.json').write_text(json.dumps({'status':'FAIL','exception':repr(e),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n');raise
