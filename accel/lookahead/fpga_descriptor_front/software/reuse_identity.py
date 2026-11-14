"""Read-only reuse of completed native import and software baseline evidence."""
from pathlib import Path
import datetime,hashlib,json,statistics,struct,subprocess
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_descriptor_front_20261114';O=R/'software_reuse_a'
OLD=ROOT.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z/closed_loop'
BASE='ccec3da64b4c5be643809c2bdda94145c4bb8187'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(8<<20),b''):h.update(x)
 return h.hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def sections(original,native):
 result={}
 with Path(original).open('rb') as a,Path(native).open('rb') as b:
  ha=a.read(56);hb=b.read(56);assert ha==hb;_,n,e,j,c,cells,groups=struct.unpack('<7Q',ha)
  for name,count in [('row',(n+1)*8),('node',n*16),('edge',e*8),('cost',c*8),('job',j*24),('cell',j*n*4)]:
   digest=hashlib.sha256();left=count
   while left:
    x=a.read(min(left,8<<20));y=b.read(len(x));assert x==y and x;digest.update(x);left-=len(x)
   result[name]={'bytes':count,'sha256':digest.hexdigest(),'exact':True}
  original_tail=a.read();native_tail=b.read();assert len(original_tail)==len(native_tail)==j*cells*8
 return {'header_sha256':hashlib.sha256(ha).hexdigest(),'all_input_arrays_exact':True,'sections':result,'original_embedded_golden_sha256':hashlib.sha256(original_tail).hexdigest(),'native_ALT_tail_sha256':hashlib.sha256(native_tail).hexdigest(),'golden_tail_not_part_of_input_identity':True}
def blob(path):
 raw=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT);return raw,{'git_commit':BASE,'path':path,'sha256':hashlib.sha256(raw).hexdigest()}
def allrows(x):
 if isinstance(x,dict):
  if all(k in x for k in ['backend','command','case']):yield x
  else:
   for v in x.values():yield from allrows(v)
 elif isinstance(x,list):
  for v in x:yield from allrows(v)
def main():
 O.mkdir(exist_ok=False);inputs=json.loads((R/'descriptor_a/binding.json').read_text())['inputs'];chain=[]
 for case,dirname in [('bnn_export','native_bnn'),('lstm_s2','native_lstm_s2')]:
  recpath=OLD/dirname/'receipt.json';rec=json.loads(recpath.read_text());inp=inputs[case];output=R/'software_functional_a'/case/'output.bin';outsha=sha(output)
  assert rec['returncode']==0 and rec['import_marker'] and rec['map_equal'] and rec['full_route_check']
  assert outsha==inp['golden_sha256']==rec['model_output_sha256'];assert sha(rec['effective_env']['VPR_LA_IMPORT'])==outsha
  assert sha(OLD/dirname/'wire_map.bin')==rec['map_sha256']==rec['historical_map_sha256']
  arrays=sections(inp['workload'],rec['native_input_path']);assert arrays['native_ALT_tail_sha256']==outsha
  oldidentity=next(x for x in json.loads((OLD/'native_input_identity.json').read_text()) if x['case']==case)
  for name,x in arrays['sections'].items():assert x['sha256']==oldidentity['sections'][name]['sha256']
  log=(OLD/dirname/'process.log').read_text(errors='replace');assert 'LA_IMPORT verified samples=40' in log
  chain.append({'case':case,'new_output_path':str(output),'new_output_sha256':outsha,'native_input_path':rec['native_input_path'],'workload_path':inp['workload'],'native_sections':arrays,'reused_import_receipt':str(recpath),'reused_import_receipt_sha256':sha(recpath),'reused_import_source_output_sha256':outsha,'wire_map_sha256':rec['map_sha256'],'wire_map_file_sha256_verified':True,'qor_receipt':str(OLD/dirname/'qor.json'),'qor_receipt_sha256':sha(OLD/dirname/'qor.json'),'inference':'Identical full input arrays, sample order and output bytes under the same unchanged import adapter imply the same native map. This is transitive identity reuse, not a new VPR process run.','new_native_import_runs':0,'STRICT_equivalence_claimed':False})
 save(O/'native_identity.json',{'status':'PACKED_NATIVE_IDENTITY_BY_VERIFIED_TRANSITIVE_CHAIN','adapter_path':'accel/lookahead/vpr_bridge.cpp','adapter_sha256':sha(ROOT/'accel/lookahead/vpr_bridge.cpp'),'native_input_identity_receipt_sha256':sha(OLD/'native_input_identity.json'),'cases':chain})
 cohorts=[('prepared_pop_gpu_b','results/fpga_sparse_stream_r2_20261112/evidence_snapshot/software_gpu_transform_complete/prepared_pop_gpu_b/',['cpu']),('private_inf_gpu_b','results/fpga_sparse_stream_r2_20261112/evidence_snapshot/software_private_inf_gpu_b_terminal/software/private_inf_gpu_b/',['control_cpu','cpu'])]
 baselines=[];sources={}
 for cohort,prefix,variants in cohorts:
  eraw,ebind=blob(prefix+'environment.json');env=json.loads(eraw);sources[prefix+'environment.json']=ebind
  for case in ['bnn_export','lstm_s2']:
   for variant in variants:
    processes=[]
    for process in range(3):
     stem=f'{case}_{variant}_p{process}';raw,binding=blob(prefix+stem+'.jsonl');sources[prefix+stem+'.jsonl']=binding
     rr,rb=blob(prefix+stem+'.receipt.json');sources[prefix+stem+'.receipt.json']=rb;receipt=json.loads(rr);assert receipt['returncode']==0
     entries=[json.loads(x) for x in raw.decode().splitlines()];assert len(entries)==4
     assert all(x['scope']=='RESIDENT_COMPLETE_BATCH_V2' and x['output_equal'] and x['threads']==8 and x['jobs']==40 for x in entries)
     assert entries[0]['warmup'] and not any(x['warmup'] for x in entries[1:]);vals=[x['resident_s'] for x in entries[1:]]
     assert receipt['command'][1]==inputs[case]['workload'] and receipt['command'][2]==inputs[case]['golden']
     processes.append({'process':process,'raw_seconds':vals,'mean_seconds':statistics.mean(vals),'command':receipt['command'],'returncode':0})
    source='cpu_private_inf.cpp' if cohort=='private_inf_gpu_b' and variant=='cpu' else 'cpu_prepared_pop.cpp';_,sb=blob(prefix+'source/'+source);sources[prefix+'source/'+source]=sb
    baselines.append({'case':case,'cohort':cohort,'variant':variant,'algorithm':entries[0]['backend'],'scope':'RESIDENT_COMPLETE_BATCH_V2','threads':8,'hostname':env['hostname'],'affinity':env['affinity'],'cpu_model':next(x.strip() for x in env['lscpu'].splitlines() if 'Model name:' in x),'same_host_as_new_packed_CPU':False,'processes':processes,'mean_of_process_means_seconds':statistics.mean(p['mean_seconds'] for p in processes),'independent_processes':3,'within_process_samples_each':3,'n9_is_not_9_independent_processes':True,'native_input_sha256':inputs[case]['workload_sha256'],'golden_sha256':inputs[case]['golden_sha256']})
 native=[]
 r62=ROOT.parent/'3D_FPGA_Interconnects_R6_2/results/lookahead_r6_2_20261109T191213Z'
 for file in ['targeted_optimization_results.json','holdout_results.json']:
  path=r62/file;d=json.loads(path.read_text());sources[str(path)]={'sha256':sha(path)}
  for row in allrows(d):
   if row['case'] not in ['bnn','lstm_s2'] or row['backend'] not in ['stock','flat','pipeline','alt_cpu']:continue
   keys=['case','backend','repeat','scope_version','hostname','affinity','E2_s','E1_wall_s','Process_wall_s','returncode','qualified','map_sha256','binary_sha256','library_sha256']
   native.append({**{k:row[k] for k in keys if k in row},'source':str(path),'scope_note':'E2=MapLookahead build, Process=whole VPR. Native stock/flat/pipeline resident search wall timer is absent; router worker-seconds are not a resident batch timer. ALT E1 retains its original native backend boundary.'})
 save(O/'software_baselines.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fixed_git_base':BASE,'resident_CPU_controls':baselines,'native_VPR_E2_Process':native,'sources':sources,'new_old_software_runs':0,'new_GPU_runs':0,'native_stock_resident_complete_batch_timer_available':False,'comparison_limit':'Do not use E2, Process or worker-seconds as resident; do not transfer ALT equivalence to STRICT; CPU cohorts use distinct hosts.'})
 print('NATIVE_IDENTITY_AND_CPU_REUSE_PASS',[(x['case'],x['variant'],x['mean_of_process_means_seconds']) for x in baselines])
if __name__=='__main__':main()
