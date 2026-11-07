"""Six fixed-layout width120 feasibility probes; no candidate timing comparisons."""
import copy
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import xml.etree.ElementTree as ET

from native_cpu_budget import audited_process, pin_budget
from prepare import sha256, write_json
from report_native_joint import log_evidence
from run_native_cpu_study import cpu_command, set_option
from run_native_hybrid import route_body
from scaling_common import metrics, verified, vpr_command, vpr_environment

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_cpu_width120_20261104'
OLD=ROOT/'results/native_cpu_large_20261102'


def read(p):return json.loads(p.read_text())
def now():return datetime.now(timezone.utc).isoformat()
def binding(p):return {'path':str(Path(p).resolve()),'sha256':sha256(p)}


def generation_command(binary,case,directory):
    case=copy.deepcopy(case);case['route_chan_width']=120
    command=cpu_command(binary,case,directory,{'router':'parallel'},8,iterations=200)
    index=command.index('--read_rr_graph');del command[index:index+2]
    set_option(command,'--place_chan_width',120)
    set_option(command,'--write_rr_graph',directory/'rr_graph.xml')
    set_option(command,'--write_router_lookahead',directory/'wire_map.bin')
    assert '--pack' not in command and '--place' not in command and '--read_router_lookahead' not in command
    return command


def freeze():
    OUT.mkdir(exist_ok=False)
    old=read(OLD/'qualification_verified_plan.json')
    assert read(OLD/'continuation.json')['status']=='complete_qualification_rejected'
    assert read(ROOT/'results/native_cpu_large_diagnostic_20261103/audit.json')['status']=='passed'
    jobs=[]
    for c in old['lanes']['serial']['cases']:
        source=Path(c['vpr_case']);case=read(source);d=OUT/c['id']
        jobs.append(dict(case=c['id'],source_case=binding(source),directory=str(d),
                         command=generation_command(old['binaries']['cpu']['path'],case,d)))
    files=['probe_native_cpu_width120.py','native_cpu_budget.py','prepare.py','report_native_joint.py',
           'run_native_cpu_study.py','run_native_hybrid.py','scaling_common.py']
    plan=dict(status='frozen',created_utc=now(),protocol_version='width120_feasibility_v1',jobs=jobs,
              source_protocol=binding(ROOT/'results/native_cpu_direction_20261102/next_experiment.json'),
              source_qualification=binding(OLD/'qualification/serial/summary.json'),
              diagnostic_conclusions=binding(ROOT/'results/native_cpu_large_diagnostic_20261103/conclusions.json'),
              binaries={k:old['binaries'][k] for k in ['original','cpu']},runtime=old['runtime'],runtime_binding=binding(old['runtime']),
              runner_bindings={f:binding(ROOT/'scripts'/f) for f in files},cpu_pool=list(range(32,40)),
              timeout_seconds=900,max_router_iterations=200,address_space_gib=64,minimum_free_disk_gib=80,
              environment={'VPR_HYBRID_LOOKAHEAD_TASKS':'0','VPR_HYBRID_LOOKAHEAD_PARALLEL':'0'},
              selection='All six previously selected layouts, one corrected baseline arm, common width120 chosen before these runs; no selection based on optimized-candidate speed.',
              comparison_scope='Feasibility diagnostic only. This process generates/writes a new native RR graph, unlike prior width100 runs that loaded one; do not compare process times as width or algorithm speedups.',
              preserved_inputs='Architecture, BLIF, packed netlist, placement, seed, utilization and native router settings unchanged except common channel width100->120; no pack/place or RR editing.',
              baseline='Same corrected ELF with serial lookahead building; native parallel routing, eight physical cores. Correctness repairs remain enabled.',
              acceptance='Legal native route, zero final overuse, original-binary independent FULL/STA agrees, actual width120 and CPU budget verified. One successful run is feasibility evidence, not repeatability or performance qualification.',
              failure_policy='Retain all six outcomes, including crashes/timeouts/unroutable cases. Stop on provenance drift, CPU audit failure, or disk floor. No retries, automatic width escalation or candidate performance submission.',
              map_scope='Map hashes retained, but no cross-implementation map-equivalence claim from this single-arm probe.',
              original_width100_gate='failed_preserved',original_formal_matrix_started=False,default_changed=False,exclusive_host=False)
    for e in plan['binaries'].values():verified(e)
    for job in jobs:verified(job['source_case'])
    write_json(OUT/'plan.json',plan)
    print('Frozen six width120 baseline probes:',OUT)


def graph_header(path):
    with path.open('rb') as f:
        beginning=f.read(16384);f.seek(max(0,path.stat().st_size-4096));ending=f.read()
    assert b'</rr_graph>' in ending, 'RR XML not complete'
    for line in beginning.splitlines():
        if line.lstrip().startswith(b'<channel '):
            attrs=ET.fromstring(line.decode()).attrib
            assert all(int(attrs[k])==120 for k in ['chan_width_max','x_max','y_max']),attrs
            return attrs
    raise RuntimeError('RR channel header missing')


def native_evidence(directory,row):
    # log_evidence uses measurement.json for successful-run fallback and timeout
    # interpretation. Persist native status before calling it (regression guard).
    write_json(directory/'measurement.json',row)
    return log_evidence(directory)


def report(state):
    rows=state['measurements']
    result=dict(status=state['status'],planned=6,attempted=len(rows),legal=sum(bool(r['success']) for r in rows),
                all_six_feasible=len(rows)==6 and all(r['success'] for r in rows),
                performance_claim=False,default_changed=False,original_width100_result_unchanged=True,
                next='Review all failures and establish repeated feasibility before freezing any width120 candidate comparison; no automatic formal matrix.')
    write_json(OUT/'analysis.json',result)
    lines=['# 线宽120的固定布局修复基线可布通性探测','',
           '全部六布局统一使用线宽120；原版默认参数准备的架构、网表、布局、种子保持不变。使用修复版串行lookahead构建、原生并行路由、同八核。没有候选性能比较。',
           '本进程生成并写出新的原生RR图，旧线宽100进程读取已有图，两者计时边界不同。不能用进程时间之比宣称加速。单次合法仅证明该运行找到了可行路由，尚不证明稳定性。','',
           '|布局|退出码|合法且独立复核|轮数/最后观察轮数|末轮过用|CPD ns|线长|','|---|---:|---|---:|---:|---:|---:|']
    for r in rows:
        e=r.get('log_evidence',{});its=e.get('iterations',[])
        last=its[-1] if its else {}
        lines.append(f'|{r["case"]}|{r.get("returncode")}|{r["success"]}|{r.get("iterations") or last.get("iteration")}|{e.get("final_overused_nodes") if e.get("final_overused_nodes") is not None else last.get("overused_nodes")}|{r.get("critical_path_ns")}|{r.get("wirelength")}|')
    lines+=['',f'状态：{state["status"]}；{result["legal"]}/{len(rows)}项合法。原线宽100失败及144项正式矩阵未启动状态保持。',
            '新增map只保存hash，本轮没有原版/优化跨实现逐字节比较。默认算法未修改。详见plan.json、summary.json、audit.json。']
    if state.get('error'):lines+=['','停止原因：'+state['error']]
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')


def audit(plan,state):
    errors=[];bindings={}
    for row,job in zip(state['measurements'],plan['jobs']):
        d=Path(row['directory']);parsed=metrics((d/'process.log').read_text(errors='replace'))
        e=log_evidence(d);cmd=row['command']
        if cmd!=job['command']:errors.append(row['case']+': unexpected command')
        if not row['cpu_budget_audit']['verified'] or row['cpu_budget_audit']['permitted_cpu_set']!=plan['cpu_pool']:
            errors.append(row['case']+': CPU audit')
        if any(parsed[k]!=row[k] for k in ['routing_success','full_check','critical_path_ns','wirelength','iterations']):errors.append(row['case']+': metrics mismatch')
        expected=False
        if row.get('independent_check'):
            checked=metrics((d/'independent_check.log').read_text(errors='replace'))
            expected=bool(row['returncode']==0 and parsed['routing_success'] and parsed['full_check']
                and e['final_overused_nodes']==0 and row.get('generated_rr_graph')
                and not row.get('graph_validation_error') and row['independent_check']['returncode']==0
                and checked['full_check'] and row['independent_check']['cpu_budget_audit']['verified']
                and all(parsed[k]==checked[k] for k in ['critical_path_ns','wirelength']))
        if row['success']!=expected:errors.append(row['case']+': success classification mismatch')
        if row['success']:
            checked=metrics((d/'independent_check.log').read_text(errors='replace'))
            if not parsed['full_check'] or not checked['full_check'] or e['final_overused_nodes']!=0:errors.append(row['case']+': FULL/overuse')
            if any(parsed[k]!=checked[k] for k in ['critical_path_ns','wirelength']):errors.append(row['case']+': STA')
            if sha256(d/'routed.route')!=row['route_sha256'] or route_body(d/'routed.route')!=row['route_body_sha256']:errors.append(row['case']+': route changed')
            graph_header(d/'rr_graph.xml')
        for filename in ['measurement.json','process.log','process.log.resources.json','independent_check.log',
                         'independent_check.log.resources.json','wire_map.bin','routed.route','report_overused_nodes.rpt','vpr_case.json']:
            if (d/filename).exists():bindings[str(d/filename)]=sha256(d/filename)
    if len(state['measurements'])!=6:errors.append('Incomplete six-layout matrix')
    write_json(OUT/'audit.json',dict(status='passed' if not errors else 'failed',errors=errors,bindings=bindings,
                                   note='Numerical failure is retained, not an artifact-audit failure. Frozen source/binary/used inputs verified separately at both boundaries.'))
    if errors:raise RuntimeError(str(errors))


def run():
    plan=read(OUT/'plan.json')
    with (OUT/'owner.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUT/'summary.json').exists():raise RuntimeError('Existing chain; observe instead of restarting')
        for e in plan['runner_bindings'].values():verified(e)
        for key in ['source_protocol','source_qualification','diagnostic_conclusions']:verified(plan[key])
        verified(plan['runtime_binding']);binaries={k:verified(e) for k,e in plan['binaries'].items()}
        inputs={};cases={}
        for job in plan['jobs']:
            case=read(verified(job['source_case']));cases[job['case']]=case
            for k,e in case['inputs'].items():
                if k!='rr_graph':inputs[e['path']]=e
        for e in inputs.values():verified(e)
        env={k:v for k,v in vpr_environment(read(Path(plan['runtime']))).items() if not k.startswith(('VPR_CPU_','VPR_HYBRID_','H3D_GPU_'))}
        env.update(plan['environment'])
        resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        os.sched_setaffinity(0,plan['cpu_pool']);budget=pin_budget(8)
        state=dict(status='running',pid=os.getpid(),started_utc=now(),plan_binding=binding(OUT/'plan.json'),measurements=[],default_changed=False)
        write_json(OUT/'summary.json',state)
        try:
            for job in plan['jobs']:
                assert shutil.disk_usage(OUT).free>plan['minimum_free_disk_gib']*1024**3,'Disk below80GiB'
                d=Path(job['directory']);d.mkdir();case=copy.deepcopy(cases[job['case']]);case['route_chan_width']=120
                for role,filename in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][role]['path'],d/filename)
                row=dict(case=job['case'],directory=str(d),status='running',success=False,cpu_budget=budget,
                         environment=plan['environment'],source_case=job['source_case'],binary_sha256=plan['binaries']['cpu']['sha256'])
                state['measurements'].append(row);write_json(OUT/'summary.json',state)
                row.update(audited_process(job['command'],d,env,900));row.update(metrics((d/'process.log').read_text(errors='replace')))
                row['log_evidence']=native_evidence(d,row)
                assert row['cpu_budget_audit']['verified'],'CPU affinity audit failed'
                for role,filename in [('packed_netlist','packed.net'),('placement','fixed.place')]:
                    assert sha256(d/filename)==case['inputs'][role]['sha256'],'Fixed input changed'
                if (d/'rr_graph.xml').exists():
                    try:
                        row['rr_channel_header']=graph_header(d/'rr_graph.xml');case['inputs']['rr_graph']=binding(d/'rr_graph.xml')
                        case.update(id=job['case']+'_w120',source_case=job['source_case'],scope='Same fixed layout; native RR generation at common width120, no RR editing.')
                        write_json(d/'vpr_case.json',case);row['generated_rr_graph']=case['inputs']['rr_graph']
                    except (AssertionError,RuntimeError) as exc:row['graph_validation_error']=repr(exc)
                if (d/'wire_map.bin').exists():row['wire_map_sha256']=sha256(d/'wire_map.bin')
                if row['returncode']==0 and row['routing_success'] and row['full_check'] and not row.get('graph_validation_error'):
                    assert 'generated_rr_graph' in row and row['log_evidence']['final_overused_nodes']==0
                    row['route_sha256']=sha256(d/'routed.route');row['route_body_sha256']=route_body(d/'routed.route')
                    row['independent_check']=audited_process(vpr_command(binaries['original'],case,d,200,route=False),d,env,900,'independent_check.log')
                    checked=metrics((d/'independent_check.log').read_text(errors='replace'));row['independent_metrics']=checked
                    row['success']=bool(row['independent_check']['returncode']==0 and checked['full_check'] and row['independent_check']['cpu_budget_audit']['verified']
                        and all(checked[k]==row[k] for k in ['critical_path_ns','wirelength']))
                    assert sha256(d/'routed.route')==row['route_sha256']
                row['finished_utc']=now();write_json(d/'measurement.json',row);write_json(OUT/'summary.json',state)
                print(json.dumps({k:row.get(k) for k in ['case','returncode','success','iterations','critical_path_ns','wirelength']}),flush=True)
            for e in list(inputs.values())+list(plan['binaries'].values())+list(plan['runner_bindings'].values()):verified(e)
            for job in plan['jobs']:verified(job['source_case'])
            for key in ['runtime_binding','source_protocol','source_qualification','diagnostic_conclusions']:verified(plan[key])
            verified(state['plan_binding']);audit(plan,state);state['status']='completed'
        except Exception as exc:state.update(status='stopped_for_review',error=repr(exc));raise
        finally:
            state['finished_utc']=now();write_json(OUT/'summary.json',state);report(state)


if __name__=='__main__':
    {'freeze':freeze,'run':run}[sys.argv[1]]()
