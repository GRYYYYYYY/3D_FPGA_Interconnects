"""Independent output/source/layout receipt audit; never re-runs the algorithms."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_descriptor_front_20261114';D=R/'descriptor_a'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(8<<20),b''):h.update(x)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 b=read(D/'binding.json');terminal=read(D/'terminal.json');assert terminal['all_pass'] and terminal['native_samples']==100
 for p,h in b['source_sha256'].items():assert sha(D/'source'/p)==h,p
 for p,h in b['binary_sha256'].items():assert sha(D/'bin'/p)==h,p
 verified=0;cases={}
 for p in (D/'receipts').glob('*_conversion.json'):
  rec=read(p);assert rec['returncode']==0
  for f,h in rec['output_sha256'].items():assert sha(Path(f))==h,f
  a=rec['full_input_admission'];assert a['descriptor_bytes']==a['sample_stride_bytes']*a['samples'];assert a['raw_descriptor_bytes']==a['nodes']*a['samples']*a['actual_format_bytes']
  assert a['sample_stride_bytes']>=a['nodes']*a['actual_format_bytes'] and a['sample_stride_bytes']%1024==0
  assert a['descriptor_end_bytes_exclusive']==a['descriptor_base_bytes']+a['descriptor_bytes'];assert a['descriptor_base_bytes']>=a['preserved_old_metadata_end_bytes']
  assert a['independently_decoded_records']==a['nodes']*a['samples'];assert a['prepared_edges']<=0xffffffff and a['cells']<=32768
  assert a['selected_format_bytes']==(8 if a['max_degree']<=65535 else 16)
  assert a['actual_format_bytes']>=a['selected_format_bytes'];assert len(a['sample_admission'])==a['samples']
  for q,x in enumerate(a['sample_admission']):
   assert x['sample']==q and x['maximum_valid_cell']<min(a['cells'],32768)
   assert x['begin_byte']==a['descriptor_base_bytes']+q*a['sample_stride_bytes'];assert x['end_byte_exclusive']==x['begin_byte']+a['sample_stride_bytes']
  cases[p.name]={'nodes':a['nodes'],'samples':a['samples'],'format':a['actual_format_bytes'],'bytes':a['descriptor_bytes']}
 for p in (D/'receipts').glob('*_cpu.json'):
  rec=read(p);assert rec['returncode']==0 and rec['output_exact'];assert rec['golden_sha256']==b['inputs'][rec['case']]['golden_sha256']
  for f,h in rec['output_sha256'].items():assert sha(Path(f))==h,f
  output=Path(next(f for f in rec['output_sha256'] if f.endswith('/output.bin')));assert sha(output)==rec['golden_sha256']
  rows=read(output.parent/'samples.json');assert len(rows)==b['inputs'][rec['case']]['jobs'];verified+=len(rows)
 assert verified==120
 fallback=read(R/'descriptor_fallback_a/receipt.json');assert fallback['fallback_output_exact'] and fallback['force8_explicit_rejection']['returncode']!=0
 assert sha(R/'descriptor_fallback_a/cpu/output.bin')==fallback['output_sha256']==fallback['golden_sha256']
 for scope in ['descriptor_native_projection_a','descriptor_native_projection_targets_a']:
  rec=read(R/scope/'receipt.json')
  for case in rec.get('cases',rec.get('commands',[])):
   path=Path(case['command'][3]);assert sha(path)==case['output_sha256'];d=read(path);assert len(d['parents'])==128
   for parent in d['parents']:
    word=int(parent['desc8_hex'],16);fallback=int(parent['desc16_hex'],16)
    begin=word&0xffffffff;degree=(word>>32)&65535;cell=(word>>48)&32767;valid=bool(word>>63)
    assert begin==parent['begin'] and begin+degree==parent['end'] and cell==parent['target_cell'] and valid==parent['target_valid']
    assert fallback&0xffffffff==begin and (fallback>>32)&0xffffffff==begin+degree and (fallback>>64)&0xffffffff==cell and (fallback>>96)==int(valid)
    assert len(parent['candidates'])==degree
 d={'status':'PASS','frozen_source_and_binary_verified':True,'complete_native_samples':100,'forced_fallback_native_samples':20,'mandatory_degree65538_fallback_graph_samples':2,'checked_complete_outputs':122,'descriptor_layouts':cases,'native_projection_parents':512,'formal_CPU_timing_claimed':False}
 (D/'independent_verification.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d))
if __name__=='__main__':main()
