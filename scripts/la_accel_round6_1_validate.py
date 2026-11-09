import sys,json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]);o=r/'validation';o.mkdir(exist_ok=False);exe=r/'cpu61';records=[]
paths=[]
for case,rd in [('native_d3_w8','round3_20261108T141500Z'),('native_d4_w8','round3_20261108T141500Z'),('native_d5_w8','round4_20261108T182500Z'),('native_d6_w8','round5_20261109T054024Z'),('native_d8_w8','round5_20261109T054024Z'),('native_d6_w8_l1','round5_20261109T054024Z')]:paths.append(R/f'results/lookahead_accel_{rd}/evidence_snapshot/{case}/workload.bin')
paths+=sorted((R/'results/lookahead_accel_round4_20261108T182500Z/evidence_snapshot/semantic_fixtures').glob('*.bin'))
paths+=[R/'results/lookahead_accel_20261108T125500Z'/c/'workload.bin' for c in ['tseng_export','bnn_export']]
for path in paths:
 case=path.parent.name if path.name=='workload.bin' else path.stem
 for shift in [0,20]:
  baseline=None
  for rep in ['original','compact']+(['direct'] if shift==20 else []):
   name=f'{case}_s{shift}_{rep}';out=o/(name+'.bin');cmd=[str(exe),str(path),str(shift),'8' if case in ['tseng_export','bnn_export'] else '1','0',str(out),'0',rep];p=subprocess.run(cmd,capture_output=True,text=True,timeout=300);(o/(name+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,(name,p.stderr)
   data=out.read_bytes()
   if baseline is None:baseline=data
   assert data==baseline,name
   records.append(dict(case=case,shift=shift,representation=rep,equal=True,output_sha256=hashlib.sha256(data).hexdigest(),measurement=json.loads(p.stdout.splitlines()[0])))
  (o/'result.json').write_text(json.dumps(records,indent=2))
print(len(records),'functional configurations passed')
