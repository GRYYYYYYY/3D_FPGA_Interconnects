"""Extract actual text-report evidence; does not waive checks or infer hardware speed."""
from pathlib import Path
import re,json,sys
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_20261114'
def timing(path):
 s=path.read_text();part=s[s.index('Design Timing Summary'):];row=next(line.split() for line in part.splitlines() if re.match(r'^\s*-?\d+\.\d+\s+-?\d+\.\d+\s+\d+',line))
 assert len(row)==12,row
 checks={k:int(n) for k,n in re.findall(r'checking ([a-z_]+) \((\d+)\)',s)}
 return {'report':str(path),'WNS_ns':float(row[0]),'TNS_ns':float(row[1]),'setup_failing_endpoints':int(row[2]),'WHS_ns':float(row[4]),'hold_failing_endpoints':int(row[6]),'WPWS_ns':float(row[8]),'pulse_failing_endpoints':int(row[10]),'check_timing_counts':checks,'all_setup_hold_pulse_and_coverage_pass':float(row[0])>=0 and float(row[4])>=0 and float(row[8])>=0 and all(n==0 for n in checks.values())}
def main():
 value={}
 for n in ['a','b','c','d','e']:
  p=R/('front_ooc_'+n);terminal=p/('final_terminal.json' if (p/'final_terminal.json').exists() else 'terminal.json');x={'terminal':json.loads(terminal.read_text())['terminal_status'] if terminal.exists() else 'RUNNING'}
  for kind in ['synth','route']:
   f=p/('timing_'+kind+'.rpt')
   if f.exists():x[kind]=timing(f)
  value[n]=x
 (R/'front_analysis_a/timing_status.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
if __name__=='__main__':main()
