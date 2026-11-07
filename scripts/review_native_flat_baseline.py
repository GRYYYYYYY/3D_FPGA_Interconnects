"""Independent terminal audit and paired summaries for the frozen flat experiment."""
import json
import math
from pathlib import Path
import re
import statistics
import sys
from collections import Counter
from datetime import datetime
from prepare import sha256, write_json
from scaling_common import metrics, verified, vpr_command
from run_native_cpu_study import cpu_command, set_option
from report_native_joint import log_evidence

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/native_flat_baseline_20261105'
ARMS=['per_group','pipeline','flat']


def read(p):return json.loads(Path(p).read_text())
def bind(p):return dict(path=str(Path(p).resolve()),sha256=sha256(p))
def stat(values):return dict(ratios=values,median=statistics.median(values),minimum=min(values),maximum=max(values))


def expected_environment(arm,directory,diagnostic=False):
    result=dict(OMP_NUM_THREADS='1',LC_ALL='C',
        VPR_HYBRID_LOOKAHEAD_TASKS='1' if arm in ['flat','pipeline'] else '0',
        VPR_HYBRID_LOOKAHEAD_PARALLEL='0' if arm=='stock' else '1')
    if arm in ['flat','pipeline']:result['VPR_CPU_GLOBAL_SCHEDULER']=arm
    if diagnostic:result.update(VPR_CPU_STAGE_MEMORY=str(directory/'stage_memory.jsonl'),VPR_HYBRID_LOOKAHEAD_REPORT=str(directory/'lookahead_profile.jsonl'))
    return result


def qos(candidate,reference):
    assert candidate['success'] and reference['success']
    changes={k:100*(candidate[k]/reference[k]-1) for k in ['critical_path_ns','wirelength']}
    return dict(passed=all(x<=5+1e-7 for x in changes.values()),changes_percent=changes)


def capture_check(row,command,env,cpus):
    assert row['command']==command
    actual=row['actual_process']
    assert actual['command']==command and actual['environment']==env and actual['cpu_set']==cpus
    budget=row['cpu_budget_audit']
    assert budget['verified'] and budget['permitted_cpu_set']==cpus and not budget['affinity_violations']
    quota=budget['cgroup_before'].get('/sys/fs/cgroup/cpu.max','max 100000').split()
    assert quota[0]=='max' or int(quota[0])/int(quota[1])>=len(cpus)


def main():
    global OUT
    if len(sys.argv)>1:OUT=Path(sys.argv[1]).resolve()
    p=read(OUT/'plan.json');s=read(OUT/'summary.json')
    assert s['status'] in ['completed','completed_with_preparation_failure'], 'Terminal review only; never call partial results final'
    assert len(s['measurements'])+len(s['skipped'])==len(p['jobs'])
    entries=[*p['runner_bindings'].values(),*p['binaries'].values(),p['runtime'],p['build'],s['plan']]
    if s.get('continuation'):
        entries.append(s['continuation']);am=read(s['continuation']['path'])
        entries += [am['original_plan'],am['previous_terminal'],am['continuation']]
        first=read(am['previous_terminal']['path'])
        assert first['status']=='stopped_for_review' and len(first['measurements'])==7
        assert first['measurements'][:6]==s['measurements'][:6]
        old=first['measurements'][6];new=s['measurements'][6]
        assert old['command']==new['command'] and old['process_seconds']==new['process_seconds']
        assert old['actual_process']==new['actual_process'] and old['wire_map_sha256']==new['wire_map_sha256']
        assert new['solver_repeated'] is False
    for x in entries:verified(x)
    for path,h in p['source_bindings'].items():assert sha256(path)==h
    if s['status']=='completed_with_preparation_failure':
        assert not s['preparation']['ready'] and not s['measurements'] and len(s['skipped'])==len(p['jobs'])
        for role in ['circuit','architecture']:verified(p['new_case'][role])
        arts=list(s['preparation']['artifacts'].values())
        for x in arts:verified(x)
        write_json(OUT/'analysis.json',dict(status='preparation_failed',performance_eligible=False,skipped=len(s['skipped']),preparation_returncode=s['preparation']['returncode'],default_changed=False))
        write_json(OUT/'independent_review.json',dict(status='passed_failure_record',reviewer=bind(Path(__file__)),summary=bind(OUT/'summary.json'),plan=bind(OUT/'plan.json'),artifacts=arts,analysis=bind(OUT/'analysis.json')))
        (OUT/'review.md').write_text('# 大型二维准备结果\n\n原始二维架构/BNN准备未通过；全部28项后续测量跳过，没有宽度重试或换样，也没有速度主张。原始输入与失败产物已复核，原因需结合prepare_bnn_2d/process.log解释。\n')
        print('Reviewed preparation failure; no performance claim',flush=True)
        return
    input_entries={}
    cases={}
    for graph,entry in s['cases'].items():
        verified(entry['reference_map']);cases[graph]=read(verified(entry['case']))
        for x in cases[graph]['inputs'].values():input_entries[x['path']]=x
    for x in input_entries.values():verified(x)
    pool=s['pool'];top={x['cpu']:x for x in s['topology']}
    assert len(pool)==16 and len({top[c]['node'] for c in pool})==1
    assert len({(top[c]['socket'],top[c]['core']) for c in pool})==16
    expected=[j['key'] for j in p['jobs'] if j['key'] not in {x['key'] for x in s['skipped']}]
    assert [r['key'] for r in s['measurements']]==expected
    jobs={j['key']:j for j in p['jobs']};artifacts=[];previous_end=None
    for row in s['measurements']:
        job=jobs[row['key']];d=Path(row['directory']);case=cases[row['graph']]
        assert read(d/'measurement.json')==row
        assert all(row[k]==v for k,v in job.items())
        if previous_end:assert datetime.fromisoformat(row['started_utc'])>=previous_end
        previous_end=datetime.fromisoformat(row['finished_utc'])
        for x in row['artifacts'].values():verified(x);artifacts.append(x)
        artifacts.append(bind(d/'measurement.json'))
        full=row['phase'] in ['qualification','full_formal']
        diagnostic=row['phase'] in ['pilot','memory_diagnostic']
        binary=p['binaries']['original' if row['arm']=='stock' else 'cpu']['path']
        cmd=cpu_command(binary,case,d,{'router':'parallel'},row['workers'],iterations=200 if full else 1)
        set_option(cmd,'--generate_rr_node_overuse_report','off');set_option(cmd,'--write_router_lookahead',d/'wire_map.bin')
        if not full:cmd.remove('--analysis')
        capture_check(row,cmd,expected_environment(row['arm'],d,diagnostic),pool[:row['workers']])
        assert read(d/'process.log.resources.json')==row['cpu_budget_audit']
        text=(d/'process.log').read_text(errors='replace');m=metrics(text)
        assert all(row[k]==v for k,v in m.items())
        timers=list(re.finditer(r'# Computing router lookahead map took ([\d.]+) seconds',text))
        assert len(timers)==1 and float(timers[0][1])==row['build_seconds']>0
        route=re.search(r'^# Routing\s*$',text,re.M);assert route and timers[0].end()<route.start()
        digest=sha256(d/'wire_map.bin')
        assert digest==row['wire_map_sha256']==s['cases'][row['graph']]['reference_map']['sha256']
        for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:assert sha256(d/name)==case['inputs'][role]['sha256']
        if row['arm'] in ['pipeline','flat']:assert text.count('CPU_GLOBAL_SCHEDULER='+row['arm']+' ')==1
        ev=log_evidence(d)
        if full:
            if row['success']:
                assert row['returncode']==0 and m['routing_success'] and m['full_check'] and ev['final_overused_nodes']==0
                ic=vpr_command(p['binaries']['original']['path'],case,d,200,route=False)
                set_option(ic,'--num_workers',row['workers'])
                capture_check(row['independent'],ic,expected_environment('stock',d/'independent'),pool[:row['workers']])
                im=metrics((d/'independent/process.log').read_text(errors='replace'))
                assert im==row['independent_metrics'] and im['full_check'] and row['independent']['returncode']==0
                assert all(im[k]==row[k] for k in ['critical_path_ns','wirelength'])
                assert sha256(d/'routed.route')==row['route_sha256']
                assert read(d/'independent/process.log.resources.json')==row['independent']['cpu_budget_audit']
        else:
            assert row['component_valid'] and row['status']!='timeout' and row['returncode'] in [0,2]
            assert len(ev['iterations'])==1 and ev['iterations'][0]['iteration']==1
            if row['returncode']==2:assert 'VPR failed to implement circuit' in text
        if diagnostic:
            memory=[json.loads(l) for l in (d/'stage_memory.jsonl').read_text().splitlines()]
            stage=[x for x in memory if x['kind']=='stage_rss'];storage=[x for x in memory if x['kind']=='storage']
            assert len(stage)==1 and stage[0]==row['memory']['stage'] and storage==row['memory']['storage']
            assert stage[0]['samples']>0 and stage[0]['read_failures']==0 and stage[0]['entry_bytes']>0
            assert stage[0]['observed_peak_bytes']>=max(stage[0]['entry_bytes'],stage[0]['exit_bytes'])
            profiles=[json.loads(l) for l in (d/'lookahead_profile.jsonl').read_text().splitlines()]
            assert profiles==row['memory']['profiles']
            assert sum(x['samples'] for x in storage)==sum(x['samples'] for x in profiles)
            assert sum(x['floods'] for x in profiles)==sum(x['samples'] for x in profiles)
            expected_scheduler={'flat':'flat_parallel_for','pipeline':'ordered_pipeline','per_group':'per_group'}[row['arm']]
            assert all(x['scheduler']==expected_scheduler for x in storage)
            if row['arm'] in ['flat','pipeline']:
                assert len(storage)==len(profiles)==1 and storage[0]['workspaces']==profiles[0]['workspaces']
                bound=storage[0]['samples'] if row['arm']=='flat' else min(storage[0]['samples'],2*row['workers'])
                assert storage[0]['sample_map_count_bound']==bound
            assert all(x['workspace_label_capacity_bytes']>0 for x in storage)
        else:assert not (d/'stage_memory.jsonl').exists() and not (d/'lookahead_profile.jsonl').exists()
    # Recheck frozen preparation, including the larger2D RR graph as an input above.
    for x in s['preparation']['artifacts'].values():verified(x);artifacts.append(x)
    qualification={r['arm']:r for r in s['measurements'] if r['phase']=='qualification'}
    legal=len(qualification)==4 and all(r['success'] for r in qualification.values())
    gate_checks={}
    if legal:
        for a,b in [('per_group','stock'),('pipeline','stock'),('flat','stock'),('pipeline','per_group'),('flat','per_group')]:
            gate_checks[a+'_vs_'+b]=qos(qualification[a],qualification[b])
    gate=legal and all(x['passed'] for x in gate_checks.values())
    assert gate==s['full_gate']['passed']
    components=[r for r in s['measurements'] if r['phase']=='component_formal']
    idx={(r['graph'],r['workers'],r['repeat'],r['arm']):r for r in components}
    comparisons={};times={}
    graph_workers=sorted({(j['graph'],j['workers']) for j in p['jobs'] if j['phase']=='component_formal'})
    for g,w in graph_workers:
        assert all((g,w,r,a) in idx for r in range(3) for a in ARMS)
        times[f'{g}/{w}']={a:statistics.median(idx[g,w,r,a]['build_seconds'] for r in range(3)) for a in ARMS}
        for a,b in [('per_group','pipeline'),('per_group','flat'),('flat','pipeline')]:
            comparisons[f'{g}/{w}/{a}_to_{b}']=stat([idx[g,w,r,a]['build_seconds']/idx[g,w,r,b]['build_seconds'] for r in range(3)])
    full_rows=[r for r in s['measurements'] if r['phase']=='full_formal'];full_results={}
    if gate:
        assert len(full_rows)==12
        fi={(r['repeat'],r['arm']):r for r in full_rows}
        for a,b in [('stock','per_group'),('stock','pipeline'),('stock','flat'),('per_group','pipeline'),('per_group','flat'),('flat','pipeline')]:
            pairs=[(fi[r,a],fi[r,b]) for r in range(3)]
            good=all(x['success'] and y['success'] for x,y in pairs)
            qs=[qos(y,x) for x,y in pairs] if good else []
            eligible=good and all(q['passed'] for q in qs)
            info=dict(eligible=eligible,quality=qs)
            if eligible:
                for field in ['process_seconds','build_seconds','routing_seconds']:
                    info[field]=stat([x[field]/y[field] for x,y in pairs])
                flows=[]
                for x,y in pairs:
                    values=[]
                    for row in [x,y]:
                        f=re.findall(r'The entire flow of VPR took ([\d.]+) seconds', (Path(row['directory'])/'process.log').read_text())
                        values.append(float(f[-1]) if f else None)
                    if all(v and v>0 for v in values):flows.append(values[0]/values[1])
                if len(flows)==3:info['native_flow_seconds']=stat(flows)
            full_results[a+'_to_'+b]=info
    memory={}
    for row in s['measurements']:
        if row['phase']!='memory_diagnostic':continue
        m=row['memory'];v=m['stage'];ss=m['storage']
        memory[f'{row["graph"]}/{row["arm"]}']=dict(
            entry_mib=v['entry_bytes']/1024**2,observed_peak_mib=v['observed_peak_bytes']/1024**2,
            exit_mib=v['exit_bytes']/1024**2,observed_growth_mib=(v['observed_peak_bytes']-v['entry_bytes'])/1024**2,
            samples=v['samples'],max_sample_gap_ms=v['max_sample_gap_ns']/1e6,
            max_live_workspace_label_capacity_mib=max(x['workspace_label_capacity_bytes'] for x in ss)/1024**2,
            max_workspaces=max(x['workspaces'] for x in ss),samples_total=sum(x['samples'] for x in ss),
            sample_map_bound=max(x['sample_map_count_bound'] for x in ss),
            group_map_count=max(x['group_map_count'] for x in ss),
            one_map_cell_backing_mib=ss[0]['one_map_cell_backing_bytes']/1024**2,
            scope='One instrumented diagnostic per arm; stage RSS sampled, allocator/page-cache history retained. Structural backing excludes cell payload/queue/allocator. Per-group counters use maximum across groups, never a simultaneous sum.')
    larger2d=OUT.name.startswith('native_large2d_followup')
    layout_text=(OUT/('prepare_bnn_2d' if larger2d else 'prepare_clma_2d')/'process.log').read_text(errors='replace')
    grid_observations=re.findall(r'FPGA sized to (\d+) x (\d+)',layout_text)
    analysis=dict(status='reviewed',measurements=len(s['measurements']),phases=dict(Counter(r['phase'] for r in s['measurements'])),
        component_times=times,component_comparisons=comparisons,full_process_comparisons=full_results,
        full_median_seconds={a:statistics.median(r['process_seconds'] for r in full_rows if r['arm']==a) for a in ['stock',*ARMS]} if gate else {},
        full_quality_gate=gate,full_legal=sum(r['success'] for r in s['measurements'] if r['phase'] in ['qualification','full_formal']),
        memory=memory,grid_observations=grid_observations,strict_isolated_measurement=False,default_changed=False,
        limitations=['Shared physical host; three runtime repetitions.',
                     'BNN2D uses original preserved KOIOS2D architecture; separate cohort from clma/native-k6 family.' if larger2d else 'clma auto-grid44x44, only8sample tasks; larger input circuit does not establish expensive large2D lookahead.',
                     '0.01second stage timers; small2D ratios coarse. Python timedwait may affect few-percent process ratios.',
                     'One-iteration component failures are not legal-routing results.','wire serialization does not independently check all derived src/opin tables.',
                     'Stage RSS is approximate sampled peak, not exact peak or workspace-only allocation.'])
    write_json(OUT/'analysis.json',analysis)
    write_json(OUT/'independent_review.json',dict(status='passed',reviewer=bind(Path(__file__)),summary=bind(OUT/'summary.json'),plan=bind(OUT/'plan.json'),
        verified_input_files=len(input_entries),verified_artifacts=len(artifacts),artifacts=artifacts,measurements=len(s['measurements']),analysis=bind(OUT/'analysis.json')))
    lines=['# Flat 对照、阶段内存与二维补充','',
        f'终态独立复核通过：{len(s["measurements"])}项测量，{len(artifacts)}份产物。共享宿主fpgaacc2，同NUMA固定物理核，单一顺序执行链。',
        'BNN采用未编辑的原始KOIOS二维架构；准备不计入性能，任何资格失败都阻止完整流程主张。' if larger2d else '初次执行在已完成stock clma布线后的记录环节停止；显式修复读取顺序并补独立检查，已完成solver没有重跑。原计划、原脚本、终态快照及续跑协议全部保留。','',
        '|图/核数|组内秒|pipeline秒|flat秒|组内→flat|flat→pipeline|','|---|---:|---:|---:|---:|---:|']
    for k,v in times.items():lines.append(f'|{k}|{v["per_group"]:.2f}|{v["pipeline"]:.2f}|{v["flat"]:.2f}|{comparisons[k+"/per_group_to_flat"]["median"]:.4f}×|{comparisons[k+"/flat_to_pipeline"]["median"]:.4f}×|')
    lines+=['','秒数为各臂中位；比值为逐repeat配对速度比的中位，二者不互换。全部阶段样本按一轮路由协议，不作为合法完整流程收益。','',
        '|完整布线进程对照|配对速度比中位|三次范围|','|---|---:|---:|']
    for k,v in full_results.items():
        if v['eligible']:
            z=v['process_seconds'];lines.append(f'|{k}|{z["median"]:.4f}×|{z["minimum"]:.4f}–{z["maximum"]:.4f}|')
        else:lines.append(f'|{k}|质量/合法性不合格，不计算|—|')
    scope=('BNN为127676个BLIF .names，原始二维架构自动选既有布局；观测网格'+str(grid_observations)+f'。完整流程门槛通过={gate}，合法测量={analysis["full_legal"]}。' if larger2d else 'clma为8381个BLIF .names，自动网格44×44，4资格+12正式全部合法的结论以analysis.json为准。它增加电路规模，但阶段仍不足一秒，尚不能填补高成本大型二维RR验证。')
    lines+=['',scope+'完整进程读冻结RR/packed/place，不包含pack/place与图生成。','',
        '|图/方法（8核）|阶段入口MiB|观测峰值MiB|峰值−入口MiB|标签容量MiB|工作区数|样本表上界|','|---|---:|---:|---:|---:|---:|---:|']
    for k,v in memory.items():lines.append(f'|{k}|{v["entry_mib"]:.1f}|{v["observed_peak_mib"]:.1f}|{v["observed_growth_mib"]:.1f}|{v["max_live_workspace_label_capacity_mib"]:.1f}|{v["max_workspaces"]}|{v["sample_map_bound"]}|')
    lines+=['','内存来自独立诊断；statm近似、2ms目标采样可能漏峰，实际间隔见analysis.json。标签容量不含队列/分配器；表数是结构上界而非RSS上限。组内各组工作区取最大同时占用，不能累加成全局峰值。','',
        '方法与等价性论证见../../docs/native_lookahead_method_argument.md；复现入口见../../docs/native_cpu_paper_reproduction.md。默认未变，无GPU收益或新调度原语主张。']
    (OUT/'review.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:analysis[k] for k in ['status','measurements','phases','full_legal']}),flush=True)


if __name__=='__main__':main()
