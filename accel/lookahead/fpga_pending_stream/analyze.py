"""Bind native trace identities, causal partial comparisons and exact no-go bound."""
from pathlib import Path
from decimal import Decimal
import collections,hashlib,json,math,struct
ROOT=Path(__file__).resolve().parents[3];R=ROOT/'results/fpga_pending_stream_20261114'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inspect(path):
 data=path.read_bytes();h=struct.unpack_from('<8Q',data);assert h[0]==0x5053545241434531
 off=64;words=collections.Counter();pops_by_bank=[0]*64
 for i in range(h[4]):
  n,arg,pv,valid,target,parent,label=struct.unpack_from('<6IQ',data,off);off+=32;words[n//4]+=1;pops_by_bank[(n//4&31)*2+((n//4>>5)&1)]+=1
 banks=[0]*64;sets=collections.Counter();reads=0;edges=0;degree=collections.Counter()
 for i in range(h[5]):
  n,count,label=struct.unpack_from('<IIQ',data,off);off+=16;degree[count]+=1;reads+=(count+7)//8;edges+=count
  for j in range(count):
   node,pair=struct.unpack_from('<IQ',data,off);off+=12;line=node//4;b=(line&31)*2+((line>>5)&1);banks[b]+=1;sets[b,(line>>6)&1023]+=1
 assert edges==h[6] and len(data)==off+h[7]*84
 return {'trace':str(path.relative_to(ROOT)),'sha256':sha(path),'sample':h[1],'wave':h[2],'bucket':h[3],'pops':h[4],'parents':h[5],'candidates':h[6],'unique_final_lines':h[7],'edge_reads_unaligned_packed_model':reads,'same_word_multiple_pop_words':sum(v>1 for v in words.values()),'same_word_extra_pops':sum(v-1 for v in words.values()),'max_pop_word_multiplicity':max(words.values(),default=0),'pops_by_bank':pops_by_bank,'candidates_by_bank':banks,'hottest_sets':[{'bank':k[0],'set':k[1],'candidates':v} for k,v in sets.most_common(8)],'degree_histogram':dict(sorted(degree.items()))}
def main():
 out=R/'analysis_a';out.mkdir(exist_ok=False)
 terminal=json.loads((R/'screen_a/terminal.json').read_text());assert terminal['all_pass'] and len(terminal['results'])==94
 traces=[];comparison=[]
 for case in ['bnn_export','lstm_s2']:
  for p in sorted((R/'capture_a'/case).glob('wave_*.bin')):
   traces.append({'case':case,**inspect(p)})
   row={'case':case,'trace':p.name,'scope':'matched relaxed POP/frontend screen only; no full-batch extrapolation','variants':{}}
   for k,s in [(1,0),(8,0),(8,1),(16,0),(16,1)]:
    q=R/'screen_a'/case/f'{p.stem}_k{k}_s{s}_j0_b0.json';x=json.loads(q.read_text());assert x['output_exact']
    assert x['edge_reads']==traces[-1]['edge_reads_unaligned_packed_model']
    assert all(z['credit_peak']<=32 and z['request_fifo_peak']<=64 and z['issued']==z['returned'] for z in x['ports'])
    assert all(z['context_peak']<=k and z['accepted']==z['retired'] for z in x['banks'])
    assert x['frontend_context_peak']<=64 and x['parent_fifo_peak']<=(64 if s else 524288)
    # Occupancy bound must hold on every native replay.
    assert x['cycles']*64>=16*x['edge_reads']+x['candidates']
    row['variants'][f'k{k}_stream{s}']={'cycles':x['cycles'],'pop_end':x['pop_end'],'frontend_start':x['frontend_start'],'frontend_end':x['frontend_end'],'wave_tail_after_pop':max(0,x['cycles']-x['pop_end']),'parent_fifo_peak':x['parent_fifo_peak'],'context_peak':max(z['context_peak'] for z in x['banks']),'credit_peak':max(z['credit_peak'] for z in x['ports']),'frontend_wait_fraction_of_context_work':x['frontend_wait_context_cycles']/max(1,x['frontend_wait_context_cycles']+x['frontend_emit_context_cycles']),'raw':str(q.relative_to(ROOT))}
   comparison.append(row)
 budget=json.loads((R/'stage_a_v2/budget.json').read_text());proof={}
 for case,b in budget.items():
  n=b['candidates'];target=Decimal(b['target_seconds']);f=Decimal(200000000);minreq=(n+7)//8;lb=Decimal(minreq)*16/64
  assert lb>target*f
  proof[case]={'native_full_batch_candidates':n,'minimum_edge_requests32B':minreq,'max_edge_reads_in_flight':64,'minimum_response_latency_cycles':16,'wait_only_lower_bound_cycles':str(lb),'conditional_lower_bound_seconds':str(lb/f),'GPU_target_seconds':str(target),'target_cycles':str(target*f),'lower_bound_over_target':str(lb/(target*f)),'minimum_edge_inflight_for_wait_only_budget':math.ceil(Decimal(minreq)*16/(target*f)),'proof':'Every edge request occupies one of at most 64 frontend contexts for >=16 cycles. Each request supplies <=8 candidates. Integrating outstanding requests over time gives 64*C >= 16*ceil(N_candidate/8). This ignores init, row/metadata, candidate emission, finalization, conflicts, scratch, directory, outputs and fences. All omitted work is nonnegative. Pending concurrency cannot increase frontend outstanding edge-read capacity.','one_local_relaxation':'Even granting perfect overlap of candidate emission with edge waits (double-buffer the returned beat but retain <=1 edge read in flight/context), the wait-only bound still fails. This is an arithmetic relaxation, not an implemented RTL correction.','scope_limit':'Assumes current no-edge-reuse frontend with 64 contexts and <=1 outstanding edge read/context. More edge-read slots or actual edge reuse invalidates this bound and requires a new implementation/configuration.','fpga_seconds':None,'board_measured':False}
 result={'decision':'NO_GO_initial_64_context_single_edge_read_frontend','stage_A':'complete','stage_B':'decisive necessary-bound rejection with matched relaxed native wave screens','stage_C':'not entered: necessary bound already misses target; no new RTL/OOC qualification claimed','stage_D':'not entered; native40 functional trace extraction is not a complete new finite model','stage_E':'not entered','validation_runs':94,'complete_native_capture_output_exact':True,'proof':proof,'comparison':comparison,'coverage_limits':['New pending service screen implements POP only, not concurrent full-line COMMIT/SEED or write ACK paths. Old serial RTL/reference are unchanged.','No new synthesizable top, shared RTL arbiter, scratch parallelism, RTL/model calibration, timing or full-resource qualification.','Candidate reduction uses off-chip verification maps with no latency; it is explicitly a relaxation, never hardware capacity. Spill counts are not reused or claimed for the changed schedule.','Same-word POP, finite pending contexts, parent FIFO backpressure, finite tags/credits and deterministic out-of-order read returns are exercised. No claims for new write-ACK/event/FIFO/reset/wrap RTL coverage.','Old complete B cycles remain independently referenced; do not compare their scope directly with partial screen cycles.']}
 for name,value in [('decision.json',result),('trace_selection_verified.json',traces)]:
  with (out/name).open('x') as f2:json.dump(value,f2,indent=2);f2.write('\n')
 print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
