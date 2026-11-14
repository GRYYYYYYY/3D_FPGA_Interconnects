"""Verify base descriptor archive and transitive native identity without reruns."""
from pathlib import Path
import json,hashlib,gzip,subprocess
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_local_fabric_20261115'
BASE='7dd79b2eb97f9bed1b36629e06b2fab3723fc4ec'; OLD=ROOT.parent/'3D_FPGA_Interconnects_DESCRIPTOR_FRONT';REL=Path('results/fpga_descriptor_front_20261114'); ARC=REL/'evidence_snapshot_final_a'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 raw=(OLD/ARC/'manifest.json').read_bytes();assert raw==subprocess.check_output(['git','show',BASE+':'+str(ARC/'manifest.json')],cwd=ROOT);m=json.loads(raw);rows={x['original_path']:x for x in m['files']};seen=set()
 for x in m['files']:
  if x['archive']in seen:continue
  data=(OLD/ARC/x['archive']).read_bytes();data=gzip.decompress(data)if x['compression']=='gzip'else data
  assert len(data)==x['bytes']and hashlib.sha256(data).hexdigest()==x['sha256'];seen.add(x['archive'])
 def bound(relative):
  p=OLD/REL/relative;assert sha(p)==rows[str(REL/relative)]['sha256'];return json.loads(p.read_text())
 native=bound(Path('software_reuse_a/native_identity.json'));assert sha(ROOT/native['adapter_path'])==native['adapter_sha256'];batch=[]
 for cfg in ['C0','F2']:
  for case in ['bnn_export','lstm_s2']:
   name=Path('model_d')/f'{cfg}_{case}_summary.json';x=bound(name);assert x['complete_batch']and x['all_pass'];batch.append({'configuration':cfg,'case':case,'cycles':x['conditional_cycles'],'summary_sha256':sha(OLD/REL/name),'full_output_sha256':x['full_output_sha256']})
 checks=[]
 for x in native['cases']:
  case=x['case'];out=R/'model_d'/f'L1_{case}_output.bin';assert sha(out)==x['new_output_sha256']
  for p,h in [('reused_import_receipt','reused_import_receipt_sha256'),('qor_receipt','qor_receipt_sha256')]:assert sha(Path(x[p]))==x[h]
  receipt=json.loads(Path(x['reused_import_receipt']).read_text())
  checks.append({'case':case,'current_full_output_sha256':sha(out),'historic_import_receipt_sha256':x['reused_import_receipt_sha256'],'qor_sha256':x['qor_receipt_sha256'],'native_all_input_arrays_exact':x['native_sections']['all_input_arrays_exact'],'adapter_sha256':native['adapter_sha256'],'wire_map_sha256':x['wire_map_sha256'],'wire_map_validation_scope':'hash-bound historic identity receipt, not a new VPR process run','STRICT_equivalence_claimed':False})
 result={'base':BASE,'historical_manifest_sha256':hashlib.sha256(raw).hexdigest(),'old_archive_files':len(m['files']),'old_archive_unique_objects_verified':len(seen),'native_identity_sha256':sha(OLD/REL/'software_reuse_a/native_identity.json'),'old_C0_F2_complete_batches':batch,'current_native_identity':checks,'new_VPR_runs':0,'historical_files_modified':False}
 (R/'native_identity_reuse.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
