#!/usr/bin/env python3
from pathlib import Path
import shutil,hashlib,json
here=Path(__file__).resolve().parent;root=here.parents[3]
old=root/'accel/lookahead/fpga_enum_commit'
out=root/'results/fpga_descriptor_front_20261114/backend'
fixtures=out/'fixtures'
source=root.parent/'3D_FPGA_Interconnects_ENUM_COMMIT/results/fpga_enum_commit_integration_20261114_a/fixtures'
fixtures.mkdir(exist_ok=True)
bindings=[]
for p in sorted(source.iterdir()):
 if p.suffix=='.hex' or p.name in ('cases.txt','manifest.json'):
  target=fixtures/p.name
  if not target.exists():shutil.copyfile(p,target)
  assert p.read_bytes()==target.read_bytes()
  bindings.append({'source':str(p),'local':str(target.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(out/'fixture_bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
s=(old/'integration/tb_backend.sv').read_text().replace('module backend_env','module context_env').replace('ec_backend_owner #(.NEW(NEW))','df_backend_context #(.NEW(NEW))')
s=s.replace('dut.','dut.core.')
s=s.replace('wait(dut.core.canonical_idle==3&&fabric_idle);','repeat(3)@(negedge clk);wait(dut.core.canonical_idle==3&&fabric_idle);')
s=s.replace('module tb_backend;\n wire a,b;backend_env #(.NEW(0)) old(a);backend_env #(.NEW(1)) candidate(b);\n initial begin wait(a&&b);$display("TEST_PASS matched_backend_native_and_stress");$finish;end\nendmodule','module tb_backend_context;\n wire finished;context_env #(.NEW(1)) candidate(finished);\n initial begin wait(finished);$display("TEST_PASS backend_context_native_and_stress");$finish;end\nendmodule')
# The frozen-port boundary is inside the physical request/return context slices.
s=s.replace('dut.core.rd,mv,mr,mv?mw:1\'b0,mv?ml:32\'b0,mv?mtag:5\'b0,mv?md:256\'b0,sv,sr,sv?stag:5\'b0,sv?sd:256\'b0,dut.core.fabric.cursor','dut.core.rd,mv,mr,mv?mw:1\'b0,mv?ml:32\'b0,mv?mtag:5\'b0,mv?md:256\'b0,sv,sr,sv?stag:5\'b0,sv?sd:256\'b0,dut.core.fabric.cursor')
# Separate exact slice replay captures every FIFO/ACK boundary, not just aggregates.
s=s.replace('integer i,b,s,idx', 'integer slicefile;\n integer i,b,s,idx')
s=s.replace('finished=0;fixed_latency=', 'slicefile=$fopen($sformatf("context_slices.csv"),"w");\n  $fdisplay(slicefile,"cycle,name,kind,width,iv,ir,id,ov,ordy,od,empty");\n  finished=0;fixed_latency=')
trace='''\n for(genvar bank=0;bank<2;bank=bank+1)begin:ctx_observe
'''
for instance,kind,width in [('candidate',0,96),('op',0,373),('directory',1,50),('result',1,277)]:
 path='dut.context_bank[bank].'+instance
 trace+=f''' always @(posedge clk)if(!dut.reset_q&&measuring&&(casename=="resident_two_waves"||casename=="empty"))
 $fdisplay(slicefile,"%0d,{instance}%0d,{kind},{width},%h,%h,%h,%h,%h,%h,%h",cycle,bank,{path}.iv,{path}.ir,{path}.iv?{path}.id:{width}'b0,{path}.ov,{path}.ordy,{path}.ov?{path}.od:{width}'b0,{path}.empty);
'''
trace+='end\n'
for instance,width in [('request',294),('response',261)]:
 path='dut.'+instance
 trace+=f''' always @(posedge clk)if(!dut.reset_q&&measuring&&(casename=="resident_two_waves"||casename=="empty"))
 $fdisplay(slicefile,"%0d,{instance},0,{width},%h,%h,%h,%h,%h,%h,%h",cycle,{path}.iv,{path}.ir,{path}.iv?{path}.id:{width}'b0,{path}.ov,{path}.ordy,{path}.ov?{path}.od:{width}'b0,{path}.empty);
'''
s=s.replace(' // Dynamic hierarchical generate indices',trace+' // Dynamic hierarchical generate indices')
(here/'tb_backend_context.sv').write_text(s)
print('fixture files',len(bindings))
