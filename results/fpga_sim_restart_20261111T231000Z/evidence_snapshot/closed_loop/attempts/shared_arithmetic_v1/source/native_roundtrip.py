import pathlib,json,hashlib,subprocess,os,struct,sys,time
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z/closed_loop';snap=root/'results/lookahead_r6_2_20261109T191213Z/evidence_snapshot'
case=sys.argv[1];file='targeted_optimization_results.json' if case=='bnn' else 'holdout_results.json'
def entries(x):
 if isinstance(x,dict):
  if 'command' in x and x.get('backend')=='alt_cpu' and x.get('case')==case and 'qualification' in str(x.get('repeat')):yield x
  for v in x.values():yield from entries(v)
 elif isinstance(x,list):
  for v in x:yield from entries(v)
old=next(entries(json.load(open(snap/file))));p=r/f'native_{case}';p.mkdir(exist_ok=True)
workload=pathlib.Path(old['effective_env']['R61_CAPTURE']+'.bin');model=r/'large'/('bnn_F1_central.bin' if case=='bnn' else 'lstm_F1_central.bin')
assert model.exists(), 'complete model output required'
with open(workload,'rb') as f:
 h=struct.unpack('<7Q',f.read(56));n=h[3]*h[5]*8;f.seek(-n,2);expected=f.read()
assert model.read_bytes()==expected,'model does not match independently qualified native ALT output'
cmd=old['command'].copy()
for key,name in [('--route_file','routed.route'),('--write_router_lookahead','wire_map.bin')]:cmd[cmd.index(key)+1]=str(p/name)
env={**os.environ,**old['effective_env']};
for key in ['VPR_LA_BACKEND','R61_CAPTURE','R61_VERIFY_CPU','VPR_LA_EXPORT']:env.pop(key,None)
env['VPR_LA_IMPORT']=str(model);env['VPR_LA_WORKLOAD']=str(workload)
env['LD_LIBRARY_PATH']=str(r.parent/'tools/tbb_local/usr/lib/x86_64-linux-gnu')+':'+env.get('LD_LIBRARY_PATH','')
receipt={'kind':'offline_model_output_native_roundtrip_not_device_runtime','command':cmd,'effective_env':{k:v for k,v in env.items() if k.startswith(('VPR_','R61_','LD_LIBRARY_PATH'))},'historical_map_sha256':old['map_sha256'],'native_input_path':str(workload),'model_output_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'sample_output_exact':True,'expected_algorithm':'qualified original ALT shift20; not STRICT equivalence'}
(p/'invocation.json').write_text(json.dumps(receipt,indent=2)+'\n')
with open(p/'process.log','w') as log:res=subprocess.run(['taskset','-c','48-55',*cmd],cwd=p,env=env,stdout=log,stderr=subprocess.STDOUT)
receipt['returncode']=res.returncode;log=(p/'process.log').read_text(errors='replace');receipt['import_marker']='LA_IMPORT verified samples=40' in log
if (p/'wire_map.bin').exists():receipt['map_sha256']=hashlib.sha256((p/'wire_map.bin').read_bytes()).hexdigest();receipt['map_equal']=receipt['map_sha256']==old['map_sha256']
receipt['full_route_check']='Routing succeeded' in log or 'Successfully routed' in log
(p/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt));assert res.returncode==0 and receipt['import_marker'] and receipt.get('map_equal')
