"""Curated immutable R6.2 evidence snapshot. Preserve originals and all failed logs."""
import json,sys,shutil,gzip
from pathlib import Path
from prepare import sha256
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();dst=r/'evidence_snapshot';dst.mkdir(exist_ok=False)
def copy(p,rel=None):
 rel=rel or p.relative_to(r);out=dst/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
for p in sorted(r.glob('*.json')):copy(p)
for p in sorted((r/'platform').glob('*')):
 if p.is_file() and p.suffix in ['.json','.log'] and p.name!='gpu_resources.json':copy(p)
for p in sorted((r/'paper').glob('*')):
 if p.is_file() and p.suffix in ['.log','.txt']:copy(p)
for case in ['s38417','bnn','lstm_s2']:
 copy(r/case/'zero_fanin_chanz.tsv')
for p in (r/'metadata_preflight').glob('*'):
 if p.is_file() and p.suffix in ['.json','.log']:copy(p)
for sub in ['profile_build','reserve_build','reserve_build_failed_relative_path']:
 d=r/sub
 if not d.exists():continue
 for p in d.glob('*'):
  if p.is_file() and p.suffix in ['.json','.log','.patch']:copy(p)
 for p in (d/'source').glob('vpr_live.cpp'):copy(p)
for name in ['cuda_solver61.cuh','cuda_backend61.cu','bucket61.hpp']:
 p=r/'profile_cuda_source/round6_1'/name
 if p.exists():copy(p)
# Raw route/map/capture stay in managed result root, bound rather than git huge binaries.
raw_bindings=[]
for p in sorted((r/'worker').rglob('*')):
 if not p.is_file():continue
 if p.name in ['routed.route','wire_map.bin'] or p.suffix=='.so' or p.name=='native_input.bin':
  raw_bindings.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha256(p)));continue
 if p.suffix=='.json':copy(p)
 elif p.suffix=='.log':
  out=dst/p.relative_to(r);out=out.with_name(out.name+'.gz');out.parent.mkdir(parents=True,exist_ok=True)
  with p.open('rb') as fi,out.open('wb') as fo:
   with gzip.GzipFile(filename='',mode='wb',fileobj=fo,mtime=0) as gz:shutil.copyfileobj(fi,gz)
# Exact frozen-source excerpts used by the graph classification.
root=R/'vendor/vtr_cpu_slices'
copy(root/'LICENSE.md',Path('p0_source/LICENSE.md'))
for name in ['build_scatter_gathers.cpp','switchblock_scatter_gather_common_utils.cpp','rr_graph_sg.cpp','rr_node_indices.cpp']:
 copy(root/'vpr/src/route/rr_graph_generation'/name,Path('p0_source')/name)
copy(root/'libs/librrgraph/src/base/check_rr_graph.cpp',Path('p0_source/check_rr_graph.cpp'))
copy(root/'vpr/src/route/route.cpp',Path('p0_source/route.cpp'))
for name in ['native_state_ablation_20261102/conclusions.json','native_state_trace_20261102/conclusions.json']:
 copy(R/'results'/name,Path('prior_attribution')/name)
(dst/'raw_artifact_bindings.json').write_text(json.dumps(raw_bindings,indent=2))
files={str(p.relative_to(dst)):dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in sorted(dst.rglob('*')) if p.is_file()}
(dst/'manifest.json').write_text(json.dumps(dict(scope='R6.2 JSON, all raw process/check logs compressed, classification node sets, source excerpts, platform and submission receipts. Large immutable inputs/ELFs/maps/routes/captures remain local with hashes.',files=files),indent=2))
print('archived',len(files),'files',sum(x['bytes'] for x in files.values()))

