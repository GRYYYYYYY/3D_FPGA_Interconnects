import sys,subprocess,json,struct,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();adapter=r/'compact_adapter.py';adapter.write_text('#!/usr/bin/env python3\nimport os,sys\na=sys.argv[1:]\nos.execv('+repr(str(r/'cpu61'))+',["cpu61"]+a[:6]+["compact"]+a[6:])\n');adapter.chmod(0o755)
p=subprocess.run(['python3',str(R/'scripts/la_accel_round6_lifecycle.py'),str(r/'compact_errors'),str(adapter)],capture_output=True,text=True);(r/'compact_error_test.log').write_text(p.stdout+p.stderr);assert p.returncode==0
# Workload with a valid native cost index outside the 11-bit packed field.
p=r/'cost2048.bin';costs=2049;n=1;data=struct.pack('<7Q',0x31414c5443495254,n,0,1,costs,1,1)+struct.pack('<2Q',0,0)+struct.pack('<IIIi',1,2048,1,-1)+struct.pack('<ff',0,0)*costs+struct.pack('<6I',0,0,0,0,0,0)+struct.pack('<i',0)+struct.pack('<ff',0,0);p.write_bytes(data)
rows=[]
for repr_ in ['original','compact','direct']:
 cmd=[str(r/'cpu61'),str(p),'20','1','0',str(r/f'cost2048_{repr_}.out'),'0',repr_];run=subprocess.run(cmd,capture_output=True,text=True);(r/f'cost2048_{repr_}.log').write_text(run.stdout+run.stderr);assert run.returncode==(0 if repr_=='original' else 10);rows.append(dict(representation=repr_,returncode=run.returncode))
(r/'compact_field_admission.json').write_text(json.dumps(rows,indent=2))

# Direct-directory lifecycle uses shift20; shift0 remains the compact tree control.
adapter=r/'direct_adapter.py';adapter.write_text('#!/usr/bin/env python3\nimport os,sys\na=sys.argv[1:]\nos.execv('+repr(str(r/'cpu61'))+',["cpu61"]+a[:6]+["direct" if a[1]=="20" else "compact"]+a[6:])\n');adapter.chmod(0o755)
p=subprocess.run(['python3',str(R/'scripts/la_accel_round6_lifecycle.py'),str(r/'direct_errors'),str(adapter)],capture_output=True,text=True);(r/'direct_errors.log').write_text(p.stdout+p.stderr);assert p.returncode==0
