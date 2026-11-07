"""Bounded, cached BNN routing diagnostics after the failed large-case gate."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import time

from native_cpu_budget import audited_process, pin_budget
from prepare import sha256, write_json
from report_native_joint import log_evidence
from run_native_hybrid import route_body
from run_native_cpu_study import cpu_command, set_option
from scaling_common import metrics, verified, vpr_command, vpr_environment

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'results/native_cpu_large_20261102'
OUT=ROOT/'results/native_cpu_large_diagnostic_20261103'


def read(p): return json.loads(p.read_text())
def now(): return datetime.now(timezone.utc).isoformat()
def binding(p): return dict(path=str(p.resolve()),sha256=sha256(p))


def freeze():
    OUT.mkdir(exist_ok=False)
    old=read(OLD/'qualification_verified_plan.json'); summary=read(OLD/'qualification/serial/summary.json')
    assert read(OLD/'continuation.json')['status']=='complete_qualification_rejected'
    cases={}
    for name in ['bnn_s1','bnn_s2']:
        entry=next(c for c in old['lanes']['serial']['cases'] if c['id']==name)
        cache=next(c for c in summary['cache_qualifications'] if c['case']==name)
        cases[name]=dict(case=binding(Path(entry['vpr_case'])),cache=dict(path=cache['shared_cache'],sha256=cache['sha256']))
    jobs=[dict(key='bnn_s1_parallel_cached',case='bnn_s1',router='parallel',workers=8,tasks='0',repeat=0),
          dict(key='bnn_s1_serial_cached',case='bnn_s1',router='timing_driven',workers=1,tasks='0',repeat=0)]
    for rep in range(3):
        for task in (['0','1'] if rep%2==0 else ['1','0']):
            jobs.append(dict(key=f'bnn_s2_cached_tasks{task}_r{rep}',case='bnn_s2',router='parallel',workers=8,tasks=task,repeat=rep))
    files=['diagnose_native_cpu_large.py','native_cpu_budget.py','prepare.py','report_native_joint.py',
           'run_native_hybrid.py','run_native_cpu_study.py','scaling_common.py']
    plan=dict(status='frozen',created_utc=now(),cases=cases,jobs=jobs,binaries=old['binaries'],runtime=old['runtime'],
              runtime_binding=binding(Path(old['runtime'])),source_summary=binding(OLD/'qualification/serial/summary.json'),
              runner_bindings={f:binding(ROOT/'scripts'/f) for f in files},timeout_seconds=900,max_iterations=200,
              cpu_pool=list(range(32,40)),scope='Diagnostics only: no new performance speedups, no pool into formal evidence. All jobs read the same previously qualified map for their case; no construction is timed.',
              hypotheses=['bnn_s1 serial router may expose route feasibility on the unchanged graph; one result does not isolate a parallel bug.',
                          'bnn_s2 repeated same-ELF cached routes test repeatability without lookahead construction. No race is inferred from route differences alone.'],
              stop_policy='Preserve numerical failures and continue the eight predefined jobs; stop on map/input/binary drift or audit failures. No automatic retries.',
              original_formal_matrix_started=False,default_changed=False)
    for e in plan['binaries'].values():verified(e)
    for e in cases.values():verified(e['case']);verified(e['cache'])
    write_json(OUT/'plan.json',plan)


def report():
    state=read(OUT/'summary.json');assert state['status']!='running'
    rows=state['measurements'];groups=defaultdict(list)
    for r in rows:
        if r.get('success'):groups[r['case']].append(r)
    s2=groups['bnn_s2']
    variants={t:sorted({r['route_body_sha256'] for r in s2 if r['tasks']==t}) for t in ['0','1']}
    analysis=dict(status=state['status'],attempted=len(rows),legal=sum(bool(r.get('success')) for r in rows),
                  bnn_s2_route_bodies_by_tasks=variants,
                  bnn_s2_within_mode_variation={t:len(v)>1 for t,v in variants.items()},
                  bnn_s1_serial_legal=any(r['success'] for r in groups['bnn_s1'] if r['router']=='timing_driven'),
                  no_performance_claim=True,default_changed=False)
    write_json(OUT/'analysis.json',analysis)
    lines=['# 大图资格失败后的缓存路由诊断','',
           '固定此前布局、线宽100与RR图，同一修复版ELF，读取已验证的map。以下全部是诊断样本，不报告加速比。串行路由一核、并行八核，不能作同资源性能对照。','',
           '|任务|退出码|合法并独立复核|路由轮数|CPD ns|线长|末轮过用节点|','|---|---:|---|---:|---:|---:|---:|']
    for r in rows:
        it=r.get('log_evidence',{}).get('iterations',[])
        lines.append(f'|{r["key"]}|{r.get("returncode")}|{r.get("success",False)}|{r.get("iterations")}|{r.get("critical_path_ns")}|{r.get("wirelength")}|{it[-1]["overused_nodes"] if it else None}|')
    lines+=['','bnn_s2缓存条件下各模式合法路由主体种类数：'+str({k:len(v) for k,v in variants.items()})+'。',
            '同一模式内部变化意味着该测试条件下不可重复；不单凭此证明竞态。没有观察到变化也不能证明确定性。',
            'bnn_s1串行若合法，只说明同一输入存在已验证的可行路由；串行/并行搜索顺序不同，仍需进一步实验才能隔离并行实现缺陷。',
            '原30项资格失败及144项未启动状态保持。诊断不替换原始负例。']
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')


def run():
    plan=read(OUT/'plan.json')
    with (OUT/'owner.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUT/'summary.json').exists():raise RuntimeError('Existing diagnostic chain; no implicit restart')
        for e in plan['runner_bindings'].values():verified(e)
        verified(plan['runtime_binding']);verified(plan['source_summary'])
        binaries={k:verified(v) for k,v in plan['binaries'].items()}
        cases={name:read(verified(e['case'])) for name,e in plan['cases'].items()}
        inputs={}
        for c in cases.values():
            for e in c['inputs'].values():inputs[e['path']]=e
        for e in inputs.values():verified(e)
        caches={name:verified(e['cache']) for name,e in plan['cases'].items()}
        env={k:v for k,v in vpr_environment(read(Path(plan['runtime']))).items() if not k.startswith(('VPR_CPU_','VPR_HYBRID_','H3D_GPU_'))}
        resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        state=dict(status='running',pid=os.getpid(),started_utc=now(),plan_binding=binding(OUT/'plan.json'),measurements=[],default_changed=False)
        write_json(OUT/'summary.json',state)
        try:
            for job in plan['jobs']:
                assert shutil.disk_usage(OUT).free>30*1024**3
                case=cases[job['case']];cache=caches[job['case']]
                directory=OUT/job['key'];directory.mkdir()
                os.sched_setaffinity(0,plan['cpu_pool']);budget=pin_budget(job['workers'])
                for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][role]['path'],directory/name)
                local=env|{'VPR_HYBRID_LOOKAHEAD_TASKS':job['tasks'],'VPR_HYBRID_LOOKAHEAD_PARALLEL':'1'}
                command=cpu_command(binaries['cpu'],case,directory,{'router':job['router']},job['workers'],cache=cache,iterations=200)
                set_option(command,'--write_router_lookahead',directory/'wire_map.bin')
                row=dict(**job,status='running',success=False,directory=str(directory),cpu_budget=budget,
                         binary_sha256=plan['binaries']['cpu']['sha256'],inputs=case['inputs'],expected_map_sha256=plan['cases'][job['case']]['cache']['sha256'],
                         environment={k:v for k,v in local.items() if k.startswith(('VPR_CPU_','VPR_HYBRID_','H3D_GPU_'))})
                state['measurements'].append(row);write_json(OUT/'summary.json',state)
                row.update(audited_process(command,directory,local,900));row.update(metrics((directory/'process.log').read_text(errors='replace')))
                row['log_evidence']=log_evidence(directory)
                wire=directory/'wire_map.bin'
                row['wire_map_sha256']=sha256(wire) if wire.exists() else None
                if row['wire_map_sha256']!=row['expected_map_sha256']:raise RuntimeError('Missing/non-equivalent map')
                if row['log_evidence']['stage_seconds'].get('lookahead_build') is not None:raise RuntimeError('Unexpected lookahead rebuild in cached diagnostic')
                if not row['cpu_budget_audit']['verified']:raise RuntimeError('Affinity audit failed')
                if row['returncode']==0 and row['routing_success'] and row['full_check']:
                    row['route_sha256']=sha256(directory/'routed.route');row['route_body_sha256']=route_body(directory/'routed.route')
                    outcome=audited_process(vpr_command(binaries['original'],case,directory,200,route=False),directory,env,900,'independent_check.log')
                    checked=metrics((directory/'independent_check.log').read_text(errors='replace'))
                    row.update(independent_check=outcome,independent_metrics=checked)
                    row['success']=bool(outcome['returncode']==0 and checked['full_check'] and outcome['cpu_budget_audit']['verified']
                        and all(row[k]==checked[k] for k in ['critical_path_ns','wirelength']) and row['log_evidence']['final_overused_nodes']==0)
                    assert sha256(directory/'routed.route')==row['route_sha256']
                row['finished_utc']=now();write_json(directory/'measurement.json',row);write_json(OUT/'summary.json',state)
                print(json.dumps({k:row.get(k) for k in ['key','returncode','success','iterations','critical_path_ns','wirelength']}),flush=True)
            for e in list(inputs.values())+list(plan['binaries'].values())+list(plan['runner_bindings'].values()):verified(e)
            for e in plan['cases'].values():verified(e['cache']);verified(e['case'])
            verified(state['plan_binding']);state['status']='completed'
        except Exception as exc:state.update(status='stopped_for_review',error=repr(exc));raise
        finally:
            state['finished_utc']=now();write_json(OUT/'summary.json',state)
            report()


if __name__=='__main__':
    {'freeze':freeze,'run':run,'report':report}[sys.argv[1]]()
