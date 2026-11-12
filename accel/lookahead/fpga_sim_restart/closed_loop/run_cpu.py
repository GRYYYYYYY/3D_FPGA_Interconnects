import pathlib,json,subprocess,os,platform,time
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z';out=r/'closed_loop/cpu';out.mkdir(exist_ok=True)
(out/'environment.json').write_text(json.dumps(dict(host=platform.node(),affinity=list(range(32,40)),scope='RESIDENT_COMPLETE_BATCH_V2',output_destination='host_DRAM',preparation='input validation, target metadata and workspace allocation before interval; every sample label/pending/output resets inside',gpu_status='nvidia-smi not available on this FPGA tooling host; no new GPU timing'),indent=2))
for x in json.load(open(root/'accel/lookahead/fpga_sim_restart/config/inputs.json')):
 for process in range(3):
  with open(out/f"{x['case']}_p{process}.jsonl",'w') as f,open(out/f"{x['case']}_p{process}.stderr",'w') as err:
   subprocess.run(['taskset','-c','32-39',str(r/'closed_loop/cpu_resident'),x['path'],str(r/f"replay/{x['case']}_F1.bin"),str(process)],stdout=f,stderr=err,check=True,env={**os.environ,'OMP_PROC_BIND':'true','OMP_PLACES':'cores'})
