"""Validate one fixed 125 MHz STA recheck of an unchanged routed R4 netlist.

This certifies constrained internal OOC paths, not AXI system integration, board
clocking or physical HBM timing. Original 200 MHz failures are preserved.
"""
import argparse,json,re
from pathlib import Path
from prepare import sha256
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--hls',type=Path,required=True);p.add_argument('--recheck',type=Path,required=True);a=p.parse_args();h=a.hls.resolve();o=a.recheck.resolve();text=(o/'timing_summary.rpt').read_text();lines=text.splitlines();slack=None
 for i,line in enumerate(lines):
  if 'WNS(ns)' in line and 'WHS(ns)' in line:
   for row in lines[i+1:i+5]:
    fields=row.split()
    if len(fields)==12:
     try:slack=dict(setup=float(fields[0]),hold=float(fields[4]),pulse=float(fields[8]));break
     except ValueError:pass
   break
 checks={k:int(v) for k,v in re.findall(r'checking ([a-z_]+) \((\d+)\)',text)}
 clock=re.search(r'^ap_clk\s+\{0\.000\s+4\.000\}\s+8\.000\s+125\.000',text,re.M)
 assert clock and slack and min(slack.values())>=0 and checks['no_clock']==0 and checks['unconstrained_internal_endpoints']==0
 assert 'All user specified timing constraints are met.' in text
 original=h/'project/solution/impl/verilog/project.runs/impl_1/bd_0_wrapper_routed.dcp';frozen=o/'design_125mhz.dcp';assert original.exists() and frozen.exists()
 result=dict(status='passed_internal_OOC',verified_mhz=125,period_ns=8,slack_ns=slack,constraint_checks=checks,
  method='One predeclared conservative clock recheck; same placed/routed netlist, no datapath change and no frequency sweep. No inferred Fmax from negative slack.',
  limitations=['Only constrained internal OOC paths; unconstrained external I/O delays are listed explicitly.','OOC clock port has no integrated HD.CLK_SRC; system clock insertion/skew and AXI integration remain unverified.','Not board timing or calibrated memory timing.'],
  original_200mhz_routed_dcp=str(original),original_dcp_sha256=sha256(original),rechecked_dcp_sha256=sha256(frozen),binding_sha256=sha256(h/'binding.json'),
  reports={f.name:sha256(f) for f in o.iterdir() if f.suffix in ['.rpt','.tcl','.xdc']})
 target=o/'result.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n');print(slack)
if __name__=='__main__':main()
