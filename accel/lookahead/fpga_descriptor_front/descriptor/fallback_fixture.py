"""Whole-graph16B selection, eligible break and zero/duplicate/invalid targets."""
from pathlib import Path
import hashlib,json,struct,subprocess,datetime
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_descriptor_front_20261114';D=R/'descriptor_a';O=R/'descriptor_fallback_a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);nodes=[(0,0,1,-1),(1,1,1,-1),(1,2,1,-1),(1,1,1,-1),(1,1,1,-1),(2,0,1,-1)]
 dst=[1]*65536+[2,3,5,4];row=[0]+[len(dst)]*6;cost=[(0.,0.),(1.,2.),(1.,1.)];jobs=[(0,0,0,0,0,0),(1,0,1,0,0,0)];cell=[-1,0,0,-1,1,-1]*2
 missing=struct.pack('<II',0x7fc00000,0x7fc00000);gold=struct.pack('<ff',1.,1.)+missing+struct.pack('<ff',0.,0.)+missing
 header=struct.pack('<7Q',0x31414c5443495254,6,len(dst),2,3,2,1)
 data=header+struct.pack('<7Q',*row)+b''.join(struct.pack('<IIIi',*n) for n in nodes)+b''.join(struct.pack('<II',v,0) for v in dst)+b''.join(struct.pack('<ff',*c) for c in cost)+b''.join(struct.pack('<6I',*j) for j in jobs)+struct.pack('<12i',*cell)+gold
 workload=O/'workload.bin';workload.write_bytes(data);(O/'golden.bin').write_bytes(gold)
 commands=[[str(D/'bin/convert'),str(workload),str(O/'converted')],[str(D/'bin/cpu'),str(workload),str(O/'golden.bin'),str(O/'converted'),'16','1','1','1',str(O/'cpu'),'fallback_functional']]
 rows=[]
 for i,cmd in enumerate(commands):
  with (O/f'command_{i}.log').open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);(O/f'command_{i}.running.json').write_text(json.dumps({'pid':p.pid,'command':cmd}));rc=p.wait()
  rows.append({'command':cmd,'returncode':rc});assert rc==0
 a=json.loads((O/'converted/admission.json').read_text());assert a['max_degree']==65538 and a['actual_format_bytes']==a['selected_format_bytes']==16
 assert a['raw_terminal_breaks']==1 and a['raw_unvisited_after_break']==1
 assert (O/'cpu/output.bin').read_bytes()==gold
 cmd=[str(D/'bin/convert'),str(workload),str(O/'rejected_force8'),'8']
 with (O/'rejected_force8.log').open('x') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
 assert rc!=0 and 'FORMAT_OVERRIDE' in (O/'rejected_force8.log').read_text()
 d={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','commands':rows,'mandatory16_graph_degree':65538,'fallback_output_exact':True,'force8_explicit_rejection':{'command':cmd,'returncode':rc},'scenarios':['65536+ degree wholegraph fallback','eligible SINK break preserves order and skips following eligible node','zero-degree valid IPIN','duplicate target cell with equal delay/congestion tiebreak','invalid-target IPIN still expands/retire','source-is-target','unreachable valid target preserves missing'],'workload_sha256':sha(workload),'output_sha256':sha(O/'cpu/output.bin'),'golden_sha256':sha(O/'golden.bin'),'binary_binding_sha256':sha(D/'binding.json')}
 (O/'receipt.json').write_text(json.dumps(d,indent=2)+'\n');print('FALLBACK_GRAPH_PASS')
if __name__=='__main__':main()
