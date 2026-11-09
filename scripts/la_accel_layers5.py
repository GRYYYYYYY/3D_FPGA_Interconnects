"""Read node layer metadata once from existing native XML; no graph search/replay."""
import argparse,array,json,re,subprocess,time
from pathlib import Path
from prepare import sha256
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);a=p.parse_args();r=a.experiment.resolve();out=r/'profiles_layers';out.mkdir(exist_ok=False)
for w in json.loads((r/'workload_manifest.json').read_text()):
 if w['case'] not in ['tseng_export','bnn_export']:continue
 folder=Path(w['path']).parent;m=json.loads((folder/'manifest.json').read_text());cmd=m['command'];xml=Path(cmd[cmd.index('--read_rr_graph')+1]);layers=array.array('I',[0])*w['N'];seen=0;node=None
 with xml.open() as f:
  for line in f:
   hit=re.search(r'<node\s+[^>]*\bid="(\d+)"',line)
   if hit:node=int(hit[1])
   if node is not None and '<loc ' in line:
    h=re.search(r'\blayer(?:_low)?="(\d+)"',line);layers[node]=int(h[1]) if h else 0;seen+=1;node=None
   if '</rr_nodes>' in line:break
 assert seen==w['N'];layer=out/(w['case']+'_layers.bin');layer.write_bytes(layers.tobytes());command=[str(r/'profile5'),w['path'],str(layer),str(out/(w['case']+'.jsonl')),'-'];t=time.monotonic()
 with (out/(w['case']+'.log')).open('w') as log:run=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
 (out/(w['case']+'_run.json')).write_text(json.dumps(dict(command=command,returncode=run.returncode,host_elapsed_s=time.monotonic()-t,xml=str(xml),layer_sha256=sha256(layer),layers=sorted(set(layers)),nodes=seen,evidence='measured',not_fpga_time=True),indent=2));assert not run.returncode
