import pathlib,subprocess,shutil,concurrent.futures,hashlib,json
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z/closed_loop'
binary=r/'verilator_64_final/Vgraph_top'
sources=[root/'accel/lookahead/fpga_sim_restart/rtl/owner_service.sv',*list((root/'accel/lookahead/fpga_sim_restart/closed_loop').glob('*.sv'))]
binding={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
def run(case):
 tag='d3' if case=='native_d3_w8' else 'd4';p=r/f'{tag}_rtl64_final_l60';p.mkdir(exist_ok=True)
 for n in ['config.txt','layout.json','memory.hex','expected.hex']:shutil.copy(r/case/n,p/n)
 (p/'binding.json').write_text(json.dumps({'sources':binding,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'backend':'Verilator 4.038','fixed_physical_mapping':'32B line modulo32; proposal base multiple32lines; two owners per channel; all arrays share ports'},indent=2))
 with open(p/'simulate.log','w') as f:subprocess.run([str(binary),str(p),'64','60'],stdout=f,stderr=subprocess.STDOUT,check=True)
 subprocess.run(['python3',str(root/'accel/lookahead/fpga_sim_restart/closed_loop/check.py'),str(p)],check=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,['native_d3_w8','native_d4_w8']))
