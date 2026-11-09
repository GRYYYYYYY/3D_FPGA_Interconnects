#!/usr/bin/env python3
"""Read-only exact-FP32 eligible-CSR functional audit. No timing claims."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

MISSING = struct.pack('<II', 0x7FC00000, 0x7FC00000)


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def numeric(value):
    bits = struct.unpack('<I', struct.pack('<f', value))[0]
    return bits == 0 or (bits >> 31 == 0 and (bits & 0x7F800000) not in (0, 0x7F800000))


def strict_push(heap, value):
    hole = len(heap)
    heap.append(value)
    while hole:
        parent = (hole - 1) // 2
        if not heap[parent][1] > value[1]:
            break
        heap[hole] = heap[parent]
        hole = parent
    heap[hole] = value


def strict_pop(heap):
    result = heap[0]
    value = heap.pop()
    count = len(heap)
    if not count:
        return result
    hole, child = 0, 2
    while child < count:
        if heap[child][1] > heap[child - 1][1]:
            child -= 1
        heap[hole] = heap[child]
        hole = child
        child = 2 * (hole + 1)
    if child == count:
        heap[hole] = heap[child - 1]
        hole = child - 1
    while hole:
        parent = (hole - 1) // 2
        if not heap[parent][1] > value[1]:
            break
        heap[hole] = heap[parent]
        hole = parent
    heap[hole] = value
    return result


class Workload:
    def __init__(self, path):
        self.path = path
        data = path.read_bytes()
        self.sha256 = hashlib.sha256(data).hexdigest()
        magic, self.n, self.e, self.j, self.k, self.c, self.g = struct.unpack_from('<7Q', data)
        assert magic == 0x31414C5443495254
        offset = 56
        self.row = struct.unpack_from('<' + 'Q' * (self.n + 1), data, offset)
        offset += 8 * (self.n + 1)
        self.nodes = list(struct.iter_unpack('<IIIi', data[offset:offset + 16 * self.n]))
        offset += 16 * self.n
        self.edges = list(struct.iter_unpack('<II', data[offset:offset + 8 * self.e]))
        offset += 8 * self.e
        self.costs = list(struct.iter_unpack('<ff', data[offset:offset + 8 * self.k]))
        offset += 8 * self.k
        self.jobs = list(struct.iter_unpack('<6I', data[offset:offset + 24 * self.j]))
        offset += 24 * self.j
        self.mapping_bytes = data[offset:offset + 4 * self.j * self.n]
        self.cells = struct.unpack('<' + 'i' * (self.j * self.n), self.mapping_bytes)
        offset += 4 * self.j * self.n
        self.golden = [data[offset + q * self.c * 8:offset + (q + 1) * self.c * 8] for q in range(self.j)]
        offset += 8 * self.j * self.c
        assert offset == len(data)
        assert all(numeric(x) for pair in self.costs for x in pair)
        assert self.row[-1] == self.e

    def targets(self, q):
        result = {self.cells[q * self.n + u] for u in range(self.n)
                  if self.nodes[u][0] == 1 and self.cells[q * self.n + u] >= 0}
        assert all(x < self.c for x in result)
        return result

    def run(self, q, early_stop):
        targets = self.targets(q)
        output = [None] * self.c
        visited = [-1.0] * self.n
        expanded = [False] * self.n
        heap, seen = [], set()
        counts = dict(pushes=0, pops=0, edge_visits=0, expanded=0, peak=0)
        stop_reason = 'heap_exhausted'
        last_pop_delay = -1.0
        if early_stop and not targets:
            stop_reason = 'empty_input_target_set'
        else:
            strict_push(heap, (self.jobs[q][0], 0.0, 0.0))
            counts['pushes'] = counts['peak'] = 1
            while heap:
                u, delay, congestion = strict_pop(heap)
                assert delay >= last_pop_delay
                last_pop_delay = delay
                counts['pops'] += 1
                if expanded[u]:
                    continue
                parent = self.nodes[u]
                cell = self.cells[q * self.n + u]
                if parent[0] == 1 and cell >= 0:
                    if output[cell] is None or delay < output[cell][0]:
                        output[cell] = (delay, congestion)
                    seen.add(cell)
                    if early_stop and len(seen) == len(targets):
                        stop_reason = 'all_input_targets_covered_before_parent_expansion'
                        break
                for i in range(self.row[u], self.row[u + 1]):
                    counts['edge_visits'] += 1
                    v = self.edges[i][0]
                    child = self.nodes[v]
                    if not child[2] or (parent[3] >= 0 and child[3] >= 0 and parent[3] != child[3]):
                        continue
                    if child[0] == 2:
                        break
                    if expanded[v]:
                        continue
                    cost_delay, cost_congestion = self.costs[child[1]]
                    next_delay = f32(delay + cost_delay)
                    next_congestion = f32(congestion + cost_congestion)
                    assert numeric(next_delay) and numeric(next_congestion)
                    if visited[v] >= 0 and visited[v] < next_delay:
                        continue
                    visited[v] = next_delay
                    strict_push(heap, (v, next_delay, next_congestion))
                    counts['pushes'] += 1
                    counts['peak'] = max(counts['peak'], len(heap))
                expanded[u] = True
                counts['expanded'] += 1
        encoded = b''.join(MISSING if item is None else struct.pack('<ff', *item) for item in output)
        return dict(**counts, target_count=len(targets), recorded_target_count=len(seen),
                    stop_reason=stop_reason, remaining_heap_entries=len(heap),
                    output_sha256=hashlib.sha256(encoded).hexdigest(),
                    matches_golden_all_bytes=(encoded == self.golden[q]))



def eligibility(parent,child):
    if not child[2] or (parent[3]>=0 and child[3]>=0 and parent[3]!=child[3]): return 0
    return -1 if child[0]==2 else 1


def compact_rows(w):
    rows=[]
    counts=dict(original_edges=w.e,kept_edges=0,removed_ineligible_before_sink=0,eligible_sink_edges=0,ignored_after_eligible_sink=0)
    for u in range(w.n):
        row=[]
        for i in range(w.row[u],w.row[u+1]):
            v=w.edges[i][0]; status=eligibility(w.nodes[u],w.nodes[v])
            if status==0:
                counts['removed_ineligible_before_sink']+=1;continue
            if status<0:
                counts['eligible_sink_edges']+=1
                counts['ignored_after_eligible_sink']+=w.row[u+1]-i-1
                break
            row.append(v);counts['kept_edges']+=1
        rows.append(row)
    assert sum(counts[k] for k in counts if k!='original_edges')==w.e
    counts['kept_fraction']=counts['kept_edges']/w.e
    return rows,counts


def replay(w,q,early,compact=None):
    targets=w.targets(q); output=[None]*w.c;visited=[-1.0]*w.n;expanded=[False]*w.n
    heap=[];seen=set();trace=hashlib.sha256()
    c=dict(pushes=0,pops=0,expanded=0,peak=0,edge_loop_iterations=0,static_eligible_candidates=0,after_expanded_filter=0,pushes_from_edges=0)
    def push(value):
        strict_push(heap,value);trace.update(struct.pack('<cIff',b'I',*value));c['pushes']+=1;c['peak']=max(c['peak'],len(heap))
    if not(early and not targets):
        push((w.jobs[q][0],0.,0.))
        while heap:
            cur=strict_pop(heap);trace.update(struct.pack('<cIff',b'P',*cur));c['pops']+=1
            u,delay,congestion=cur
            if expanded[u]: continue
            cell=w.cells[q*w.n+u]
            if w.nodes[u][0]==1 and cell>=0:
                if output[cell] is None or delay<output[cell][0]: output[cell]=(delay,congestion)
                seen.add(cell)
                if early and len(seen)==len(targets): break
            candidates=compact[u] if compact is not None else (w.edges[i][0] for i in range(w.row[u],w.row[u+1]))
            for v in candidates:
                c['edge_loop_iterations']+=1
                if compact is None:
                    s=eligibility(w.nodes[u],w.nodes[v])
                    if s==0:continue
                    if s<0:break
                c['static_eligible_candidates']+=1
                if expanded[v]:continue
                c['after_expanded_filter']+=1
                dc,cc=w.costs[w.nodes[v][1]];nd=f32(delay+dc);nc=f32(congestion+cc)
                assert numeric(nd) and numeric(nc)
                if visited[v]>=0 and visited[v]<nd:continue
                visited[v]=nd;push((v,nd,nc));c['pushes_from_edges']+=1
            expanded[u]=True;c['expanded']+=1
    encoded=b''.join(MISSING if x is None else struct.pack('<ff',*x) for x in output)
    return dict(counts=c,output_sha256=hashlib.sha256(encoded).hexdigest(),golden_match=encoded==w.golden[q],
        heap_event_sha256=trace.hexdigest(),final_heap_sha256=hashlib.sha256(b''.join(struct.pack('<Iff',*x) for x in heap)).hexdigest(),
        visited_sha256=hashlib.sha256(b''.join(struct.pack('<f',x) for x in visited)).hexdigest(),
        expanded_sha256=hashlib.sha256(bytes(expanded)).hexdigest(),remaining_heap=len(heap))


def audit_one(path):
    w=Workload(path);rows,static=compact_rows(w);result=[]
    for mode,early in [('full',False),('early',True)]:
        jobs=[]
        for q in range(w.j):
            original=replay(w,q,early);compressed=replay(w,q,early,rows);reference=w.run(q,early)
            assert original['golden_match'] and compressed['golden_match'] and reference['matches_golden_all_bytes']
            for key in ['output_sha256','heap_event_sha256','final_heap_sha256','visited_sha256','expanded_sha256','remaining_heap']:
                assert original[key]==compressed[key],(q,mode,key)
            for key in ['pushes','pops','expanded','peak']:
                assert original['counts'][key]==compressed['counts'][key]==reference[key]
            assert original['counts']['edge_loop_iterations']==reference['edge_visits']
            for key in ['static_eligible_candidates','after_expanded_filter','pushes_from_edges']:
                assert original['counts'][key]==compressed['counts'][key]
            assert compressed['counts']['edge_loop_iterations']==original['counts']['static_eligible_candidates']
            jobs.append(dict(qid=q,original=original,compressed=compressed))
        totals={k:sum(j['original']['counts'][k] for j in jobs) for k in jobs[0]['original']['counts'] if k!='peak'}
        totals['max_per_sample_heap_peak']=max(j['original']['counts']['peak'] for j in jobs)
        totals['sum_per_sample_heap_peaks']=sum(j['original']['counts']['peak'] for j in jobs)
        totals['compressed_edge_loop_iterations']=sum(j['compressed']['counts']['edge_loop_iterations'] for j in jobs)
        totals['edge_loop_reduction_fraction']=1-totals['compressed_edge_loop_iterations']/totals['edge_loop_iterations']
        result.append(dict(mode=mode,totals=totals,jobs=jobs))
    return dict(workload=str(path),workload_sha256=w.sha256,dimensions=dict(N=w.n,E=w.e,J=w.j,C=w.c),static=static,
        all_maps_match_golden=True,all_heap_event_sequences_and_final_state_identical=True,modes=result)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r3=a.root/'results/lookahead_accel_round3_20261108T141500Z/evidence_snapshot'
    r4=a.root/'results/lookahead_accel_round4_20261108T182500Z/evidence_snapshot'
    paths=[r3/'native_d3_w8/workload.bin',r3/'native_d4_w8/workload.bin',r4/'native_d5_w8/workload.bin']
    items=[audit_one(x) for x in paths]
    report=dict(source_commit='fa07aef',evidence_type='read_only_python_functional_operation_audit_not_timing',
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),workloads=items,
        notes=['Static input-only CSR transformation preserves original retained edge order and truncates only at the first eligible SINK.',
        'No algorithmic candidates, heap entries, or equivalent-delay choices are dropped.',
        'Edge statistics change; maps, complete push/pop event sequence, final heap, visited and expanded states are checked identical.',
        'CSR preparation/upload costs must be reported; the same representation optimization must be offered to CPU/GPU.',
        'Fewer edge-loop iterations do not directly predict hardware cycle gains; heap work is unchanged.'])
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    for x in items:
        print(Path(x['workload']).parent.name,'static',x['static'])
        for mode in x['modes']:print(mode['mode'],mode['totals'])
if __name__=='__main__':main()
