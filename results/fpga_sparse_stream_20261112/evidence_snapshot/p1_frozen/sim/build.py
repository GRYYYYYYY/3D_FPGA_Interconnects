from pathlib import Path
import os,subprocess,sys,json,hashlib,shutil
root=Path(__file__).resolve().parents[4]
src=root/'accel/lookahead/fpga_sparse_stream'
r=root/'results/fpga_sparse_stream_20261112'
old=root.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z/tools/verilator_local/usr'
env=os.environ.copy();env['VERILATOR_ROOT']=str(old/'share/verilator')
variant=sys.argv[1] if len(sys.argv)>1 else 'tile'
flags=sys.argv[2:]
extra_cflags=' -DSPARSE_SMALL_MEMBER' if '-GMEMBER_CAP=2' in flags else ''
build=r/(variant+'_build'); frozen=build/'source';frozen.mkdir(parents=True,exist_ok=True)
for f in src.glob('rtl/*.sv'):shutil.copy2(f,frozen/f.name)
shutil.copy2(src/'sim/tile_driver.cpp',frozen/'tile_driver.cpp')
manifest={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in list(src.glob('rtl/*.sv'))+[src/'sim/tile_driver.cpp']}
(build/'source_binding.json').write_text(json.dumps({'source_sha256':manifest,'flags':flags},indent=2))
cmd=[str(old/'bin/verilator'),'--cc','--exe','--build','-j','4','--top-module','sparse_tile','--Mdir',str(r/(variant+'_build')),'-Wno-fatal','-O3','-CFLAGS',f'-O3 -std=c++17 -I{root}/accel/lookahead/include{extra_cflags}',*flags,*map(str,frozen.glob('*.sv')),str(frozen/'tile_driver.cpp')]
with open(r/(variant+'_build.log'),'w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,env=env)
