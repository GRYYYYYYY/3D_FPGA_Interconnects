"""Publish earliest-divergence evidence and bounded conclusions."""
import json
from pathlib import Path
from datetime import datetime,timezone
from prepare import write_json,sha256
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_state_trace_20261102'
def main():
 a=json.loads((OUT/'analysis.json').read_text());assert a['legal']==24
 for d in a['comparisons']:
  if d['comparison']=='none_vs_both':
   one,two=d['iterations'][:2];assert one['bb_differences']==one['owner_differences']==one['order_partitions']==0
   assert two['bb_differences']==0 and two['owner_differences']>0
 proof=[]
 for case in ['s38417_s1','s38417_s2']:
  none=next(t for t in a['trace_summaries'] if t['case']==case and t['repeat']==0 and t['variant']=='on_none')
  both=next(t for t in a['trace_summaries'] if t['case']==case and t['repeat']==0 and t['variant']=='on_both')
  proof.append(dict(case=case,generated_notifications=both['iterations'][0]['dynamic'],delivered_none=none['iterations'][0]['notifications'],delivered_both=both['iterations'][0]['notifications'],first_moves=both['iterations'][0]['partition_moves'],first_same_partition_reinsertions=both['iterations'][0]['same_partition_reinsertions'],stale_none=[x['stale_count'] for x in none['iterations']],stale_both=[x['stale_count'] for x in both['iterations']]))
 c=dict(status='complete',samples=24,legal_samples=24,proof=proof,performance_claim=False,default_changed=False,
 conclusion='First iteration generates equal dynamic BB update sets; missing delivery leaves stale partition ownership at iteration2 with identical net BBs. Fixed runs maintain the original 2D containment predicate in all captured iterations. This establishes the notification-to-assignment mechanism in these traces, not the full origin of all timing or predecessor-state nondeterminism.',
 order_finding='Most delivered updates erase/reinsert nets without changing partition. Notification sets repeat but delivery order can vary; per-partition orders can differ despite equal BBs and ownership. Existing stable fanout sort inherits unordered-set tie order. Skipping no-op reinsertion/canonical tie order are candidates, not validated optimizations.',
 perturbation='Both-fixed controls agree across old/trace-off/trace-on for all4 case-repeat pairs. One of4 no-fix off/on pairs differs; tracing perturbation cannot be excluded. No speedup from diagnostic timings.',
 limits=['Only first5 iterations, two layouts and two repeats.','No RR predecessor write tracing or direct data-race proof.','The previous full parallel no-fix endpoint gate remains failed.','The prior small same-ELF cached runtime regression remains unresolved.'])
 write_json(OUT/'conclusions.json',c)
 lines=['# 逐轮 BB 通知、分区归属与执行顺序诊断','', '24项诊断运行全部合法，map字节等价、原生及独立FULL/STA通过。八份逐轮日志通过事件序号、首五轮覆盖、任务开始/结束配对、实际env/执行顺序/八核亲和性核验。全部运行仅作诊断，不报告性能加速。', '',
 '## 最早分歧','', '两布局、两次重复均观察到：第一轮的BB、分区归属和分区内计划顺序一致。第一轮结束后，无修复模式丢弃动态更新通知；修复模式送达。第二轮开始，网络BB仍相同，但分区归属已经不同；第三轮起BB也随路由轨迹分化。', '',
 '|布局|首轮通知生成数|无修复送达|修复送达|实际迁移|同分区删除再插入|无修复第1–5轮越界网络数|修复越界数|','|---|---:|---:|---:|---:|---:|---|---|']
 for x in proof:lines.append(f"|{x['case']}|{x['generated_notifications']}|{x['delivered_none']}|{x['delivered_both']}|{x['first_moves']}|{x['first_same_partition_reinsertions']}|{x['stale_none']}|{x['stale_both']}|")
 lines+=['','越界判定直接复用原PartitionTree的二维包含条件；不是最终布线非法的同义词。例：s1第二轮网络2850的BB x范围0–9，但仍分配在x范围0–8的分区2。修复后的归属满足边界条件；不能把遗漏通知保留旧分区作为提速策略。', '',
 '## 顺序变化与可研究优化','',
 'PartitionTree::update_nets即使old==new仍erase/insert；ParallelNetlistRouter随后从unordered_set生成列表，再按扇出stable_sort。首轮s1有142次、s2有131次同分区重新插入。重复运行中通知集合相同但到达顺序可以不同；s1修复模式第二轮起出现分区内顺序差异，而BB和归属仍相同。该机制与容器顺序/同扇出排序敏感性一致，不代表全局线程启动顺序必须一致。', '',
 '下一候选是保留所有必要通知与跨分区迁移，仅跳过old==new的删除再插入；另一个候选是显式稳定同扇出次序。两者都会改变既有启发式顺序，必须独立验证合法性、质量和未诊断完整进程收益；本轮尚未实现或证明它们有收益。', '',
 '## 诊断扰动与边界','',
 '四组两修复对照中，旧ELF、trace关闭、trace开启的最终路由/质量/轮数均一致。无修复四组中有一组trace关闭/开启不一致：51轮/8.33758ns与49轮/7.05387ns。不能排除诊断扰动，也不能把旧的无修复端点等价失败改写为通过。', '',
 '记录只覆盖前五轮，不能覆盖后期全量重载机制；没有记录RR前驱状态写入，不宣称证明了竞态或全部运行波动根因。上一轮同ELF缓存约3.3%退化仍未解决。默认两修复保持开启，历史源码/二进制不变。', '',
 '## 重现与字段','',
 'build_native_state_trace.py构建隔离route.cpp.o和partition_tree.cpp.o；run_native_state_trace.py执行24项；analyze_native_state_trace.py分析日志；本脚本写结论。首次overlay头文件重复定义的编译失败保留在build_first_failed.log，增加优先include路径后构建通过。', '',
 'state_trace.tsv各列：seq、iteration、kind、net、partition_path、aux、BB xmin/xmax/ymin/ymax/layer_min/layer_max、partition xmin/xmax/ymin/ymax。kind=0轮初快照、1分区内计划位置、2调用开始、3调用结束（aux为rerouted/retry/success位）、4通知送达、5迁移前、6迁移后、7动态更新列表。分区路径root=1,left=2p,right=2p+1。全局seq是观测点的原子线性化次序，不是确定性的完整路由执行顺序；按分区比较计划顺序才有意义。线程缓冲在barrier后输出。', '',
 '证据：analysis.json、conclusions.json、acceptance.json、evidence_verification.json、build_provenance.json及runs/serial各measurement.json/state_trace.tsv。']
 (OUT/'report.md').write_text('\n'.join(lines)+'\n')
 active=[]
 for d in Path('/proc').iterdir():
  if not d.name.isdigit():continue
  try:
   cmd=(d/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');cwd=(d/'cwd').resolve()
   if str(cwd).startswith(str(OUT)) and cmd.split(' ')[0].endswith(('vpr','vpr_state','vpr_trace')):active.append(d.name)
  except OSError:pass
 assert not active
 write_json(OUT/'solver_process_check.json',dict(status='passed',active_owned_solvers=active,observed_utc=datetime.now(timezone.utc).isoformat()))
 h=ROOT/'HANDOFF.md';s=h.read_text();start=s.index('## 逐轮BB与分区顺序诊断');end=s.index('## 并行状态修复消融',start)
 (OUT/'HANDOFF.before_finalization.md').write_text(s)
 head='''## 逐轮BB与分区顺序诊断已完成（最新）

results/native_state_trace_20261102：24/24诊断样本合法，map字节等价、原生及独立FULL/STA通过，八份trace日志结构/env/CPU核验通过。report.md、analysis.json、conclusions.json、acceptance.json与evidence_verification.json；无活动求解/监督队列，勿重启。全部诊断不算正式速度比，默认未变。

两布局两重复的最早机制已定位：首轮BB/归属/分区内顺序一致；首轮后动态通知s1=151、s2=139，无修复均未送达；第二轮开始BB仍同，但无修复有9/8个网络超出所属分区，修复均0。无修复前五轮越界数s1=[0,9,19,28,32]，s2=[0,8,14,21,27]，修复全0。第三轮起BB也分化。此为原二维分区包含条件，不等于最终非法；明确遗漏通知导致过期分区，不能据其快而撤销修复。

首轮通知中仅9/8次实际迁移，142/131次同分区erase/insert。通知集合重复一致但顺序可变；s1修复模式第2轮出现分区内次序变化，归属/BB仍相同。源码unordered_set转vector后按扇出stable_sort，会继承同扇出容器顺序。下一候选：保留通知/迁移，仅跳过old==new重插入；再独立验证显式同扇出排序。尚未实现或证明性能收益。

扰动：both四组旧ELF/off/on路由质量轮数全同；none有一组off/on不一致（51轮8.33758ns vs49轮7.05387ns），不能排除诊断扰动，旧并行端点门槛失败保持。仅前5轮，未记录RR前驱写入，不证明竞态或完整根因；先前同ELF缓存小幅退化仍未解决。隔离两对象构建，首次overlay重复头文件失败日志保留，优先include路径修正后通过，历史源/库/ELF不改。

'''
 h.write_text(s[:start]+head+s[end:])
 files=list(OUT.glob('*.json'))+list(OUT.glob('*.md'))+[ROOT/'scripts'/n for n in ['build_native_state_trace.py','run_native_state_trace.py','analyze_native_state_trace.py','finalize_native_state_trace.py']]
 write_json(OUT/'final_artifact_manifest.json',{str(p.relative_to(ROOT)):sha256(p) for p in files})
 print(json.dumps(c,ensure_ascii=False))
if __name__=='__main__':main()
