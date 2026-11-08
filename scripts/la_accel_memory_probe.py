"""Replay generated RTL with explicit AXI request latency; a sensitivity probe, NOT a calibrated HBM model."""
import argparse,json,re,shutil,subprocess,os,time
from pathlib import Path
from prepare import sha256

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--hls',type=Path,required=True);p.add_argument('--latency',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert a.latency>=1;o=a.output.resolve();o.mkdir(parents=True,exist_ok=False)
 source=a.hls.resolve()/'project/solution/sim';sim=o/'sim';shutil.copytree(source,sim,ignore=shutil.ignore_patterns('*.wdb','core.*','xsim.dir','*.log','*.jou'))
 # Remove copied observations: only freshly generated RTL may count.
 for stale in (sim/'tv/rtldatafile').glob('*'):stale.unlink()
 for stale in (sim/'verilog').glob('*.performance.result.transaction.xml'):stale.unlink()
 config=dict(evidence_type='fpga_rtl_latency_sensitivity',calibrated_hbm=False,request_latency_cycles=a.latency,read_write_arbitration='independent; NOT a complete bounded external-memory model',source_hls=str(a.hls.resolve()),memory_files={})
 for path in (sim/'verilog').glob('AESL_axi_master_*.v'):
  old=path.read_text();new=re.sub(r'(parameter (?:ReadReqLatency|WriteReqLatency) = 32\x27d )\d+',lambda m:m[1]+str(a.latency),old);assert new!=old
  path.write_text(new);config['memory_files'][path.name]={'before':sha256(source/'verilog'/path.name),'after':sha256(path)}
 # Avoid embedding old waveform paths and costly full wave logging; outputs and transaction monitor remain.
 tcl=sim/'verilog/lookahead_top.tcl';s=tcl.read_text();s='\n'.join(line for line in s.splitlines() if not any(v in line for v in ['log_wave','save_wave_config','add_wave']));tcl.write_text(s+'\n')
 (o/'config.json').write_text(json.dumps(config,indent=2));env=os.environ.copy();env['LD_PRELOAD']='/lib/x86_64-linux-gnu/libudev.so.1';start=time.time()
 with (o/'simulation.log').open('w') as f:r=subprocess.run(['bash','run_xsim.sh'],cwd=sim/'verilog',env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 ports={}
 for c in (sim/'tv/cdatafile').glob('c.lookahead_top.autotvout_result.dat'):
  rtl=sim/'tv/rtldatafile'/c.name.replace('c.lookahead_top','rtl.lookahead_top');ports[c.name]=c.read_bytes()==rtl.read_bytes()
 rpt=sim/'verilog/lookahead_top.performance.result.transaction.xml';cycles=[int(x) for x in re.findall(r'transaction\s+\d+:\s+(\d+)',rpt.read_text())] if rpt.exists() else []
 result=dict(returncode=r.returncode,elapsed_host_s=time.time()-start,not_fpga_runtime=True,rtl_result_ports_match_c=ports,cycles=cycles,cycle_report=str(rpt),fresh_cycle_report=rpt.exists() and rpt.stat().st_mtime>=start,status='passed' if r.returncode==0 and ports and all(ports.values()) and cycles and rpt.stat().st_mtime>=start and '$finish called' in (o/'simulation.log').read_text() else 'failed')
 (o/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return result['status']!='passed'
if __name__=='__main__':raise SystemExit(main())
