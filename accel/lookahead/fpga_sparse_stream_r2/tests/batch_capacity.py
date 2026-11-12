from pathlib import Path
import struct,subprocess,json,hashlib,sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';v=sys.argv[1] if len(sys.argv)>1 else 'm2c';exe='Vr2_many_tile' if v.startswith('many') else 'Vr2_external_tile' if v.startswith('external') else 'Vsparse_tile';out=r/'rtl'/f'{v}_batch_capacity';out.mkdir(exist_ok=False)
for name,n,cells,jobs,target in [('max_node_max_cell_q40',4096,32768,40,True),('partial_line_missing_q40',1,25538,40,False)]:
 d=out/name;d.mkdir();w=d/'workload.bin';mapping=[]
 for q in range(jobs):mapping.extend([-1]*(n-1)+[cells-1 if q%2==0 else 0])
 with w.open('wb') as f:
  f.write(struct.pack('<7Q',0x31414c5443495254,n,0,jobs,1,cells,1));f.write(struct.pack('<%dQ'%(n+1),*([0]*(n+1))))
  for i in range(n):f.write(struct.pack('<IIIi',1 if target and i==n-1 else 0,0,1,-1))
  f.write(struct.pack('<2f',0,0))
  for q in range(jobs):f.write(struct.pack('<6I',n-1,0,q,0,0,0))
  f.write(struct.pack('<%di'%len(mapping),*mapping));f.write(struct.pack('<%dI'%(cells*jobs*2),*([0x7fc00000]*(cells*jobs*2))))
 cmds=[[str(r/'semantics/original_ALT'),str(w),str(d/'original_ALT.bin')],[str(r/'semantics/reference_pop_reduce'),str(w),str(d/'original_ALT.bin'),str(d/'pop'),'524288','524288'],[str(r/f'rtl/{v}_build/{exe}'),str(w),str(d/'pop/prepared.bin'),str(d/'original_ALT.bin'),str(d/'rtl'),'60','20261112','4']]
 for i,cmd in enumerate(cmds):
  with (d/f'run{i}.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  (d/f'receipt{i}.json').write_text(json.dumps({'command':cmd,'returncode':p.returncode},indent=2))
  if p.returncode:raise RuntimeError((d/f'run{i}.log').read_text())
 h=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
 assert h(d/'rtl/output.bin')==h(d/'original_ALT.bin')
 print(name,'PASS',flush=True)
