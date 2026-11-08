"""Replay a validated dual RTL design and observe real simultaneous engine activity."""
import argparse,json,os,re,shutil,subprocess,time
from pathlib import Path
from prepare import sha256

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--hls',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 src=a.hls.resolve()/'project/solution/sim';o=a.output.resolve();o.mkdir(parents=True,exist_ok=False);sim=o/'sim'
 shutil.copytree(src,sim,ignore=shutil.ignore_patterns('*.wdb','core.*','xsim.dir','*.log','*.jou'))
 for stale in (sim/'tv/rtldatafile').glob('*'):stale.unlink()
 for stale in (sim/'verilog').glob('*.performance.result.transaction.xml'):stale.unlink()
 tb=sim/'verilog/lookahead_dual.autotb.v';old=tb.read_text();at=old.index('endmodule')
 monitor='''
integer la_cycle=0, la_active0=0, la_active1=0, la_overlap=0;
reg [3:0] la_prev=4'bxxxx;
always @(posedge ap_clk) begin
 la_cycle=la_cycle+1;
 if (!`AUTOTB_DUT_INST.engine_0_U0_ap_idle) la_active0=la_active0+1;
 if (!`AUTOTB_DUT_INST.engine_1_U0_ap_idle) la_active1=la_active1+1;
 if (!`AUTOTB_DUT_INST.engine_0_U0_ap_idle && !`AUTOTB_DUT_INST.engine_1_U0_ap_idle) la_overlap=la_overlap+1;
 if ({`AUTOTB_DUT_INST.engine_0_U0_ap_idle,`AUTOTB_DUT_INST.engine_1_U0_ap_idle,`AUTOTB_DUT_INST.engine_0_U0_ap_done,`AUTOTB_DUT_INST.engine_1_U0_ap_done} !== la_prev) begin
  $display("LA_EVENT cycle=%0d idle0=%0b idle1=%0b done0=%0b done1=%0b",la_cycle,`AUTOTB_DUT_INST.engine_0_U0_ap_idle,`AUTOTB_DUT_INST.engine_1_U0_ap_idle,`AUTOTB_DUT_INST.engine_0_U0_ap_done,`AUTOTB_DUT_INST.engine_1_U0_ap_done);
  la_prev={`AUTOTB_DUT_INST.engine_0_U0_ap_idle,`AUTOTB_DUT_INST.engine_1_U0_ap_idle,`AUTOTB_DUT_INST.engine_0_U0_ap_done,`AUTOTB_DUT_INST.engine_1_U0_ap_done};
 end
end
final $display("LA_OVERLAP active0=%0d active1=%0d both=%0d",la_active0,la_active1,la_overlap);
'''
 tb.write_text(old[:at]+monitor+old[at:]);tcl=sim/'verilog/lookahead_dual.tcl';tcl.write_text('\n'.join(l for l in tcl.read_text().splitlines() if not any(k in l for k in ['log_wave','save_wave_config','add_wave']))+'\n')
 (o/'config.json').write_text(json.dumps(dict(source=str(src),source_tb_sha256=sha256(src/'verilog'/tb.name),monitor_tb_sha256=sha256(tb),scope='observed RTL activity, not physical HBM parallelism'),indent=2))
 env=os.environ.copy();env['LD_PRELOAD']='/lib/x86_64-linux-gnu/libudev.so.1';start=time.time()
 with (o/'simulation.log').open('w') as f:r=subprocess.run(['bash','run_xsim.sh'],cwd=sim/'verilog',env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 log=(o/'simulation.log').read_text();m=re.search(r'LA_OVERLAP active0=(\d+) active1=(\d+) both=(\d+)',log);ports={}
 for c in (sim/'tv/cdatafile').glob('c.lookahead_dual.autotvout_result*.dat'):
  rtl=sim/'tv/rtldatafile'/c.name.replace('c.lookahead_dual','rtl.lookahead_dual');ports[c.name]=rtl.exists() and rtl.stat().st_mtime>=start and rtl.read_bytes()==c.read_bytes()
 rpt=sim/'verilog/lookahead_dual.performance.result.transaction.xml'
 result=dict(returncode=r.returncode,events=re.findall(r'LA_EVENT[^\n]+',log),active_cycles=list(map(int,m.groups())) if m else None,rtl_result_ports_match_c=ports,cycles=[int(v) for v in re.findall(r'transaction\s+\d+:\s+(\d+)',rpt.read_text())] if rpt.exists() else [],evidence_type='fpga_rtl_functional',status='passed' if r.returncode==0 and m and int(m[3])>0 and len(ports)==2 and all(ports.values()) else 'failed')
 (o/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return result['status']!='passed'
if __name__=='__main__':raise SystemExit(main())
