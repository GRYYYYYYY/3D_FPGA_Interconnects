"""Independent complete-model receipt, source, capacity and timing-boundary audit."""
from run import *
from decimal import Decimal
import csv

def main():
 d=json.loads((OUT/'binding.json').read_text());assert sha(OUT/'bin/model')==d['binary_sha256']
 for path,want in d['source_sha256'].items():assert sha(OUT/'source'/path)==want,path
 small=json.loads((OUT/'small_terminal.json').read_text());full=json.loads((OUT/'full_terminal.json').read_text());assert small['all_pass'] and full['all_pass'] and small['sample_runs']==40 and full['sample_runs']==80
 result={'all_pass':True,'small_runs':40,'full_runs':80,'binary_sha256':d['binary_sha256'],'source_binding_sha256':sha(OUT/'binding.json'),'cases':{},'fifo_telemetry_note':'fifo_peaks[2] is configured four enum stages, NOT measured occupied-stage peak; [0,1,3,4,5] are measured reservation/FIFO peaks','calibration_complete':False,'complete_kernel_clock_qualified':False,'fpga_seconds':None,'board_measured':False}
 for case,inp in d['inputs'].items():
  assert sha(inp['workload'])==inp['workload_sha256'] and sha(inp['golden'])==inp['golden_sha256']
  summary=json.loads((OUT/(case+'_summary.json')).read_text());assert summary['all_pass'] and summary['functional_work_counts_match_frozen_profile'];receipts=summary['samples'];assert [x['sample'] for x in receipts]==list(range(inp['jobs']))
  total_cycles=0;phase={'sample_init':0,'POP_expand':0,'finalize_including_bitmap_clear':0,'output_export':0,'other_seed_bucket_drain':0};stats={};traffic=[[0]*32 for _ in range(11)];bank_set_stalls=bank_word_stalls=0;fifo_peaks=[0]*6;tx_peak=dir_peak=spill_peak=credit_peak=queue_peak=return_peak=0;allout=[]
  for x in receipts:
   assert x['returncode']==0 and x['output_exact'];assert x['binary_sha256']==d['binary_sha256'];assert sha(x['output_path'])==x['output_sha256'];allout.append(Path(x['output_path']).read_bytes());q=json.loads(Path(x['finite_path']).read_text());total_cycles+=q['cycles'];assert q['output_ACKs']==(inp['cells']+3)//4;assert q['output_sample_stride_lines']==(((inp['cells']+3)//4+31)//32)*32;assert q['output_base_line']+q['output_ACKs']<=q['cost_base_line'];assert q['export_end']-q['export_start']>=(q['output_ACKs']+1)//2+2;phase['sample_init']+=q['init_end'];wave_rows=list(csv.DictReader((Path(x['finite_path']).parent/'waves.csv').open()));assert len(wave_rows)==q['waves']
   assert [int(w['wave']) for w in wave_rows]==list(range(1,len(wave_rows)+1));assert all(int(w['start'])<=int(w['pop_expand_end'])<=int(w['final_end']) for w in wave_rows)
   assert sum(int(w['parents']) for w in wave_rows)==q['parents'] and sum(int(w['candidates']) for w in wave_rows)==q['candidates'];assert sum(int(w['commits']) for w in wave_rows)==q['canonical_lines'];assert sum(int(w['changed_lines']) for w in wave_rows)==q['changed_lines'];assert sum(int(w['spills']) for w in wave_rows)==q['spills']
   expand=sum(int(w['pop_expand_end'])-int(w['start']) for w in wave_rows);final=sum(int(w['final_end'])-int(w['pop_expand_end']) for w in wave_rows);phase['POP_expand']+=expand;phase['finalize_including_bitmap_clear']+=final;phase['output_export']+=q['export_end']-q['export_start'];phase['other_seed_bucket_drain']+=q['cycles']-q['init_end']-expand-final-(q['export_end']-q['export_start'])
   assert sum(q['lane_emit'])==q['candidates'];assert all(a<=b for a,b in zip(q['fork_H_E_M_slots_peak'],[128,128,256,128,512]));assert len(q['bank_stats'])==64 and len(q['port_stats'])==32
   for bk in q['bank_stats']:
    assert bk['tx_peak']<=8 and bk['spill_id_peak']<=2048;assert bk['commit']==bk['commit_admit'];assert all(a<=b for a,b in zip(bk['fifo_peaks'],[16,16,4,2,16,16]));tx_peak=max(tx_peak,bk['tx_peak']);spill_peak=max(spill_peak,bk['spill_id_peak']);bank_set_stalls+=bk['set_stalls'];bank_word_stalls+=bk['word_stalls'];fifo_peaks=[max(a,b) for a,b in zip(fifo_peaks,bk['fifo_peaks'])]
   for port in q['port_stats']:
    assert port['issued']==port['returned'];assert port['credit_peak']<=32 and port['queue_peak']<=64 and port['return_peak']<=4;credit_peak=max(credit_peak,port['credit_peak']);queue_peak=max(queue_peak,port['queue_peak']);return_peak=max(return_peak,port['return_peak'])
   for k in range(11):
    for p in range(32):traffic[k][p]+=q['traffic'][k][p]
   dir_peak=max(dir_peak,max(q['directory_bank_peaks']));assert dir_peak<=8192
  output=b''.join(allout);assert hashlib.sha256(output).hexdigest()==inp['golden_sha256'];assert total_cycles==summary['cycles'] and sum(phase.values())==total_cycles;assert traffic==summary['traffic']
  target={'bnn_export':'0.151799969444','lstm_s2':'0.15949799988888888'}.get(case)
  semantic=summary['counts'];init_requests=sum(traffic[0]);profile=json.loads((R/'baseline/profile_a'/case/'physical_profile.json').read_text());assert init_requests==sum(profile['requests_by_kind_port'][4]);assert sum(traffic[1])==sum(profile['requests_by_kind_port'][0]);assert sum(traffic[2])==sum(profile['requests_by_kind_port'][1]);assert sum(traffic[3])==semantic['parents'];assert sum(traffic[4])==semantic['pop_transactions'];assert sum(traffic[5])==semantic['canonical_lines']+sum(1 for x in receipts if json.loads(Path(x['finite_path']).read_text())['parents']);assert sum(traffic[6])==semantic['changed_lines']+sum(1 for x in receipts if json.loads(Path(x['finite_path']).read_text())['parents'])
  assert sum(traffic[10])==3*inp['jobs'];final_reads=sum(traffic[7]);repeat_expand_reads=final_reads-semantic['scratch_final_reads'];assert repeat_expand_reads>=0;assert sum(traffic[8])==semantic['spills'];counts={'init_requests':init_requests,'row':sum(traffic[1]),'edge':sum(traffic[2]),'meta':sum(traffic[3]),'pop_read':sum(traffic[4]),'canonical_read_including_seed':sum(traffic[5]),'canonical_write_including_seed':sum(traffic[6]),'scratch_read_all':final_reads,'scratch_expand_repeated_reads':repeat_expand_reads,'scratch_expand_writes':sum(traffic[8]),'scratch_final_reads':semantic['scratch_final_reads'],'output_write':sum(traffic[9]),'cost_load':sum(traffic[10])}
  v={'sequential_cycles':total_cycles,'conditional_seconds':str(Decimal(total_cycles)/200000000),'exclusive_phase_cycles':phase,'semantic_counts':semantic,'new_traffic_counts':counts,'tx_peak':tx_peak,'credit_peak':credit_peak,'physical_queue_peak':queue_peak,'return_peak':return_peak,'directory_peak_per_bank':dir_peak,'spill_id_peak_per_bank':spill_peak,'fifo_max_telemetry':fifo_peaks,'overlapping_set_stall_attempts':bank_set_stalls,'overlapping_word_stall_attempts':bank_word_stalls,'full_output_sha256':inp['golden_sha256']}
  if target:
   v['GPU_target_seconds']=target;v['conditional_model_exceeds_target']=Decimal(total_cycles)>Decimal(target)*200000000;v['if_entire_finalize_were_free_seconds']=str(Decimal(total_cycles-phase['finalize_including_bitmap_clear'])/200000000);v['scratch_concurrency_decision']='No 2/4 followup: POP+expand dominates wall time and no exclusive critical-stall attribution isolates one scratch read. Fresh traffic/reservations are reported; peaks and overlapping attempt counts do not prove decisive wall-time causation.'
  result['cases'][case]=v
 dump(OUT/'independent_verification.json',result);print('COMPLETE_MODEL_AUDIT_PASS',json.dumps({c: {'cycles':x['sequential_cycles'],'phase':x['exclusive_phase_cycles']} for c,x in result['cases'].items()}))
if __name__=='__main__':main()
