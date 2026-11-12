import pathlib,json,subprocess,concurrent.futures,hashlib,time
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z/closed_loop';out=r/'large'
inputs=json.load(open(root/'accel/lookahead/fpga_sim_restart/config/inputs.json'));by={x['case']:x for x in inputs}
central=json.load(open(out/'bnn_F1_central.json'));assert central['jobs']==40 and central['output_equal']
scenarios=[('central',60,128000000000),('bandwidth_64',60,64000000000),('bandwidth_192',60,192000000000),('latency_150',30,128000000000),('latency_600',120,128000000000)]
tasks=[('bnn_export','F0',scenarios[0]),('lstm_s2','F1',scenarios[0])]
for case in ['bnn_export','lstm_s2']:
 for scenario in scenarios[1:]:tasks.append((case,'F1',scenario))
tasks.append(('lstm_s2','F0',scenarios[0]))
plan={'source_sha256':hashlib.sha256((root/'accel/lookahead/fpga_sim_restart/closed_loop/model.cpp').read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256((r/'model').read_bytes()).hexdigest(),'frequency_hz':200000000,'frequency_provenance':'assumed target; final full OOC gate pending','tasks':tasks,'max_concurrent':4}
(out/'execution_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def run(task):
 case,ablation,(sid,lat,bw)=task;tag=('bnn' if case=='bnn_export' else 'lstm')+'_'+ablation+'_'+sid;prefix=out/tag
 command=[str(r/'model'),by[case]['path'],str(r.parent/f'replay/{case}_F1.bin'),str(prefix),'64',ablation,str(lat),str(bw)]
 start=time.time()
 with open(str(prefix)+'.log','w') as f:res=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
 receipt={'command':command,'returncode':res.returncode,'elapsed_host_s':time.time()-start,'host_elapsed_is_not_FPGA_time':True}
 if res.returncode==0:
  j=json.load(open(str(prefix)+'.json'));assert j['jobs']==40 and j['output_equal'];receipt['output_sha256']=hashlib.sha256(pathlib.Path(str(prefix)+'.bin').read_bytes()).hexdigest()
 pathlib.Path(str(prefix)+'.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 return tag,receipt
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for tag,receipt in pool.map(run,tasks):
  print(json.dumps({'tag':tag,**receipt}),flush=True)
  if receipt['returncode']:raise RuntimeError(tag)
