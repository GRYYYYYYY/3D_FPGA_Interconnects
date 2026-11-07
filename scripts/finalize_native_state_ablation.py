"""Preserve failed parallel attribution gate alongside serial diagnostic."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from prepare import write_json,sha256
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_state_ablation_20261102'
def main():
 a=json.loads((OUT/'analysis.json').read_text());serial=json.loads((OUT/'serial_control/serial/summary.json').read_text());audit=json.loads((OUT/'serial_evidence_verification.json').read_text());assert audit['status']=='passed'
 rows=serial['measurements'];assert len(rows)==12 and all(r['success'] for r in rows)
 groups=[]
 for case in sorted({r['case'] for r in rows}):
  rr=[r for r in rows if r['case']==case];keys=['iterations','critical_path_ns','wirelength','route_body_sha256']
  same=all(all(r[k]==rr[0][k] for k in keys) for r in rr);assert same
  for r in rr:
   cmd=r['command'];assert cmd[cmd.index('--router_algorithm')+1]=='timing_driven' and r['workers']==1 and r['cpu_budget']['cpu_set']==[32]
  groups.append(dict(case=case,equal_across_six_arms=same,**{k:rr[0][k] for k in keys}))
 c=dict(status='complete_with_failed_parallel_attribution_gate',parallel_samples=36,serial_diagnostic_samples=12,legal_samples=48,parallel_endpoint_gate_passed=a['endpoint_gate_passed'],both_endpoint_matches=sum(x['equivalent'] for x in a['endpoints'] if x['mode']=='both'),none_endpoint_matches=sum(x['equivalent'] for x in a['endpoints'] if x['mode']=='none'),serial=groups,
 conclusion='Dynamic notification mode consistently associates with changed parallel iteration counts; no strict attribution claim because the no-fix parallel endpoint did not reproduce stock in all repetitions. Both-fixed endpoint reproduces frozen in all six. Serial six-arm routes are identical per layout; this supports parallel sensitivity but proves neither a race nor a complete root cause.',
 limitations=['Serial diagnostic has one run per arm/layout.','No-fix s1 repeat2 CPD8.33758 versus stock7.05387 exceeds5% quality gate; legality alone is insufficient.','Cached same-ELF small regression from prior study remains unresolved.','Reload fix changes s1 final wirelength87885 to87893 despite same68 iterations, so it is not behaviorally inert.'],
 next='Capture per-iteration net partition assignment and BB notification histories, locate earliest divergence in parallel no-fix vs fixed modes; keep correctness fixes enabled by default.',default_changed=False)
 write_json(OUT/'conclusions.json',c)
 acceptance=json.loads((OUT/'acceptance.json').read_text());acceptance.update(total_legal_samples=48,serial_diagnostic_samples=12,serial_gate_passed=True,scientific_attribution_gate='failed');write_json(OUT/'acceptance.json',acceptance)
 with (OUT/'report.md').open('a') as f:
  f.write('\n## 端点门槛与追加诊断结论\n\n两修复→既有修复版6/6等价；无修复→原版仅3/6等价，整体并行归因门槛失败。无修复s1第三轮CPD8.33758ns，相对原版7.05387ns增加约18.2%，合法不代表质量合格。不能以该消融宣布严格定位，或为了速度撤销修复。\n\n追加单线程timing_driven串行对照12/12合法，每布局六臂的路由主体、CPD、线长、轮数完全相同：s1为55轮/7.52035ns/88168，s2为56轮/7.9263ns/89800。这与并行通知/分区执行敏感性相符，但不证明竞态或完整根因；串行只有每臂一次。\n\n动态通知开启与s1的68轮、s2的47轮稳定关联。重载通知也并非完全无影响：s1仅动态模式线长87885，两修复87893，虽然均68轮。下一步应捕获每轮BB通知、网络分区与执行顺序，寻找最早分歧。先前同ELF缓存约3.3%退化仍未完全定位。默认、历史二进制和源码保持不变。\n')
 active=[]
 for d in Path('/proc').iterdir():
  if not d.name.isdigit():continue
  try:
   cmd=(d/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');cwd=(d/'cwd').resolve()
   if str(cwd).startswith(str(OUT)) and cmd.split(' ')[0].endswith(('vpr','vpr_state','vpr_cpu')):active.append(d.name)
  except OSError:pass
 assert not active
 write_json(OUT/'solver_process_check.json',dict(status='passed',active_owned_solvers=active,observed_utc=datetime.now(timezone.utc).isoformat()))
 h=ROOT/'HANDOFF.md';s=h.read_text();start=s.index('## 并行状态修复消融');end=s.index('## 新电路重复',start)
 (OUT/'HANDOFF.before_finalization.md').write_text(s)
 head='''## 并行状态修复消融已完成，归因门槛未通过（最新）

results/native_state_ablation_20261102：36项同八核缓存消融+12项追加单线程timing_driven诊断，48项全部合法且map字节等价、原生及独立FULL/STA通过。报告report.md、analysis.json、acceptance.json、conclusions.json；独立两份evidence_verification.json和serial_evidence_verification.json。无待运行求解/队列，勿重启owner。默认源码/二进制不改。

隔离构建只替换route.cpp.o（单ELF四模式none/dynamic/reload/both），使用原编译/链接参数与只读旧库，补丁及build_provenance.json留存。外部stock/frozen端点作校验。both与frozen6/6路由/CPD/WL/轮数一致；none与stock仅3/6，预声明整体并行归因门槛失败，不作严格因果定位。none s1第三轮CPD8.33758ns对stock7.05387ns退化约18.2%，不能把合法都当作质量合格。

动态通知开启的模式均稳定s1=68轮、s2=47轮；关闭时s1=49/51、s2=60/61。重载通知不是完全无影响：s1仅dynamic线长87885，both87893，均68轮。串行追加12项每布局六模式路由主体完全相同（s1 55轮/7.52035ns/88168；s2 56轮/7.9263ns/89800），支持并行通知/分区执行敏感性，但未证明竞态或完整根因；串行每臂仅一次。

下一步：记录每轮BB通知、网络分区归属与执行顺序，定位最早分歧；保持两修复默认开启，不以不稳定无修复路径作为速度优化。上一轮同ELF缓存小幅退化仍未解决，不能宣称全是噪声。以下旧状态以本节为准。

'''
 h.write_text(s[:start]+head+s[end:])
 files=list(OUT.glob('*.json'))+list(OUT.glob('*.md'))+list(OUT.glob('*.patch'))+[ROOT/'scripts'/n for n in ['build_native_state_ablation.py','run_native_state_ablation.py','report_native_state_ablation.py','finalize_native_state_ablation.py']]
 write_json(OUT/'final_artifact_manifest.json',{str(p.relative_to(ROOT)):sha256(p) for p in files})
 print(json.dumps(c,ensure_ascii=False))
if __name__=='__main__':main()
