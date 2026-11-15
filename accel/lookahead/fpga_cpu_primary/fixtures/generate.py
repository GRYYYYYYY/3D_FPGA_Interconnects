#!/usr/bin/env python3
"""Independent workload parser -> sparse runtime memory; golden never enters input.

The C++ validator separately uses the production Graph/packed descriptor code.
Only the two bound native small graphs are generated; no model/RTL is executed.
"""
from pathlib import Path
import argparse,hashlib,json,struct
ROOT=Path(__file__).resolve().parents[4]
OLD=ROOT.parent/'3D_FPGA_Interconnects_LOCAL_FABRIC/results/fpga_local_fabric_20261115/model_d'
FIELDS=['magic','version','nodes','prepared_edges','costs','cells','jobs','groups','row_base_line','edge_base_line','meta_base_line','meta_stride_lines','descriptor_base_line','descriptor_stride_lines','label_base_line','scratch_base_line','output_base_line','output_stride_lines','cost_base_line','maximum_line','port_rows','descriptor_bytes']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def align(n,k=32):return (n+k-1)&~(k-1)
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def parse(path):
 data=path.read_bytes();head=struct.unpack_from('<7Q',data);magic,n,e,j,c,z,g=head;assert magic==0x31414c5443495254
 pos=56
 def records(fmt,count):
  nonlocal pos
  st=struct.Struct('<'+fmt);out=[st.unpack_from(data,pos+i*st.size)for i in range(count)];pos+=st.size*count;return out
 row=[x[0]for x in records('Q',n+1)];nodes=records('IIIi',n);edges=records('II',e);costs=records('II',c);jobs=records('6I',j);cells=[x[0]for x in records('i',j*n)];embedded_golden=records('II',j*z)
 assert pos==len(data)and row[0]==0 and row[-1]==e
 return {'header':head,'row':row,'nodes':nodes,'edges':edges,'costs':costs,'jobs':jobs,'cells':cells,'embedded_golden':embedded_golden}
def case(name,spec,out):
 workload=Path(spec['workload']);golden=Path(spec['golden']);assert sha(workload)==spec['workload_sha256']and sha(golden)==spec['golden_sha256'];w=parse(workload);_,n,rawedges,j,c,z,groups=w['header'];assert n<=4194304 and z<=32768 and c<=16
 row=[];edge=[]
 for src,a in enumerate(w['nodes']):
  row.append(len(edge))
  for ei in range(w['row'][src],w['row'][src+1]):
   dst=w['edges'][ei][0];b=w['nodes'][dst]
   if not b[2]or(a[3]>=0 and b[3]>=0 and a[3]!=b[3]):continue
   if b[0]==2:break
   assert b[1]<c and b[1]<16 and dst<n
   edge.append(dst|(b[1]<<28))
 row.append(len(edge));assert max(row[i+1]-row[i]for i in range(n))<=65535
 edgebase=align((n+1+3)//4);metabase=align(edgebase+(len(edge)+7)//8);metastride=align((n+3)//4);dbase=align(metabase+j*metastride);dstride=align((n+3)//4);labelbase=dbase+j*dstride;scratchbase=align(labelbase+(n+3)//4);outputbase=align(scratchbase+(n+3)//4);ostride=align((z+3)//4);costbase=align(outputbase+j*ostride);maxline=costbase+(c+3)//4-1
 cfg=dict(zip(FIELDS,[0x43504631,1,n,len(edge),c,z,j,groups,0,edgebase,metabase,metastride,dbase,dstride,labelbase,scratchbase,outputbase,ostride,costbase,maxline,maxline//32+1,8]));assert maxline<2**32
 out.mkdir();inp=out/'input';val=out/'validation';inp.mkdir();val.mkdir();mem={};regions=[]
 def install(base,values,bits,region):
  lanes=256//bits;length=(len(values)+lanes-1)//lanes
  for i in range(length):
   addr=base+i;assert addr not in mem;mem[addr]=sum(x<<(bits*k)for k,x in enumerate(values[i*lanes:(i+1)*lanes]))
  regions.append({'name':region,'base_line':base,'lines':length,'element_bits':bits,'elements':len(values)})
 install(0,row,64,'prepared_CSR_rows');install(edgebase,edge,32,'prepared_edges');install(costbase,[(d<<32)|cc for d,cc in w['costs']],64,'FP32_cost_pairs')
 samples=[]
 for q in range(j):
  desc=[];targets=set();target_nodes=[]
  for node in range(n):
   cell=w['cells'][q*n+node];valid=w['nodes'][node][0]==1 and cell>=0
   assert -1<=cell<z
   if valid:targets.add(cell);target_nodes.append({'node':node,'cell':cell,'degree':row[node+1]-row[node]})
   desc.append(row[node]|((row[node+1]-row[node])<<32)|((cell if valid else 0)<<48)|(int(valid)<<63))
  install(dbase+q*dstride,desc,64,f'descriptor_sample_{q}')
  entry={'sample':q,'source_node':w['jobs'][q][0],'target_count':len(targets),'seed_required':bool(targets),'descriptor_base_line':dbase+q*dstride,'output_base_line':outputbase+q*ostride,'target_nodes':target_nodes,'job':dict(zip(['source','group','ordinal','layer','segment','channel'],w['jobs'][q]))}
  assert entry['source_node']<n;samples.append(entry)
 dump(out/'config.json',{'schema':'CPU_PRIMARY_FIXTURE_V1','case':name,'config_fields':FIELDS,**cfg,'raw_edges':rawedges,'samples':samples,'input_regions':regions,'reserved_unloaded_regions':[{'name':'legacy_META_not_used_by_L1','base_line':metabase,'lines':j*metastride},{'name':'canonical_DUT_initializes','base_line':labelbase,'lines':(n+3)//4},{'name':'scratch_DUT_writes_before_read','base_line':scratchbase,'lines':(n+3)//4},{'name':'output_DUT_exports','base_line':outputbase,'lines':j*ostride}]})
 (out/'config.hex').write_text(''.join(f'{cfg[k]:08x}\n'for k in FIELDS));(out/'samples.hex').write_text(''.join(f'{q:08x}{s["target_count"]:08x}{s["source_node"]:08x}{int(s["seed_required"]):08x}\n'for q,s in enumerate(samples)))
 for port in range(32):
  rows=[(a>>5,d)for a,d in sorted(mem.items())if a&31==port]
  (inp/f'port_{port:02d}.hex').write_text(''.join(f'@{a:08x}\n{d:064x}\n'for a,d in rows))
  (inp/f'port_{port:02d}_valid.hex').write_text(''.join(f'@{a:08x}\n1\n'for a,d in rows))
 (inp/'lines.txt').write_text(''.join(f'{a:08x} {d:064x}\n'for a,d in sorted(mem.items())))
 # Expected data is deliberately produced after the entire input memory map.
 gd=golden.read_bytes();assert len(gd)==j*z*8;(val/'output.bin').write_bytes(gd)
 pairs=[]
 for q in range(j):
  sample=[(d<<32)|cc for d,cc in struct.iter_unpack('<II',gd[q*z*8:(q+1)*z*8])];pairs.extend(sample)
  (val/f'sample_{q}_pairs.hex').write_text(''.join(f'{x:016x}\n'for x in sample));padded=sample+[0x7fc000007fc00000]*((-z)%4)
  (val/f'sample_{q}_beats.hex').write_text(''.join(f'{sum(x<<(k*64)for k,x in enumerate(padded[i:i+4])):064x}\n'for i in range(0,len(padded),4)))
 (val/'all_pairs.hex').write_text(''.join(f'{x:016x}\n'for x in pairs))
 diag=[]
 for q in range(j):
  path=OLD/'runs/L1'/name/f'sample_{q}/finite.json';f=json.loads(path.read_text());diag.append({'sample':q,'historic_scope':'L1 finite model, not new complete-core RTL','source_sha256':sha(path),'cycles':f['cycles'],'waves':f['waves'],'parents':f['parents'],'candidates':f['candidates'],'events':f['events'],'spills':f['spills'],'same_word_stalls':sum(b['word_stalls']for b in f['bank_stats']),'candidate_input_peak':max(b['input_candidate_peak']for b in f['bank_stats']),'K8_peak':max(b['tx_peak']for b in f['bank_stats'])})
 dump(out/'coverage_sources.json',{'samples':diag,'intrinsic_boundaries':{'nodes_mod4':n%4,'cells_mod4':z%4,'costs_mod4':c%4,'samples_without_targets':[s['sample']for s in samples if not s['target_count']],'zero_degree_nodes':sum(row[i]==row[i+1]for i in range(n))},'not_proven_by_these_graphs':['full8192 directory membership','maximum scratch spill IDs','highest legal32-bit external line','core config overflow rejection'],'recommended_integration_stress':'same full top, deterministic external request backpressure and held OOO returns; compare all outputs; use prior local capacity tests plus new core admission negatives'})
 return {'case':name,'workload':str(workload),'workload_sha256':sha(workload),'golden_validation_only':str(golden),'golden_sha256':sha(golden),'jobs':j,'nodes':n,'prepared_edges':len(edge),'cells':z,'port_rows':cfg['port_rows'],'input_lines':len(mem),'files':{str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()}}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);binding=json.loads((OLD/'binding.json').read_text());cases=[case(n,binding['inputs'][n],a.out/n)for n in ['native_d3_w8','native_d4_w8']]
 dump(a.out/'manifest.json',{'schema':'CPU_PRIMARY_FIXTURE_V1','base':'3c7f96e6037030949b729240977c2ced373843c6','generator_sha256':sha(Path(__file__)),'old_binding_sha256':sha(OLD/'binding.json'),'input_contract':'32B physical lines, port=line&31, local_index=line>>5; input map includes only prepared rows/edges/descriptors/costs; canonical/scratch/output absent until DUT writes','golden_drives_hardware':False,'cases':cases});print(json.dumps([{k:x[k]for k in ['case','jobs','nodes','prepared_edges','cells','port_rows','input_lines']}for x in cases],indent=2))
if __name__=='__main__':main()
