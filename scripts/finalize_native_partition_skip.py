"""Retain quality-rejected candidate and diagnose configuration correction."""
from pathlib import Path
from datetime import datetime,timezone
import json
from prepare import write_json,sha256
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_partition_skip_20261102'
def read(p):return json.loads(p.read_text())
def main():
 assert read(OUT/'evidence_verification.json')['status']=='passed'
 gate=read(OUT/'gate/serial/summary.json')['measurements'];diag=read(OUT/'diagnostic_repair/serial/summary.json')['measurements'];assert len(gate)==10 and len(diag)==4 and all(r['success'] for r in gate+diag)
 q=[];invariants=[];excluded=[];bindings={}
 for r in gate:
  want={'VPR_HYBRID_LOOKAHEAD_PARALLEL':'1'}
  if r['variant'] in ['control','candidate']:want['VPR_CPU_SKIP_SAME_PARTITION']='1' if r['variant']=='candidate' else '0'
  if r['variant'].startswith('diag_'):
   assert 'VPR_CPU_STATE_TRACE' not in r['candidate_environment'];excluded.append(dict(key=r['key'],actual_env=r['candidate_environment'],reason='Suffix collision selected plain control/candidate environment; not a diagnostic capture. Retained, excluded from claims.'));continue
  assert r['candidate_environment']==want and r['workers']==8 and r['cpu_budget']['cpu_set']==list(range(32,40))
 for case in ['s38417_s1','s38417_s2']:
  rr={r['variant']:r for r in gate if r['case']==case};ref,a,b=[rr[v] for v in ['reference','control','candidate']]
  assert all(a[k]==ref[k] for k in ['critical_path_ns','wirelength','iterations','route_body_sha256'])
  cp=100*(b['critical_path_ns']/a['critical_path_ns']-1);wl=100*(b['wirelength']/a['wirelength']-1)
  q.append(dict(case=case,control_cpd_ns=a['critical_path_ns'],candidate_cpd_ns=b['critical_path_ns'],cpd_regression_percent=cp,wirelength_regression_percent=wl,control_wirelength=a['wirelength'],candidate_wirelength=b['wirelength'],iterations=[a['iterations'],b['iterations']],quality_passed=cp<=5 and wl<=5))
  dd={r['variant']:r for r in diag if r['case']==case}
  for name,plain in [('tracectrl',a),('traceskip',b)]:
   r=dd[name];want={'VPR_HYBRID_LOOKAHEAD_PARALLEL':'1','VPR_CPU_REPAIR_MODE':'both','VPR_CPU_STATE_TRACE':'1','VPR_CPU_STATE_TRACE_ITERS':'5','VPR_CPU_SKIP_SAME_PARTITION':'1' if name=='traceskip' else '0'}
   assert r['candidate_environment']==want and r['workers']==8
   assert all(r[k]==plain[k] for k in ['critical_path_ns','wirelength','iterations','route_body_sha256'])
   d=Path(r['directory']);f=d/'state_invariants.tsv';records=[list(map(int,l.split())) for l in f.read_text().splitlines()];assert [x[0] for x in records]==list(range(1,r['iterations']+1)) and all(x[1]>0 and x[2]==0 for x in records)
   t=d/'state_trace.tsv';events=[list(map(int,l.split())) for l in t.read_text().splitlines()];skips=[x for x in events if x[2]==8];assert bool(skips)==(name=='traceskip')
   for file in [f,t]:bindings[str(file)]=sha256(file)
   invariants.append(dict(case=case,variant=name,iterations=len(records),net_boundary_checks=sum(x[1] for x in records),stale=0,first5_skips=len(skips),plain_diagnostic_endpoint_equal=True))
 assert not all(x['quality_passed'] for x in q)
 assert not (OUT/'guard').exists() and not (OUT/'formal').exists()
 result=dict(status='complete_candidate_rejected',total_native_samples=14,legal_samples=14,plain_gate_samples=6,valid_diagnostic_samples=4,misconfigured_diagnostic_samples=4,excluded=excluded,quality=q,invariants=invariants,trace_bindings=bindings,guard_run=False,formal_run=False,performance_claim=False,default_changed=False,reason='CPD quality gate failed in both layouts although containment and legal routing pass. No-op set mutations affect heuristic order and QoR.')
 write_json(OUT/'analysis.json',result);write_json(OUT/'acceptance.json',dict(status='candidate_rejected',quality_gate_passed=False,all_iteration_containment_passed=True,control_endpoint_passed=True,diagnostic_endpoint_passed=True,legal_samples=14,valid_diagnostic_samples=4,misconfigured_diagnostic_samples=4,formal_samples=0,default_changed=False))
 lines=['# 跳过同分区无效重插入：候选未通过质量门槛','', '候选已实现并验证，结论是不采用。保留动态BB通知、全量重载通知和必要跨分区迁移，仅在old==new时跳过erase/insert与重复映射赋值。开关默认关闭，历史源/库/二进制不变。', '',
 '|布局|控制CPD ns|候选CPD ns|CPD变化|线长变化|轮数 控制→候选|质量门槛|','|---|---:|---:|---:|---:|---|---|']
 for x in q:lines.append(f"|{x['case']}|{x['control_cpd_ns']}|{x['candidate_cpd_ns']}|{x['cpd_regression_percent']:+.2f}%|{x['wirelength_regression_percent']:+.2f}%|{x['iterations'][0]}→{x['iterations'][1]}|未通过|")
 lines+=['','两布局候选均超过预声明CPD最多恶化5%的门槛。门槛实验每臂一次，未进行性能重复，因此不报告速度比。s1轮数减少不代表优化成功；s2轮数反而增加。', '',
 '## 正确性与归因','',
 '6项未诊断门槛（两布局×reference/control/candidate）：新同ELF控制与既有修复版路由主体、CPD、线长、轮数相同。4项正确启用诊断的补充运行与对应plain端点也一致。所有14次原生运行均合法，map逐字节等价、原生及独立FULL/STA通过；合法不能替代质量门槛。', '',
 '|布局|诊断臂|检查轮数|网络边界检查数|越界数|首五轮跳过重插入数|','|---|---|---:|---:|---:|---:|']
 for x in invariants:lines.append(f"|{x['case']}|{x['variant']}|{x['iterations']}|{x['net_boundary_checks']}|0|{x['first5_skips']}|")
 lines+=['','保持分区归属正确，并不意味着启发式路由顺序和质量不变。这个候选移除了同分区重插入所带来的容器顺序变化，实际改变了后续路径选择；不能将其视为严格语义不变的性能优化。没有撤销任何正确性修复。', '',
 '## 保留的执行问题','',
 '最初4个diag_control/diag_candidate臂因旧包装器按后缀选变体，与control/candidate冲突，实际未开启trace。原记录及env保留，不用于边界诊断结论。改为不冲突的tracectrl/traceskip后仅补4项；已有plain门槛不重跑。监督器因此留下stopped_for_review原回执；final_status.json记录复核后的拒绝终态。原冻结runner未修改。', '',
 'elliptic预定案例路径在提交前发现不存在，按既有数据修正，原计划与planning_correction.json保留；由于s38417质量失败，elliptic guard及72项正式性能矩阵均未启动。这是按门槛停止推广，不是性能工作遗漏。', '',
 '## 结论与后续','',
 '拒绝本候选，保留既有CPU lookahead主线和两处状态修复。若继续研究确定性同扇出排序，应作为独立的QoR敏感算法变更重新设门槛；不能以本次跳过重插入结果宣称加速。优先扩展已有lookahead主线的大图独立验证。', '',
 '复现：build_native_partition_skip.py、run_native_partition_skip.py、finalize_native_partition_skip.py；修改仅candidate.patch，来源build_provenance.json，原生审计evidence_verification.json，详细env/失败门槛/trace绑定analysis.json。本报告不改变此前CPU主线测量结论。']
 (OUT/'report.md').write_text('\n'.join(lines)+'\n')
 active=[]
 for d in Path('/proc').iterdir():
  if not d.name.isdigit():continue
  try:
   cmd=(d/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');cwd=(d/'cwd').resolve()
   if str(cwd).startswith(str(OUT)) and cmd.split(' ')[0].endswith(('vpr','vpr_plain','vpr_diag','vpr_cpu')):active.append(d.name)
  except OSError:pass
 assert not active
 write_json(OUT/'final_status.json',dict(status='complete_candidate_rejected',observed_utc=datetime.now(timezone.utc).isoformat(),active_owned_solvers=active,guard_run=False,formal_run=False,original_supervisor_preserved=True))
 h=ROOT/'HANDOFF.md';s=h.read_text();start=s.index('## 同分区无效重插入');end=s.index('## 逐轮BB',start);(OUT/'HANDOFF.before_finalization.md').write_text(s)
 head='''## 同分区无效重插入候选已拒绝（最新）

results/native_partition_skip_20261102：候选实现完成但质量门槛失败，不推广、不改默认。report.md、analysis.json、acceptance.json、final_status.json为终态，无活动求解/队列。原supervisor.json保留诊断包装器异常的stopped_for_review，不要重启。

s38417_s1控制→候选CPD6.96051→8.61087ns（+23.71%），轮数68→65；s2为7.7556→8.28151ns（+6.78%），轮数47→54。均超过CPD/WL最多5%退化门槛。跳过old==new删除再插入保持分区归属正确，但改变启发式顺序，不能当严格语义不变优化。

14次原生运行全部合法且map字节等价、原生/独立FULL/STA通过：6项plain门槛、最初4项错误未启用trace的诊断（保留并排除）、补4项正确诊断。旧wrapper按后缀匹配diag_control/candidate撞上control/candidate；改名tracectrl/traceskip补跑，未修改冻结runner。有效诊断control/candidate的68/65与47/54轮均零分区越界，候选首5轮跳过851/785次重插入，plain/diag最终路由质量一致。新control与既有frozen端点一致。

质量失败后按冻结协议未启动elliptic guard和72项正式性能矩阵，不报告速度比。guard的错误case路径在提交前修正并留planning_correction.json，仍未执行。当前两处正确性修复保留，跳过开关默认0；隔离构建未改变历史source/library/ELF。

下一步建议回到已验证的CPU lookahead大图泛化；若研究显式同扇出排序，需独立QoR门槛，不能沿用此候选的加速主张。此前同ELF缓存小幅退化仍未解决，旧无修复端点门槛失败保持。以下历史状态以本节为准。

'''
 h.write_text(s[:start]+head+s[end:]);files=list(OUT.glob('*.json'))+list(OUT.glob('*.md'))+list(OUT.glob('*.patch'))+[ROOT/'scripts'/n for n in ['build_native_partition_skip.py','run_native_partition_skip.py','finalize_native_partition_skip.py']]
 write_json(OUT/'final_artifact_manifest.json',{str(f.relative_to(ROOT)):sha256(f) for f in files})
 print(json.dumps(dict(status=result['status'],quality=q,invariants=invariants),ensure_ascii=False))
if __name__=='__main__':main()
