from pathlib import Path
import json,subprocess,hashlib,sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_20261112'
prior=root.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z'
lat=sys.argv[1] if len(sys.argv)>1 else '60';variant=sys.argv[2] if len(sys.argv)>2 else 'tile';suffix=sys.argv[3] if len(sys.argv)>3 else 'checked'
for x in json.load(open(root/'accel/lookahead/fpga_sim_restart/config/inputs.json'))[:2]:
 out=r/f"{variant}_{x['case']}_l{lat}_{suffix}";out.mkdir(exist_ok=True)
 cmd=[str(r/f'{variant}_build/Vsparse_tile'),x['path'],str(r/x['case']/'prepared.bin'),str(prior/f"replay/{x['case']}_F1.bin"),str(out),lat]
 with open(out/'console.log','w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 (out/'receipt.json').write_text(json.dumps({'command':cmd,'returncode':p.returncode,'sources':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (root/'accel/lookahead/fpga_sparse_stream/rtl').glob('*.sv')}},indent=2))
 print(x['case'],p.returncode,(out/'console.log').read_text()[-800:],flush=True)
 if p.returncode:sys.exit(p.returncode)
