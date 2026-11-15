#!/usr/bin/env python3
"""Freeze an observation-only TB patch; run unchanged complete conservative d3."""
from pathlib import Path
import argparse,csv,datetime,hashlib,json,os,re,shutil,socket,struct,subprocess
from analyze_full import analyze
S=Path(__file__).resolve().parent;BIN=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('fixtures',type=Path);p.add_argument('out',type=Path);p.add_argument('--base-run',type=Path,required=True);p.add_argument('--frozen',type=Path,required=True);a=p.parse_args()
 for k in ['fixtures','out','base_run','frozen']:setattr(a,k,getattr(a,k).resolve())
 a.out.mkdir(parents=True,exist_ok=False);src=a.out/'source';src.mkdir();commands=[];base=json.loads((a.base_run/'binding.json').read_text());base_terminal=json.loads((a.base_run/'terminal.json').read_text());assert base_terminal['status']=='PASS'
 service=base['service'];assert(service['period_ps'],service['memory_latency_cycles'],service['memory_issue_cycles'])==(5000,32,2)
 dut=[n for n in base['source']if'/fixtures/'not in n];assert len(dut)==30;bindings={}
 for n,v in base['source'].items():
  f=(a.frozen if n in dut else a.base_run/'source')/Path(n).name;assert sha(f)==v;shutil.copyfile(f,src/f.name)
 before=(src/'tb_full_core.sv').read_text();patch=(S/'drain_probe.svh').read_text();assert before.count('\nendmodule')==1
 (a.out/'tb_full_core_before_probe.sv').write_text(before);(src/'tb_full_core.sv').write_text(before.replace('\nendmodule','\n'+patch+'\nendmodule'))
 for n in ['run_drain_probe.py','drain_probe.svh','analyze_full.py']:shutil.copyfile(S/n,a.out/n)
 bindings={n:sha(src/Path(n).name)for n in base['source']}
 dump(a.out/'binding.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':bindings,'DUT30_unchanged_from_baseline':True,'base_binding_sha256':sha(a.base_run/'binding.json'),'fixture_manifest_sha256':sha(a.fixtures/'manifest.json'),'probe_patch_sha256':sha(a.out/'drain_probe.svh'),'service':service,'probe_window':{'sample':2,'relative_first':21520,'relative_last':21545,'sampling':'posedge pre-NBA'},'full_production_parameters':True,'clock_is_timing_proof':False})
 dump(a.out/'process_identity.json',{'pid':os.getpid(),'ppid':os.getppid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'linux_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'hostname':socket.gethostname(),'argv':list(__import__('sys').argv)})
 env=dict(os.environ,LD_PRELOAD='/lib/x86_64-linux-gnu/libudev.so.1')
 def run(cmd,log):
  rec={'argv':cmd,'log':str(log),'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};commands.append(rec);dump(a.out/'commands.json',commands);print('RUN',log,flush=True)
  with log.open('w')as f:r=subprocess.run(cmd,cwd=a.out,env=env,stdout=f,stderr=subprocess.STDOUT)
  rec['returncode']=r.returncode;rec['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(a.out/'commands.json',commands);return r.returncode
 try:
  assert run([str(BIN/'xvlog'),'--sv',*[str(src/Path(n).name)for n in dut],str(src/'cp_sparse_memory.sv'),str(src/'tb_full_core.sv')],a.out/'compile.log')==0
  assert run([str(BIN/'xelab'),'tb_full_core','-s','snapshot','--timescale','1ns/1ps','-mt','4'],a.out/'elaborate.log')==0
  rd=a.out/'native_d3_w8_none';rd.mkdir();case=a.fixtures/'native_d3_w8';log=rd/'run.log'
  rc=run([str(BIN/'xsim'),'snapshot','-runall','-testplusarg','DIR='+str(case),'-testplusarg','OUT='+str(rd),'-testplusarg','NEG=none','-testplusarg','STRESS=0','-testplusarg','MAX_CYCLES=2000000','-testplusarg','PERIOD_PS=5000','-testplusarg','LATENCY_CYCLES=32','-testplusarg','ISSUE_CYCLES=2','-log',str(rd/'xsim.log')],log)
  txt=log.read_text();assert rc==0 and'TEST_PASS FULL_NATIVE_BATCH'in txt and'DRAIN_PROBE_CAPTURED'in txt and'Fatal:'not in txt and'ERROR:'not in txt,txt[-3000:]
  cfg=[int(t,16)for t in(case/'config.hex').read_text().split()];data=bytearray()
  for q in range(cfg[6]):
   words=[int(t,16)for t in(rd/f'sample_{q}_actual_beats.hex').read_text().split()];assert len(words)==(cfg[5]+3)//4
   for i in range(cfg[5]):
    pair=(words[i//4]>>(64*(i%4)))&((1<<64)-1);data.extend(struct.pack('<II',pair>>32,pair&0xffffffff))
  (rd/'output.bin').write_bytes(data);assert data==(case/'validation/output.bin').read_bytes();cal=analyze(rd);assert cal['status']=='PASS';dump(rd/'calibration.json',cal)
  prior=a.base_run/'native_d3_w8_none';comparisons={n:sha(rd/n)==sha(prior/n)for n in ['output.bin','events.csv','samples.csv','phase_cycles.csv','request_kinds.csv']+[f'sample_{q}_actual_beats.hex'for q in range(cfg[6])]};assert all(comparisons.values()),comparisons
  finish=lambda p:re.search(r'\$finish called at time\s*:\s*(\d+) ps',p.read_text()).group(1)
  assert finish(log)==finish(prior/'run.log')
  probe={}
  for n in ['drain_probe_global.csv','drain_probe_front_10.csv','drain_probe_front_11.csv']:
   rows=list(csv.DictReader((rd/n).open()));assert len(rows)==26 and [int(x['relative_cycle'])for x in rows]==list(range(21520,21546));assert all(None not in x for x in rows);probe[n]=sha(rd/n)
  dump(a.out/'terminal.json',{'status':'PASS','scope':'observation-only d3 full8-job conservative batch; sampled q2 drain26edges','all_jobs':cfg[6],'all_pairs':cfg[5]*cfg[6],'cycles':sum(x['cycles']for x in cal['samples'].values()),'baseline_artifacts_identical':comparisons,'absolute_finish_ps':finish(log),'probe_csv_sha256':probe,'output_sha256':sha(rd/'output.bin'),'DUT30_unchanged':True,'clock_qualification':None});print('PASS full8jobs +26edge probe; all baseline traces/output/cycles/time identical',flush=True)
 except BaseException as e:dump(a.out/'failure.json',{'exception':str(e)});raise
if __name__=='__main__':main()
