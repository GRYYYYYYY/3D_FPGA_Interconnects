"""Independently verify completed cached diagnostic artifacts and classification."""
import copy
import json
from pathlib import Path
from prepare import sha256, write_json
from report_native_joint import log_evidence
from run_native_hybrid import route_body
from scaling_common import metrics

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_cpu_large_diagnostic_20261103'


def main():
    plan=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'summary.json').read_text())
    errors=[];bindings={};raw_rows=summary['measurements'];rows=copy.deepcopy(raw_rows);corrections=[]
    def check(cond,msg):
        if not cond:errors.append(msg)
    def bind(path):bindings[str(path.resolve())]=sha256(path)
    check(summary['status']=='completed','Diagnostic chain is not complete')
    check(len(rows)==len(plan['jobs'])==8,'Incomplete diagnostic accounting')
    check([r['key'] for r in rows]==[r['key'] for r in plan['jobs']],'Unexpected job order')
    check(sha256(OUT/'plan.json')==summary['plan_binding']['sha256'],'Changed plan')
    for row,job in zip(rows,plan['jobs']):
        d=Path(row['directory']);key=row['key'];cmd=row['command'];env=row['environment']
        native=metrics((d/'process.log').read_text(errors='replace'));e=log_evidence(d)
        check(cmd[cmd.index('--num_workers')+1]==str(job['workers']),key+': workers')
        check(cmd[cmd.index('--router_algorithm')+1]==job['router'],key+': router')
        check(cmd[cmd.index('--read_router_lookahead')+1]==plan['cases'][job['case']]['cache']['path'],key+': cache path')
        check(env=={'VPR_HYBRID_LOOKAHEAD_TASKS':job['tasks'],'VPR_HYBRID_LOOKAHEAD_PARALLEL':'1'},key+': unexpected env')
        check(e['stage_seconds'].get('lookahead_build') is None,key+': rebuild occurred')
        check(sha256(d/'wire_map.bin')==row['expected_map_sha256']==row['wire_map_sha256'],key+': map mismatch')
        audit=json.loads((d/'process.log.resources.json').read_text())
        check(audit['verified'] and audit['permitted_cpu_set']==list(range(32,32+job['workers'])),key+': affinity')
        check(Path(cmd[0]).resolve()==Path(plan['binaries']['cpu']['path']).resolve(),key+': binary')
        for field in ['critical_path_ns','wirelength','iterations','full_check','routing_success']:
            check(native[field]==row.get(field),key+': log mismatch '+field)
        # The frozen diagnostic runner called log_evidence before measurement.json
        # existed. That helper needs the saved routing_success flag to infer zero
        # overuse from the last iteration. Re-evaluate only metadata, never rerun.
        row['log_evidence']=e
        independent_path=d/'independent_check.log'
        independent=metrics(independent_path.read_text(errors='replace')) if independent_path.exists() else {}
        valid=bool(row['returncode']==0 and native['routing_success'] and native['full_check']
                   and independent.get('full_check') and e['final_overused_nodes']==0
                   and all(independent.get(k)==native[k] for k in ['critical_path_ns','wirelength'])
                   and row.get('independent_check',{}).get('returncode')==0
                   and row.get('independent_check',{}).get('cpu_budget_audit',{}).get('verified')
                   and row['cpu_budget_audit']['verified'])
        if valid!=row['success']:
            corrections.append(dict(key=key,original_success=row['success'],verified_success=valid,
                                    reason='Original log_evidence read before measurement.json existed; native and independent checks are complete.'))
        row['success']=valid
        if valid:
            ind=metrics((d/'independent_check.log').read_text(errors='replace'))
            check(native['full_check'] and native['routing_success'] and ind['full_check'],key+': FULL')
            check(e['final_overused_nodes']==0,key+': overuse')
            check(all(ind[k]==native[k] for k in ['critical_path_ns','wirelength']),key+': STA')
            check(row['independent_check']['returncode']==0 and row['independent_check']['cpu_budget_audit']['verified'],key+': readback')
            check(sha256(d/'routed.route')==row['route_sha256'],key+': route bytes')
            check(route_body(d/'routed.route')==row['route_body_sha256'],key+': route body')
        for name in ['measurement.json','process.log','process.log.resources.json','wire_map.bin',
                     'independent_check.log','independent_check.log.resources.json','routed.route','report_overused_nodes.rpt']:
            if (d/name).exists():bind(d/name)
    for p in [OUT/'plan.json',OUT/'summary.json',Path(__file__)]:bind(p)
    receipt=dict(status='passed' if not errors else 'failed',attempted=len(rows),legal=sum(bool(r['success']) for r in rows),
                 errors=errors,retained_artifacts_checked=len(bindings),bindings=bindings,
                 classification_corrections=corrections,
                 source_and_input_scope='Runner verified all frozen input, binary and source hashes at both execution boundaries; this audit independently checks retained diagnostic outputs and actual settings.',
                 performance_claim=False)
    write_json(OUT/'audit.json',receipt)
    verified_summary=copy.deepcopy(summary);verified_summary['measurements']=rows
    verified_summary['derived_from']={'path':str(OUT/'summary.json'),'sha256':sha256(OUT/'summary.json')}
    verified_summary['classification_corrections']=corrections
    write_json(OUT/'verified_summary.json',verified_summary)
    patterns={t:sorted({r['route_body_sha256'] for r in rows if r['case']=='bnn_s2' and r['tasks']==t and r['success']}) for t in ['0','1']}
    conclusions=dict(status=receipt['status'],attempted=len(rows),legal=receipt['legal'],route_bodies_by_tasks=patterns,
                     within_mode_variation={k:len(v)>1 for k,v in patterns.items()},
                     completed_bnn_s2=len([r for r in rows if r['case']=='bnn_s2' and r['success']]),
                     performance_claim=False,default_changed=False,
                     cache_scope='Wire map build skipped; src/opin preparation remains. No exclusive attribution to a routing race.',
                     original_qualification_unchanged='failed',formal_matrix_started=False)
    write_json(OUT/'verified_analysis.json',conclusions)
    lines=['# 缓存诊断的独立复核结果','',
           '以本复核和verified_summary.json为准；原summary.json、measurement.json与自动report.md保留。',
           f'八项诊断中已验证合法 {receipt["legal"]} 项；输出审计状态 {receipt["status"]}。', '',
           '冻结执行器在measurement.json写出前调用了依赖该文件的log_evidence，导致成功路由的末轮零过用被记为null、success误记false。此处依据已保存原生日志、独立FULL/STA、路由hash和CPU审计重算；未重跑求解、修改路由或放宽合法性条件。', '',
           '|任务|退出码|复核合法|完成轮数/最后观察轮数|CPD ns|线长|末轮过用|','|---|---:|---|---:|---:|---:|---:|']
    for r in rows:
        it=r['log_evidence']['iterations'];last=it[-1] if it else {}
        lines.append(f'|{r["key"]}|{r["returncode"]}|{r["success"]}|{r.get("iterations") or last.get("iteration")}|{r.get("critical_path_ns")}|{r.get("wirelength")}|{r["log_evidence"]["final_overused_nodes"]}|')
    lines+=['','BNN_s2各TASKS模式下合法路由主体种类数：'+str({k:len(v) for k,v in patterns.items()})+'。',
            '本轮仅检查轨迹重复性，不报告性能速度比。缓存跳过wire map构建，仍有src/opin预处理；观察到变化不直接证明路由竞态，未观察到变化也不证明确定性。',
            'BNN_s1串行和并行是否布通，应分别依据上表合法性；不得把未收敛样本视为加速证据。原30项资格拒绝与144项正式未启动保持。']
    (OUT/'verified_report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='bindings'}))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
