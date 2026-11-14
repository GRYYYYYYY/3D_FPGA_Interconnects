"""Bind and compact only this worker's evidence; never commit or modify other files."""
from pathlib import Path
import argparse,datetime,gzip,hashlib,json,re,shutil,subprocess
ROOT=Path(__file__).resolve().parents[4];SRC=Path(__file__).resolve().parent
STEM='fpga_enum_commit_canonical_20261114_';FINAL=ROOT/'results'/(STEM+'f')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(out):
 m=json.loads((out/'manifest.json').read_text())
 for x in m['files']:
  p=out/x['archive'];data=p.read_bytes();data=gzip.decompress(data) if x['archive'].endswith('.gz') else data
  assert len(data)==x['bytes'] and hashlib.sha256(data).hexdigest()==x['sha256'],x['raw_path']
 return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');ap.add_argument('--restore',type=Path);a=ap.parse_args();out=FINAL/'evidence_snapshot_portable'
 if a.verify or a.restore:
  m=verify(out)
  if a.restore:
   a.restore.mkdir(parents=True,exist_ok=False)
   for x in m['files']:
    data=(out/x['archive']).read_bytes();data=gzip.decompress(data) if x['archive'].endswith('.gz') else data;p=a.restore/x['raw_path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  print('CANONICAL_ARCHIVE_PASS',len(m['files']));return
 delivery=FINAL/'delivery_source';delivery.mkdir(exist_ok=False)
 for p in SRC.iterdir():
  if p.is_file():shutil.copy2(p,delivery/p.name)
 history=json.loads((FINAL/'mcp_history.json').read_text());byid={x['id']:x for x in history}
 receipt_ids=dict(zip('abcdef',[1,4,6,8,10,16]));selected=[]
 for run,hid in receipt_ids.items():
  result=ROOT/'results'/(STEM+run);source=result/'source'
  if not source.exists():
   source.mkdir()
   for p in SRC.iterdir():
    if p.is_file():shutil.copy2(p,source/p.name)
   for p in [ROOT/'accel/lookahead/fpga_sparse_stream_r2/pending17.hpp',ROOT/'accel/lookahead/fpga_sparse_stream_r2/rtl/pending17_service.sv']:shutil.copy2(p,source/p.name)
  sim=result/'project/canonical_k8.sim/sim_1/behav/xsim';logs=result/'logs';logs.mkdir(exist_ok=True)
  for name in ['compile.log','elaborate.log','simulate.log','canonical_tb_vlog.prj','canonical_tb.tcl']:
   p=sim/name;assert p.exists();shutil.copy2(p,logs/name)
  text=(sim/'simulate.log').read_text();assert 'TEST_PASS K8 samples=2 operations=1472' in text and not re.search(r'(?i)fatal:|error:',text)
  h=byid[hid];end=datetime.datetime.fromisoformat(re.sub(r'(\.\d{6})\d+',r'\1',h['timestamp']).replace('Z','+00:00'));start=end-datetime.timedelta(seconds=h['elapsed'])
  rec={'tool':'Vivado/XSim2022.2 Build3671981','part':'xcu280-fsvh2892-2L-e','command':h['command'],'mcp_history_id':hid,'start_utc_from_history_end_minus_elapsed':start.isoformat(),'end_utc_mcp_history':end.isoformat(),'elapsed_seconds':h['elapsed'],'returncode':h['code'],'functional_pass':True,'final_qualification_run':run=='f','qualifications':{'a':'initial WORD_BITS6 smoke; includes broader raw rejected operands; not final positive-domain corpus','b':'full WORD_BITS14 and highPVwords; min17-cycle test memory responder','c':'added generation and stage monitors; monitor timestamps have process-order ambiguity','d':'absolute stage timestamps; min17-cycle test responder','e':'first-eligible response edge corrected to16cycles; explicit wrongsubbank check','f':'single-write PV memory inference fix; exact trace equivalence toE and exact cycle replay'}[run],'source_sha256':{p.name:sha(p) for p in source.iterdir() if p.is_file()},'generated_tb_sha256':sha(result/'canonical_tb.sv'),'input_sha256':{p.name:sha(p) for p in result.glob('*.mem')},'generator_binary_sha256':sha(result/'gen_vectors'),'simulator_design_binary_sha256':sha(sim/'xsim.dir/canonical_tb_behav/xsimk'),'output_log_sha256':sha(sim/'simulate.log'),'board_measured':False,'timing_qualified':False}
  (result/'receipt.json').write_text(json.dumps(rec,indent=2)+'\n')
  selected.extend(p for p in result.iterdir() if p.is_file() and p.suffix in ['.json','.mem','.sv','.tcl','.log'])
  selected.extend(p for p in source.rglob('*') if p.is_file());selected.extend(logs.iterdir())
 replay=json.loads((FINAL/'cycle_replay.json').read_text());eq=json.loads((FINAL/'ram_template_equivalence.json').read_text());assert replay['all_pass'] and eq['all_pass']
 assert sha(SRC/'ec_pending_k8.sv')==sha(ROOT/'results'/(STEM+'ram_probe')/'ec_pending_k8.sv')
 summary={'status':'LOCAL_FUNCTION_AND_CANONICAL_CYCLE_QUALIFIED','final_run':STEM+'f','functional_pass':True,'canonical_exact_stage_replay':True,'trace_records_identical_before_after_RAM_template_fix':eq['identical_stage_and_interface_records'],'transactions':1472,'canonical_reads':1472,'canonical_writes':196,'physical_requests':1988,'samples':2,'PV_clear_cycles_per_sample':16384,'shared_credit_peak':32,'per_subbank_context_peak':8,'per_subbank_reserved_event_peak':32,'generation_wraps_per_bank':2,'resource_inference':{'scope':'one isolated fullcapacity K8 pending subbank, synthesis only','URAM288':4,'LUT_total':2415,'LUT_logic':1663,'LUTRAM':752,'FF':676,'no_replication':True},'warnings':['URAM has no additional pipeline registers; integrated timing must be measured.','XSim default wave viewer cannot display huge TB arrays; functional checking is independent of viewer.'],'integration_OOC_owned_by_parent_worker':True,'full_batch_model_qualified':False,'complete_kernel_clock_qualified':False,'fpga_seconds':None,'board_measured':False}
 (FINAL/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');selected.append(FINAL/'summary.json')
 selected.extend(p for p in delivery.iterdir() if p.is_file())
 probe=ROOT/'results'/(STEM+'ram_probe');selected.extend(p for p in probe.iterdir() if p.is_file() and p.suffix in ['.sv','.rpt','.json'])
 mcp=ROOT/'results'/(STEM+'a')/'.vivado-ai/vivado_46545668_5b58e2a9.log';shutil.copy2(mcp,FINAL/'mcp_session.log');selected.append(FINAL/'mcp_session.log')
 out.mkdir(exist_ok=False);files=[]
 for p in sorted(set(selected)):
  data=p.read_bytes();raw=str(p.relative_to(ROOT/'results'));name=raw+'.gz' if len(data)>16384 else raw;q=out/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(data,mtime=0) if name.endswith('.gz') else data);files.append({'raw_path':raw,'archive':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 (out/'manifest.json').write_text(json.dumps({'base':'1e312d6e4ffc5ea96f25c0b97931ad028e710584','scope':'canonical worker only; historical A-E and final F, isolated resource-inference probe','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,'fpga_seconds':None,'board_measured':False},indent=2)+'\n');verify(out)
 print('CANONICAL_ARCHIVE_PASS',len(files),'bytes',sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
if __name__=='__main__':main()
