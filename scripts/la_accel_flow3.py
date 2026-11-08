"""Sequential phase supervisor for a fresh round-three HLS cohort."""
import argparse,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--workload',type=Path,required=True)
 p.add_argument('--top',default='lookahead_top');p.add_argument('--testbench',type=Path);p.add_argument('--period-ns',type=float,default=5.0);p.add_argument('--contexts',type=int,default=1);p.add_argument('--define',action='append',default=[]);p.add_argument('--phases',nargs='+',default=['csim','csynth','cosim','impl'])
 a=p.parse_args();assert not (a.output/'supervisor.json').exists(),'Use a fresh cohort directory';a.output.mkdir(parents=True,exist_ok=True);env=os.environ.copy();env['LA_TRACE_LEVEL']='none'
 state={'trace_level':'none','phases':{},'source':str(a.source.resolve()),'workload':str(a.workload.resolve())};receipt=a.output/'supervisor.json'
 for phase in a.phases:
  state['active']=phase;receipt.write_text(json.dumps(state,indent=2)+'\n')
  cmd=[sys.executable,str(ROOT/'scripts/la_accel_hls.py'),'--phase',phase,'--output',str(a.output),'--source',str(a.source),'--workload',str(a.workload),'--top',a.top,'--contexts',str(a.contexts),'--aligned-depths','--period-ns',str(a.period_ns)]
  if a.testbench:cmd+=['--testbench',str(a.testbench)]
  for d in a.define:cmd+=['--define',d]
  if phase!='csim':cmd+=['--frozen-flow']
  proc=subprocess.run(cmd,env=env);state['phases'][phase]=proc.returncode
  if proc.returncode:state['status']='failed';receipt.write_text(json.dumps(state,indent=2)+'\n');return proc.returncode
 state.update(active=None,status='completed');receipt.write_text(json.dumps(state,indent=2)+'\n');return 0
if __name__=='__main__':raise SystemExit(main())
