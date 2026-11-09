"""Independent Python / C++ byte and immutable path-version witness checks."""
import sys, json, subprocess, struct, inspect, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'accel/lookahead/round6'))
import python_reference as ref
import probe_io as m
# Add output collection to an in-memory analysis copy, leave the oracle unchanged.
s=inspect.getsource(ref.run).replace('stats=[];diff=[0,0]','stats=[];diff=[0,0];encoded=[]').replace('  stats.append(', '  encoded.append(enc)\n  stats.append(').replace('return dict(delay_word_differences=', 'return dict(encoded=b"".join(encoded),delay_word_differences=')
exec(s,ref.__dict__)
o=Path(sys.argv[1]);o.mkdir(exist_ok=True,parents=True);exe=sys.argv[2]
paths=[]
for case,rd in [('native_d3_w8','round3_20261108T141500Z'),('native_d4_w8','round3_20261108T141500Z'),('native_d5_w8','round4_20261108T182500Z'),('native_d6_w8','round5_20261109T054024Z'),('native_d8_w8','round5_20261109T054024Z'),('native_d6_w8_l1','round5_20261109T054024Z')]:paths.append(ROOT/f'results/lookahead_accel_{rd}/evidence_snapshot/{case}/workload.bin')
paths+=sorted((ROOT/'results/lookahead_accel_round4_20261108T182500Z/evidence_snapshot/semantic_fixtures').glob('*.bin'))
records=[]
for path in paths:
 w=m.Workload(path);name=path.parent.name if path.name=='workload.bin' else path.stem
 for shift in [0,20]:
  expected=ref.run(w,shift);out=o/(name+f'_s{shift}.bin');cmd=[exe,str(path),str(shift),'1','1',str(out),'2'];p=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
  (o/(name+f'_s{shift}.log')).write_text(p.stdout+p.stderr)
  assert p.returncode==0,(name,p.stdout,p.stderr)
  assert out.read_bytes()==expected['encoded'],(name,shift,'C++/Python mismatch')
  rows=[json.loads(x) for x in p.stdout.splitlines()];profiles=[x for x in rows if x['kind']=='profile'];checked=0
  for q,z in enumerate(profiles):
   witnesses=z['witness']
   for i,(parent,v,db,cb) in enumerate(witnesses):
    if i==0:assert (v,db,cb)==(w.jobs[q][0],0,0);continue
    assert parent<i
    _,u,pd,pc=witnesses[parent];a=struct.unpack('<f',struct.pack('<I',pd))[0];b=struct.unpack('<f',struct.pack('<I',pc))[0];cost=w.costs[w.nodes[v][1]]
    assert struct.pack('<ff',m.f32(a+cost[0]),m.f32(b+cost[1]))==struct.pack('<II',db,cb)
    eligible=[]
    for k in range(w.row[u],w.row[u+1]):
     dst=w.edges[k][0];e=m.eligibility(w.nodes[u],w.nodes[dst])
     if e<0:break
     if e>0:eligible.append(dst)
    assert v in eligible;checked+=1
   # Every reported output pair belongs to an immutable version of an IPIN in its cell.
   pairs={(w.cells[q*w.n+v],db,cb) for _,v,db,cb in witnesses if w.nodes[v][0]==1}
   for c,(db,cb) in enumerate(struct.iter_unpack('<II',expected['encoded'][q*w.c*8:(q+1)*w.c*8])):
    if db!=0x7fc00000:assert (c,db,cb) in pairs
  records.append(dict(case=name,shift=shift,input_sha256=w.sha256,output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),cpp_python_bytes_equal=True,witness_versions_checked=checked,batch=rows[0],raw=sum(z['raw'] for z in profiles),eligible=sum(z['eligible'] for z in profiles)))
  # Full witnesses retained for the directed fixtures; random/native logs compressed at archive time.
 (o/'validation.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(dict(configurations=len(records),all_cpp_python_match=True,native_differences=[{k:r[k] for k in ['case','shift','batch']} for r in records if r['batch']['delay_diff'] or r['batch']['congestion_diff']])))
