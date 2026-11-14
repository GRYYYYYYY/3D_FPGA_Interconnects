"""Compact local evidence manifest; parent owns final repository publication."""
from pathlib import Path
import json,gzip,hashlib,datetime
ROOT=Path(__file__).resolve().parents[4]
def main():
 a=ROOT/'results/fpga_enum_commit_integration_20261114_a';f=ROOT/'results/fpga_enum_commit_integration_20261114_fixed';out=f/'evidence_snapshot';out.mkdir(exist_ok=False)
 assert json.loads((f/'sim_d/receipt.json').read_text())['status']=='PASS'
 terminal=json.loads((ROOT/'results/fpga_enum_commit_integration_20261114_ooc_d/terminal.json').read_text());assert terminal['status']!='RUNNING'
 roots=[a/'failure_01_no_progress',a/'sim_b',a/'ooc_a',a/'ooc_b',a/'fixtures',f/'sim_a',f/'sim_b',f/'sim_c',f/'sim_d',ROOT/'results/fpga_enum_commit_integration_20261114_ooc_c',ROOT/'results/fpga_enum_commit_integration_20261114_ooc_d',ROOT/'results/fpga_enum_commit_integration_20261114_port_stress',ROOT/'accel/lookahead/fpga_enum_commit/integration']
 files={p for root in roots for p in root.rglob('*') if p.is_file() and p.suffix in {'.json','.rpt','.log','.csv','.sv','.v','.hpp','.cpp','.tcl','.xdc','.txt','.hex','.py','.md'}}
 files={p for p in files if not any(x in p.parts for x in ('__pycache__','.Xil','.vivado-ai','sim_project','project'))}
 rows=[]
 for p in sorted(files):
  data=p.read_bytes();rel=str(p.relative_to(ROOT));dest=rel+('.gz' if len(data)>16384 else '');q=out/dest;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(data,mtime=0) if dest.endswith('.gz') else data)
  rows.append({'raw_path':rel,'archive':dest,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 m={'scope':'local two-subbank actual taggedport; nativeprojection not fullgraph','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':rows,'ooc_terminal':terminal,'main_sim':'results/fpga_enum_commit_integration_20261114_fixed/sim_d/receipt.json','omitted_checkpoints':'DCP hashes and original server paths in source_binding/terminal; reports plus exact source recreate design','board_measured':False}
 (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 for x in rows:
  data=(out/x['archive']).read_bytes();data=gzip.decompress(data) if x['archive'].endswith('.gz') else data
  assert hashlib.sha256(data).hexdigest()==x['sha256'] and len(data)==x['bytes']
 print('INTEGRATION_ARCHIVE_PASS',len(rows),sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
if __name__=='__main__':main()
