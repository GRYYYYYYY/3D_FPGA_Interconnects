"""Audit actual A2 captures and final maps; decoder uses frozen generated schema."""
import sys,json,hashlib,struct,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();decoder=Path(sys.argv[2]).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
identities=[];diff=[]
for case in ['s38417','bnn']:
 actual=[];d=r/'native_cpu_qualification_b'
 for arm in ['alt_s0','alt_s20']:
  p=d/f'{case}_{arm}'/'native_input.bin';h=struct.unpack('<7Q',p.open('rb').read(56));cut=p.stat().st_size-h[3]*h[5]*8;dig=hashlib.sha256()
  with p.open('rb') as f:
   remain=cut
   while remain:b=f.read(min(remain,8*1024*1024));dig.update(b);remain-=len(b)
   out=hashlib.sha256(f.read()).hexdigest()
  actual.append(dict(arm=arm,header=h,input_prefix_sha256=dig.hexdigest(),output_sha256=out,path=str(p)))
 for x,y in [('alt_s0','control'),('alt_s20','control'),('alt_s20','alt_s0')]:
  cmd=[str(decoder),str(d/f'{case}_{x}'/'wire_map.bin'),str(d/f'{case}_{y}'/'wire_map.bin')];p=subprocess.run(cmd,capture_output=True,text=True,check=True);diff.append(dict(case=case,pair=x+'_vs_'+y,**json.loads(p.stdout)))
 same_input=actual[0]['input_prefix_sha256']==actual[1]['input_prefix_sha256'];assert same_input
 identities.append(dict(case=case,actual_inputs=actual,ALT20_vs_ALT0_sample_equal=actual[0]['output_sha256']==actual[1]['output_sha256'],ALT20_vs_ALT0_native_map_equal=sha(d/f'{case}_alt_s0'/'wire_map.bin')==sha(d/f'{case}_alt_s20'/'wire_map.bin'),ALT_vs_STRICT_native_map_equal=sha(d/f'{case}_alt_s20'/'wire_map.bin')==sha(d/f'{case}_control'/'wire_map.bin')))
(r/'native_cpu_identity.json').write_text(json.dumps(identities,indent=2));(r/'native_cpu_map_diff.json').write_text(json.dumps(diff,indent=2));(r/'native_map_decoder_binding.json').write_text(json.dumps(dict(executable=str(decoder),sha256=sha(decoder),source='accel/lookahead/round6/native_map_diff6.cpp',source_sha256=sha(R/'accel/lookahead/round6/native_map_diff6.cpp'),method='frozen generated CapnProto schema, dimensions and FP32 fields, six current A2 map pairs'),indent=2))
p=R/'results/lookahead_accel_20261108T125500Z/bnn_export/workload.bin';h=struct.unpack('<7Q',p.open('rb').read(56));remain=p.stat().st_size-h[3]*h[5]*8;dig=hashlib.sha256()
with p.open('rb') as f:
 while remain:b=f.read(min(remain,8*1024*1024));dig.update(b);remain-=len(b)
native=next(x for x in identities if x['case']=='bnn')['actual_inputs'][1]['input_prefix_sha256'];(r/'bnn_export_native_identity.json').write_text(json.dumps(dict(case='bnn',offline_input_prefix_sha256=dig.hexdigest(),native_input_prefix_sha256=native,equal=dig.hexdigest()==native,note='output suffix excluded; no qualification inheritance'),indent=2))
