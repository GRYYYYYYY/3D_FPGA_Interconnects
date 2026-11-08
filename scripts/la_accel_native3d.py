"""Generate an entire native Hecate 3D graph and export the native global sample list."""
import argparse,json,os,shutil,struct,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
from prepare import sha256
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--binary',type=Path,required=True)
 p.add_argument('--dimension',type=int,required=True);p.add_argument('--width',type=int,required=True)
 a=p.parse_args();o=a.output.resolve();o.mkdir(parents=True,exist_ok=False)
 arch=ROOT/'results/native_cpu_evidence_20261102/sources/architecture.xml'
 shutil.copy2(arch,o/'architecture.xml')
 shutil.copy2(ROOT/'results/lookahead_accel_20261108T125500Z/tiny_native/tiny.blif',o/'tiny.blif')
 cmd=[str(a.binary.resolve()),str(o/'architecture.xml'),str(o/'tiny.blif'),
      '--device_width',str(a.dimension),'--route_chan_width',str(a.width),'--num_workers','2',
      '--router_lookahead','map','--write_rr_graph',str(o/'rr.xml'),
      '--write_router_lookahead',str(o/'wire_map.bin'),'--max_router_iterations','1']
 env={k:v for k,v in os.environ.items() if not k.startswith(('VPR_','OMP_','H3D_'))}
 env.update(LD_LIBRARY_PATH=str(ROOT/'data/vpr_runtime_20261025'),
     VPR_LA_EXPORT=str(o/'workload.bin'),VPR_HYBRID_LOOKAHEAD_TASKS='1',
     VPR_HYBRID_LOOKAHEAD_PARALLEL='1',VPR_CPU_GLOBAL_SCHEDULER='flat',OMP_NUM_THREADS='2')
 manifest=dict(command=cmd,environment={k:v for k,v in env.items() if k.startswith(('VPR_','OMP_'))},
     binary_sha256=sha256(a.binary),architecture_source=str(arch),architecture_sha256=sha256(arch),
     dimension=a.dimension,channel_width=a.width,graph_scope='complete native RRG; no edge editing or sample selection',timing_eligible=False)
 (o/'invocation.json').write_text(json.dumps(manifest,indent=2)+'\n')
 with (o/'stdout.log').open('w') as f:run=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180)
 manifest['returncode']=run.returncode
 if run.returncode not in (0,2) or not (o/'workload.bin').exists():
  manifest['status']='failed';(o/'manifest.json').write_text(json.dumps(manifest,indent=2));raise RuntimeError('native export failed: '+str(o))
 header=struct.unpack('<7Q',(o/'workload.bin').open('rb').read(56));n=header[1]
 layers=[None]*n
 for event,e in ET.iterparse(o/'rr.xml',events=['end']):
  if e.tag=='node':
   loc=e.find('loc');layers[int(e.attrib['id'])]=int(loc.attrib.get('layer_low',loc.attrib.get('layer','0')));e.clear()
 assert all(x is not None for x in layers) and len(set(layers))>=2
 (o/'layers.bin').write_bytes(struct.pack('<'+'I'*n,*layers))
 manifest.update(status='exported',layers=sorted(set(layers)),dimensions=dict(zip(['magic','nodes','edges','jobs','costs','cells','groups'],header)),
     workload_sha256=sha256(o/'workload.bin'),rr_graph_sha256=sha256(o/'rr.xml'),layer_map_sha256=sha256(o/'layers.bin'),native_wire_map_sha256=sha256(o/'wire_map.bin'))
 (o/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest['dimensions']))
if __name__=='__main__':main()
