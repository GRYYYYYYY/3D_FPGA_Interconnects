"""Cycle calibration of the SAME enum_clock used by the frozen full model.

Starts at the enum pipeline's first eligible scan boundary. Recorded FR is an
external input. Scan times, fragment times/order/line and supported payload are
predictions, not drivers. Flush/DRAIN/sample init and remaining services are not
claimed calibrated by this test.
"""
from run import *
import csv

def main():
 out=R/'model_enum_calibration_c';out.mkdir(exist_ok=False);src=OUT/'source';binary=out/'enum_model'
 cmd=['g++','-O3','-std=c++17','-ffp-contract=off','-I'+str(src/'accel/lookahead/include'),'-I'+str(src/'accel/lookahead/round6_1'),str(src/'accel/lookahead/fpga_enum_commit/model/enum_calibrate.cpp'),'-o',str(binary)]
 start=now()
 with (out/'build.log').open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 rtl=ROOT/'results/fpga_enum_commit_enum_20261114_a/enum_project_e/enum_unit.sim/sim_1/behav/xsim';records=list(csv.DictReader((rtl/'enum_trace.csv').open()));ticks=list(csv.DictReader((rtl/'enum_ticks.csv').open()));results=[]
 for wave in [0,1,3]:
  w=[x for x in records if x['variant']=='1' and int(x['wave'])==wave];scans=[x for x in w if x['event']=='scan'];anchor=int(scans[0]['time_ps'])//5000;n=len(scans)
  accepted=[x for x in w if x['event']=='accept'];assert len(accepted)==n
  for i,x in enumerate(accepted):assert int(x['line'],16)==i*256+i%4 and int(x['data'],16)==0x3f80000040000000+i
  expected=sorted((int(x['time_ps'])//5000-anchor,x['event'],int(x['line'],16)) for x in w if x['event'] in ['scan','fragment'])
  stimulus=out/f'wave_{wave}_ready.csv'
  with stimulus.open('x') as f:
   f.write('cycle,ready\n')
   for x in ticks:
    rel=int(x['time_ps'])//5000-anchor
    if x['variant']=='1' and rel>=0:f.write(str(rel)+','+x['fr']+'\n')
  output=out/f'wave_{wave}_model.csv';command=[str(binary),str(n),str(anchor+1),'0','0',str(output),str(stimulus)];p=subprocess.run(command,capture_output=True,text=True);(out/f'wave_{wave}.log').write_text(p.stdout+p.stderr)
  actual=sorted((int(x['cycle']),x['event'],int(x['line'])) for x in csv.DictReader(output.open()));exact=actual==expected
  # No dependence on output oracle: payload constants are actual accepted operands.
  for x in csv.DictReader(output.open()):
   if x['event']=='fragment':assert int(x['data'],16)==0x3f80000040000000+int(x['line'])//64
  results.append({'wave':wave,'returncode':p.returncode,'cycle_exact':exact,'events':len(expected),'same_cycle_log_order_ignored':True,'command':command,'ready_sha256':sha(stimulus),'model_output_sha256':sha(output)})
  assert p.returncode==0 and exact
 value={'scope':__doc__,'start_utc':start,'end_utc':now(),'build_command':cmd,'binary_sha256':sha(binary),'frozen_full_model_binding_sha256':sha(OUT/'binding.json'),'full_model_shared_function':'finite.hpp::enum_clock','input_RTL_trace_sha256':{str(r.relative_to(ROOT)):sha(r) for r in [rtl/'enum_trace.csv',rtl/'enum_ticks.csv']},'RTL_source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'accel/lookahead/fpga_enum_commit/enumerator/enum2_bank.sv',ROOT/'accel/lookahead/fpga_sparse_stream_r2/rtl/sync_fifo.sv']},'results':results,'all_pass':True,'full_scratch_canonical_front_top_cycle_qualified':False}
 dump(out/'calibration.json',value);print('ENUM_SHARED_CONTROL_CYCLE_EXACT',sum(x['events'] for x in results))
if __name__=='__main__':main()
