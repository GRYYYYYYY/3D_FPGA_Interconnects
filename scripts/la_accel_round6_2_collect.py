"""Collect R6.2 only after finite worker stops; raw negative results retained."""
import json,sys,struct,hashlib,statistics,subprocess
from pathlib import Path
from prepare import sha256
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]);o=r/'worker';rows=json.load(open(o/'rows.json'))
finished=json.load(open(o/'finished.json'))
assert finished['status']=='completed', 'Do not collect partial experiment statistics as a completed result'
def stat(values):return dict(samples=values,n=len(values),median=statistics.median(values),mean=statistics.mean(values),sample_SD=statistics.stdev(values) if len(values)>1 else None,min=min(values),max=max(values))
formal=[x for x in rows if isinstance(x['repeat'],int) and not x['qualification_diagnostic']]
summary=[]
for case,arm in sorted(set((x['case'],x['backend']) for x in formal)):
 a=[x for x in formal if x['case']==case and x['backend']==arm]
 summary.append(dict(case=case,backend=arm,E2_s=stat([x['E2_s'] for x in a]),Process_s=stat([x['Process_wall_s'] for x in a]),qor=[dict(repeat=x['repeat'],CPD_ns=x['metrics']['critical_path_ns'],wirelength=x['metrics']['wirelength'],iterations=x['metrics'].get('iterations'),qualified=x['qualified']) for x in a],all_qualified=all(x['qualified'] for x in a),cohort='R6.2 same worker',cross_worker_ratios_allowed=False))
ratios=[];by={(x['backend'],x['repeat']):x for x in formal if x['case']=='lstm_s2'}
if len(by)==15:
 for base in ['stock','flat','pipeline','alt_cpu']:
  for candidate in ['alt_cpu','alt_cuda']:
   if base==candidate:continue
   for scope in ['E2_s','Process_wall_s']:
    vals=[by[base,i][scope]/by[candidate,i][scope] for i in range(3)]
    ratios.append(dict(case='lstm_s2',baseline=base,candidate=candidate,scope=scope,paired=stat(vals),ratio_of_medians=statistics.median([by[base,i][scope] for i in range(3)])/statistics.median([by[candidate,i][scope] for i in range(3)])))
qual=[x for x in rows if x['case']=='lstm_s2' and x['repeat']=='qualification']
diffs=[]
for a,b in [('pipeline','flat'),('stock','flat'),('alt_cpu','flat'),('alt_cuda','alt_cpu')]:
 p=o/f'lstm_s2_{a}_qualification/wire_map.bin';q=o/f'lstm_s2_{b}_qualification/wire_map.bin'
 if p.exists() and q.exists():
  cmd=[str(r/'native_map_diff6'),str(p),str(q)];z=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=60)
  diffs.append(dict(pair=a+'_vs_'+b,**json.loads(z.stdout)))
caps=[]
for arm in ['alt_cpu','alt_cuda']:
 p=o/f'lstm_s2_{arm}_qualification/native_input.bin'
 if not p.exists():continue
 with p.open('rb') as f:h=struct.unpack('<7Q',f.read(56))
 cut=p.stat().st_size-h[3]*h[5]*8;dig=hashlib.sha256();oh=hashlib.sha256()
 with p.open('rb') as f:
  remain=cut
  while remain:buf=f.read(min(remain,8*1024*1024));assert buf;dig.update(buf);remain-=len(buf)
  for buf in iter(lambda:f.read(8*1024*1024),b''):oh.update(buf)
 caps.append(dict(backend=arm,header=h,input_prefix_sha256=dig.hexdigest(),output_sha256=oh.hexdigest(),path=str(p),file_sha256=sha256(p)))
cap_equal=len(caps)==2 and caps[0]['input_prefix_sha256']==caps[1]['input_prefix_sha256'] and caps[0]['output_sha256']==caps[1]['output_sha256']
out=dict(status=json.load(open(o/'finished.json')),plan_sha256=sha256(r/'holdout_plan.json'),worker=json.load(open(o/'worker.json')),qualification=qual,formal_rows=formal,summary=summary,paired_ratios=ratios,map_differences=diffs,sample_capture_bindings=caps,all_live_CPU_CUDA_pairs_equal=cap_equal,qualification_gate=json.load(open(o/'qualification_gate.json')) if (o/'qualification_gate.json').exists() else None,Pipeline_supplement='s38417/BNN three processes each on new worker, same frozen ELF and mapped/QoR checked. No ratio to historical worker; R6.1 GPU-vs-Flat remains Flat-only.',generalization='one preselected LSTM seed2; no architecture or seed sweep; structural audit covers no-fanin subset only',STRICT_equivalent=False,compact_direct_native_qualified=False,selector_implemented=False)
out['three_dimensional_usage']=json.load(open(r/'holdout_3d_scope.json'))
(r/'holdout_results.json').write_text(json.dumps(out,indent=2))
# Include affected candidate qualifications and negative timing if P2 ran.
launch_path=r/'targeted_optimization_launch.json';opt=json.load(open(launch_path))
orecs=[x for x in rows if str(x['repeat']).startswith('reserve_')]
if orecs:
 result=dict(launch_decision=opt,rows=orecs,paired_statistics=[],complete_input_output_identity=[])
 prior=json.load(open(R/'results/lookahead_accel_round6_1_20261109T160000Z/native_cpu_identity.json'))
 for x in [v for v in orecs if v['repeat']=='reserve_qualification']:
  p=Path(x['native_capture']['path']);expected=next(v for v in prior if v['case']==x['case']);expected=next(v for v in expected['actual_inputs'] if v['arm']=='alt_s20')
  with p.open('rb') as f:head=struct.unpack('<7Q',f.read(56))
  cut=p.stat().st_size-head[3]*head[5]*8;dig=hashlib.sha256();oh=hashlib.sha256()
  with p.open('rb') as f:
   remain=cut
   while remain:buf=f.read(min(remain,8*1024*1024));assert buf;dig.update(buf);remain-=len(buf)
   for buf in iter(lambda:f.read(8*1024*1024),b''):oh.update(buf)
  eq=dig.hexdigest()==expected['input_prefix_sha256'] and oh.hexdigest()==expected['output_sha256'];assert eq,'P2 changed dense input/output bytes'
  result['complete_input_output_identity'].append(dict(case=x['case'],backend=x['backend'],header=head,input_prefix_sha256=dig.hexdigest(),output_sha256=oh.hexdigest(),frozen_R61_input_output_equal=eq))
 for case in ['s38417','bnn']:
  for scope in ['E2_s','Process_wall_s']:
   a=[next(x for x in orecs if x['case']==case and x['backend']=='alt_cuda' and x.get('optimization_repeat')==i)[scope] for i in range(3)]
   b=[next(x for x in orecs if x['case']==case and x['backend']=='alt_cuda_reserve' and x.get('optimization_repeat')==i)[scope] for i in range(3)]
   result['paired_statistics'].append(dict(case=case,scope=scope,baseline=stat(a),candidate=stat(b),paired=stat([x/y for x,y in zip(a,b)]),ratio_of_medians=statistics.median(a)/statistics.median(b)))
 (r/'targeted_optimization_results.json').write_text(json.dumps(result,indent=2))
 assert len(orecs)==16 and all(x['qualified'] for x in orecs)
 conclusions=[]
 for case in ['s38417','bnn']:
  for scope in ['E2_s','Process_wall_s']:
   s=next(x['paired'] for x in result['paired_statistics'] if x['case']==case and x['scope']==scope)
   outcome='三对均加速' if min(s['samples'])>1 else '三对均变慢' if max(s['samples'])<1 else '三对方向不一致，未证明一致收益'
   conclusions.append(f"{case} {scope}: {s['mean']:.3f}±{s['sample_SD']:.3f}×（{outcome}）。")
 final=opt|dict(status='completed_qualified_measured',launch_request_sha256=sha256(launch_path),
  results_sha256=sha256(r/'targeted_optimization_results.json'),affected_qualifications=4,
  paired_formal_processes=12,default_changed=False,LSTM_optimized_qualification_inherited=False,
  CPU_candidate_formal_timing=False,stop_decision='STOP_P2_NO_SECOND_CANDIDATE',
  measured_interpretation=' '.join(conclusions)+' 唯一候选保留为独立实验，不改默认路径；本轮P2到此结束。',
  paired_statistics=result['paired_statistics'],build_setup_failure_retained='candidate_build_failure.json')
 (r/'targeted_optimization.json').write_text(json.dumps(final,indent=2))
print('collected',len(formal),'formal rows; captures equal',cap_equal,'map diff',diffs)

