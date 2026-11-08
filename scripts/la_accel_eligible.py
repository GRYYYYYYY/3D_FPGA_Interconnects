"""Compile native static edge filters into CSR while preserving duplicates, order and SINK truncation."""
import argparse,struct,json
from pathlib import Path
import numpy as np
from prepare import sha256
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workload',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 with a.workload.open('rb') as f:header=list(struct.unpack('<7Q',f.read(56)))
 _,n,e,j,k,c,g=header
 row=np.memmap(a.workload,mode='r',dtype='<u8',offset=56,shape=(n+1,));nodes=np.memmap(a.workload,mode='r',dtype='<i4',offset=56+(n+1)*8,shape=(n,4));edge_offset=56+(n+1)*8+n*16;edges=np.memmap(a.workload,mode='r',dtype='<u4',offset=edge_offset,shape=(e,2))
 newrow=np.zeros(n+1,dtype='<u8');keep=np.zeros(e,dtype=bool)
 for u in range(n):
  start,end=int(row[u]),int(row[u+1]);child=nodes[edges[start:end,0]];valid=(child[:,2]!=0)&~((nodes[u,3]>=0)&(child[:,3]>=0)&(nodes[u,3]!=child[:,3]));sinks=np.flatnonzero(valid&(child[:,0]==2));
  if len(sinks):valid[sinks[0]:]=False
  keep[start:end]=valid;newrow[u+1]=newrow[u]+np.count_nonzero(valid)
 filtered=edges[keep];header[2]=len(filtered);out=a.output/'workload.bin'
 with out.open('wb') as f:
  f.write(struct.pack('<7Q',*header));newrow.tofile(f);nodes.tofile(f);filtered.tofile(f)
  with a.workload.open('rb') as src:
   src.seek(edge_offset+e*8)
   while True:
    b=src.read(8*1024*1024)
    if not b:break
    f.write(b)
 import shutil
 if Path(str(a.workload)+'.groups.bin').exists():shutil.copyfile(str(a.workload)+'.groups.bin',str(out)+'.groups.bin')
 (a.output/'manifest.json').write_text(json.dumps(dict(variant='eligible_CSR',source_sha256=sha256(a.workload),workload_sha256=sha256(out),nodes=n,original_edges=e,eligible_edges=len(filtered),semantic_mode='STRICT_FP32',golden_unchanged=True),indent=2))
if __name__=='__main__':main()
