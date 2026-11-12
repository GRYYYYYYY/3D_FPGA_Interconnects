from pathlib import Path
from array import array
import json,struct,subprocess,sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';v=sys.argv[1];d=r/'rtl'/f'{v}_external_changed_overflow';d.mkdir(exist_ok=False)
n=8192
with (d/'workload.bin').open('wb') as f:
 f.write(struct.pack('<7Q',0x31414c5443495254,n,n-1,1,2,1,1));array('Q',[0]+[n-1]*n).tofile(f)
 for i in range(n):f.write(struct.pack('<IIIi',int(i==n-1),int(i==n-1),1,-1))
 for i in range(1,n):f.write(struct.pack('<II',i,0))
 f.write(struct.pack('<4f',0,0,1,0));f.write(struct.pack('<6I',0,0,0,0,0,0));array('i',[-1]*(n-1)+[0]).tofile(f);f.write(struct.pack('<2I',0x7fc00000,0x7fc00000))
commands=[[str(r/'semantics/original_ALT'),str(d/'workload.bin'),str(d/'original_ALT.bin')],[str(r/'semantics/reference_pop_reduce'),str(d/'workload.bin'),str(d/'original_ALT.bin'),str(d/'pop'),'524288','524288'],[str(r/f'rtl/{v}_build/Vr2_external_tile'),str(d/'workload.bin'),str(d/'pop/prepared.bin'),str(d/'original_ALT.bin'),str(d/'rtl'),'120','221112','4']]
receipts=[]
for i,c in enumerate(commands):
 with (d/f'run{i}.log').open('w') as log:rc=subprocess.run(c,stdout=log,stderr=subprocess.STDOUT).returncode
 receipts.append({'command':c,'returncode':rc})
 if i<2:assert rc==0
s=(d/'run2.log').read_text();assert rc!=0 and 'DUT error' in s and 'bank=' in s and not (d/'rtl/output.bin').exists(),s
(d/'receipt.json').write_text(json.dumps({'scope':'explicit external changed capacity rejection; no output published','requests_per_owner_up_to':1024,'configured_capacity_per_owner':512,'receipts':receipts,'console':s},indent=2));print('EXPECTED_CAPACITY_REJECTION',s)
