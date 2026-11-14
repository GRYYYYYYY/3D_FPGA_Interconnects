"""Freeze compact F evidence only after final own implementation is terminal."""
from pathlib import Path
import json,gzip,hashlib,datetime,sys,shutil
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_20261114';S=ROOT/'accel/lookahead/fpga_enum_commit/front';O=R/'front_evidence_a'
def verify():
 m=json.loads((O/'manifest.json').read_text())
 for x in m['files']:
  b=(O/x['archive']).read_bytes();b=gzip.decompress(b) if x['archive'].endswith('.gz') else b
  assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],x['raw_path']
 print('FRONT_ARCHIVE_VERIFY_PASS',len(m['files']))
def main():
 if '--verify' in sys.argv:verify();return
 assert json.loads((R/'front_ooc_e/final_terminal.json').read_text())['terminal_status']=='COMPLETED'
 O.mkdir(exist_ok=False);rows=[];allowed={'.json','.log','.csv','.cpp','.hpp','.py','.sv','.v','.tcl','.prj','.sh','.txt','.md','.rpt','.xdc','.hex','.jou'}
 names=['front_compare_a','front_grouped_a','front_grouped_b','front_independent_a','front_analysis_a','front_bindings_a','front_rtl_a','front_rtl_b','front_rtl_c','front_rtl_d','front_allocator_rtl_a','front_offset_bounds_a','front_offset_bounds_b','front_ooc_a','front_ooc_b','front_ooc_c','front_ooc_d','front_ooc_e']
 files=[(str(p.relative_to(R)),p) for name in names for p in sorted((R/name).rglob('*')) if p.is_file() and p.suffix in allowed and '/.Xil/' not in str(p) and not p.name.startswith('vivado_proxy_')]
 files.extend(('delivery_source/'+p.name,p) for p in sorted(S.iterdir()) if p.is_file())
 for raw,p in files:
  b=p.read_bytes();dest=raw+'.gz' if len(b)>16384 else raw;q=O/dest;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(b,mtime=0) if dest.endswith('.gz') else b)
  rows.append({'raw_path':raw,'archive':dest,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 m={'scope':'F paired local frontend, completed-header group RTL and actual local OOC; no complete kernel qualification','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base':'1e312d6e4ffc5ea96f25c0b97931ad028e710584','files':rows,'unchanged_native_traces':'reuse059 manifest capture_a, stress windows frozen1e312d6 front_stress_b, per-run SHA receipts','checkpoints':'raw server front_ooc_*/{synth,route}.dcp kept; exact hashes in terminal receipts, binary checkpoints omitted from compact Git archive','board_measured':False}
 (O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');verify();print('compressed_bytes',sum(p.stat().st_size for p in O.rglob('*') if p.is_file()))
if __name__=='__main__':main()
