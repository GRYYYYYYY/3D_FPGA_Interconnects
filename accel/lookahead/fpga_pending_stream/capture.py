from pathlib import Path
import concurrent.futures,datetime,hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[3];S=ROOT/'accel/lookahead/fpga_pending_stream';R=ROOT/'results/fpga_pending_stream_20261114'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 out=R/'capture_a';out.mkdir(exist_ok=False)
 cmd=['g++','-O3','-std=c++17','-ffp-contract=off','-DPROFILE_PRIVATE_INF=1','-I'+str(ROOT/'accel/lookahead/include'),'-I'+str(ROOT/'accel/lookahead/round6_1'),'-I'+str(ROOT/'accel/lookahead/fpga_sparse_stream_r2'),str(S/'capture_reference.cpp'),'-o',str(out/'capture')]
 with (out/'build.log').open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 selection=json.loads((R/'stage_a_v2/representative_selection.json').read_text());binding=json.loads((R/'stage_a_v2/binding.json').read_text())
 def run(old):
  case=Path(old['command'][3]).name;d=out/case;d.mkdir();selected=selection.get(case,{'waves':[{'sample':0,'wave':x} for x in range(1,300)]})['waves'];p=d/'selected.txt';p.write_text(''.join(f"{x['sample']} {x['wave']}\n" for x in selected))
  env=os.environ.copy();env['PENDING_STREAM_SELECTION']=str(p)
  cmd=[str(out/'capture'),*old['command'][1:3],str(d),*old['command'][4:]]
  with (d/'console.log').open('x') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
   identity={'pid':proc.pid,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'executable_sha256':sha(out/'capture'),'selection':selected};(d/'running.json').write_text(json.dumps(identity,indent=2));rc=proc.wait()
  assert rc==0,(case,rc);assert sha(d/'output.bin')==old['output_sha256']
  identity.update(returncode=rc,output_exact=True,trace_sha256={p.name:sha(p) for p in d.glob('wave_*.bin')},scope='new native wave capture with unchanged ALT oracle; not GPU rerun or hardware timing')
  (d/'receipt.json').write_text(json.dumps(identity,indent=2));return identity
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,binding['input_receipts']))
 (out/'terminal.json').write_text(json.dumps({'all_pass':True,'results':results},indent=2))
if __name__=='__main__':main()
