from pathlib import Path
import json,subprocess,sys,hashlib
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112'
prior=root.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z'
variant=sys.argv[1];lat=sys.argv[2] if len(sys.argv)>2 else '60';seed=sys.argv[3] if len(sys.argv)>3 else '1729';gap=sys.argv[4] if len(sys.argv)>4 else '2'
for x in json.load(open(root/'accel/lookahead/fpga_sim_restart/config/inputs.json'))[:2]:
 out=r/'rtl'/f"{variant}_{x['case']}_l{lat}_s{seed}_g{gap}";out.mkdir(exist_ok=False)
 cmd=[str(r/f'rtl/{variant}_build/Vsparse_tile'),x['path'],str(r/f"semantics/{x['case']}/prepared.bin"),str(prior/f"replay/{x['case']}_F1.bin"),str(out),lat,seed,gap]
 with open(out/'console.log','w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 (out/'receipt.json').write_text(json.dumps({'command':cmd,'returncode':p.returncode,'build_binding':json.load(open(r/f'rtl/{variant}_build/source_binding.json')),'executable_sha256':hashlib.sha256(Path(cmd[0]).read_bytes()).hexdigest()},indent=2))
 print(x['case'],p.returncode,(out/'console.log').read_text()[-1000:],flush=True)
 if p.returncode:sys.exit(p.returncode)
