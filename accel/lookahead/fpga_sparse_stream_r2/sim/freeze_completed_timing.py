"""Archive explicitly completed OOC stages; never treat active reports as final."""
from pathlib import Path
import gzip,hashlib,json,sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112'
out=r/'evidence_snapshot'/sys.argv[1];out.mkdir(exist_ok=False)
files=set();stages=[]
for spec in sys.argv[2:]:
 variant,stage=spec.split(':');p=r/'timing'/variant
 run=next(p.glob('project/*.runs/'+stage))
 text=(run/'runme.log').read_text()
 if 'Exiting Vivado' not in text:raise RuntimeError('stage still active: '+spec)
 stages.append({'variant':variant,'stage':stage,'end_marker':True,'error_lines':[x for x in text.splitlines() if x.startswith('ERROR:')]})
 for x in p.iterdir():
  if x.is_file() and x.suffix in ['.json','.tcl','.xdc','.rpt','.md','.diff']:files.add(x)
 files.update(x for x in (p/'source').iterdir() if x.is_file())
 files.update(x for x in run.iterdir() if x.is_file() and x.suffix in ['.log','.rpt','.tcl','.rst'])
items=[]
for p in sorted(files):
 raw=p.read_bytes();dst=out/p.relative_to(r);dst.parent.mkdir(parents=True,exist_ok=True)
 if len(raw)>16384:dst=dst.with_name(dst.name+'.gz');dst.write_bytes(gzip.compress(raw,mtime=0))
 else:dst.write_bytes(raw)
 items.append({'raw_path':str(p.relative_to(r)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'archive':str(dst.relative_to(out))})
(out/'manifest.json').write_text(json.dumps({'scope':'completed OOC stages; qualification depends on actual constraints, clock context and all setup/hold/DRC results','stages':stages,'files':items},indent=2))
print('FROZEN',len(items),'files')
