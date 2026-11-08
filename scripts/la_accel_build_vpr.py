"""Build opt-in native workload export in an isolated archive; never mutate frozen evidence."""
import argparse,json,shutil,subprocess,hashlib
from pathlib import Path
from prepare import sha256
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return sha256(Path(p))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--tbb-include',type=Path,required=True);a=p.parse_args();o=a.output.resolve();o.mkdir(parents=True,exist_ok=False);(o/'source').mkdir();(o/'bin').mkdir()
 frozen=ROOT/'results/native_flat_baseline_20261105';steps=json.loads((frozen/'build_inputs.json').read_text())['commands']
 for src in (frozen/'source').iterdir(): shutil.copy2(src,o/'source'/src.name)
 src=o/'source/router_lookahead_map_utils.cpp';s=src.read_text();s='#include "io.hpp"\n'+s
 marker='std::vector<t_routing_cost_map> get_routing_cost_maps_pipeline('
 assert s.count(marker)==1;s=s.replace(marker,'#include "vpr_bridge.cpp"\n'+marker)
 marker='    /** The token bound limits in-flight sample maps';assert s.count(marker)==1;s=s.replace(marker,'    la_export(jobs, groups);\n    if (la_import(jobs, results)) return results;\n'+marker);src.write_text(s)
 commands=[]
 for cwd,cmd in steps:
  cmd=[str(x).replace(str(frozen),str(o)) for x in cmd]
  if '-c' in cmd: cmd[1:1]=['-I'+str(a.tbb_include.resolve()),'-I'+str(ROOT/'accel/lookahead/include'),'-I'+str(ROOT/'accel/lookahead'),'-ffp-contract=off','-fno-fast-math']
  cmd=[str(ROOT/"data/vpr_runtime_20261025"/({"libtbb.so.12.5":"libtbb.so.12","libtbbmalloc_proxy.so.2.5":"libtbbmalloc_proxy.so.2","libtbbmalloc.so.2.5":"libtbbmalloc.so.2"}[Path(x).name])) if Path(x).name in {"libtbb.so.12.5","libtbbmalloc_proxy.so.2.5","libtbbmalloc.so.2.5"} else x for x in cmd]
  if "-c" not in cmd and cmd[0].endswith("c++"):cmd.insert(1,"-Wl,-rpath-link,"+str(ROOT/"data/vpr_runtime_20261025"))
  commands.append([cwd,cmd])
 before={str(x):sha(x) for x in [ROOT/'build_cpu_slices/vpr/libvpr.a',frozen/'bin/vpr_flat']}
 (o/'commands.json').write_text(json.dumps(commands,indent=2))
 with (o/'build.log').open('w') as f:
  for cwd,cmd in commands: subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,check=True)
 assert before=={x:sha(x) for x in before}
 (o/'provenance.json').write_text(json.dumps({'frozen_unchanged':before,'binary_sha256':sha(o/'bin/vpr_flat'),'source_sha256':{str(x):sha(x) for x in (o/'source').iterdir()},'commands':commands},indent=2))
if __name__=='__main__':main()
