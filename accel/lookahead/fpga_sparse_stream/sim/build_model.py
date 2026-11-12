from pathlib import Path
import argparse,hashlib,json,subprocess,shutil
root=Path(__file__).resolve().parents[4]
src=root/'accel/lookahead/fpga_sparse_stream'
run=root/'results/fpga_sparse_stream_20261112'
p=argparse.ArgumentParser();p.add_argument('variant');a=p.parse_args()
out=run/(a.variant+'_model_source');out.mkdir(parents=True,exist_ok=True)
for f in [*src.glob('*.hpp'),src/'sim/tile_driver.cpp']:shutil.copy2(f,out/f.name)
flags=['-DSPARSE_F0_MODEL','-DSPARSE_F0_TELEMETRY'] if a.variant.startswith('f0') else []
cmd=['g++','-O3','-ffp-contract=off','-std=c++17','-DSPARSE_TILE_MODEL',*flags,
     '-I'+str(root/'accel/lookahead/include'),'-I'+str(out),str(out/'tile_driver.cpp'),'-o',str(run/(a.variant+'_model'))]
subprocess.run(cmd,check=True)
(out/'binding.json').write_text(json.dumps({'command':cmd,'sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.suffix in ['.hpp','.cpp']}},indent=2)+'\n')
