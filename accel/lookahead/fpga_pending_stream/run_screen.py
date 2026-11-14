from pathlib import Path
import concurrent.futures,hashlib,json,subprocess,datetime,os
ROOT=Path(__file__).resolve().parents[3];S=ROOT/'accel/lookahead/fpga_pending_stream';R=ROOT/'results/fpga_pending_stream_20261114'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'screen_a';out.mkdir(exist_ok=False)
 cmd=['g++','-O3','-std=c++17','-Wall','-Wextra','-I'+str(ROOT/'accel/lookahead/fpga_sparse_stream_r2'),str(S/'screen.cpp'),'-o',str(out/'screen')]
 with (out/'build.log').open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 capture=json.loads((R/'capture_a/terminal.json').read_text());assert capture['all_pass']
 # For small graphs select all waves; large workload selection is native, never concatenated.
 tasks=[]
 for row in capture['results']:
  case=Path(row['command'][3]).name
  for trace in sorted((R/'capture_a'/case).glob('wave_*.bin')):
   for k,stream in [(1,0),(8,0),(8,1),(16,0),(16,1)]:tasks.append((case,trace,k,stream,0,0))
 # Fixed-seed-equivalent deterministic jitter and sustained token backpressure.
 for case in ['native_d3_w8','native_d4_w8']:
  for trace in sorted((R/'capture_a'/case).glob('wave_*.bin')):
   tasks.append((case,trace,16,1,1,256))
 def run(t):
  case,trace,k,stream,jitter,block=t;d=out/case;d.mkdir(exist_ok=True);name=f'{trace.stem}_k{k}_s{stream}_j{jitter}_b{block}';p=d/name
  cmd=[str(out/'screen'),str(trace),str(k),str(stream),str(p),str(jitter),str(block)]
  with p.with_suffix('.log').open('x') as f:
   proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT)
   p.with_suffix('.running.json').write_text(json.dumps({'pid':proc.pid,'command':cmd,'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}));rc=proc.wait()
  receipt={'command':cmd,'returncode':rc,'trace_sha256':sha(trace),'binary_sha256':sha(out/'screen')}
  p.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2));return receipt
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(run,tasks))
 (out/'terminal.json').write_text(json.dumps({'all_pass':all(x['returncode']==0 for x in rows),'results':rows,'source_sha256':sha(S/'screen.cpp'),'pending17_sha256':sha(ROOT/'accel/lookahead/fpga_sparse_stream_r2/pending17.hpp')},indent=2));assert all(x['returncode']==0 for x in rows)
 print('SCREEN_SUITE_PASS',len(rows))
if __name__=='__main__':main()
