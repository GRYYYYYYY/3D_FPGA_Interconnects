"""Independent terminal review from raw logs, actual commands, topology and hashes.

Does not call the study report or its validity/statistics helpers. No solver runs.
"""
import json,math,re,statistics
from pathlib import Path
from datetime import datetime,timezone
from prepare import sha256,write_json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_paper_closure_20261105/scaling'
def read(p):return json.loads(Path(p).read_text())
def bind(p):return dict(path=str(Path(p).resolve()),sha256=sha256(p))
def counters(s):return {line.split()[0]:int(line.split()[1]) for line in s.splitlines()}
def ratios(v):return dict(ratios=v,median=statistics.median(v),minimum=min(v),maximum=max(v))
def close(a,b):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(a,b)
def main():
 plan=read(OUT/'plan.json');state=read(OUT/'summary.json');published=read(OUT/'analysis.json');audit=read(OUT/'audit.json')
 assert state['status']=='completed' and audit['status']=='passed'
 verified={}
 def verify(b):
  if b['path'] not in verified:verified[b['path']]=sha256(b['path'])
  assert verified[b['path']]==b['sha256'],b['path']
 for b in list(plan['bindings'].values())+list(plan['binaries'].values())+[plan['runtime'],state['plan']]:verify(b)
 for b in read(plan['runtime']['path'])['libraries']:verify(b)
 # Scope source from the parent study; performance binary is separately frozen.
 prior=read(ROOT/'results/native_lookahead_component_20261104/plan.json')
 for b in prior['scope_source_bindings'].values():verify(b)
 for b in audit['artifacts']:verify(b)
 cases={}
 for g,e in plan['cases'].items():
  verify(e['case']);verify(e['reference_map']);cases[g]=read(e['case']['path'])
  for b in cases[g]['inputs'].values():verify(b)
 assert len({c['inputs']['rr_graph']['sha256'] for c in cases.values()})==3
 rows=state['measurements'];assert len(rows)==len(plan['jobs'])==96
 topology={x['cpu']:x for x in state['topology']};pool=state['pool'];assert len(pool)==16
 assert len({(topology[c]['socket'],topology[c]['core']) for c in pool})==16
 assert len({topology[c]['node'] for c in pool})==1
 extracted=[];last_end=None;artifact_files={};memory=[];cgroup=[];diagnostics={}
 for job,row in zip(plan['jobs'],rows):
  assert all(row[k]==v for k,v in job.items());d=Path(row['directory']);assert d==OUT/job['key']
  assert read(d/'measurement.json')==row
  begin=datetime.fromisoformat(row['started_utc']);end=datetime.fromisoformat(row['finished_utc']);assert begin<end
  if last_end:assert last_end<=begin,'Overlapping jobs'
  last_end=end
  c=cases[row['graph']];args=row['actual_process']['command'];assert args==row['command']
  assert args[:3]==[plan['binaries']['cpu']['path'],c['inputs']['architecture']['path'],c['inputs']['circuit']['path']]
  def opt(k):assert args.count(k)==1,k;return args[args.index(k)+1]
  assert opt('--num_workers')==str(row['workers']) and opt('--max_router_iterations')=='1'
  assert opt('--router_algorithm')=='parallel' and opt('--router_lookahead')=='map'
  assert opt('--read_rr_graph')==c['inputs']['rr_graph']['path']
  assert opt('--route_chan_width')==str(c['route_chan_width']) and opt('--seed')==str(c['seed'])
  assert opt('--device_width')==str(c['device_width']) and opt('--target_utilization')==str(c['target_utilization'])
  assert opt('--generate_rr_node_overuse_report')=='off'
  assert opt('--write_router_lookahead')==str(d/'wire_map.bin')
  assert '--read_router_lookahead' not in args and '--analysis' not in args and '--route' in args
  for role,n,k in [('packed_netlist','packed.net','--net_file'),('placement','fixed.place','--place_file')]:
   assert opt(k)==str(d/n);assert sha256(d/n)==c['inputs'][role]['sha256']
  want={'OMP_NUM_THREADS':'1','LC_ALL':'C','VPR_HYBRID_LOOKAHEAD_TASKS':'1' if row['arm']=='pipeline' else '0','VPR_HYBRID_LOOKAHEAD_PARALLEL':'1'}
  if row['phase']=='diagnostic':want['VPR_HYBRID_LOOKAHEAD_REPORT']=str(d/'lookahead_profile.jsonl')
  assert row['actual_process']['environment']==want
  cpus=pool[:row['workers']];resource=read(d/'process.log.resources.json');assert resource==row['cpu_budget_audit']
  assert resource['verified'] and resource['samples']>0 and not resource['affinity_violations']
  assert cpus==row['actual_process']['cpu_set']==resource['permitted_cpu_set']==row['cpu_budget']['cpu_set']
  assert begin<=datetime.fromisoformat(row['actual_process']['utc'])<=end
  for snap in ['cgroup_before','cgroup_after']:
   quota=resource[snap]['/sys/fs/cgroup/cpu.max'].split();assert quota[0]=='max' or int(quota[0])/int(quota[1])>=row['workers']
  before=counters(resource['cgroup_before']['/sys/fs/cgroup/cpu.stat']);after=counters(resource['cgroup_after']['/sys/fs/cgroup/cpu.stat'])
  events_before=counters(resource['cgroup_before']['/sys/fs/cgroup/memory.events']);events_after=counters(resource['cgroup_after']['/sys/fs/cgroup/memory.events'])
  cgroup.append(dict(key=row['key'],throttled_usec_delta=after.get('throttled_usec',0)-before.get('throttled_usec',0),oom_delta=events_after.get('oom',0)-events_before.get('oom',0),oom_kill_delta=events_after.get('oom_kill',0)-events_before.get('oom_kill',0)))
  text=(d/'process.log').read_text();timer=list(re.finditer(r'^# Computing router lookahead map took ([\d.]+) seconds \(max_rss ([\d.]+) MiB, delta_rss ([+\-\d.]+) MiB\)',text,re.M));route=re.search(r'^# Routing\s*$',text,re.M)
  assert len(timer)==1 and route and timer[0].end()<route.start()
  sec=float(timer[0][1]);assert sec>0;close(sec,row['build_seconds'])
  iterations=re.findall(r'^\s*(\d+)\s+[\d.]+\s+[\d.eE+-]+\s+\d+\s+[\d.eE+]+\s+\d+\s+\d+\s+\d+\s+\(',text,re.M)
  assert iterations==['1'] and row['returncode']==2 and row['status']=='failed' and 'VPR failed to implement circuit' in text
  assert not row['routing_success_observed'] and row['component_valid'] and row['normal_capped_exit']
  expected=plan['cases'][row['graph']]['reference_map']['sha256'];assert sha256(d/'wire_map.bin')==expected==row['wire_map_sha256']
  flow=re.findall(r'The entire flow of VPR took [\d.]+ seconds \(max_rss ([\d.]+) MiB\)',text);rr=re.findall(r'Loading routing resource graph took [\d.]+ seconds \(max_rss ([\d.]+) MiB',text)
  assert len(flow)==len(rr)==1
  ext=resource['peak_observed_hwm_kib']/1024;native=float(flow[0]);pre=float(rr[0]);la=float(timer[0][2])
  memory.append(dict(key=row['key'],graph=row['graph'],arm=row['arm'],workers=row['workers'],phase=row['phase'],repeat=row['repeat'],native_flow_max_rss_mib=native,after_rr_load_high_water_mib=pre,after_lookahead_high_water_mib=la,lookahead_high_water_increase_mib=float(timer[0][3]),external_sampled_hwm_mib=ext,external_samples=resource['samples'],external_missed_native_high_water_by_over_1pct=ext<native*.99))
  extracted.append(dict(key=row['key'],graph=row['graph'],arm=row['arm'],workers=row['workers'],phase=row['phase'],repeat=row['repeat'],seconds=sec))
  if row['phase']=='diagnostic':
   events=[json.loads(l) for l in (d/'lookahead_profile.jsonl').read_text().splitlines()]
   diagnostics[row['graph']+'/'+row['arm']]=dict(events=events,total_samples=sum(e['samples'] for e in events),maximum_group_width=max(e['samples'] for e in events) if row['arm']=='per_group' else None,search_thread_seconds=sum(e['search_ns'] for e in events)/1e9,scheduler_wall_seconds=sum(e['wall_ns'] for e in events)/1e9,workspaces=events[0].get('workspaces') if row['arm']=='pipeline' else None)
  for n in ['process.log','measurement.json','process.log.resources.json','wire_map.bin','packed.net','fixed.place','lookahead_profile.jsonl']:
   f=d/n
   if f.exists():artifact_files[str(f)]=bind(f)
 formal=[r for r in extracted if r['phase']=='formal'];assert len(formal)==90
 idx={(r['graph'],r['arm'],r['workers'],r['repeat']):r for r in formal};assert len(idx)==90
 scaling={};incremental={};memgroups={}
 for g in cases:
  for a in ['per_group','pipeline']:
   for w in [1,2,4,8,16]:
    values=[idx[g,a,1,r]['seconds']/idx[g,a,w,r]['seconds'] for r in range(3)];key=f'{g}/{a}/{w}'
    v=ratios(values);v.update(median_seconds=statistics.median(idx[g,a,w,r]['seconds'] for r in range(3)),efficiency=v['median']/w);scaling[key]=v
    for k in ['median','minimum','maximum','median_seconds','efficiency']:close(v[k],published['scaling'][key][k])
    assert values==published['scaling'][key]['ratios']
    mr=[x for x in memory if x['phase']=='formal' and x['graph']==g and x['arm']==a and x['workers']==w]
    memgroups[key]=dict(native_flow_max_rss_mib=[x['native_flow_max_rss_mib'] for x in mr],native_flow_median_mib=statistics.median(x['native_flow_max_rss_mib'] for x in mr),native_lookahead_high_water_mib=[x['after_lookahead_high_water_mib'] for x in mr],external_sampling_misses=sum(x['external_missed_native_high_water_by_over_1pct'] for x in mr))
  for w in [1,2,4,8,16]:
   key=f'{g}/{w}';v=ratios([idx[g,'per_group',w,r]['seconds']/idx[g,'pipeline',w,r]['seconds'] for r in range(3)]);incremental[key]=v
   assert v['ratios']==published['incremental'][key]['ratios']
   for k in ['median','minimum','maximum']:close(v[k],published['incremental'][key][k])
 review=dict(status='passed',utc=datetime.now(timezone.utc).isoformat(),formal_valid=90,diagnostics_valid=6,routing_successes=0,expected_capped_rc2=96,artifacts_reverified=len(artifact_files),bound_inputs_sources_and_existing_artifacts_reverified=len(verified),execution_order_nonoverlapping=True,actual_commands_env_affinities_verified=True,statistics_recomputed=True,scaling=scaling,incremental=incremental,memory_groups=memgroups,memory_rows=memory,diagnostics=diagnostics,cgroup_deltas=cgroup,
  caveats=['Shared host, separate existing CPU quota instance. No exclusive physical-core reservation.','All96 tails intentionally failed at1iteration; only stage/map validity, no end-to-end speed or QoR claim.','Native max_rss is RUSAGE_SELF process lifetime high-water mark, rounded0.1MiB, not a stage-local live-memory peak. External5second sampling can miss short processes.','Cgroup counter deltas include other work in the instance; lack of throttling does not certify lack of interference.','Native wall timers rounded0.01s; tseng0.1–0.3s cannot support precise small-percent differences.','Speedup baseline is each method at1core, not stock VPR; paired medians differ from ratios of median times.'],
  source_bindings={str(p):bind(p) for p in [ROOT/'vendor/vtr_cpu_slices/libs/libvtrutil/src/vtr_rusage.cpp',ROOT/'vendor/vtr_cpu_slices/libs/libvtrutil/src/vtr_time.cpp',Path(__file__)]},artifact_manifest=list(artifact_files.values()),default_changed=False)
 write_json(OUT/'independent_review.json',review)
 lines=['# 扩展性实验独立复核','', '90项正式与6项诊断全部完成：冻结输入/ELF/runner、实际命令/env/同NUMA物理核、96项顺序不重叠、582份产物和配对统计均重核通过。全部按预定1轮路由返回2，仅为lookahead阶段有效，不是96次合法路由。','', '|图|组内4核秒|组内16核秒|pipeline16核秒|pipeline1→16核|16核组内→pipeline|','|---|---:|---:|---:|---:|---:|']
 for g in cases:lines.append(f"|{g}|{scaling[g+'/per_group/4']['median_seconds']:.2f}|{scaling[g+'/per_group/16']['median_seconds']:.2f}|{scaling[g+'/pipeline/16']['median_seconds']:.2f}|{scaling[g+'/pipeline/16']['median']:.4f}×|{incremental[g+'/16']['median']:.4f}×|")
 lines+=['','大图组内方法在4核后进入平台期；pipeline在8/16核仍有稳定的阶段增益。DLA四核pipeline相对组内三次全部较慢（中位0.9526×），不能推广为所有核数获益。两核效率略高于100%是当前测量比值，不能据三次共享宿主测量宣称算法超线性。','', '独立诊断证实：BNN/DLA都是10组×4样本、pipeline40样本且8个工作区；tseng只有2组×4样本，总并行任务数8。后者16核收益小、效率低有明确任务规模限制，但未测硬件CPU忙闲占比或逐任务尾部等待，不能把累计线程搜索时间当CPU利用率。','', '|图|16核组内原生日志峰值MiB|16核pipeline原生日志峰值MiB|','|---|---:|---:|']
 for g in cases:lines.append(f"|{g}|{memgroups[g+'/per_group/16']['native_flow_median_mib']:.1f}|{memgroups[g+'/pipeline/16']['native_flow_median_mib']:.1f}|")
 misses=sum(x['external_missed_native_high_water_by_over_1pct'] for x in memory if x['phase']=='formal')
 lines += ['',f'外部5秒采样在{misses}/90项正式测量中低于原生日志峰值超过1%；小图采样常只看到进程启动。原始采样保留，但不作为小图内存占用结论。上述原生峰值来自getrusage(RUSAGE_SELF)，是截至timer结束的进程历史最高RSS。RR加载时的峰值可掩盖后续工作区增长，因此没有证据据此宣称pipeline省内存、零新增内存或阶段内存硬上限。','', '资源仍是共享宿主的另一CPU实例，严格隔离测量未完成。主指标只覆盖完整lookahead构建，不覆盖RR加载、序列化或布线；不能把这里约12×写成完整流程或相对原版的加速。','', '![阶段扩展性](scaling_review.png)','', '![进程历史峰值](memory_review.png)']
 (OUT/'review.md').write_text('\n'.join(lines)+'\n');print(json.dumps({k:review[k] for k in ['status','formal_valid','diagnostics_valid','artifacts_reverified','bound_inputs_sources_and_existing_artifacts_reverified']}));print('formal_external_memory_misses',misses)
if __name__=='__main__':main()
