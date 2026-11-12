from pathlib import Path
from array import array
import struct,subprocess,json,sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';n=int(sys.argv[1]);d=r/'semantics'/f'external_nodes_{n}';d.mkdir(exist_ok=False)
# Long-address nodes spread over all owners; duplicate destinations, repeated
# wave entries, zero-outdegree targets, two targets folding to the same cell.
ids=sorted(set([0,31,32,4095,4096,8193,n-33,n-2,n-1]))
adj={ids[0]:ids[1:]+[ids[1]],ids[1]:[ids[2],ids[-1]],ids[2]:[ids[3],ids[-2]],ids[3]:[ids[-1]]}
row=array('Q',[0])*(n+1);e=[]
for u in range(n):e.extend(adj.get(u,[]));row[u+1]=len(e)
with (d/'workload.bin').open('wb') as f:
 f.write(struct.pack('<7Q',0x31414c5443495254,n,len(e),1,3,32768,1));row.tofile(f)
 for u in range(n):f.write(struct.pack('<IIIi',1 if u in ids[-2:] else 0,1 if u==ids[-1] else 2 if u==ids[-2] else 0,1,-1))
 for v in e:f.write(struct.pack('<II',v,0))
 f.write(struct.pack('<6f',0,0,1,2,1,1));f.write(struct.pack('<6I',0,0,0,0,0,0))
 cells=array('i',[-1])*n;cells[ids[-1]]=32767;cells[ids[-2]]=32767;cells.tofile(f);array('I',[0x7fc00000])*(32768*2)
 array('I',[0x7fc00000]*65536).tofile(f)
cmds=[[str(r/'semantics/original_ALT'),str(d/'workload.bin'),str(d/'original_ALT.bin')],[str(r/'semantics/reference_pop_reduce'),str(d/'workload.bin'),str(d/'original_ALT.bin'),str(d/'pop'),'524288','524288']]
for i,cmd in enumerate(cmds):
 with (d/f'prepare{i}.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 (d/f'receipt{i}.json').write_text(json.dumps({'command':cmd,'returncode':p.returncode},indent=2));assert p.returncode==0
(d/'contract.json').write_text(json.dumps({'nodes':n,'active_ids':ids,'actual_full_external_initialization':True,'intended_output':'cell32767 whole-pair (1,1); all others missing','not_native_BNN_LSTM':True},indent=2))
print('PREPARED',d)
