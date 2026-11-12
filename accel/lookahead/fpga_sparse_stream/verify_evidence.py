"""Final binding and scope audit. Does not run new performance experiments."""
from pathlib import Path
import hashlib,json,subprocess
root=Path(__file__).resolve().parents[3];src=root/'accel/lookahead/fpga_sparse_stream';r=root/'results/fpga_sparse_stream_20261112'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
out={}
assert sha(r/'owner_cycles.csv')==sha(r/'owner_model_cycles.csv')
assert 'OWNER_PASS' in (r/'owner_test.log').read_text() and 'OWNER_PASS' in (r/'owner_model.log').read_text()
out['saturated_owner_cycle_calibration_exact']=True
ev=r/'owner_changed_eviction';ev_receipt=read(ev/'receipt.json')
assert ev_receipt['returncode']==0 and 'OWNER_CHANGED_PASS' in (ev/'run.log').read_text()
for name,h in ev_receipt['source_sha256'].items():
 assert sha(ev/'source'/name)==h
 assert sha(src/('rtl' if (src/'rtl'/name).exists() else 'sim')/name)==h
out['owner_changed_eviction_and_delayed_ACK_verified']=True
for name in ['batch_f1','f0_batch']:
 b=r/(name+'_build');d=read(b/'source_binding.json')
 for rel,h in d['source_sha256'].items():assert sha(src/rel)==h,(name,rel)
 for rel,h in d['compiled_snapshot_sha256'].items():assert sha(b/'source'/rel)==h
 model=r/(name+'_model_source');m=read(model/'binding.json')
 for rel,h in m['sha256'].items():
  assert sha(model/rel)==h
  assert sha(src/('sim/'+rel if rel=='tile_driver.cpp' else rel))==h
 records=list((r/'calibration').glob(name+'_*.json'));assert records
 for f in records:
  for record in read(f):
   assert all(record['checks'].values())
   left,right=[root/p for p in record['paths']]
   for filename in record['checks']:assert sha(left/filename)==sha(right/filename),(f,filename)
   for d in [left,right]:assert read(d/'receipt.json')['returncode']==0
 out[name]={'binding_verified':True,'calibrated_complete_runs':sum(len(read(f)) for f in records)}
o=r/'tile_ooc_resident_batch';d=read(o/'source_binding.json')
for rel,h in d.items():
 assert sha(o/'source'/rel)==h
 if rel.startswith('rtl/'):assert sha(src/rel)==h
out['final_OOC_RTL_binding_verified']=True
out['final_OOC_returncode']=read(o/'receipt.json')['returncode']
assert out['final_OOC_returncode']==0
audit=read(o/'postroute_receipt.json')
assert audit['returncode']==0 and audit['checkpoint_unchanged']
assert sha(src/'sim/postroute_audit.tcl')==audit['script_sha256']
physical=read(r/'physical_audit.json')
for rel,h in physical['report_sha256'].items():assert sha(o/rel)==h
config=read(src/'config/experiment.json')
assert config['physical_target']['setup_WNS_ns']==physical['timing_200MHz']['WNS_ns']
assert config['physical_target']['hold_WHS_ns']==physical['timing_200MHz']['WHS_ns']
assert config['verification_state']['tile_ooc_timing_supported']==physical['target_200MHz_timing_supported']
for rel,h in read(r/'optimistic_bound.json')['source_sha256'].items():assert sha(root/rel)==h
out['physical_audit_sha256']=sha(r/'physical_audit.json')
assert 'PHYSICAL_BEGIN' not in (root/'docs/lookahead_fpga_sparse_stream.md').read_text()
out['final_route_and_readonly_audit_complete']=True
for f in read(r/'batch_capacity_tests.json'):assert f['returncode']!=0 and f['no_output_published']
assert read(r/'batch65/rejected/receipt.json')['no_output_published']
assert read(r/'batch_native_d3_w8_xsim/receipt.json')[-1]['explicit_pass']
out['capacity_and_xsim_verified']=True
orig=root.parent/'3D_FPGA_Interconnects'
refs=subprocess.check_output(['git','-C',str(orig),'rev-parse','HEAD','main'],text=True).splitlines()
assert refs==['480ba6d5cc2b9d73696a44315777c0e658d8a7b4','068aabd0f604a094c3b42b378028d9e9b5f54b39']
assert not subprocess.check_output(['git','-C',str(orig),'diff','--name-only'],text=True).strip()
assert not subprocess.check_output(['git','-C',str(orig),'diff','--cached','--name-only'],text=True).strip()
assert sha(orig/'docs/CODEX_FPGA_SPARSE_STREAMING_REPAIR.md')==sha(src/'config/CODEX_FPGA_SPARSE_STREAMING_REPAIR.md')
package=orig/'FPGA_Sparse_Streaming_Repair_20261112'
package_hashes={}
for line in (package/'SHA256SUMS').read_text().splitlines():
 h,name=line.split(maxsplit=1);name=name.lstrip('*')
 assert sha(package/name)==h
 package_hashes[name]=h
assert sha(package/'review_metrics.json')==sha(src/'config/review_metrics.json')
out['original_guidance_package_manifest_verified']=package_hashes
out['original_HEAD_and_main_unchanged']=refs
out['original_tracked_files_clean']=True
out['guidance_original_sha256']=sha(orig/'docs/CODEX_FPGA_SPARSE_STREAMING_REPAIR.md')
out['base_is_ancestor']=subprocess.run(['git','merge-base','--is-ancestor','fe659f008fc58c913bb1c0232d9898caf79fd524','HEAD'],cwd=root).returncode==0
assert out['base_is_ancestor']
out['board_measured']=False
out['configuration_sha256']=sha(src/'config/experiment.json')
(r/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
