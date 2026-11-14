from pathlib import Path
import subprocess,datetime,json,os
R=Path(__file__).resolve().parents[4]/'results/fpga_enum_commit_20261114/front_offset_bounds_b'
def main():
 env=dict(os.environ);env['PATH']='/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin:'+env['PATH'];rows=[]
 for name in ['compile.sh','elaborate.sh','simulate.sh']:
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  with (R/(name+'.console.log')).open('x') as f:rc=subprocess.run(['bash',name],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
  rows.append({'command':['bash',name],'returncode':rc,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});(R/'receipts.json').write_text(json.dumps(rows,indent=2));assert rc==0
 text=(R/'simulate.log').read_text();assert 'TEST_PASS offset_bounds legal32_max_and_upper32_rejection' in text and 'Fatal:' not in text;print('OFFSET_DOMAIN_PASS')
if __name__=='__main__':main()
