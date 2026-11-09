"""Validate complete R5 evidence, scope gates and preservation before publishing."""
import argparse,json,re,subprocess
from pathlib import Path
from prepare import sha256
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);p.add_argument('--archive',type=Path);a=p.parse_args();r=a.experiment.resolve();root=Path(__file__).resolve().parents[1];checks=[]
def check(v,label):
 assert v,label
 checks.append(label)
for path,digest in json.loads((r/'plan.json').read_text())['protected'].items():check(sha256(root/path)==digest,'protected '+path)
d=json.loads((r/'report_final.json').read_text());check(len(d['workloads'])==8,'eight real complete inputs');check(d['board_measured'] is False,'no board claim')
for w in d['workloads']:
 check(sha256(Path(w['path']))==w['sha256'],'input '+w['case'])
 rows=[json.loads(l) for l in (r/'per_sample_stats.jsonl').read_text().splitlines() if json.loads(l)['case']==w['case']];check(len(rows)==2*w['J'],'all native qids both modes '+w['case']);check(all(x['map_match'] for x in rows),'maps '+w['case'])
for h in d['hardware']:
 ctx=h['contexts'];base=r/f'hls_ctx{ctx}_clean';b=json.loads((base/'binding.json').read_text())
 for name,digest in b['sources'].items():check(sha256(base/'source_snapshot'/name)==digest,f'ctx{ctx} frozen '+name)
 for name in ['interleave5.cpp','api5.hpp','loader5.hpp','search5.hpp','tb5.cpp']:check(sha256(root/'accel/lookahead/round5'/name)==b['sources'][name],f'ctx{ctx} current '+name)
 check(h['dispatch_ii']==3,'observed HLS II ctx'+str(ctx));check(h['verified_mhz'] is None,'no invented clock ctx'+str(ctx));check(h['rtl_probe']['status']=='passed','bounded cosim ctx'+str(ctx));check(h['monitor']['status']=='passed','observer ctx'+str(ctx));check(h['monitor']['warm_graph_axi_zero'],'no warm graph traffic ctx'+str(ctx));check(h['monitor']['cycles']==h['rtl_cycles'],'unchanged observer cycles ctx'+str(ctx))
 for i,t in enumerate(h['monitor']['transactions']):
  check(all(p['read_requests']==p['read_completions'] and p['write_requests']==p['write_responses'] for p in t['ports']),'AXI drain '+str(ctx)+'/'+str(i))
 check(h['calls'][0]['dispatch_observed_gap_min']==3 and h['calls'][0]['dispatch_observed_gap_max']==3,'actual issue gap ctx'+str(ctx))
 check(h['calls'][0]['pipeline_overlap_cycles']>0,'actual pipeline overlap ctx'+str(ctx))
 check(not (base/'impl.json').exists(),'OOC gate respected ctx'+str(ctx))
worker=r/'gpu_worker_new';done=json.loads((worker/'finished.json').read_text());check(done['status']=='passed' and done['processes']==80,'new software cohort');rows=json.loads((worker/'measurements.json').read_text());check(sum(len(x['measurements']) for x in rows)==480,'480 checked timed calls')
for name in ['cpu4.cpp','cuda4.cu','cuda_kernel4.cuh','reference4.hpp']:check(sha256(worker/'source/round4'/name)==sha256(root/'accel/lookahead/round4'/name),'unchanged benchmark '+name)
for row in rows:
 check(all(x['all_golden_bits_match'] for x in row['measurements']),'software map '+row['log'])
 profile=next(w['early'] for w in d['workloads'] if w['case']==row['case']);check(all((m['pops'],m['pushes'],m['edges'])==(profile['pops'],profile['pushes'],profile['original_edges']) for m in row['measurements']),'same algorithm counts '+row['log'])
check('100% tests passed' in (r/'ctest.log').read_text(),'CTest all old/new');check(json.loads((r/'heap_audit/result.json').read_text())['status']=='passed','entire heap arrangement full/early')
# Previous immutable evidence indices are checked in place, not copied.
history=[]
for idx in sorted((root/'results').glob('*/evidence_snapshot/index.json')):
 if idx.parent.parent==r:continue
 files=json.loads(idx.read_text())['files']
 for name,meta in files.items():assert sha256(idx.parent/name)==meta['sha256'],name
 history.append(dict(path=str(idx.relative_to(root)),files=len(files)))
check(len(history)==4,'four historical archives unchanged')
if a.archive:
 idx=json.loads((a.archive/'index.json').read_text())
 for name,meta in idx['files'].items():check(sha256(a.archive/name)==meta['sha256'],'archive '+name)
name='archive_validation.json' if a.archive else 'validation.json';target=r/name;assert not target.exists()
target.write_text(json.dumps(dict(status='passed',checks=len(checks),names=checks,history=history,report_sha256=sha256(r/'report_final.json')),indent=2)+'\n');print(len(checks),'checks passed')
