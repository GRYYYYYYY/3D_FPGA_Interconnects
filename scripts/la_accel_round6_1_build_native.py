import json,sys,shutil,subprocess
from pathlib import Path
from prepare import sha256
R=Path(__file__).resolve().parents[1];o=Path(sys.argv[1]).resolve();o.mkdir(exist_ok=False);old=(R/'results/lookahead_accel_round2_20261108T122100Z/native_live_build_v2').resolve();shutil.copytree(old/'source',o/'source');(o/'bin').mkdir()
p=o/'source/router_lookahead_map.cpp';s=p.read_text();s='#include <chrono>\n#include <cstdio>\nstruct R61BuildScope {std::chrono::steady_clock::time_point start=std::chrono::steady_clock::now();~R61BuildScope(){fprintf(stdout,"R61_NATIVE_BUILD scope_version=R6_1_NATIVE_BUILD_V1 E2_wall_s=%.9f\\n",std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count());}};\n'+s;s=s.replace('void MapLookahead::compute(const std::vector<t_segment_inf>& segment_inf) {','void MapLookahead::compute(const std::vector<t_segment_inf>& segment_inf) {\n R61BuildScope r61_scope;');p.write_text(s)
commands=[]
for cwd,cmd in json.load(open(old/'commands.json')):
 cmd=[x.replace(str(old),str(o)) for x in cmd]
 # The stored paths may name the same directory through the original repository.
 for i,x in enumerate(cmd):
  if 'native_live_build_v2' in x:cmd[i]=x.replace(x[:x.index('native_live_build_v2')]+ 'native_live_build_v2',str(o))
 runtime=R/'data/vpr_runtime_20261025';cmd=[str(runtime/Path(x).name.replace('.so.12.5','.so.12').replace('.so.2.5','.so.2')) if Path(x).name.startswith(('libtbb.so','libtbbmalloc')) else x for x in cmd]
 if '-c' not in cmd and cmd[0].endswith('c++'):cmd.insert(1,'-Wl,-rpath-link,'+str(runtime))
 commands.append([cwd,cmd])
(o/'commands.json').write_text(json.dumps(commands,indent=2))
with (o/'build.log').open('w') as f:
 for cwd,cmd in commands:subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=300,check=True)
(o/'binding.json').write_text(json.dumps(dict(binary_sha256=sha256(o/'bin/vpr_flat'),source_sha256={p.name:sha256(p) for p in (o/'source').iterdir() if p.is_file()},scope_version='R6_1_NATIVE_BUILD_V1',start='MapLookahead::compute entry before stage_memory/timer',end='function exit after wire interpolation, SOURCE/OPIN lookahead, minimum maps and interposer lookahead; excludes later serialize and RR load'),indent=2))
