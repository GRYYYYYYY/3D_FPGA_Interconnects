"""Summarize retained native slice experiments without mixing diagnostic timing."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re
import statistics

from prepare import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/native_cpu_slices_20261101'


def read_events(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def diagnostic(row):
    """Keep nested wall scopes and summed worker work distinct."""
    directory = Path(row['directory'])
    events = read_events(directory/'cpu_trace.jsonl')
    grouped = defaultdict(list)
    for event in events:
        grouped[event['event']].append(event)
    phases = {name:{'calls':len(es),'sum_seconds':sum(e['duration_ns'] for e in es)/1e9,
                    'max_observed_rss_kib':max(e['rss_kib'] for e in es)} for name,es in grouped.items()}
    floods = grouped['flood']
    by_source = defaultdict(list)
    for event in floods: by_source[event['source']].append(event)
    locations = defaultdict(list)
    for event in grouped['sample_selection']:
        for rank,source in enumerate(event['sources']):
            locations[source].append({'layer':event['layer'],'segment':event['segment'],
                                      'channel':event['channel'],'rank':rank})
    repeated = {source:locations[source] for source,es in by_source.items() if len(es)>1}
    total_work = sum(e['duration_ns'] for e in floods)
    duplicate_work = sum(sum(e['duration_ns'] for e in es[1:]) for es in by_source.values())
    # Maximum number of overlapping native flood intervals, distinct from thread count.
    changes = sorted([(e['start_ns'],1) for e in floods]+[(e['end_ns'],-1) for e in floods])
    active=0; peak=0
    for _,change in changes: active+=change;peak=max(peak,active)
    group_profiles = read_events(directory/'lookahead_profile.jsonl')
    profile = {field:(sum(e.get(field,0) for e in group_profiles)/1e9 if any(field in e for e in group_profiles) else None)
               for field in ['selection_ns','init_ns','search_ns','merge_ns','wall_ns']}
    main = phases.get('main_total',{}).get('sum_seconds')
    log=(directory/'process.log').read_text(errors='replace')
    root_timers=[{'name':name,'seconds':float(value)} for name,value in
                 re.findall(r'^# (.+?) took ([0-9.]+) seconds',log,re.M)]
    residual=row['native_process_seconds']-sum(t['seconds'] for t in root_timers)
    return {'key':row['key'],'case':row['case'],'variant':row['variant'],
            'process_seconds':row['native_process_seconds'],'phase_scopes':phases,
            'worker_flood_seconds':total_work/1e9,'flood_count':len(floods),'unique_sources':len(by_source),
            'duplicate_sources':repeated,'duplicate_worker_seconds':duplicate_work/1e9,
            'duplicate_work_fraction':duplicate_work/total_work if total_work else None,
            'peak_concurrent_floods':peak,'peak_queue_entries':max([e['peak_queue'] for e in floods]+[0]),
            'rr_nodes':max([e['rr_nodes'] for e in floods]+[0]),
            'work_counts':{k:sum(e[k] for e in floods) if floods else None for k in ['pushes','pops','expanded','edge_visits']},
            'lookahead_profile_seconds':profile,
            'outside_main_seconds':row['native_process_seconds']-main if main is not None else None,
            'root_timers':root_timers,'root_timer_residual_seconds':residual,
            'residual_after_xml_and_cleanup_seconds':residual-phases.get('post_routing_xml',{}).get('sum_seconds',0)-phases.get('vpr_free_all',{}).get('sum_seconds',0) if main is not None else None,
            'scheduler_budget':grouped['scheduler_budget'],
            'scope':'Nested phase scopes overlap; flood/profile search sums are worker work, not parallel wall time.'}


def distribution(values):
    return {'values':values,'median':statistics.median(values),'min':min(values),'max':max(values)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--partial',action='store_true')
    parser.add_argument('--memory-config',action='store_true')
    args=parser.parse_args()
    summaries=[];rows=[];all_terminal=True
    for plan_path in sorted(OUT.glob('*_plan.json')):
        plan=json.loads(plan_path.read_text());stage=plan_path.stem.removesuffix('_plan')
        entry={'stage':stage,'planned':plan['planned_samples'],'completed':0,'successful':0,'pending':0,
               'diagnostics':plan['diagnostics'],'lanes':{}}
        for lane in plan['lanes']:
            path=Path(plan['output'])/lane/'summary.json'
            if not path.exists():all_terminal=False;entry['lanes'][lane]='not_started';continue
            summary=json.loads(path.read_text());entry['lanes'][lane]=summary['status']
            all_terminal &= summary['status']=='completed'
            for row in summary['measurements']:
                if row['status']=='running':entry['pending']+=1;continue
                row=dict(row,stage=stage,effective_diagnostics=plan['diagnostics'])
                rows.append(row);entry['completed']+=1;entry['successful']+=bool(row['success'])
        summaries.append(entry)
    diagnostics=[diagnostic(row) for row in rows if row['effective_diagnostics'] and row['success']]
    if args.memory_config:
        path=OUT/'memory_config.json'
        if path.exists():raise RuntimeError('Memory configuration already frozen')
        selected=[d for d in diagnostics if d['variant']=='refactored' and d['case'] in ['gemm','elliptic']]
        if len(selected)!=2 or any(d['flood_count']!=40 for d in selected):
            raise RuntimeError('Need complete 40-flood refactored diagnostics for both cases')
        estimates=[]
        for d in selected:
            label_bytes=4*d['rr_nodes']+math.ceil(d['rr_nodes']/8)
            # Source PQ_Entry: StrongId<uint32_t> plus four floats = 20 bytes.
            # Allow <2x observed queue occupancy for vector capacity, then 25% margin.
            estimate=math.ceil((label_bytes+2*d['peak_queue_entries']*20)*1.25/(1<<20))*(1<<20)
            estimates.append(dict(case=d['case'],observed_peak_queue=d['peak_queue_entries'],
                                  rr_nodes=d['rr_nodes'],estimated_workspace_bytes=estimate))
        config={'environment':{'VPR_CPU_LOOKAHEAD_TEMP_BYTES':str(2<<30),
                               'VPR_CPU_LOOKAHEAD_WORKSPACE_BYTES':str(max(e['estimated_workspace_bytes'] for e in estimates))},
                'estimates':estimates,'selection':'Fixed 2 GiB temporary target, one conservative maximum workspace estimate for both circuits and all thread counts; no speed-based tuning.',
                'bound_scope':'Map count and workspace object count are bounded. Heap capacity, allocator retention, graph and total RSS are not hard-capped by this estimate.',
                'evidence':{str(OUT/'diagnostic'/d['case']/d['key']/'cpu_trace.jsonl'):
                            sha256(OUT/'diagnostic'/d['case']/d['key']/'cpu_trace.jsonl') for d in selected}}
        write_json(path,config)
    paired=[]
    formal=[row for row in rows if row['stage']=='confirmation']
    lookup={(row['case'],row['workers'],row['cache_mode'],row['repeat'],row['variant']):row for row in formal}
    for case in ['gemm','elliptic']:
        for workers in [4,8]:
            for cache in ['rebuild','reuse']:
                for control,candidate in [('frozen','slice'),('slice','compact'),('compact','bounded'),('frozen','compact'),('frozen','bounded'),('frozen','pipeline'),('pipeline','bounded')]:
                    pairs=[]
                    for repeat in range(3):
                        a=lookup.get((case,workers,cache,repeat,control));b=lookup.get((case,workers,cache,repeat,candidate))
                        if not a or not b:continue
                        quality=a['success'] and b['success'] and b['critical_path_ns']<=1.05*a['critical_path_ns'] and b['wirelength']<=1.05*a['wirelength']
                        equal_cpu=a['cpu_budget']['cpu_set']==b['cpu_budget']['cpu_set']
                        if not equal_cpu:raise RuntimeError('Pair does not share a physical CPU set')
                        if not quality:continue
                        pairs.append({'repeat':repeat,'process_ratio':a['native_process_seconds']/b['native_process_seconds'],
                                      'workflow_ratio':a['workflow_seconds']/b['workflow_seconds'],
                                      'lookahead_ratio':a['log_evidence']['stage_seconds'].get('lookahead_build',0)/b['log_evidence']['stage_seconds']['lookahead_build'] if b['log_evidence']['stage_seconds'].get('lookahead_build',0) else None,
                                      'control_seconds':a['native_process_seconds'],'candidate_seconds':b['native_process_seconds'],
                                      'same_route_body':a['route_body_sha256']==b['route_body_sha256'],
                                      'control_hwm_kib':a['cpu_budget_audit']['peak_observed_hwm_kib'],
                                      'candidate_hwm_kib':b['cpu_budget_audit']['peak_observed_hwm_kib']})
                    if pairs:
                        paired.append({'case':case,'workers':workers,'cache_mode':cache,'control':control,'candidate':candidate,
                                       'valid_pairs':len(pairs),'pairs':pairs,
                                       'process_ratio':distribution([p['process_ratio'] for p in pairs]),
                                       'workflow_ratio':distribution([p['workflow_ratio'] for p in pairs])})
    failure=[{'stage':r['stage'],'key':r['key'],'returncode':r.get('returncode'),'directory':r['directory']} for r in rows if not r['success']]
    status='complete' if all_terminal and any(s['stage']=='confirmation' and s['completed']==s['planned'] for s in summaries) else 'in_progress'
    if not args.partial and status!='complete':raise RuntimeError('Experiment has not finished')
    promotion=False
    if status=='complete' and not failure:
        main_pairs=[p for p in paired if p['control']=='frozen' and p['candidate']=='bounded']
        promotion=len(main_pairs)==8 and all(p['valid_pairs']==3 for p in main_pairs)
        for p in main_pairs:
            if p['case']=='gemm' and p['cache_mode']=='rebuild':
                promotion &= p['process_ratio']['min']>1 and p['process_ratio']['median']>1.02
            else:
                promotion &= p['process_ratio']['median']>=1/1.02
    data={'status':status,'stages':summaries,'failures':failure,'diagnostics':diagnostics,
          'paired_comparisons':paired,'promotion_rule_passed':promotion,
          'successful_maps':sum(r.get('wire_map_matches_serial',False) for r in rows),
          'successful_routes':sum(r['success'] for r in rows),
          'diagnostic_flag_note':'The old runner sets execution_settings.diagnostics=false. Use frozen plan diagnostics and top-level diagnostic_sample; no raw records were rewritten.',
          'limitations':['Shared host and memory; no resource exclusivity','One fixed placement seed; runtime repeats, not independent placements',
                         'Single and dual layer native gates; higher layer interpolation evidence remains synthetic',
                         'Peak process RSS may be dominated by RR XML loading, masking temporary-map differences']}
    write_json(OUT/('analysis.partial.json' if args.partial else 'analysis.json'),data)
    print(json.dumps({'status':status,'stages':summaries,'failures':failure,'promotion':promotion}))


if __name__=='__main__':
    main()
