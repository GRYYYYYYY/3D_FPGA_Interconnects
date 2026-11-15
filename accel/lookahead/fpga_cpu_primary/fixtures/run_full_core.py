#!/usr/bin/env python3
"""Freeze production closure, execute complete native XSim batches and rejection tests."""
from pathlib import Path
from decimal import Decimal, InvalidOperation
import argparse,datetime,hashlib,json,os,shutil,struct,subprocess
from analyze_full import analyze
S=Path(__file__).resolve().parent;ROOT=S.parents[3];BIN=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def positive_decimal(value):
 try:d=Decimal(value)
 except InvalidOperation as e:raise argparse.ArgumentTypeError('expected a finite positive decimal')from e
 if not d.is_finite()or d<=0:raise argparse.ArgumentTypeError('expected a finite positive decimal')
 return d

def ceil_decimal_ratio(numerator,denominator):
 # Decimal inputs retain exact text values; integer ratios make ceil exact even
 # arbitrarily close to an integer, without float or context rounding.
 an,ad=numerator.as_integer_ratio();bn,bd=denominator.as_integer_ratio()
 return -(-(an*bd)//(ad*bn))

def service_config(period,latency,issue,scenario):
 pn,pd=period.as_integer_ratio();ps_num=pn*1000
 if ps_num%pd:raise ValueError('period must be exactly representable in integer picoseconds')
 period_ps=ps_num//pd
 if period_ps%2 or period_ps<=200 or period_ps>2147483647:
  raise ValueError('period_ps must be an even signed32-bit integer >200 (existing TB stimulus settles for100ps)')
 latency_cycles=ceil_decimal_ratio(latency,period);issue_cycles=ceil_decimal_ratio(issue,period)
 if max(latency_cycles,issue_cycles)>2147483647:raise ValueError('memory cycles exceed signed32-bit service counters')
 if not scenario.strip():raise ValueError('scenario label must not be empty')
 return {'scenario':scenario,'clock_period_ns':str(period),'period_ps':period_ps,
  'memory_latency_requested_ns':str(latency),'memory_issue_requested_ns':str(issue),
  'memory_latency_cycles':latency_cycles,'memory_issue_cycles':issue_cycles,
  'memory_latency_implemented_ns':str(Decimal(period_ps*latency_cycles)/1000),
  'memory_issue_implemented_ns':str(Decimal(period_ps*issue_cycles)/1000),
  'memory_service_evidence_type':'declared_simulation_assumption',
  'stress_semantics':'core clock edges: jitter0..16cycles, request-open14of19cycles; unchanged across periods',
  'clock_is_timing_proof':False,'qualified_clock_mhz':None}

def run_modes(skip_negatives=False,skip_stress=False):
 modes=[('native_d3_w8','none',0),('native_d4_w8','none',0)]
 if not skip_stress:modes.append(('native_d4_w8','none',1))
 if not skip_negatives:modes.extend(('native_d3_w8',n,0)for n in ['nodes','cells','costs','jobs','high_address','unaligned','stride','descriptor_end','source','targets','missing_job'])
 return modes

def main():
 ap=argparse.ArgumentParser();ap.add_argument('fixtures',type=Path);ap.add_argument('out',type=Path)
 ap.add_argument('--frozen',type=Path,help='selected frozen DUT source directory; copied and hashed, never modified')
 ap.add_argument('--sources-list',type=Path,help='explicit source closure JSON; default delivery/sources.json')
 ap.add_argument('--max-cycles',type=int,default=2000000)
 ap.add_argument('--period-ns',type=positive_decimal,default=Decimal('5'))
 ap.add_argument('--latency-ns',type=positive_decimal,default=Decimal('80'))
 ap.add_argument('--issue-ns',type=positive_decimal,default=Decimal('5'))
 ap.add_argument('--scenario',default='baseline',help='explicit service scenario label; does not change numeric parameters')
 ap.add_argument('--skip-negatives',action='store_true',help='reuse prior configuration rejection evidence')
 ap.add_argument('--skip-stress',action='store_true',help='run only both normal native batches for the declared service scenario')
 ap.add_argument('--check-config',action='store_true',help='print exact converted configuration and test selection; create no files or tools')
 a=ap.parse_args()
 try:service=service_config(a.period_ns,a.latency_ns,a.issue_ns,a.scenario)
 except ValueError as e:ap.error(str(e))
 if a.max_cycles<=0 or a.max_cycles+max(service['memory_latency_cycles'],service['memory_issue_cycles'])+17>2147483647:ap.error('watchdog and service delay exceed signed32-bit cycle accounting')
 modes=run_modes(a.skip_negatives,a.skip_stress)
 if a.check_config:print(json.dumps({'service':service,'tests':modes},indent=2));return
 a.fixtures=a.fixtures.resolve();a.out=a.out.resolve()
 if a.frozen:a.frozen=a.frozen.resolve()
 a.out.mkdir(parents=True,exist_ok=False);source=a.out/'source';source.mkdir();commands=[];rows=[]
 dump(a.out/'service_config.json',service)
 closure_path=(a.sources_list or S.parent/'delivery/sources.json').resolve();closure=json.loads(closure_path.read_text());assert closure and len(set(closure))==len(closure) and len({Path(n).name for n in closure})==len(closure) and all(isinstance(n,str)and n.endswith('.sv')for n in closure)
 shutil.copyfile(closure_path,a.out/'sources.json');bindings={}
 for n in ['run_full_core.py','analyze_full.py']:shutil.copyfile(S/n,a.out/n)
 dump(a.out/'driver_binding.json',{n:sha(a.out/n)for n in ['run_full_core.py','analyze_full.py']})
 for n in closure:
  p=(a.frozen/Path(n).name)if a.frozen else ROOT/n
  dest=source/Path(n).name;assert not dest.exists(),n;shutil.copyfile(p,dest);bindings[n]=sha(dest)
 for n in ['cp_sparse_memory.sv','tb_full_core.sv']:shutil.copyfile(S/n,source/n);bindings[str((S/n).relative_to(ROOT))]=sha(source/n)
 dump(a.out/'binding.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':bindings,'fixture_manifest_sha256':sha(a.fixtures/'manifest.json'),'full_production_parameters':True,'banks':64,'lanes':64,'backend':'XSim2022.2','simulation':'behavioral','clock_period_ns':service['clock_period_ns'],'clock_is_timing_proof':False,'max_cycles':a.max_cycles,'service':service,'selected_tests':modes,'frozen_source_directory':str(a.frozen)if a.frozen else None,'source_closure_sha256':sha(a.out/'sources.json'),'dut_source_count':len(closure)})
 env=dict(os.environ,LD_PRELOAD='/lib/x86_64-linux-gnu/libudev.so.1')
 def execute(cmd,log):
  commands.append({'argv':cmd,'cwd':str(a.out),'log':str(log),'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});dump(a.out/'commands.json',commands);print('RUN',log,flush=True)
  with log.open('w')as f:r=subprocess.run(cmd,cwd=a.out,env=env,stdout=f,stderr=subprocess.STDOUT)
  commands[-1]['returncode']=r.returncode;commands[-1]['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(a.out/'commands.json',commands);return r.returncode
 try:
  assert execute([str(BIN/'xvlog'),'--sv',*[str(source/Path(n).name)for n in closure],str(source/'cp_sparse_memory.sv'),str(source/'tb_full_core.sv')],a.out/'compile.log')==0,'compile failed'
  assert execute([str(BIN/'xelab'),'tb_full_core','-s','snapshot','--timescale','1ns/1ps','-mt','4'],a.out/'elaborate.log')==0,'elaboration failed'
  for case,negative,stress in modes:
   rd=a.out/(case+'_'+negative+('_stress'if stress else''));rd.mkdir();log=rd/'run.log';rc=execute([str(BIN/'xsim'),'snapshot','-runall','-testplusarg','DIR='+str(a.fixtures/case),'-testplusarg','OUT='+str(rd),'-testplusarg','NEG='+negative,'-testplusarg','STRESS='+str(stress),'-testplusarg','MAX_CYCLES='+str(a.max_cycles),'-testplusarg','PERIOD_PS='+str(service['period_ps']),'-testplusarg','LATENCY_CYCLES='+str(service['memory_latency_cycles']),'-testplusarg','ISSUE_CYCLES='+str(service['memory_issue_cycles']),'-log',str(rd/'xsim.log')],log);txt=log.read_text();ok=rc==0 and'TEST_PASS'in txt and'Fatal:'not in txt and'ERROR:'not in txt
   row={'case':case,'negative':negative,'stress':stress,'returncode':rc,'pass':ok,'log_sha256':sha(log)};rows.append(row);dump(a.out/'progress.json',rows);assert ok,txt[-4000:]
   if negative=='none':
    cfg=[int(t,16)for t in(a.fixtures/case/'config.hex').read_text().split()];data=bytearray()
    for q in range(cfg[6]):
     words=[int(t,16)for t in(rd/f'sample_{q}_actual_beats.hex').read_text().split()];assert len(words)==(cfg[5]+3)//4
     for i in range(cfg[5]):
      pair=(words[i//4]>>(64*(i%4)))&((1<<64)-1);data.extend(struct.pack('<II',pair>>32,pair&0xffffffff))
    (rd/'output.bin').write_bytes(data);assert data==(a.fixtures/case/'validation/output.bin').read_bytes(),'full binary mismatch';row['output_sha256']=sha(rd/'output.bin');row['all_jobs']=cfg[6];row['all_pairs']=cfg[5]*cfg[6];calibration=analyze(rd);dump(rd/'calibration.json',calibration);assert calibration['status']=='PASS',calibration['errors']
   dump(a.out/'progress.json',rows);print(rd.name,'PASS',flush=True)
  dump(a.out/'terminal.json',{'status':'PASS','full_core_functional_verified':True,'full_core_timing_verified':False,'service':service,'selected_tests':modes,'config_rejections_reused':a.skip_negatives,'stress_skipped':a.skip_stress,'results':rows})
 except BaseException as e:dump(a.out/'failure.json',{'exception':str(e),'results':rows});raise
if __name__=='__main__':main()
