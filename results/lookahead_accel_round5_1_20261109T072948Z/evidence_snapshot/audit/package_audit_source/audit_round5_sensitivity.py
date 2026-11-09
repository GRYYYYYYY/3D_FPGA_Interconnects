#!/usr/bin/env python3
"""Conditional round-five trace sensitivity; no new FPGA performance claims."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

REL = Path('results/lookahead_accel_round5_20261109T054024Z/evidence_snapshot')
POINTS = [(3,7,3),(2,7,3),(3,3,3),(2,3,3),(1,1,1)]


def latency(op, work, hp, edge, discard):
    return hp*work+5 if op == 'P' else hp*work+2 if op == 'U' else edge if work else discard


def simulate(streams, n, cells, contexts, parts, hp, edge, discard, pq_ii):
    # Original model operation order and static qid-to-partition assignment.
    # pq_ii=None keeps a partition occupied for the complete feedback latency.
    # pq_ii=1/2 assumes a real multi-operation pipeline, NOT implemented R5 RTL.
    ready=[0]*min(contexts,len(streams));owners=list(range(len(ready)));idx=[0]*len(ready)
    next_q=len(ready);pq_free=[0]*parts;edge_free=0;finish=[]
    while owners:
        s=min(range(len(owners)),key=lambda k:ready[k]);q=owners[s];t=ready[s]
        if idx[s]==0:t+=n+cells
        if idx[s]>=len(streams[q]):
            finish.append(t+cells+8)
            if next_q<len(streams):owners[s]=next_q;next_q+=1;idx[s]=0;ready[s]=t+cells+8
            else:owners.pop(s);idx.pop(s);ready.pop(s)
            continue
        op,work=streams[q][idx[s]];idx[s]+=1;lat=latency(op,work,hp,edge,discard)
        if op in ('P','U'):
            part=q%parts;start=max(t,pq_free[part]);pq_free[part]=start+(lat if pq_ii is None else pq_ii)
        else:start=max(t,edge_free);edge_free=start+1
        ready[s]=start+lat
    return max(finish,default=0)


def main(root):
    r=root/REL;report_bytes=(r/'report_final.json').read_bytes();report=json.loads(report_bytes)
    hw2=next(h for h in report['hardware'] if h['contexts']==2)
    hw4=next(h for h in report['hardware'] if h['contexts']==4)
    manifest={w['case']:w for w in json.loads((r/'workload_manifest.json').read_text())}
    result=[]
    for c in hw2['calls']:
        case=c['case'];w=manifest[case];path=r/'profiles'/(case+'.csv')
        streams=[[] for _ in range(w['J'])]
        with path.open() as f:
            for early,q,op,work,seq in csv.reader(f):
                if early=='1':streams[int(q)].append((op,int(work)))
        original_best=min((x for x in report['model']['candidates'] if x['case']==case),key=lambda x:x['batch_cycles'])
        replay=simulate(streams,w['N'],w['cells'],original_best['contexts'],original_best['pq_partitions'],3,7,3,None)
        # Compare only one-lane original minima directly; multi-lane may differ by a few cycles.
        baseline_one_lane=min((x for x in report['model']['candidates'] if x['case']==case and x['edge_lanes']==1),key=lambda x:x['batch_cycles'])
        assert simulate(streams,w['N'],w['cells'],baseline_one_lane['contexts'],baseline_one_lane['pq_partitions'],3,7,3,None)==baseline_one_lane['batch_cycles']
        points=[]
        for hp,edge,discard in POINTS:
            chains=[];pq_tot=[0]*w['J']
            for q,events in enumerate(streams):
                chains.append(w['N']+2*w['cells']+8+sum(latency(op,k,hp,edge,discard) for op,k in events))
                pq_tot[q]=sum(latency(op,k,hp,edge,discard) for op,k in events if op in ('P','U'))
            estimates=[]
            for parts in [1,2,4]:
                occupancy=max(sum(v for q,v in enumerate(pq_tot) if q%parts==p) for p in range(parts))
                for pq_ii in [None,1,2]:
                    cyc=simulate(streams,w['N'],w['cells'],w['J'],parts,hp,edge,discard,pq_ii)
                    estimates.append({'actual_context_limit':w['J'],'pq_partitions':parts,
                        'pq_service': 'nonpreemptive_feedback_occupancy' if pq_ii is None else 'hypothetical_operation_II'+str(pq_ii),
                        'batch_cycles_estimated':cyc,'over_cpu_200mhz_cycle_budget':cyc/(c['cpu_early_measured_s']*200e6),
                        'static_partition_occupancy_bound_if_nonpreemptive':occupancy})
            points.append({'heap_cycles_per_measured_level':hp,'eligible_edge_feedback':edge,'discard_edge_feedback':discard,
                'per_qid_feedback_chain_with_reset_output':chains,'critical_qid':max(range(len(chains)),key=lambda q:chains[q]),
                'critical_feedback_chain_cycles':max(chains),'total_nonpreemptive_pq_occupancy_cycles':sum(pq_tot),
                'per_qid_nonoverlapped_pq_cycles':pq_tot,'critical_nonoverlapped_pq_chain_cycles':max(pq_tot),
                'estimates':estimates})
        phase=[]
        for h in [hw2,hw4]:
            z=next(x for x in h['calls'] if x['case']==case);v=z['phase_visits'];productive=sum(v[:-1])
            row={'contexts':h['contexts'],'phase_visits':sum(v),'dead_visits':v[-1],'non_dead_visits':productive,
                'optimistic_search_cycles_one_global_dispatcher_II1_no_dead':productive,
                'no_dead_global_II1_over_cpu_200mhz_budget':productive/(c['cpu_early_measured_s']*200e6)}
            if z['rtl_cycles'] is not None:
                no_dead=z['rtl_cycles']-z['dispatch_observed_gap_mean']*v[-1]
                row.update({'observed_rtl_cycles':z['rtl_cycles'],'conditional_no_dead_same_II_residual_cycles':no_dead,
                    'ready_only_speedup_ceiling_same_II_and_residual':z['rtl_cycles']/no_dead})
            phase.append(row)
        result.append({'case':case,'N':w['N'],'E':w['E'],'J':w['J'],'cpu_early_us':c['cpu_early_measured_s']*1e6,
            'cpu_reference_budget_cycles_125mhz':c['cpu_early_measured_s']*125e6,
            'cpu_reference_budget_cycles_200mhz':c['cpu_early_measured_s']*200e6,
            'trace_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'best_original_report_model':original_best,'original_one_lane_model_reproduced':True,
            'global_dispatch_conditions':phase,'sensitivity':points})
    return {'source_commit':'52b5622687867756e9109b94c99685712ad0e21f',
        'report_sha256':hashlib.sha256(report_bytes).hexdigest(),'evidence':'conditional_model_estimates_and_arithmetic',
        'new_hardware_implemented':False,'new_verified_frequency':None,'board_measured':False,
        'limits':[
            'Trace replay preserves per-qid operation order, one operation in flight per qid and actual J.',
            'One edge pipe is assumed to accept at II1; graph/label/output port constraints beyond the old model remain unmodeled.',
            'PQ initiation interval1/2 cases require genuinely pipelined PQ hardware and sufficient banks/hazard handling, absent from current RTL.',
            'Heap per-level1 and edge feedback1 are optimistic limits; no synthesis or timing feasibility is established.',
            'Reset/output for different contexts may overlap as in the old model; actual shared resources may increase cycles.',
            'Per-qid chain and occupancy bounds only apply to the given feedback assumptions, not all exact-search architectures.',
            '200MHz is only a reference budget, not a new achieved frequency.',
            'No native E2, board timing, or new software measurements are generated.'
        ],'workloads':result}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    d=main(a.root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n')
    for w in d['workloads']:
        print(w['case'],'J',w['J'],'CPU200budget',w['cpu_reference_budget_cycles_200mhz'])
        for s in w['sensitivity']:
            best=min(s['estimates'],key=lambda e:e['batch_cycles_estimated'])
            b2=next(e for e in s['estimates'] if e['pq_partitions']==2 and e['pq_service']=='nonpreemptive_feedback_occupancy')
            i2=next(e for e in s['estimates'] if e['pq_partitions']==2 and e['pq_service']=='hypothetical_operation_II1')
            print(' level/edge=',s['heap_cycles_per_measured_level'],s['eligible_edge_feedback'],
                  'chain=',s['critical_feedback_chain_cycles'],'2PQblocking=',b2['batch_cycles_estimated'],
                  '2PQII1=',i2['batch_cycles_estimated'],'best=',best['batch_cycles_estimated'])
