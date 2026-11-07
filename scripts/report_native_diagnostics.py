"""Analyze uniquely keyed batch timings and actual native takeover evidence.

Host intervals and CUDA event intervals overlap and are never summed together.
Snapshots/repetitions are diagnostic data, never deployable dispatch features.
"""
import argparse
from collections import Counter,defaultdict
import csv
import json
from pathlib import Path
import re
import statistics
from prepare import write_json


def rows(path):
    if not path.exists():return []
    with path.open() as f:result=list(csv.DictReader(f))
    if any(None in row or any(v is None for v in row.values()) for row in result):raise ValueError('incomplete CSV: '+str(path))
    return result


def integer(row,key):
    return int(row.get(key,0))


def stats(values):
    if not values:return {'count':0}
    values=sorted(values)
    return {'count':len(values),'sum':sum(values),'median':statistics.median(values),'p95':values[min(len(values)-1,int(len(values)*.95))],'max':max(values)}


def batch_observation(b):
    """Nonexclusive evidence flags, not proofs of intrinsic independence."""
    if integer(b,'size')>1:return ['multiple_ready_queries']
    flags=[]
    if integer(b,'active_partitions')==1 and integer(b,'queued_partitions')==0 and integer(b,'branch_parents')>0:flags.append('single_parent_partition_with_children_unreleased')
    if integer(b,'lease_waiters')>0:flags.append('ownership_waiters_present')
    if integer(b,'active_searches')>integer(b,'ready_queries'):flags.append('other_native_searches_not_yet_ready')
    if integer(b,'queued_partitions')>0:flags.append('native_partition_tasks_queued')
    if not flags:flags.append('insufficient_ready_queries_at_deadline_unresolved')
    return flags


def replay_comparison(directory, data):
    """Compare within this worker/run only; refuse missing or duplicate repeats."""
    grouped=defaultdict(list)
    for r in data:grouped[int(r['sequence'])].append(r)
    native_files={int(p.name.split('.')[0].split('_')[1]):p for p in directory.glob('takeover_*.native.csv')}
    if not grouped or set(grouped)!=set(native_files):raise ValueError('replay/native snapshot coverage mismatch')
    samples=[]
    for seq,rs in sorted(grouped.items()):
        if sorted(int(r['repeat']) for r in rs)!=[-1,0,1,2] or any(r['valid']!='1' for r in rs):raise ValueError('invalid/incomplete GPU repetitions')
        cpu=rows(native_files[seq])
        if sorted(int(r['repeat']) for r in cpu)!=[0,1,2] or any(r['identical']!='1' for r in cpu):raise ValueError('invalid/incomplete native repetitions')
        if len({(r['cost'],r['pops'],r['path_edges']) for r in cpu})!=1:raise ValueError('native continuation changed')
        if any(int(r['sequence'])!=seq or r['net']!=rs[0]['net'] or r['iteration']!=rs[0]['iteration'] for r in cpu):raise ValueError('CPU/GPU snapshot identity mismatch')
        warm=[r for r in rs if int(r['repeat'])>=0]
        samples.append({'sequence':seq,'net':int(rs[0]['net']),'iteration':int(rs[0]['iteration']),
                        'native_median_ns':statistics.median(int(r['cpu_remaining_ns']) for r in cpu),
                        'gpu_median_ns':statistics.median(int(r['dispatch_ns']) for r in warm),
                        'kernel_median_ns':statistics.median(int(r['search_kernel_event_ns']) for r in warm)})
    return {'snapshots':len(samples),'native_repetitions':3*len(samples),'gpu_warmup_paths':len(samples),'gpu_measured_paths':3*len(samples),
            'native_median_sum_seconds':sum(r['native_median_ns'] for r in samples)/1e9,
            'gpu_median_sum_seconds':sum(r['gpu_median_ns'] for r in samples)/1e9,
            'kernel_median_sum_seconds':sum(r['kernel_median_ns'] for r in samples)/1e9,
            'gpu_median_wins':sum(r['gpu_median_ns']<r['native_median_ns'] for r in samples),
            'net_count':len({r['net'] for r in samples}),
            'iteration_range':[min(r['iteration'] for r in samples),max(r['iteration'] for r in samples)],
            'samples':samples,'scope':'Same-worker native CPU continuations vs offline GPU medians; distinct host implementation and cache effects, not production scheduling evidence.'}


def summarize(directory):
    queries=rows(directory/'hybrid.json.queries.csv');batches=rows(directory/'hybrid.json.batches.csv');events=rows(directory/'hybrid.json.events.csv');commits=rows(directory/'hybrid.json.commits.csv')
    ids=[integer(b,'batch_id') for b in batches]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate batch ID')
    counts=Counter(integer(q,'batch_id') for q in queries if integer(q,'batch_id'))
    for b in batches:
        if counts[integer(b,'batch_id')]!=integer(b,'size'):raise ValueError('batch/query membership mismatch')
    bmap={integer(b,'batch_id'):b for b in batches}
    for q in queries:
        if integer(q,'batch_id') and integer(q,'batch_id') not in bmap:raise ValueError('query refers to missing batch')
    native_fields=['init_ns','state_prepare_ns','queue_ns','commit_ns','capture_ns','native_replay_ns']
    batch_fields=[k for k in (batches[0] if batches else {}) if k.endswith('_ns') and k!='dispatch_elapsed_ns']
    result={'queries':len(queries),'batches':len(batches),'batch_size_histogram':dict(Counter(integer(b,'size') for b in batches)),
            'query_host_seconds':{k:sum(integer(q,k) for q in queries)/1e9 for k in native_fields},
            'unique_batch_seconds':{k:sum(integer(b,k) for b in batches)/1e9 for k in batch_fields},
            'native_tree_commit_seconds':sum(integer(c,'native_tree_commit_ns') for c in commits)/1e9,
            'gpu_failures':sum(integer(q,'failed') or not integer(q,'ran') for q in queries),
            'batch_observation_counts':dict(Counter(flag for b in batches for flag in batch_observation(b))),
            'partition_depth_at_offload':dict(Counter(integer(q,'partition_depth') for q in queries)),
            'queue_depth_at_dispatch':stats([integer(b,'queue_depth') for b in batches]),
            'ready_at_dispatch':stats([integer(b,'ready_queries') for b in batches]),
            'ownership_wait_events':sum(e['event']=='lease_wait' for e in events),
            'own_expansion_only_conflict_events':sum(integer(e,'expanded_only_conflicts')>0 for e in events),
            'note':'Batch clocks counted once. Host wait includes device execution; CUDA event brackets around pageable copies can include staging/idle, not hardware bus utilization. Search events bracket the search kernel. Active counters are sampled concurrently, not an atomic scheduler snapshot.'}
    pair=[q for q in queries if q['mode']=='pair' and integer(q,'ran') and not integer(q,'failed')]
    if pair:
        def clean(q):return integer(q,'dispatch_ns')-integer(q,'init_ns')-integer(q,'capture_ns')-integer(q,'native_replay_ns')
        groups={name:[q for q in pair if bool(integer(q,'captured'))==captured] for name,captured in [('captured',True),('uncaptured',False)]}
        result['paired']={name:{'queries':len(qs),'gpu_full_handoff_wins':sum(clean(q)<integer(q,'cpu_remaining_ns') for q in qs),
                               'cpu_remaining_seconds':sum(integer(q,'cpu_remaining_ns') for q in qs)/1e9,
                               'handoff_excluding_initialization_capture_replay_seconds':sum(clean(q) for q in qs)/1e9,
                               'kernel_slower_than_cpu':sum(integer(bmap[integer(q,'batch_id')],'search_kernel_event_ns')>=integer(q,'cpu_remaining_ns') for q in qs),
                               'kernel_seconds':sum(integer(bmap[integer(q,'batch_id')],'search_kernel_event_ns') for q in qs)/1e9}
                          for name,qs in groups.items()}
        result['paired_samples']=[{**{k:q[k] for k in ['sequence','net','iteration','cpu_pops','seeds','active_seeds','captured']},
                                   'cpu_remaining_ns':integer(q,'cpu_remaining_ns'),'gpu_handoff_ns':clean(q),
                                   'kernel_ns':integer(bmap[integer(q,'batch_id')],'search_kernel_event_ns')} for q in pair]
    path=directory/'process.log'
    if path.exists():
        text=path.read_text(errors='replace')
        result['vpr_stage_seconds']={name:float(v[-1]) if v else None for name,pattern in [
            ('rr_graph_load',r'Loading routing resource graph took ([\d.]+) seconds'),
            ('lookahead_build',r'Computing router lookahead map took ([\d.]+) seconds'),
            ('routing',r'# Routing took ([\d.]+) seconds')] for v in [re.findall(pattern,text)]}
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    source=json.loads((args.run/'routing/summary.json').read_text());report={'scope':'diagnostic; no production speedup ratios','measurements':[]}
    for m in source['measurements']:
        directory=args.run/'routing'/Path(m['directory']).name
        row={k:m.get(k) for k in ['case','variant','success','status','returncode','native_process_seconds','workflow_seconds','critical_path_ns','wirelength','routing_seconds','hybrid']}
        try:row['diagnostics']=summarize(directory)
        except ValueError as e:row['incomplete_diagnostics']=str(e)
        report['measurements'].append(row)
    report['replays']=[]
    for path in sorted(args.run.glob('*_pair_replay.log')):
        parse_error=None
        try:data=rows(path)
        except ValueError as e:
            parse_error=str(e)
            with path.open() as f:data=[r for r in csv.DictReader(f) if None not in r and all(v is not None for v in r.values())]
        warm=[r for r in data if int(r['repeat'])>=0];group=defaultdict(list)
        for r in warm:group[int(r['sequence'])].append(r)
        entry={'file':str(path),'parse_error':parse_error,'complete':parse_error is None,'paths':len(data),'valid':sum(r['valid']=='1' for r in data),'warm_queries':len(group),'samples':[]}
        for seq,rs in group.items():
            entry['samples'].append({'sequence':seq,'net':int(rs[0]['net']),'iteration':int(rs[0]['iteration']),
                                     'dispatch_ns':stats([int(r['dispatch_ns']) for r in rs]),'kernel_ns':stats([int(r['search_kernel_event_ns']) for r in rs])})
        if entry['complete']:
            try:entry['same_state_comparison']=replay_comparison(args.run/'routing'/path.stem.removesuffix('_replay')/'takeovers',data)
            except ValueError as e:entry.update(complete=False,comparison_error=str(e))
        report['replays'].append(entry)
    write_json(args.output,report)


if __name__=='__main__':main()
