"""Select contiguous native parent windows; never concatenate/repeat parents."""
from run_profile import *
import struct

def main():
 out=R/'front_stress_b';out.mkdir(exist_ok=False);binding=json.loads((R/'profile_a/reused_binding.json').read_text());rows=[]
 for old in binding['input_receipts']:
  case=Path(old['command'][3]).name
  if case not in ['bnn_export','lstm_s2']:continue
  source=max((R/'front_b'/case).glob('wave_*.bin'),key=lambda p:p.stat().st_size);data=source.read_bytes();h=list(struct.unpack_from('<8Q',data));off=64+h[4]*32;parents=[]
  for i in range(h[5]):
   n,d,pair=struct.unpack_from('<IIQ',data,off);size=16+d*12;parents.append((n,d,data[off:off+size]));off+=size
  size=min(128,len(parents));scores=[int(0<d<=9)+int(n%4==3) for n,d,_ in parents];score=sum(scores[:size]);best=(score,0)
  for start in range(1,len(parents)-size+1):
   score+=scores[start+size-1]-scores[start-1]
   if score>best[0]:best=(score,start)
  selected=parents[best[1]:best[1]+size];h[4]=0;h[5]=size;h[6]=sum(x[1] for x in selected);h[7]=0;p=out/(case+'.bin');p.write_bytes(struct.pack('<8Q',*h)+b''.join(x[2] for x in selected))
  selection={'source':str(source),'source_sha256':sha(source),'contiguous_parent_begin':best[1],'contiguous_parent_end':best[1]+size,'score':best[0],'trace_sha256':sha(p),'criterion':'nonempty degree<=9 plus row two-line boundary; preserve original contiguous order'};(out/(case+'_selection.json')).write_text(json.dumps(selection,indent=2))
  for mode in 'ABC':
   cmd=[str(R/'front_b/front'),old['command'][1],str(p),mode,str(out/(case+'_'+mode+'.json')),'jitter'];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
   with (out/(case+'_'+mode+'.log')).open('x') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
   x={'command':cmd,'returncode':rc,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'binary_sha256':sha(R/'front_b/front'),'trace_sha256':sha(p)};rows.append(x)
 (out/'terminal.json').write_text(json.dumps({'all_pass':all(x['returncode']==0 for x in rows),'results':rows},indent=2));assert all(x['returncode']==0 for x in rows)
if __name__=='__main__':main()
