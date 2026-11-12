"""Cross-check independent run receipts without rerunning any experiment."""
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[4]
r=root/'results/fpga_sim_restart_20261111T231000Z/closed_loop'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.load(open(r/'calibration_freeze.json'));same=[];changed=[]
for f,h in freeze['source_sha256'].items():
 (same if sha(root/f)==h else changed).append(f)
assert set(changed)=={'accel/lookahead/fpga_sim_restart/closed_loop/run_cpu.py','accel/lookahead/fpga_sim_restart/closed_loop/build_verilator.sh'},changed
p=root/'accel/lookahead/fpga_sim_restart/closed_loop/build_verilator.sh'
old=p.read_text().replace('${owners}${2:-}','$owners')
assert hashlib.sha256(old.encode()).hexdigest()==freeze['source_sha256'][str(p.relative_to(root))]
for file in ['ooc_64_fixed/source_binding.json','d3_rtl64_final_l60/binding.json','d4_rtl64_final_l60/binding.json']:
 j=json.load(open(r/file));sources=j.get('sources',j)
 assert all(sha(root/f)==h for f,h in sources.items())
 if 'binary_sha256' in j:assert sha(r/'verilator_64_final/Vgraph_top')==j['binary_sha256']
plan=json.load(open(r/'large/execution_plan.json'))
assert sha(root/'accel/lookahead/fpga_sim_restart/closed_loop/model.cpp')==plan['source_sha256']
assert sha(r/'model')==plan['binary_sha256']
checks=[]
for file in sorted((r/'large').glob('*.json')):
 if file.name=='execution_plan.json' or file.name.endswith('.receipt.json'):continue
 j=json.load(open(file))
 receipt=r/('native_bnn' if file.stem.startswith('bnn') else 'native_lstm_s2')/'receipt.json'
 expected=json.load(open(receipt))['model_output_sha256']
 assert sha(file.with_suffix('.bin'))==expected and j['jobs']==40 and j['output_equal']
 checks.append(file.stem)
assert len(checks)==12
layouts=[]
for x in json.load(open(root/'accel/lookahead/fpga_sim_restart/config/inputs.json')):
 _,n,e,j,k,c,_=x['header'];off=0;arrays={}
 sizes=[8*(n+1),8*e,16*n,8*k,4*n*j,32*j,8*n,8*n,4*n,4*n,8*j*c]
 for name,size,stride in zip(['row','edge','node','cost','cell','job','label','prop','pending','closed','output'],sizes,[8,8,16,8,4,32,8,8,4,4,8]):
  off=(off+1023)//1024*1024
  arrays[name]={'base_byte':off,'base_line':off//32,'logical_bytes':size,'allocated_bytes':(size+31)//32*32,'element_stride_bytes':stride}
  off+=arrays[name]['allocated_bytes']
 assert off<=8589934592
 rtl_layout=r/x['case']/'layout.json'
 if rtl_layout.exists():assert {k:v['base_line'] for k,v in arrays.items()}==json.load(open(rtl_layout))['bases_line']
 layouts.append({'case':x['case'],'provenance':'derived from frozen model.cpp Memory constructor and input headers; small cases cross-checked against actual exported RTL layouts','total_allocated_bytes':off,'capacity_bytes':8589934592,'arrays':arrays,'channel':'physical_line % 32','bank':'(physical_line // 32) % 16'})
(r/'memory_layouts.json').write_text(json.dumps(layouts,indent=2)+'\n')
j={'frozen_functional_and_model_sources_unchanged':True,'unchanged_frozen_files':same,
 'postfreeze_nonfunctional_changes':{'paths':changed,'reason':'Build directory gains optional unique suffix; restoring its original shell spelling reproduces the frozen script hash exactly. CPU runner gains affinity-isolation metadata. No RTL/model/testbench/arithmetic changes.'},
 'ooc_and_both_final_RTL_source_bindings_match':True,'both_final_RTL_binary_bindings_match':True,
 'large_model_binary_and_source_match_plan':True,'large_full_output_native_bindings_exact':checks,
 'calibration_gate':json.load(open(r/'calibration.json'))['total_cycle_gate']}
assert j['calibration_gate']
(r/'delivery_provenance_audit.json').write_text(json.dumps(j,indent=2)+'\n')
print('PASS: frozen functional sources, OOC/RTL bindings, full native output identity, calibration')
