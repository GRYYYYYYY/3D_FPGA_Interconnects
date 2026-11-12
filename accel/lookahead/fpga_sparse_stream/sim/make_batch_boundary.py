from pathlib import Path
import struct,json
root=Path(__file__).resolve().parents[4];run=root/'results/fpga_sparse_stream_20261112'
for jobs in [64,65]:
 out=run/f'batch{jobs}';out.mkdir(exist_ok=True)
 with (out/'workload.bin').open('wb') as f:
  f.write(struct.pack('<7Q',0x31414c5443495254,2,1,jobs,2,1,1))
  f.write(struct.pack('<3Q',0,1,1))
  f.write(struct.pack('<8i',0,0,1,-1,1,1,1,-1))
  f.write(struct.pack('<2I',1,0));f.write(struct.pack('<4f',0,0,1,0))
  for q in range(jobs):f.write(struct.pack('<6I',0,0,0,0,0,0))
  f.write(struct.pack('<'+str(2*jobs)+'i',*([-1,0]*jobs)))
  f.write(struct.pack('<'+str(2*jobs)+'I',*([0x7fc00000]*(2*jobs))))
 (out/'contract.json').write_text(json.dumps({'jobs':jobs,'expected':'complete output retained across all64 samples' if jobs==64 else 'wrapper admission rejection, no output published'},indent=2))
