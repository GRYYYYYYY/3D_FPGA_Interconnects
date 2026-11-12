"""Append closed-loop evidence; preserve the first-delivery snapshot entries."""
import pathlib,hashlib,json,gzip,shutil
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z';srcroot=r/'closed_loop';dst=r/'evidence_snapshot'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  while b:=f.read(8<<20):h.update(b)
 return h.hexdigest()
metadata=['status.json','replay_summary.json','resident_existing.json','model_comparison.json']
idx=json.load(open(dst/'index.json'));idx['files']=[x for x in idx['files'] if not x['path'].startswith('closed_loop/') and x['path'] not in metadata]
allowed={'.json','.jsonl','.csv','.hex','.txt','.log','.rpt','.xdc','.sv','.py','.bin','.stderr','.png','.svg','.md'}
for src in sorted(srcroot.rglob('*')):
 if not src.is_file() or src.suffix not in allowed:continue
 rel=src.relative_to(r);parts=src.relative_to(srcroot).parts
 if any(x in ['__pycache__','build','xsim.dir'] or x.startswith('verilator_') for x in parts):continue
 # Native route/netlist files are indexed separately; keep full final wire map.
 if src.name in ['core','plot_dependencies.log'] or src.name.startswith('hs_err'):continue
 data=src.read_bytes();compressed=src.suffix in ['.csv','.hex','.bin'] or (len(data)>150000 and src.suffix not in ['.png','.svg'])
 target=dst/(str(rel)+('.gz' if compressed else ''));target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(gzip.compress(data,mtime=0) if compressed else data)
 idx['files'].append({'path':str(rel),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'snapshot':str(target.relative_to(dst)),'compressed':compressed})
for name in metadata:
 src=r/name
 if not src.exists():continue
 shutil.copy2(src,dst/name)
 idx['files'].append({'path':name,'bytes':src.stat().st_size,'sha256':sha(src),'snapshot':name,'compressed':False})
# Every checkpoint, including superseded attempts, has an explicit local-only binding.
idx['large_local_checkpoints']=[{'path':str(p.relative_to(r)),'bytes':p.stat().st_size,'sha256':sha(p),'uploaded_to_git':False} for p in sorted(r.rglob('*.dcp'))]
idx['other_large_local_artifacts']=[{'path':str(p.relative_to(r)),'bytes':p.stat().st_size,'sha256':sha(p),'uploaded_to_git':False} for p in sorted(srcroot.glob('native_*/*.route'))]
idx['source_sha256']={str(p.relative_to(root)):sha(p) for p in sorted((root/'accel/lookahead/fpga_sim_restart').rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
idx['source_sha256']['docs/lookahead_fpga_sim_restart.md']=sha(root/'docs/lookahead_fpga_sim_restart.md')
idx['source_base_commit']=idx.pop('source_commit',idx.get('source_base_commit','7e63b917f37273f80c03327e024d86b797ee221b'));idx['source_version_strategy']='file SHA256 bindings; publication commit reported separately';idx['first_delivery_commit']='857bfce454a86947965f7dd706f643bc376f6cf9';idx['final_delivery_scope']='complete closed-loop prototype and negative projected results; unresolved baselines/timing stated explicitly';idx['board_measured']=False
(dst/'index.json').write_text(json.dumps(idx,indent=2)+'\n');shutil.copy2(r/'status.json',dst/'status.json')
# A missing/truncated compressed artifact is a hard failure, not a warning.
for entry in idx['files']:
 p=dst/entry['snapshot'];data=gzip.decompress(p.read_bytes()) if entry['compressed'] else p.read_bytes();assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256'],p
print('Verified evidence files',len(idx['files']),'snapshot bytes',sum(p.stat().st_size for p in dst.rglob('*') if p.is_file()))
