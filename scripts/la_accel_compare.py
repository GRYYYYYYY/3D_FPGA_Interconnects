"""Verify compact sample and original-order group maps bitwise; never compare unlike timing scopes."""
import argparse,json,struct
from pathlib import Path
from prepare import sha256
import numpy as np
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workload',type=Path,required=True);p.add_argument('--actual',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();a.output.mkdir(parents=True)
 with a.workload.open('rb') as f:h=struct.unpack('<7Q',f.read(56))
 _,n,e,j,k,c,g=h;job_offset=56+(n+1)*8+n*16+e*8+k*8;gold_offset=job_offset+j*24+j*n*4
 jobs=np.memmap(a.workload,dtype='<u4',mode='r',offset=job_offset,shape=(j,6));gold=np.memmap(a.workload,dtype='<u4',mode='r',offset=gold_offset,shape=(j,c,2));actual=np.fromfile(a.actual,dtype='<u4');size_ok=actual.size==j*c*2
 result=dict(schema_version='la_accel_v1',semantic_mode='STRICT_FP32',workload_sha256=sha256(a.workload),output_sha256=sha256(a.actual),matches_reference=False)
 if size_ok:
  actual=actual.reshape(j,c,2);diff=np.argwhere(actual!=gold);result.update(matches_reference=len(diff)==0,first_mismatch=diff[0].tolist() if len(diff) else None)
  merged=np.full((g,c,2),0x7fc00000,dtype='<u4');mf=merged.view('<f4');af=actual.view('<f4')
  for q in range(j):
   group=jobs[q,1];take=np.isnan(mf[group,:,0])|(af[q,:,0]<mf[group,:,0]);take &= ~np.isnan(af[q,:,0]);merged[group,take]=actual[q,take]
  merged.tofile(a.output/'groups.bin');native=Path(str(a.workload)+'.groups.bin')
  result['groups_match_native']=native.exists() and sha256(native)==sha256(a.output/'groups.bin')
 else:result['failure_reason']='size_mismatch'
 (a.output/'comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return 0 if result['matches_reference'] else 1
if __name__=='__main__':raise SystemExit(main())
