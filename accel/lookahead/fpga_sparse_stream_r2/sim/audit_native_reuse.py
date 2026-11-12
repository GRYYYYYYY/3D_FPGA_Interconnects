from pathlib import Path
import json,hashlib,struct
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';out=r/'baselines/native_reuse';out.mkdir(parents=True,exist_ok=False)
e=root/'results/lookahead_r6_2_20261109T191213Z/evidence_snapshot';hold=json.loads((e/'holdout_results.json').read_text());opt=json.loads((e/'targeted_optimization_results.json').read_text())
def digest(path,limit=None,start=0):
 h=hashlib.sha256()
 with path.open('rb') as f:
  f.seek(start)
  while limit is None or limit:
   b=f.read((8<<20) if limit is None else min(limit,8<<20))
   if not b:break
   h.update(b)
   if limit is not None:limit-=len(b)
 return h.hexdigest()
def bind(path):
 with path.open('rb') as f:h=struct.unpack('<7Q',f.read(56))
 output_bytes=h[3]*h[5]*8;prefix=path.stat().st_size-output_bytes
 return {'path':str(path),'header':h,'file_sha256':digest(path),'input_prefix_sha256':digest(path,prefix),'sample_output_sha256':digest(path,start=prefix),'sample_output_bytes':output_bytes}
items=json.loads((r/'semantics/native_complete.json').read_text());results=[]
for x in items[2:]:
 c=x['command'];case=Path(c[3]).name;native_name='bnn_alt_cpu_reserve_qualification' if case=='bnn_export' else 'lstm_s2_alt_cpu_qualification';native=root.parent/'3D_FPGA_Interconnects_R6_2/results/lookahead_r6_2_20261109T191213Z/worker'/native_name/'native_input.bin'
 a,b=bind(Path(c[1])),bind(native);computed=digest(Path(c[3])/'output.bin');gold=digest(Path(c[2]));exact=a['input_prefix_sha256']==b['input_prefix_sha256'] and a['header']==b['header'] and computed==gold==b['sample_output_sha256'];results.append({'case':case,'R2_input':a,'qualified_native_capture':b,'R2_functional_output_sha256':computed,'frozen_ALT_golden_sha256':gold,'same_inputs_and_complete_ALT_output':exact})
rows=[]
for x in hold['formal_rows']:
 rows.append({k:x.get(k) for k in ['case','backend','repeat','hostname','affinity','scope_version','E2_s','E2_precision_s','Process_wall_s','qualified','map_sha256','route_sha256','zero_overuse','binary_sha256','library_sha256']})
j={'scope':'read-only identity/qualification reuse; no new native timing and no new physical FPGA execution','native_identity':results,'all_inputs_and_outputs_exact':all(x['same_inputs_and_complete_ALT_output'] for x in results),'new_route_needed_for_same_output':not all(x['same_inputs_and_complete_ALT_output'] for x in results),'E2_Process_rows':rows,'E2_Process_summary':hold['summary'],'map_differences':hold['map_differences'],'STRICT_equivalent':False,'existing_native_cohort':hold['worker'],'V2_comparison_eligible':False,'reason_not_V2':'Native E2 includes conversion/constructor; Process includes routing/FULL/STA. Reuse these in a separate native table; never divide by simulated resident cycles. The new CUDA/CPU prepared-POP cohort supplies V2 software comparison.','remaining_limitations':['No new native CUDA prepared representation bridge or cold FPGA E2 is timed.','ALT congestion differs from STRICT as preserved in historical map_differences.','Complete FPGA architecture outputs still pending; their future native reuse requires the same full output hashes.'],'source_bindings':{p.name:digest(p) for p in [e/'holdout_results.json',e/'targeted_optimization_results.json',e/'raw_artifact_bindings.json']}}
(out/'audit.json').write_text(json.dumps(j,indent=2));print('NATIVE_IDENTITY',j['all_inputs_and_outputs_exact'],len(rows));assert j['all_inputs_and_outputs_exact']
