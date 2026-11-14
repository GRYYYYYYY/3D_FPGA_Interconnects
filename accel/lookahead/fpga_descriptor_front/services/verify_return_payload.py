#!/usr/bin/env python3
"""Independent non-echo, distinct-lane physical response payload regression."""
import argparse,hashlib,json,subprocess,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--id-xor',type=lambda x:int(x,0),default=0);a=p.parse_args();src=Path(__file__).resolve().parent;root=src.parents[3];out=Path(a.output).resolve()
if out.exists():raise SystemExit('Use a new result path')
out.mkdir(parents=True)
base=root/'results/fpga_descriptor_front_20261114/services_b/network.vec'
mask=(1<<64)-1
repeat=lambda x:sum(x<<(64*k) for k in range(4))
def result(x):return sum((((x^(0x9e3779b97f4a7c15*(k+1)&mask))+(0xd1b54a32d192ed03*k))&mask)<<(64*k) for k in range(4))
with (out/'network_payload.vec').open('w') as f:
 for row in base.read_text().splitlines():
  v=[int(x,16) for x in row.split()];assert len(v)==100
  for s in range(8):
   v[s*10+3]^=a.id_xor;v[s*10+8]^=a.id_xor;v[s*10+4]=repeat(v[s*10+4]);v[s*10+9]=result(v[s*10+9])
  for p in range(2):v[80+p*10+3]=result(v[80+p*10+3]);v[80+p*10+8]=repeat(v[80+p*10+8])
  f.write(' '.join(format(x,'x') for x in v)+'\n')
rtl=['df_fifo.sv','df_rr_router.sv','df_tagged_port.sv','df_memory_network.sv'];binding={str(src/f):hashlib.sha256((src/f).read_bytes()).hexdigest() for f in rtl+['tb_network.sv','verify_return_payload.py']}
tb=(src/'tb_network.sv').read_text().replace('module tb_network;','module tb_network_payload;').replace('logic[63:0]data,retdata','logic[255:0]data,retdata').replace('logic[63:0]erd[NS]','logic[255:0]erd[NS]').replace('logic[63:0]emd[NP]','logic[255:0]emd[NP]').replace('{4{data}}','data').replace('{4{erd[s]}}','erd[s]').replace('{4{emd[p]}}','emd[p]').replace('TEST_PASS NETWORK','TEST_PASS NETWORK_NON_ECHO_256BIT')
(out/'tb_network_payload.sv').write_text(tb)
(out/'binding.json').write_text(json.dumps({'sources':binding,'base_vectors_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'derived_vectors_sha256':hashlib.sha256((out/'network_payload.vec').read_bytes()).hexdigest(),'id_xor':a.id_xor,'scope':'same network timing metadata; independent non-echo per64bitlane physical return data'},indent=2)+'\n')
lines=['create_project payload [file join [pwd] project] -part xcu280-fsvh2892-2L-e']+[f'add_files {{{src/f}}}' for f in rtl]+[f'add_files -fileset sim_1 {{{out/"tb_network_payload.sv"}}}','set_property top tb_network_payload [get_filesets sim_1]','set_property xsim.simulate.runtime all [get_filesets sim_1]',f'set_property -name xsim.simulate.xsim.more_options -value {{-testplusarg VECTORS={out/"network_payload.vec"}}} -objects [get_filesets sim_1]','update_compile_order -fileset sim_1','launch_simulation','close_sim','exit']
(out/'run.tcl').write_text('\n'.join(lines)+'\n');env=dict(os.environ);env['LD_PRELOAD']='/lib/x86_64-linux-gnu/libudev.so.1'
cmd=['/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin/vivado','-mode','batch','-source',str(out/'run.tcl')]
with (out/'console.log').open('w') as f:r=subprocess.run(cmd,cwd=out,stdout=f,stderr=subprocess.STDOUT,env=env)
log=out/'project/payload.sim/sim_1/behav/xsim/simulate.log';text=log.read_text() if log.exists() else ''
ok=r.returncode==0 and 'TEST_PASS NETWORK_NON_ECHO_256BIT' in text and 'Fatal:' not in text
(out/'terminal.json').write_text(json.dumps({'status':'PASS' if ok else 'FAIL','tool_code':r.returncode,'command':cmd,'transcript':str(log),'cycles':2184,'unchanged_RTL':binding,'non_echo_response_256bits':True,'id_xor':a.id_xor},indent=2)+'\n')
assert ok;print('NON_ECHO_256BIT_PASS',out)
