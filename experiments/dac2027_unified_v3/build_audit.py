import hashlib,json,os,shlex,subprocess
from pathlib import Path
here=Path(__file__).resolve().parent
base=here.parents[2]
stock=base/'3D_FPGA_routing/vendor/vtr'
freezer=base/'3D_FPGA_routing/artifacts/bin/baseline'
manifest=json.loads((freezer/'manifest.json').read_text())
build=here/'build'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4<<20),b''): h.update(b)
    return h.hexdigest()
assert manifest['commit']==subprocess.check_output(['git','-C',stock,'rev-parse','HEAD'],text=True).strip()
assert sha(freezer/'CMakeCache.txt')==manifest['cache_sha256']
src=subprocess.check_output(['git','-C',stock,'show',manifest['commit']+':vpr/src/main.cpp'])
assert hashlib.sha256(src).hexdigest()==sha(stock/'vpr/src/main.cpp')
candidate=next((base/'3D_FPGA_Interconnects_R6_1/results').glob('*/native_build/commands.json'))
link=stock/'build/vpr/CMakeFiles/vpr.dir/link.txt'
commands=[(stock/'build/vpr',shlex.split(link.read_text())),json.loads(candidate.read_text())[-1]]
paths=[link,candidate,freezer/'CMakeCache.txt',stock/'vpr/src/main.cpp',stock/'build/vpr/CMakeFiles/libvpr.dir/flags.make',
       build/'stock/pristine.tar',base/'3D_FPGA_Interconnects/build_cpu_slices/CMakeCache.txt']
for directory,cmd in commands:
    for arg in cmd:
        p=Path(directory)/arg
        if p.is_file() and (p.suffix in ('.o','.a') or '.so' in p.name): paths.append(p)
for arm in ('stock','candidate'):
    paths.extend([build/arm/'router_lookahead_map.cpp',build/arm/'libvpr.a'])
paths.extend(here/f for f in ['reserve.py','worker.py','cases.json','build_timers.py','e2_timer.hpp'])
env=dict(os.environ,LD_LIBRARY_PATH=str(base/'3D_FPGA_Interconnects/data/vpr_runtime_20261025'))
bins={str(p):subprocess.check_output([p,'--version'],env=env,text=True).strip() for p in [freezer/'vpr',build/'stock/vpr_stock',build/'candidate/vpr']}
assert all('release VTR_ASSERT_LEVEL=2' in s for s in bins.values())
result=dict(original_manifest=manifest,version_banners=bins,link_inputs_sha256={str(p):sha(p) for p in set(paths)},
            compiler=subprocess.check_output(['g++-11','--version'],text=True).splitlines()[0])
(here/'audit/build_provenance.json').write_text(json.dumps(result,indent=2)+'\n')
