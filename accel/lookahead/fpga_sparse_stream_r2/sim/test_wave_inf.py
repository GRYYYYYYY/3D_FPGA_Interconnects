"""Real two-subbank RTL, finite 8-entry fragment queues and bounded scratch TB."""
from pathlib import Path
import os,sys,json,hashlib,subprocess,shutil,datetime
root=Path(__file__).resolve().parents[4];s=root/'accel/lookahead/fpga_sparse_stream_r2';r=root/'results/fpga_sparse_stream_r2_20261112';out=r/'accumulator'/sys.argv[1];out.mkdir(exist_ok=False);f=out/'source';f.mkdir()
for p in [s/'rtl/wave_inf_bank.sv',s/'sim/wave_inf_driver.cpp']:shutil.copy2(p,f/p.name)
u=root.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z/tools/verilator_local/usr';env=os.environ.copy();env['VERILATOR_ROOT']=str(u/'share/verilator')
cmd=[str(u/'bin/verilator'),'--cc','--exe','--build','-j','4','--top-module','wave_inf_owner','--Mdir',str(out/'build'),'-Wno-fatal','-O3','-CFLAGS','-O3 -std=c++17',str(f/'wave_inf_bank.sv'),str(f/'wave_inf_driver.cpp')]
with (out/'build.log').open('x') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env).returncode
(out/'source_binding.json').write_text(json.dumps({'command':cmd,'returncode':rc,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f.iterdir()},'scope':'two subbanks only; not full kernel; physical frequency unqualified'},indent=2)+'\n');assert rc==0
results=[]
for case in (sys.argv[2].split(',') if len(sys.argv)>2 else ['empty','capacity4096','capacity4097','directed','native_d3_w8','native_d4_w8','bnn_export','lstm_s2']):
 source=case if case in ['two_waves','empty','capacity4096','capacity4097','directed'] else str(r/'accumulator/profile_a'/case/'representative_wave.bin')
 cmd=[str(out/'build/Vwave_inf_owner'),source,str(out/(case+'_cycles.csv')),str(out/(case+'_output.csv'))]
 with (out/(case+'.log')).open('x') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
 results.append({'case':case,'command':cmd,'returncode':rc,'log':(out/(case+'.log')).read_text()});print(case,rc,flush=True)
(out/'receipt.json').write_text(json.dumps({'all_pass':all(x['returncode']==0 for x in results),'results':results,'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n');sys.exit(not all(x['returncode']==0 for x in results))
