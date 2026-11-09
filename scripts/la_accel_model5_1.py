#!/usr/bin/env python3
"""R5.1 bounded parent/edge replay and conditional bounds; never hardware timing.

Reuses R5 traces without changing STRICT search. A P event starts a parent and
E.seq is an absolute CSR index. U attaches to its preceding E (except seed).
No new search, golden-based task filtering, software timing, or Vivado run.
"""
import argparse
import bisect
import csv
import hashlib
import json
import math
import struct
from collections import deque
from pathlib import Path

SNAPSHOT = Path('results/lookahead_accel_round5_20261109T054024Z/evidence_snapshot')
DEFAULT = dict(name='old_blocking_pq', evidence='unverified_conditional_assumptions',
               level_cycles=3, pop_base=5, push_base=2,
               edge_latency=7, edge_ii=1, commit_latency=2,
               map_latency=4, candidate_depth=4, pq_queue_depth=4,
               pq_enqueue_ii=1, map_queue_depth=4, contexts=2, partitions=2,
               reset_writes_per_cycle=1, output_cells_per_cycle=1,
               barrier_cycles=1, drain_cycles=8, edge_parent_hol=True,
               pq_mapping='context', reset_mode='shared_commit', commit_owner_ii=1)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def read_trace(root, w, pop_trace=None):
    path = root / SNAPSHOT / 'profiles' / (w['case'] + '.csv')
    workload = Path(w['path'])
    if not workload.exists():
        workload = root / str(workload).split('/3D_FPGA_Interconnects/')[-1]
    assert sha(workload) == w['sha256'], 'workload changed'
    raw = workload.read_bytes()
    rows = struct.unpack_from('<' + 'Q' * (w['N'] + 1), raw, 56)
    edge_base = 56 + (w['N'] + 1) * 8 + w['N'] * 16
    queries = [dict(seed=None, parents=[]) for _ in range(w['J'])]
    previous = [None] * w['J']
    counts = dict(parents=0, edges=0, pushes=0, duplicate_dst_within_parent=0,
                  parents_without_edges=0)
    with path.open() as f:
        for early, q, op, work, seq in csv.reader(f):
            if early != '1':
                continue
            q, work, seq = int(q), int(work), int(seq)
            query = queries[q]
            if op == 'P':
                assert seq == len(query['parents']) + 1
                query['parents'].append(dict(levels=work, seq=seq, edges=[]))
                counts['parents'] += 1
            elif op == 'E':
                assert query['parents']
                parent = query['parents'][-1]
                source = bisect.bisect_right(rows, seq) - 1
                ordinal = seq - rows[source]
                edges = parent['edges']
                if edges:
                    assert source == parent['source'] and ordinal == edges[-1]['ordinal'] + 1
                else:
                    assert ordinal == 0
                    parent['source'] = source
                dst = struct.unpack_from('<I', raw, edge_base + 8 * seq)[0]
                edges.append(dict(index=seq, ordinal=ordinal, dst=dst,
                                  eligible=bool(work), push=None))
                counts['edges'] += 1
            elif op == 'U':
                if not query['parents']:
                    assert query['seed'] is None and seq == 1
                    query['seed'] = work
                else:
                    assert previous[q] == 'E'
                    edge = query['parents'][-1]['edges'][-1]
                    assert edge['push'] is None and edge['eligible']
                    edge['push'] = work
                counts['pushes'] += 1
            else:
                raise ValueError(op)
            previous[q] = op
    profile = [json.loads(s) for s in (path.with_suffix('.jsonl')).read_text().splitlines()]
    for q, query in enumerate(queries):
        p = next(p for p in profile if p['early'] and p['qid'] == q)
        assert len(query['parents']) == p['pops']
        edges = [e for par in query['parents'] for e in par['edges']]
        assert len(edges) == p['original_edges']
        assert sum(e['push'] is not None for e in edges) + (query['seed'] is not None) == p['pushes']
        query['profile_heap_peak'] = p['heap_peak']
        query['heap_down_levels'] = p['heap_down_levels']
        query['heap_up_levels'] = p['heap_up_levels']
        for par in query['parents']:
            counts['duplicate_dst_within_parent'] += len(par['edges']) - len({e['dst'] for e in par['edges']})
            counts['parents_without_edges'] += not par['edges']
    extra = {}
    if pop_trace is not None and pop_trace.exists():
        split_count = 0
        with pop_trace.open() as f:
            for row in csv.DictReader(f):
                if row['early'] != '1':
                    continue
                parent = queries[int(row['qid'])]['parents'][int(row['pop']) - 1]
                down, up = int(row['down']), int(row['up_compares'])
                assert down + up == parent['levels'] and 'split' not in parent
                parent['split'] = (down, up, int(row['up_moves']), int(row['initial_size']))
                split_count += 1
        assert split_count == counts['parents']
        extra = dict(pop_split_trace_sha256=sha(pop_trace), pop_split_trace_path=str(pop_trace))
    return queries, dict(trace_sha256=sha(path), workload_sha256=sha(workload), **counts, **extra)


def latency(op, levels, c):
    if isinstance(levels, (tuple, list)):
        down, up = levels[:2]
        if c.get('pop_formula') == 'rtl_path51':
            assert len(levels) == 4
            return 4 if levels[3] == 1 else 11 + 2 * down + levels[2]
        if c.get('pop_formula') == 'observer_d_envelope' and levels[3] == 1:
            return c['singleton_pop_cycles']
        return c['level_cycles'] * (down + up) + c['pop_base'] - c.get('pop_up_saved_cycles', 0) * up
    if op == 'P' and c.get('pop_up_saved_cycles', 0):
        raise ValueError('POP-UP savings require validated per-POP split trace')
    return c['level_cycles'] * levels + c['pop_base' if op == 'P' else 'push_base']


def bounds(queries, w, c):
    per_q = []
    for q in queries:
        total = latency('U', q['seed'], c) if q['seed'] is not None else 0
        for p in q['parents']:
            total += latency('P', p.get('split', p['levels']), c)
            total += sum(latency('U', e['push'], c) for e in p['edges'] if e['push'] is not None)
        per_q.append(total)
    parts = c['partitions']
    partition = [sum(t for i, t in enumerate(per_q) if i % parts == p) for p in range(parts)]
    return dict(per_qid_pq_serial_cycles=per_q, total_blocking_pq_service_cycles=sum(per_q),
                evidence_scope='conditional_resource_bound_for_assigned_model_latencies_not_proven_native_hardware_lower_bound',
                observer_envelope_extrapolated=c.get('pop_formula') == 'observer_d_envelope',
                ideal_balanced_partition_bound_cycles=math.ceil(sum(per_q) / parts),
                static_qid_partition_bound_cycles=max(partition),
                longest_same_qid_pq_chain_cycles=max(per_q),
                combined_pq_bound_cycles=max(max(partition) if c['pq_mapping'] == 'qid_static' else math.ceil(sum(per_q)/parts), max(per_q)),
                ideal_partition_bounds={str(p): math.ceil(sum(per_q)/p) for p in (1, 2, 4)},
                static_partition_bound_applies=c['pq_mapping'] == 'qid_static',
                conditions=['Same qid heap operations cannot overlap; includes seed.',
                            'Each partition is occupied for full feedback. Static-qid bound only applies with qid_static mapping; context mapping uses ideal aggregate bound.',
                            'Edge/reset/map/output hidden completely; this is not a universal exact-search bound.'])


def path_cache_bounds(queries, w):
    """Aggregate POP-UP work is exact; per-operation DOWN/UP split is absent."""
    old = bounds(queries, w, DEFAULT)
    pop_up = []
    for q in queries:
        push_levels = (q['seed'] or 0) + sum(
            e['push'] for p in q['parents'] for e in p['edges'] if e['push'] is not None)
        value = q['heap_up_levels'] - push_levels
        assert value >= 0
        assert sum(p['levels'] for p in q['parents']) == q['heap_down_levels'] + value
        pop_up.append(value)
    points = []
    for saved in (1, 2, 3):
        per_q = [t - saved * u for t, u in zip(old['per_qid_pq_serial_cycles'], pop_up)]
        points.append(dict(assumed_cycles_saved_per_pop_up_level=saved,
                           total_pq_service_cycles=sum(per_q),
                           per_qid_pq_serial_cycles=per_q,
                           longest_same_qid_pq_chain_cycles=max(per_q),
                           ideal_partition_bounds={str(p): math.ceil(sum(per_q)/p) for p in (1, 2, 4)},
                           measured=False, full_replay_estimate_available=False))
    return dict(per_qid_pop_up_levels=pop_up, points=points,
                assumption='Only POP-UP levels save 1, 2, or all 3 cycles; DOWN and PUSH remain old 3-cycle levels and base costs remain 5/2. No added path register/writeback overhead.',
                limitation='Trace aggregates DOWN+UP per POP; JSONL provides aggregate exact split per qid. These are bounds, not invented per-POP timing or a measured path-cache contract.')


def simulate(queries, w, c, max_cycles=10000000):
    """Cycle-stepped finite-resource model, fixed round-robin resource arbitration.

    One active PQ op/partition (no invented level banking), queue acceptance II
    separate from operation latency. Candidates reserve a slot at edge launch,
    retain it through commit, and can launch while earlier pushes are unfinished.
    One shared edge lane, one commit owner, one map owner, one output writer.
    Reset and label RMW share a round-robin commit owner by default.
    """
    for key, value in c.items():
        if isinstance(value, int) and not isinstance(value, bool):
            assert value > 0, key
    ctx = min(c['contexts'], len(queries))
    if not ctx:
        return dict(batch_cycles=0)
    queues = [deque() for _ in range(c['partitions'])]
    busy = [None] * c['partitions']
    pq_start_free = [0] * c['partitions']
    responses = [deque() for _ in range(c['partitions'])]
    enqueue_free = [0] * c['partitions']
    pq_starts = [[] for _ in range(c['partitions'])]
    pq_retires = [[] for _ in range(c['partitions'])]
    map_queue, map_busy = deque(), None
    contexts, nextq, completed = [], 0, 0
    edge_free = commit_free = output_free = 0
    edge_owner = None
    stats = dict(edge_launches=0, commits=0, pq_enqueues=0, pq_starts=0,
                 pq_retires=0, max_candidate_occupancy=0, max_pq_fifo_occupancy=0,
                 candidate_full_cycles=0, pq_fifo_full_cycles=0,
                 same_parent_edge_launch_while_push_pending=0,
                 max_logical_size=0, duplicate_dst_commits=0,
                 max_map_fifo_occupancy=0, map_fifo_full_cycles=0,
                 pq_queue_wait_cycles=0, pq_feedback_latency_cycles=0,
                 reset_label_writes=0, max_response_fifo_occupancy=0)
    witness = []
    finish = []
    capacity = c.get('heap_capacity', w['E'] + 1)

    def assign(q, t, slot):
        return dict(q=q, slot=slot, state='reset', until=t + math.ceil(w['N'] / c['reset_writes_per_cycle']) + w['cells'],
                    reset_remaining=w['N'],
                    parent=0, edge=0, candidates=deque(), pending=0, logical=0,
                    peak=0, committed=-1, seen_dst=set())

    for _ in range(ctx):
        contexts.append(assign(nextq, 0, len(contexts)))
        nextq += 1

    def enqueue(x, op, levels, t):
        part = (x['q'] if c['pq_mapping'] == 'qid_static' else x['slot']) % c['partitions']
        if len(queues[part]) >= c['pq_queue_depth'] or t < enqueue_free[part]:
            stats['pq_fifo_full_cycles'] += 1
            return False
        if op == 'U':
            if x['logical'] >= capacity:
                raise OverflowError('QUEUE_OVERFLOW at semantic push acceptance (not a FIFO stall)')
            x['logical'] += 1
            x['peak'] = max(x['peak'], x['logical'])
        else:
            assert x['logical'] > 0
            x['logical'] -= 1
        stats['max_logical_size'] = max(stats['max_logical_size'], x['logical'])
        x['pending'] += 1
        queues[part].append((t + 1, x, op, levels))
        enqueue_free[part] = t + c['pq_enqueue_ii']
        stats['pq_enqueues'] += 1
        stats['max_pq_fifo_occupancy'] = max(stats['max_pq_fifo_occupancy'], len(queues[part]))
        return True

    for t in range(max_cycles):
        # Each owner progresses every cycle; no shared dispatcher issue slot.
        if map_busy is not None and map_busy[0] <= t:
            _, x = map_busy
            x['until'] = t
            map_busy = None
        if map_busy is None and map_queue and map_queue[0][0] <= t:
            _, x = map_queue.popleft()
            map_busy = (t + c['map_latency'], x)
        for part in range(c['partitions']):
            if busy[part] is not None and busy[part][0] <= t and len(responses[part]) < 4:
                _, x, op = busy[part]
                stats['pq_retires'] += 1
                pq_retires[part].append(t)
                pq_start_free[part] = t + (c.get('pop_reaccept_gap', 0) if op == 'P' else c.get('push_reaccept_gap', 0))
                busy[part] = None
                responses[part].append((t + c.get('response_latency', 0), x, op))
                stats['max_response_fifo_occupancy'] = max(stats['max_response_fifo_occupancy'], len(responses[part]))
            if responses[part] and responses[part][0][0] <= t:
                _, x, op = responses[part].popleft()
                x['pending'] -= 1
                if op == 'P':
                    assert x['state'] == 'pop_wait'
                    x['state'] = 'map'
            if busy[part] is None and t >= pq_start_free[part] and queues[part] and queues[part][0][0] <= t:
                ready, x, op, levels = queues[part].popleft()
                busy[part] = (t + latency(op, levels, c), x, op)
                stats['pq_starts'] += 1
                pq_starts[part].append(t)
                stats['pq_queue_wait_cycles'] += t - ready + 1
                stats['pq_feedback_latency_cycles'] += latency(op, levels, c)
        for offset in range(ctx):
            slot = (t + offset) % ctx
            x = contexts[slot]
            if x is None:
                continue
            q = queries[x['q']]
            state = x['state']
            commit_turn = t % c['commit_owner_ii'] == 0 and slot == (t // c['commit_owner_ii']) % ctx
            if state == 'reset' and c['reset_mode'] == 'shared_commit':
                if commit_turn and t >= commit_free:
                    amount = min(c['reset_writes_per_cycle'], x['reset_remaining'])
                    x['reset_remaining'] -= amount
                    stats['reset_label_writes'] += amount
                    commit_free = t + c['commit_owner_ii']
                    if not x['reset_remaining']:
                        x.update(state='reset_wait', until=t + 1 + w['cells'])
            elif state in ('reset', 'reset_wait') and t >= x['until']:
                if state == 'reset':
                    stats['reset_label_writes'] += w['N']
                x['state'] = 'seed' if q['seed'] is not None else 'output'
            elif state == 'seed':
                if enqueue(x, 'U', q['seed'], t):
                    x['state'] = 'seed_wait'
            elif state == 'seed_wait' and not x['pending']:
                x['state'] = 'pop' if q['parents'] else 'output'
            elif state == 'pop':
                parent = q['parents'][x['parent']]
                if enqueue(x, 'P', parent.get('split', parent['levels']), t):
                    x['state'] = 'pop_wait'
            elif state == 'map':
                # Trace omits stale-pop/map flags: charge one conservative map slot per pop.
                if len(map_queue) < c['map_queue_depth']:
                    map_queue.append((t + 1, x))
                    x['until'] = max_cycles + 1
                    x['state'] = 'map_wait'
                    stats['max_map_fifo_occupancy'] = max(stats['max_map_fifo_occupancy'], len(map_queue))
                else:
                    stats['map_fifo_full_cycles'] += 1
            elif state == 'map_wait' and t >= x['until']:
                x.update(state='edges', edge=0, committed=-1, seen_dst=set())
            elif state == 'edges':
                edges = q['parents'][x['parent']]['edges']
                candidates = x['candidates']
                # Ordered label RMW. The label write occurs only with push credit.
                if candidates and commit_turn:
                    candidate = candidates[0]
                    e = candidate['edge']
                    if candidate['phase'] == 'ready' and candidate['until'] <= t and t >= commit_free:
                        candidate.update(phase='commit', until=t + c['commit_latency'])
                        commit_free = t + c.get('commit_issue_ii', c['commit_latency'])
                    elif candidate['phase'] == 'commit' and candidate['until'] <= t:
                        accepted = e['push'] is None or enqueue(x, 'U', e['push'], t)
                        if accepted:
                            assert e['ordinal'] == x['committed'] + 1
                            x['committed'] = e['ordinal']
                            stats['duplicate_dst_commits'] += e['dst'] in x['seen_dst']
                            x['seen_dst'].add(e['dst'])
                            candidates.popleft()
                            stats['commits'] += 1
                if x['edge'] < len(edges):
                    if len(candidates) >= c['candidate_depth']:
                        stats['candidate_full_cycles'] += 1
                    elif t >= edge_free and (not c['edge_parent_hol'] or edge_owner is None or edge_owner is x):
                        if c['edge_parent_hol']:
                            edge_owner = x
                        e = edges[x['edge']]
                        if x['pending']:
                            stats['same_parent_edge_launch_while_push_pending'] += 1
                            if len(witness) < 16:
                                witness.append(dict(cycle=t, qid=x['q'], parent_seq=x['parent'] + 1,
                                                    edge_ordinal=e['ordinal'], pending_pushes=x['pending']))
                        candidates.append(dict(edge=e, until=t + c['edge_latency'], phase='ready'))
                        x['edge'] += 1
                        if x['edge'] == len(edges):
                            edge_owner = None
                        edge_free = t + c['edge_ii']
                        stats['edge_launches'] += 1
                        stats['max_candidate_occupancy'] = max(stats['max_candidate_occupancy'], len(candidates))
                if x['edge'] == len(edges) and not candidates and not x['pending']:
                    x.update(state='barrier', until=t + c['barrier_cycles'])
            elif state == 'barrier' and t >= x['until']:
                x['parent'] += 1
                x['state'] = 'pop' if x['parent'] < len(q['parents']) else 'output'
            elif state == 'output' and t >= output_free:
                output_free = t + math.ceil(w['cells'] / c['output_cells_per_cycle'])
                x.update(state='drain', until=output_free + c['drain_cycles'])
            elif state == 'drain' and t >= x['until']:
                assert not x['pending'] and not x['candidates']
                assert x['peak'] == q.get('profile_heap_peak', x['peak'])
                finish.append(dict(qid=x['q'], finish_cycle=t, heap_peak=x['peak']))
                completed += 1
                if nextq < len(queries):
                    contexts[slot] = assign(nextq, t, slot)
                    nextq += 1
                else:
                    contexts[slot] = None
        if completed == len(queries):
            assert all(not queue for queue in queues) and all(b is None for b in busy)
            assert all(not queue for queue in responses)
            assert not map_queue and map_busy is None
            assert stats['pq_enqueues'] == stats['pq_starts'] == stats['pq_retires']
            assert stats['edge_launches'] == stats['commits']
            def gaps(times):
                values = [b-a for a, b in zip(times, times[1:])]
                return dict(events=len(times), min_gap=min(values, default=None),
                            mean_gap=sum(values)/len(values) if values else None,
                            max_gap=max(values, default=None))
            return dict(batch_cycles=t, stats=stats, per_qid=finish,
                        pq_service_model_metrics=[dict(partition=i, request_accept_ii=c['pq_enqueue_ii'],
                                                       operation_start=gaps(pq_starts[i]),
                                                       operation_retire=gaps(pq_retires[i]))
                                                  for i in range(c['partitions'])],
                        same_parent_overlap_model_witness=witness, fifo_drained=True)
    raise RuntimeError('model exceeded bounded completion guard')


def diagnostic(root):
    r = root / SNAPSHOT
    report = json.loads((r / 'report_final.json').read_text())
    rows = []
    for contexts in (2, 4):
        path = r / f'monitor_ctx{contexts}/result.json'
        monitor = json.loads(path.read_text())
        m = monitor['transactions'][1]
        h = next(h for h in report['hardware'] if h['contexts'] == contexts)
        c = next(c for c in h['calls'] if c['case'] == 'native_d3_w8')
        assert m['phases'] == c['phase_visits']
        assert monitor['cycles'][1] == c['rtl_cycles']
        visits, dead, assign = sum(m['phases']), m['phases'][-1], m['phases'][0]
        assert m['gap_min'] == m['gap_max'] == 3
        rows.append(dict(contexts=contexts, phases=m['phases'], visits=visits, dead=dead, assign=assign,
                         rtl_cycles=c['rtl_cycles'], residual_cycles=c['rtl_cycles'] - 3 * visits,
                         revisit_cycles=3 * contexts,
                         pop_feedback_mean=m['pop_feedback_sum'] / m['pops'],
                         push_feedback_mean=m['push_feedback_sum'] / m['pushes'],
                         no_dead_same_ii_cycles=c['rtl_cycles'] - 3 * dead,
                         no_dead_ii1_visits=visits - dead, monitor_sha256=sha(path)))
    a, b = rows
    assert a['phases'][1:-1] == b['phases'][1:-1]
    assert a['residual_cycles'] == b['residual_cycles'] == 1217
    assert b['rtl_cycles'] - a['rtl_cycles'] == 3 * (b['dead'] - a['dead'] + b['assign'] - a['assign']) == 31215
    source = root / 'accel/lookahead/round5/search5.hpp'
    return dict(evidence='archived_RTL_monitor_crosschecked_with_report_and_source', contexts=rows,
                source_sha256=sha(source), source_path=str(source), report_sha256=sha(r/'report_final.json'),
                reset_visits=8*654, reference_200mhz_cpu_budget=5184,
                ready_only_speedup_ceiling=a['rtl_cycles']/a['no_dead_same_ii_cycles'],
                conclusion='DEAD and ASSIGN delta exactly explains regression; feedback is dispatcher recurrence, not isolated PQ latency.')


def selftest():
    edges = [dict(ordinal=i, dst=1, push=2, eligible=True) for i in range(8)]
    q = [dict(seed=0, parents=[dict(levels=0, edges=edges)], profile_heap_peak=8)]
    w = dict(N=2, E=8, cells=1)
    c = {**DEFAULT, 'contexts': 1, 'partitions': 1, 'pq_queue_depth': 1, 'candidate_depth': 4}
    result = simulate(q, w, c)
    assert result['stats']['same_parent_edge_launch_while_push_pending'] > 0
    assert result['stats']['duplicate_dst_commits'] == 7
    assert result['stats']['max_pq_fifo_occupancy'] == 1
    assert result['stats']['max_candidate_occupancy'] <= 4
    assert result['stats']['pq_fifo_full_cycles'] > 0
    try:
        simulate(q, w, {**c, 'heap_capacity': 2})
    except OverflowError:
        pass
    else:
        raise AssertionError('logical overflow incorrectly became backpressure')
    empty = simulate([dict(seed=None, parents=[], profile_heap_peak=0)], w, c)
    assert empty['stats']['pq_starts'] == 0 and empty['fifo_drained']
    return dict(passed=True, checks=['ordered duplicate dst', 'finite FIFO backpressure',
                                    'same-parent edge/PUSH overlap', 'logical capacity overflow',
                                    'empty target lifecycle', 'complete drain'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--experiment', type=Path, required=True)
    p.add_argument('--contract', type=Path, help='JSON object overrides defaults, or list of such objects')
    args = p.parse_args()
    root = args.root.resolve()
    r = args.experiment
    dump(r/'audit/dispatcher_recheck.json', diagnostic(root))
    contracts = [{**DEFAULT, 'contexts': n, 'name': f'old_blocking_pq_ctx{n}'} for n in (2, 4)]
    contracts.append({**DEFAULT, 'contexts': 4, 'pop_up_saved_cycles': 2,
                      'name': 'hypothetical_path_pop_up_one_cycle'})
    measured_path = r/'pq/rtl_transactions.json'
    measured_contract = None
    schedule_contract = None
    observer_contract = None
    if measured_path.exists():
        transactions = json.loads(measured_path.read_text())
        for tx in transactions:
            expected = 4 if tx['count'] == 1 else 11 + 2 * tx['down'] + tx['moves']
            assert tx['path_latency'] == expected
            assert tx['path_interval'] is None or tx['path_interval'] == expected + 1
        measured_contract = dict(path=str(measured_path), sha256=sha(measured_path),
                                 transactions=len(transactions), formula_matched=True,
                                 scope='Isolated CAP16385 POP module RTL; native service integration and PUSH latency unmeasured.')
        schedule_contract = {}
        for owner, loop in [('edge', '73_3'), ('commit', '110_3')]:
            report = r/'mechanism/hls_b/project/solution/syn/report'/f'{owner}_Pipeline_VITIS_LOOP_{loop}_csynth.rpt'
            line = next(line for line in report.read_text().splitlines() if f'|- VITIS_LOOP_{loop}' in line)
            fields = line.split('|')
            schedule_contract[owner] = dict(path=str(report), sha256=sha(report),
                                            iteration_latency=int(fields[4]), achieved_ii=int(fields[5]))
        contracts.append({**DEFAULT, 'contexts': 2, 'name': 'scheduled_services_rtl_pop_mixed_contract',
                          'evidence': 'HLS_schedule_edge_commit_and_isolated_POP_RTL_with_native_extrapolation',
                          'edge_ii': schedule_contract['edge']['achieved_ii'],
                          'edge_latency': schedule_contract['edge']['iteration_latency'],
                          'commit_latency': schedule_contract['commit']['iteration_latency'],
                          'commit_issue_ii': schedule_contract['commit']['achieved_ii'],
                          'commit_owner_ii': schedule_contract['commit']['achieved_ii'],
                          'pop_formula': 'rtl_path51', 'pop_reaccept_gap': 1})
    observer_path = r/'mechanism/observer_d_zero/result.json'
    if observer_path.exists():
        observer = json.loads(observer_path.read_text())
        assert observer['passed'] and observer['zero_hold']
        ops = [o for tx in observer['transactions'] for o in tx['operations']]
        push_base = max(o['retire']-o['start']-2*o['up_compares'] for o in ops if o['kind'] == 1)
        pop_base = max(o['retire']-o['start']-2*(o['down']+o['up_compares'])
                       for o in ops if o['kind'] == 2 and o['heap_size_before'] > 1)
        singleton = max(o['retire']-o['start'] for o in ops if o['kind'] == 2 and o['heap_size_before'] == 1)
        response_latency = max(o['feedback']-o['retire'] for o in ops)
        scheduled = {}
        for owner, loop in [('edge', '76_3'), ('commit', '116_3'), ('heap_0', '57_4')]:
            report = r/'mechanism/hls_d/project/solution/syn/report'/f'{owner}_Pipeline_VITIS_LOOP_{loop}_csynth.rpt'
            line = next(line for line in report.read_text().splitlines() if f'|- VITIS_LOOP_{loop}' in line)
            fields = line.split('|')
            scheduled[owner] = dict(path=str(report), sha256=sha(report), iteration_latency=int(fields[4]), achieved_ii=int(fields[5]))
        assert scheduled['heap_0']['achieved_ii'] == 2
        candidate = {**DEFAULT, 'contexts': 2, 'name': 'observer_d_baseline_pq_envelope_native_extrapolation',
                     'evidence': 'D_zero_hold_mechanism_RTL_envelope_and_D_schedule_native_depth_extrapolation',
                     'level_cycles': 2, 'pop_base': pop_base, 'push_base': push_base,
                     'singleton_pop_cycles': singleton, 'pop_formula': 'observer_d_envelope',
                     'pop_reaccept_gap': 1, 'push_reaccept_gap': 1, 'response_latency': response_latency,
                     'pq_enqueue_ii': min(tx['fifo_enqueue_gap']['min'] for tx in observer['transactions']),
                     'edge_ii': scheduled['edge']['achieved_ii'], 'edge_latency': scheduled['edge']['iteration_latency'],
                     'commit_owner_ii': scheduled['commit']['achieved_ii'],
                     'commit_issue_ii': scheduled['commit']['achieved_ii'],
                     'commit_latency': scheduled['commit']['iteration_latency']}
        for o in ops:
            work = (o['down'], o['up_compares'], o['up_moves'], o['heap_size_before']) if o['kind'] == 2 else o['up_compares']
            assert latency('P' if o['kind'] == 2 else 'U', work, candidate) >= o['retire']-o['start']
        for tx in observer['transactions']:
            assert tx['retire_to_start_when_queued']['min'] == tx['retire_to_start_when_queued']['max'] == 1
        observer_contract = dict(path=str(observer_path), sha256=sha(observer_path), scope=observer['scope'],
                                 operations_checked=len(ops), scheduled=scheduled,
                                 observed_max_heap_size=max(o['heap_size_before'] for o in ops),
                                 observed_max_down=max(o['down'] for o in ops),
                                 observed_max_up=max(o['up_compares'] for o in ops),
                                 envelope_covers_all_observed_execute_latencies=True,
                                 envelope='PUSH=max_observed_residual+2*UP; POP singleton measured maximum, otherwise max_observed_residual+2*(DOWN+UP). Response latency uses max(retire-to-feedback). Observed minimum FIFO enqueue gap is used as a model throttle, not proof of intrinsic queue initiation interval.',
                                 limitations='Baseline service PQ, not integrated path cache. Maximum-residual envelope covers only observed mechanism operations, not a proven upper/lower bound for deeper native heaps. Native depth/capacity, queue return timing, MAP and lifecycle remain extrapolated.')
        contracts.append(candidate)
    if args.contract:
        incoming = json.loads(args.contract.read_text())
        contracts = [{**DEFAULT, **c} for c in (incoming if isinstance(incoming, list) else [incoming])]
    for c in contracts:
        if c.get('pq_operation_overlap', False):
            raise ValueError('Overlapping PQ requires explicit banks/hazard model; unsupported, not assumed II1.')
    manifest = json.loads((root/SNAPSHOT/'workload_manifest.json').read_text())
    sensitivity = json.loads((r/'audit/round5_sensitivity.json').read_text())
    results = []
    for case in ('native_d3_w8', 'native_d4_w8', 'native_d5_w8'):
        w = next(w for w in manifest if w['case'] == case)
        queries, trace = read_trace(root, w, r/'pq'/(case+'.csv.pop_path.csv'))
        sw = next(w for w in sensitivity['workloads'] if w['case'] == case)
        path_bounds = path_cache_bounds(queries, w)
        for c in contracts:
            bound = bounds(queries, w, c)
            estimate = simulate(queries, w, c)
            budget = sw['cpu_reference_budget_cycles_200mhz']
            row = dict(case=case, actual_J=w['J'], resident_contexts=min(c['contexts'], w['J']),
                       heap_capacity_per_context=w['E']+1,
                       context_state_bytes=w['dynamic_bytes_per_context'] * min(c['contexts'], w['J']),
                       contract=c, trace=trace, bounds=bound, **estimate,
                       path_cache_conditional_bounds=path_bounds,
                       cpu_measured_us=sw['cpu_early_us'], reference_200mhz_budget_cycles=budget,
                       strict_max_integer_winning_cycles=math.ceil(budget)-1,
                       lower_bound_excludes_at_reference_frequency=bound['combined_pq_bound_cycles'] >= budget,
                       estimate_reference_budget_ratio=estimate['batch_cycles']/budget,
                       required_frequency_MHz=estimate['batch_cycles']/sw['cpu_early_us'],
                       model_cycle_sensitivity_plus_25pct=math.ceil(estimate['batch_cycles']*1.25),
                       model_cycle_sensitivity_plus_35pct=math.ceil(estimate['batch_cycles']*1.35),
                       engineering_20pct_margin_pass=estimate['batch_cycles'] <= 0.8*budget)
            results.append(row)
            print(case, c['name'], estimate['batch_cycles'], 'PQ bound', bound['combined_pq_bound_cycles'], flush=True)
    payload = dict(evidence='conditional_finite_resource_trace_model_not_RTL',
                   new_implemented_frequency_hz=None, board_measured=False,
                   model_script_sha256=sha(Path(__file__)),
                   trace_producer_sha256=sha(root/'accel/lookahead/round5/profile5.cpp'),
                   selftest=selftest(), candidates=results,
                   isolated_pop_rtl_contract=measured_contract,
                   synthesis_schedule_contract=schedule_contract,
                   integrated_mechanism_observer_contract=observer_contract,
                   contract_file_sha256=sha(args.contract) if args.contract else None,
                   memory_and_protocol_contract={
                       'pq': 'One dedicated single-operation owner/RAM per partition; every level uses configured cycles; no layer overlap or hidden extra ports. Request FIFO accepts at configured II; actual starts wait full previous retire.',
                       'edge': 'One shared lane locked to a parent until all its edges launch; finite candidate fullness causes head-of-line blocking across qids. Separate CSR, node and cost read banks, each one read port; synchronous reads included in edge_latency. Edge_ii throttles all three banks. Parent CSR startup included in map latency; no root_ready prefetch.',
                       'candidate': 'Finite per-context credit includes all launched/inflight/ready candidates; FIFO slot retained through label commit.',
                       'labels': 'Per-context RAM owned by label service, one nonoverlapped RMW/context in commit_latency; shared commit issue arbitration, per-context completion ports. Strict original edge order, label commit before next label read, including duplicate dst.',
                       'reset': 'Default shared_commit: round-robin commit owner issues one label reset write per visit, competing with ordered label RMW; per-context search waits for reset. Cell-map initialization adds cells cycles. Optional independent reset is an unverified alternative. Warm initialization included.',
                       'map': 'Single shared map owner; map_latency per POP, including stale/early-stop POPs (trace lacks exact map event flags). Completion precedes candidate side effects.',
                       'output': 'One shared output RAM/writer, configured cells/cycle, complete map write then drain per qid.',
                       'capacity': 'Logical size increments at accepted PUSH, decrements at accepted POP, includes pending operations once. Service queue full only backpressures; logical capacity overflow raises immediately. E+1 per context.',
                       'parent_barrier': 'All original edges committed in order and every required PUSH retired before expanded barrier and next POP.',
                       'generation': 'One immutable graph/cost generation per replay; recycled context only after own FIFO/pending/output drain. Cross-call reload protocol not simulated.'},
                   limits=[
                       'Default service latencies/ports are conditional assumptions. The separately named scheduled_services_rtl_pop_mixed_contract reads edge II9/iteration10 and commit II4/iteration7 from synthesis reports plus the 45-transaction isolated POP RTL formula; PUSH retains old assumptions.',
                       'Pipeline depth10 is provisionally used as candidate feedback, not a measured full edge-service latency. Commit II4 gives two-context revisit8; reset shares that owner and writes at most one node every four cycles. No integrated native E1 contract is available.',
                       'observer_d_baseline_pq_envelope_native_extrapolation is a separate baseline-PQ point calibrated to D zero-hold mechanism operations. Its resource bounds are conditional on assigning those envelope latencies, not a hardware lower-bound proof. No complete native batch or deeper heap was measured by that observer.',
                       'Real mechanism prototype has N32/E128/C8/J8 and two dedicated-context PQs. Full native capacity, four-context sharing and this model service timing are not proven by that prototype.',
                       'Shared round-robin reset/label contention is explicit; other lifecycle transitions are not cycle-exact controller replicas. D mechanism FIFO enqueue and PQ start/retire intervals are measured only for its small test; complete native service timing remains unmeasured.',
                       'Single-parent edge lane HOL and depth4 PQ response FIFOs are modeled. Default contracts consume responses immediately; D observer envelope adds measured maximum retire-to-feedback9 and reaccept1. Parent/end-token and MAP turnaround, and native ACK arbitration under new loads remain extrapolated.',
                       'Old trace establishes parent boundaries, original edge ordinals/dst, accepted PUSHs and heap levels. Bounded path-cache profile supplies validated per-POP DOWN/UP split. Both omit parent identity on zero-edge POPs, exact MAP/expanded branches and speculative suffix activity.',
                       'Trace accepted/rejected decisions are fixed STRICT workload replay, not an executable proof of FP32, error/cancellation semantics or new algorithm behavior. No speculative suffix is modeled.',
                       'Repeated dst reads are serialized behind prior commit; model checks ordering/capacity/drain, not numerical label data.',
                       'Physical bank/address conflicts are excluded by dedicated banks and nonoverlapping RMW/PQ service, not assumed hazard-free layered pipelining. Wider concurrent PQ model is deliberately unsupported.',
                       'Cold graph loading and cost-version invalidation excluded and not estimated; full warm reset/output/drain included. Map-slot cost is conservative but unmodeled control can increase timing.',
                       'The +25% and +35% cycle sensitivities are not confidence intervals. Historical worst error used actual as denominator: a 25.6% underprediction needs 1/(1-0.256)=1.344086 times the prediction to recover actual. +35% illustrates that scale; +25% alone is insufficient compensation and neither guarantees future conservatism.',
                       '200MHz is only a reference budget; required frequency is a threshold, not achieved frequency; no FPGA microseconds or E2/board claim.'])
    dump(r/'model/parent_edge_service_model.json', payload)
    dump(r/'model/assumptions.json', dict(memory_and_protocol_contract=payload['memory_and_protocol_contract'], limits=payload['limits']))


if __name__ == '__main__':
    main()
