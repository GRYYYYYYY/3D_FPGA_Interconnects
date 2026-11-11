#!/usr/bin/env python3
"""Package complete small evidence and losslessly compressed full outputs."""
import pathlib,hashlib,json,gzip,shutil
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z';dst=r/'evidence_snapshot';dst.mkdir(exist_ok=True)
files=[]
for group in ['directed','directed_ii1','directed_latency60','directed_owner64','real_waves','real_waves_d4','rejection','replay','attempts','provenance','ooc_owner','ooc_recovery','ooc_v2']:
 p=r/group
 if not p.exists():continue
 for src in sorted(p.iterdir()):
  if not src.is_file() or src.suffix in ['.pb','.wdb','.dcp']:continue
  if src.suffix not in ['.csv','.hex','.txt','.json','.jsonl','.log','.rpt','.xdc','.sv','.py','.bin','.stderr']:continue
  rel=src.relative_to(r);data=src.read_bytes();compress=src.suffix in ['.csv','.hex','.bin'] or len(data)>150000
  target=dst/(str(rel)+('.gz' if compress else ''));target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(gzip.compress(data,mtime=0) if compress else data)
  files.append(dict(path=str(rel),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),snapshot=str(target.relative_to(dst)),compressed=compress))
for name in ['replay_summary.json','resident_existing.json','model_comparison.json','status.json']:
 if (r/name).exists():shutil.copy2(r/name,dst/name)
source={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'accel/lookahead/fpga_sim_restart').rglob('*')) if p.is_file() and '__pycache__' not in str(p)}
raw=[dict(path=str(p.relative_to(r)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(r.rglob('*.dcp'))]
(dst/'index.json').write_text(json.dumps(dict(source_commit='7e63b917f37273f80c03327e024d86b797ee221b',run_id=r.name,source_sha256=source,files=files,large_local_checkpoints=raw,board_measured=False),indent=2)+'\n')
print('packaged',len(files),'files;',sum(p.stat().st_size for p in dst.rglob('*') if p.is_file()),'bytes')
