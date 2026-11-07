"""Expand the manuscript's fixed cohorts; no solver runs or sample selection."""
import csv
import hashlib
import html
import json
import math
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median, stdev

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def summary(values):
    values = list(values)
    return dict(n=len(values), values=values, mean=mean(values) if values else None,
                sample_sd=stdev(values) if len(values)>1 else None,
                median=median(values) if values else None,
                minimum=min(values) if values else None, maximum=max(values) if values else None)

def build_statistics():
    sources = {
        'evidence': ['results/native_cpu_evidence_20261102/'+x for x in
                     ['triad','scaling','generalization','generalization_tail']],
        'confirmation': ['results/native_pipeline_confirm_20261102/runs'],
        'ablation': ['results/native_cpu_slices_20261101/confirmation'],
    }
    records, bindings, by_key = [], [], {}
    dest = HERE/'evidence'/'statistics_measurements'
    dest.mkdir(exist_ok=True)
    for cohort, directories in sources.items():
        for directory in directories:
            for path in sorted((ROOT/directory).rglob('measurement.json')):
                raw=path.read_bytes();d=json.loads(raw)
                assert d['success'] and d['wire_map_matches_serial']
                assert not d['diagnostic_sample']
                assert d['log_evidence']['final_overused_nodes']==0
                assert d['full_check'] and d['routing_success']
                ident=(cohort,d['key']);assert ident not in by_key
                by_key[ident]=d
                copy=dest/(cohort+'__'+d['key']+'.json')
                if copy.exists():assert copy.read_bytes()==raw, path
                else:copy.write_bytes(raw)
                bindings.append(dict(cohort=cohort,key=d['key'],source=str(path.relative_to(ROOT)),
                                     snapshot=str(copy.relative_to(HERE)),sha256=hashlib.sha256(raw).hexdigest()))
                stage=d['log_evidence']['stage_seconds']
                records.append(dict(cohort=cohort,phase=d['phase'],case=d['case'],workers=d['workers'],
                    cache=d['cache_mode'],variant=d['variant'],repeat=d['repeat'],key=d['key'],
                    process_seconds=d['process_seconds'],workflow_seconds=d['workflow_seconds'],
                    lookahead_seconds=stage.get('lookahead_build'),routing_seconds=d['routing_seconds'],
                    rr_load_seconds=stage.get('rr_graph_load'),critical_path_ns=d['critical_path_ns'],
                    wirelength=d['wirelength'],iterations=d['iterations']))
    assert Counter(r['cohort'] for r in records)=={'evidence':66,'confirmation':36,'ablation':120}
    fields=['cohort','phase','case','workers','cache','variant']
    records.sort(key=lambda r:tuple(str(r[f]) for f in fields)+(r['repeat'],))
    grouped=defaultdict(list)
    for r in records:grouped[tuple(r[f] for f in fields)].append(r)
    absolute=[]
    metrics=['process_seconds','workflow_seconds','lookahead_seconds','routing_seconds','rr_load_seconds']
    for key,rs in grouped.items():
        rs.sort(key=lambda r:r['repeat'])
        assert len({r['repeat'] for r in rs})==len(rs)
        assert len(rs)==(1 if key[1]=='generalization' else 3), key
        absolute.append(dict(zip(fields,key))|dict(repeats=[r['repeat'] for r in rs],
            metrics={m:summary(r[m] for r in rs if r[m] is not None) for m in metrics}))
    assert len(absolute)==98
    lookup={(r['cohort'],r['case'],r['workers'],r['cache'],r['variant'],r['repeat']):r for r in records}
    assert len(lookup)==len(records)
    analyses={n:json.loads((HERE/'evidence'/f'{n}.json').read_text()) for n in ['triad','confirmation','ablation']}
    pairs, comparisons=[],[]
    groups=[('evidence',g) for g in analyses['triad']['comparisons']]
    groups += [('confirmation',g) for g in analyses['confirmation']['comparisons']]
    groups += [('ablation',g) for g in analyses['ablation']['paired_comparisons']]
    for cohort,g in groups:
        workers=g.get('workers',8);cache=g.get('cache',g.get('cache_mode'))
        control=g.get('control','frozen');candidate=g.get('candidate','pipeline')
        meta=dict(cohort=cohort,phase=g.get('stage', 'confirm' if cohort=='confirmation' else 'confirmation'),
                  case=g['case'],workers=workers,cache=cache,control=control,candidate=candidate)
        current=[]
        for p in sorted(g['pairs'],key=lambda p:p['repeat']):
            c=lookup[(cohort,g['case'],workers,cache,control,p['repeat'])]
            v=lookup[(cohort,g['case'],workers,cache,candidate,p['repeat'])]
            cd,vd=by_key[(cohort,c['key'])],by_key[(cohort,v['key'])]
            assert cd['inputs']==vd['inputs']
            assert cd['cpu_budget']['cpu_set']==vd['cpu_budget']['cpu_set']
            assert cd['wire_map_sha256']==vd['wire_map_sha256']
            assert v['critical_path_ns']<=1.05*c['critical_path_ns']
            assert v['wirelength']<=1.05*c['wirelength']
            ratio=c['process_seconds']/v['process_seconds']
            assert math.isclose(ratio,p.get('process_ratio',p.get('ratio')),rel_tol=1e-12)
            workflow=c['workflow_seconds']/v['workflow_seconds']
            assert math.isclose(workflow,p['workflow_ratio'],rel_tol=1e-12)
            lookahead=c['lookahead_seconds']/v['lookahead_seconds'] if cache=='rebuild' else None
            r=meta|dict(repeat=p['repeat'],control_key=c['key'],candidate_key=v['key'],
                control_seconds=c['process_seconds'],candidate_seconds=v['process_seconds'],
                process_ratio=ratio,workflow_ratio=workflow,lookahead_ratio=lookahead)
            pairs.append(r);current.append(r)
        comparisons.append(meta|dict(repeats=[r['repeat'] for r in current],
            metrics={m:summary(r[m] for r in current if r[m] is not None)
                     for m in ['process_ratio','workflow_ratio','lookahead_ratio']}))
    assert len(pairs)==246 and len(comparisons)==106
    # Check legacy published summaries without changing their estimators.
    for g in analyses['triad']['configuration_summaries']:
        a=next(a for a in absolute if (a['cohort'],a['phase'],a['case'],a['workers'],a['cache'],a['variant'])==
               ('evidence',g['stage'],g['case'],g['workers'],g['cache'],g['variant']))
        for m in ['process_seconds','workflow_seconds']:
            assert math.isclose(a['metrics'][m]['median'],g[m]['median'],rel_tol=1e-12)
    out=HERE/'statistics';out.mkdir(exist_ok=True)
    def csvwrite(filename,rows):
        with (out/filename).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    csvwrite('raw_runs.csv',records);csvwrite('paired_runs.csv',pairs)
    def flatten(groups,filename):
        rows=[]
        for g in groups:
            for metric,s in g['metrics'].items():
                row={k:v for k,v in g.items() if k not in ['metrics','repeats']}
                row|=dict(metric=metric,n=s['n'],repeat_ids=';'.join(map(str,g['repeats'])),
                         raw_values=';'.join(map(repr,s['values'])))
                row.update({k:v for k,v in s.items() if k not in ['values','n']})
                rows.append(row)
        csvwrite(filename,rows)
    flatten(absolute,'absolute_statistics.csv');flatten(comparisons,'paired_statistics.csv')
    result=dict(absolute=absolute,comparisons=comparisons,records=records,
                counts=dict(runs=222,configuration_groups=98,paired_runs=246,comparison_groups=106),
                definition='Arithmetic mean; sample SD with n-1 denominator; SD unavailable for n<2. Missing lookahead build is not zero.',
                new_solver_runs=0,primary_summary='arithmetic mean +/- sample SD',
                reporting_policy_changed=True,historical_selection_unchanged=True)
    (out/'statistics.json').write_text(json.dumps(result,indent=2)+'\n')
    checked=0
    for group in absolute+comparisons:
        for s in group['metrics'].values():
            xs=s['values'];n=len(xs)
            if n:
                mu=math.fsum(xs)/n
                assert math.isclose(mu,s['mean'],rel_tol=1e-12)
            if n>1:
                sd=math.sqrt(math.fsum((x-mu)**2 for x in xs)/(n-1))
                assert math.isclose(sd,s['sample_sd'],rel_tol=1e-11,abs_tol=1e-12)
            else:
                assert s['sample_sd'] is None
            checked+=1
    assert checked==808
    (out/'calculation_check.json').write_text(json.dumps(dict(status='passed',summaries_checked=checked,
        mean_formula='sum(x)/n',sample_sd_formula='sqrt(sum((x-mean)^2)/(n-1))',
        statistics_json_sha256=hashlib.sha256((out/'statistics.json').read_bytes()).hexdigest()),indent=2)+'\n')
    (out/'source_manifest.json').write_text(json.dumps(bindings,indent=2)+'\n')
    (out/'README.txt').write_text('运行统计补充（用于论文复核，不是新增实验）\n\n'
        '包含现稿固定的222项正式性能运行：三方/泛化/扩展66项、独立确认36项、正式消融120项。'
        '排除诊断、缓存资格、失败的布线和后续新增实验；原论文失败分母与负例保留。\n'
        'raw_runs.csv：每次运行的原始秒数、关键路径、线长、轮数及稳定key。\n'
        'absolute_statistics.csv：98个配置各指标的原值、算术均值、样本标准差、中位数、最小/最大值。\n'
        'paired_runs.csv / paired_statistics.csv：246个配对观测、106个比较组，先逐次计算速度比，再统计。'
        '同一运行会用于不同对照，这246对不是492次独立运行。\n'
        '标准差使用n−1分母；n=1时为空（不适用），不是0。缓存跳过的构建时间也不填0。'
        'repeat_ids保留原0/1/2编号；图中小点为原始重复、连线/大标记为算术均值、误差线为±1样本SD。'
        '均值±SD描述已观察离散程度，不是置信区间，不能消除共享节点偏差。\n'
        'statistics.html可直接打开浏览全部时间、配对结果和重复值；JSON保留全精度。\n'
        '论文主报告统一采用均值±样本SD；跨电路速度比采用电路等权几何平均。'
        '历史中位数仅保留用于审计，历史选型记录不改写；不混合电路/布局来扩大运行重复数。\n')
    def fmt(x):return 'N/A' if x is None else f'{x:.6f}'
    def table(groups):
        lines=['<table><thead><tr><th>队列 / 阶段</th><th>电路</th><th>核数 / 模式</th><th>实现或对照</th><th>指标</th><th>n</th><th>重复值（原顺序）</th><th>均值</th><th>样本SD</th><th>中位数</th><th>范围</th></tr></thead><tbody>']
        for g in groups:
            for m,s in g['metrics'].items():
                label=g.get('variant') or g['control']+' → '+g['candidate']
                cells=[g['cohort']+' / '+g['phase'],g['case'],str(g['workers'])+' / '+g['cache'],label,m,str(s['n']),
                       ', '.join(fmt(x) for x in s['values']),fmt(s['mean']),fmt(s['sample_sd']),fmt(s['median']),
                       fmt(s['minimum'])+' – '+fmt(s['maximum'])]
                lines.append('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in cells)+'</tr>')
        return '\n'.join(lines)+ '</tbody></table>'
    page='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>论文运行统计补充</title>
<style>body{font:14px system-ui;margin:24px;color:#183046}h1{font-size:24px}table{border-collapse:collapse;width:100%;font-size:12px;margin:20px 0}td,th{padding:6px;border:1px solid #ccd7df;text-align:left}th{background:#e6eef4;position:sticky;top:0}tr:nth-child(even){background:#f7fafb}td:nth-child(n+6){font-variant-numeric:tabular-nums;white-space:nowrap}</style>
<h1>论文运行统计补充</h1><p>222 次正式运行，98 个配置组；246 个配对观测，106 个比较组。同一运行可参与多个比较。没有新增求解。</p>
<p>时间单位为秒，速度比为无量纲。论文主报告采用算术均值±样本SD，SD 使用 n−1 分母。N/A 表示无足够样本或未执行该阶段。SD 不是置信区间。中位数及范围仅保留用于审计；历史选型记录和失败分母保持不变。</p>
<p><a href="raw_runs.csv">每次运行 CSV</a> · <a href="absolute_statistics.csv">时间汇总 CSV</a> · <a href="paired_runs.csv">每次配对 CSV</a> · <a href="paired_statistics.csv">配对汇总 CSV</a></p>'''
    search='<p><label>筛选表格：<input id="search" placeholder="例如 gemm、pipeline、rebuild" style="padding:8px;width:320px"></label></p>'
    js='''<script>document.getElementById('search').addEventListener('input',function(){const terms=this.value.toLowerCase().split(/\\s+/).filter(Boolean);document.querySelectorAll('tbody tr').forEach(r=>{r.style.display=terms.every(t=>r.textContent.toLowerCase().includes(t))?'':'none';});});</script>'''
    (out/'statistics.html').write_text(page+search+'<h2>绝对时间</h2>'+table(absolute)+'<h2>配对速度比</h2>'+table(comparisons)+js+'</html>')
    (out/'verification.json').write_text(json.dumps(dict(status='passed',**result['counts'],
        recomputed_from_measurement_records=True,raw_measurement_hashes_bound=len(bindings),
        archived_medians_unchanged=True,primary_summary='arithmetic mean +/- sample SD',
        historical_selection_unchanged=True,quality_and_input_pairing_checked=True,
        sample_sd_ddof=1,single_sample_sd=None,lookahead_reuse_missing_not_zero=True,new_solver_runs=0),indent=2)+'\n')
    with zipfile.ZipFile(HERE/'statistics_data.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for filename in ['README.txt','raw_runs.csv','absolute_statistics.csv','paired_runs.csv',
                         'paired_statistics.csv','statistics.json','statistics.html','source_manifest.json','verification.json','calculation_check.json']:
            z.write(out/filename,filename)
    return result

if __name__=='__main__':
    print(json.dumps(build_statistics()['counts']))
