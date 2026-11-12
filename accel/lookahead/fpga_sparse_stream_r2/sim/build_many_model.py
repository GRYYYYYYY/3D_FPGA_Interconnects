from pathlib import Path
import subprocess,shutil,json,hashlib,sys
root=Path(__file__).resolve().parents[4];s=root/'accel/lookahead/fpga_sparse_stream_r2';r=root/'results/fpga_sparse_stream_r2_20261112/model'/sys.argv[1];r.mkdir(parents=True,exist_ok=False);f=r/'source';f.mkdir()
for p in [*s.glob('*model*.hpp'),s.parent/'fpga_sparse_stream/owner_model.hpp',s.parent/'fpga_sparse_stream/tile_model.hpp',s/'sim/many_tile_driver.cpp']:
 dst=f/p.name;shutil.copy2(p,dst);dst.write_text(dst.read_text().replace('../fpga_sparse_stream/owner_model.hpp','owner_model.hpp').replace('../fpga_sparse_stream/tile_model.hpp','tile_model.hpp'))
p=f/'many_tile_driver.cpp';p.write_text(p.read_text().replace('#include "Vr2_many_tile.h"\n#include "verilated.h"','#include "many_tile_model.hpp"\nusing Vr2_many_tile=r2_model::ManyTileModel<TILE_L,TILE_P,TILE_MC,TILE_CC>;').replace('Verilated::commandArgs(argc,argv);','').replace('RTL functional cycles; hypothetical bounded physical memory; no qualified clock','independent C++ cycle model; hypothetical bounded physical memory; no qualified clock'))
cmd=['g++','-O3','-std=c++17','-ffp-contract=off',f'-DTILE_L={sys.argv[2]}',f'-DTILE_P={sys.argv[3]}',f'-DTILE_MC={sys.argv[4]}',f'-DTILE_CC={sys.argv[5]}','-I'+str(root/'accel/lookahead/include'),str(p),'-o',str(r/'model')]
with (r/'build.log').open('w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
(r/'source_binding.json').write_text(json.dumps({'command':cmd,'returncode':rc,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f.iterdir()}},indent=2));print('BUILD',rc,r);sys.exit(rc)
