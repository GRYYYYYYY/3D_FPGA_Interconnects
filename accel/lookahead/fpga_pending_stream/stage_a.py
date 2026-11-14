"""Append-only source/evidence binding and exact conditional screening arithmetic."""
from pathlib import Path
from decimal import Decimal
import csv,gzip,hashlib,json,math,subprocess
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/fpga_pending_stream_20261114'
OLD=ROOT.parent/'3D_FPGA_Interconnects_SPARSE_STREAM_R2'
R=OLD/'results/fpga_sparse_stream_r2_20261112'
E=R/'evidence_snapshot/inf_followup_combination2317/accumulator/inf_finite_native_b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def main():
 out=OUT/'stage_a_v2';out.mkdir(exist_ok=False)
 source=ROOT/'accel/lookahead/fpga_sparse_stream_r2'
 sw=R/'evidence_snapshot/software_private_inf_gpu_b_terminal/software/private_inf_gpu_b'
 binding=json.loads((sw/'binding.json').read_text()); summary=json.loads((sw/'summary.json').read_text())
 assert summary['all_receipts_pass'] and summary['receipt_count']==254
 files={};supp=out/'cuda_source_supplement';supp.mkdir()
 for name in ['cuda_private_inf.cu','cuda_prepared_pop.cu']:
  p=source/name;assert sha(p)==binding['source_sha256'][name]
  (supp/name).write_bytes(p.read_bytes());files[name]={'sha256':sha(p),'frozen_binding':str(sw/'binding.json')}
 write(supp/'manifest.json',{'append_only':True,'old_snapshot_modified':False,'GPU_rerun':False,'files':files})
 rows={}; selection={}
 for case,target,qs in [('bnn_export','0.151799969444',(41026160,220725437,413585276,179797431)),('lstm_s2','0.15949799988888888',(41667320,224677406,419417421,183220655))]:
  d=E/case;m=json.loads((d/'finite_service.json').read_text());s=json.loads((d/'summary.json').read_text());qi,qp,qe,qf=map(Decimal,qs);n=Decimal(m['candidates']);f=Decimal(200000000);target=Decimal(target)
  sep=(qi+qp+qf)/32+max(qe/32,n/64);stream=(qi+qf)/32+max((qp+qe)/32,n/64)
  # Each of 64 contexts waits for its edge read, then emits at most eight candidates.
  # ceil(N/8) is schedule-independent even if grouping/replacement changes.
  edge_requests_min=(int(n)+7)//8
  rows[case]={'target_seconds':str(target),'budget_cycles':str(target*f),'old_B_cycles':m['cycles'],'candidates':int(n),'parents':s['active'],'ideal_separated_cycles':str(sep),'ideal_stream_cycles':str(stream),'ideal_stream_ms':str(stream/f*1000),'headroom_ms':str((target-stream/f)*1000),'headroom_percent':str((target-stream/f)/target*100),'assumed_frequency_hz':int(f),'latency_cycles':16,'gap_cycles':1,'frontend_wait_only_lower_bound_cycles':str(Decimal(edge_requests_min)*16/64),'frontend_wait_emit_lower_bound_cycles':str((Decimal(edge_requests_min)*16+n)/64),'old_B_sources':{str(d/x):sha(d/x) for x in ['finite_service.json','summary.json','waves.csv.gz','finite_service_cycles.csv.gz']},'fpga_seconds':None,'board_measured':False}
  with gzip.open(d/'waves.csv.gz','rt') as fp:waves=list(csv.DictReader(fp))
  with gzip.open(d/'finite_service_cycles.csv.gz','rt') as fp:cycles=list(csv.DictReader(fp))
  prof=R/'accumulator/profile_a'/case/'wave_lines.jsonl'
  profiles=[json.loads(x) for x in prof.read_text().splitlines()]
  chosen={}
  def take(row,reason):chosen.setdefault((int(row['sample']),int(row['wave'])),[]).append(reason)
  take(max(waves,key=lambda x:int(x['active'])),'largest native frontier')
  take(max(cycles,key=lambda x:int(x['spill_fragments'])),'largest old B spill count; candidate schedule must recount')
  take(max(profiles,key=lambda x:max(x['candidates_by_owner_subbank'])/max(1,x['candidates']) if x['candidates']>=10000 else -1),'largest bank skew among >=10000-candidate native waves')
  take(max(profiles,key=lambda x:x['owner_window8_merge_opportunities']),'largest native near-line reuse count; exact same-set/word counts collected in new trace')
  selection[case]={'profile_path':str(prof),'profile_sha256':sha(prof),'waves':[{'sample':q,'wave':w,'reasons':why} for (q,w),why in sorted(chosen.items())]}
 write(out/'budget.json',rows);write(out/'representative_selection.json',selection)
 write(out/'binding.json',{'hardware_base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'software_base':'a64c934956be6514a27f66fd1a46f09ef4a2fab9','GPU_archive':'cc71869709bcf3124ae81ebfdcd8f36819c4c90d','scope':'RESIDENT_COMPLETE_BATCH_V2','input_receipts':json.loads((R/'semantics/native_complete.json').read_text()),'software_summary_sha256':sha(sw/'summary.json'),'software_binding_sha256':sha(sw/'binding.json'),'config':{'pending_contexts_per_subbank':[8,16],'frontend_contexts_total':64,'ports':32,'credits_per_port':32,'parent_fifo':64,'scratch_commands_per_subbank':1,'latency_ns':80,'issue_gap_ns':5,'assumed_frequency_hz':200000000,'MAX_N':4194304,'spill_ids_per_subbank':2048},'complete_kernel_clock_qualified':False,'fpga_seconds':None,'board_measured':False})
 print(json.dumps({'budget':rows,'selection':selection},indent=2))
if __name__=='__main__':main()
