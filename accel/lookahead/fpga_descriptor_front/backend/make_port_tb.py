#!/usr/bin/env python3
from pathlib import Path
h=Path(__file__).resolve().parent;old=h.parents[1]/'fpga_enum_commit'
s=(old/'integration/tb_port_stress.sv').read_text()
s=s.replace('ec_tagged_port dut(.*);','''wire c_mv,c_mr,c_mw,c_sv,c_sr;wire [31:0] c_ml;wire [4:0] c_mtag,c_stag;wire [255:0] c_md,c_sd;wire request_empty,response_empty,core_idle;
 ec_tagged_port dut(.clk,.reset,.cv,.cr,.cw,.cl,.cid,.cd,.rv,.rr,.rid,.rd,.mv(c_mv),.mr(c_mr),.mw(c_mw),.ml(c_ml),.mtag(c_mtag),.md(c_md),.sv(c_sv),.sr(c_sr),.stag(c_stag),.sd(c_sd),.idle(core_idle),.error,.credits_used,.peak_credits,.client_accepted,.physical_issued,.physical_returned,.client_returned);
 df_fifo2 #(.WIDTH(294)) request(.clk,.reset,.iv(c_mv),.ir(c_mr),.id({c_mw,c_ml,c_mtag,c_md}),.ov(mv),.ordy(mr),.od({mw,ml,mtag,md}),.empty(request_empty));
 df_fifo2 #(.WIDTH(261)) response(.clk,.reset,.iv(sv),.ir(sr),.id({stag,sd}),.ov(c_sv),.ordy(c_sr),.od({c_stag,c_sd}),.empty(response_empty));
 assign idle=core_idle&&request_empty&&response_empty;''')
s=s.replace('integer cycle=0,','integer slicefile;integer cycle=0,')
s=s.replace('clean_rd,mv,mr,mv?mw:1\'b0,mv?ml:32\'b0,mv?mtag:5\'b0,mv?md:256\'b0,sv,sr,sv?stag:5\'b0,sv?sd:256\'b0,dut.cursor','clean_rd,c_mv,c_mr,c_mv?c_mw:1\'b0,c_mv?c_ml:32\'b0,c_mv?c_mtag:5\'b0,c_mv?c_md:256\'b0,c_sv,c_sr,c_sv?c_stag:5\'b0,c_sv?c_sd:256\'b0,dut.cursor')
s=s.replace('if(!reset)begin\n   $fdisplay', '''if(!reset)begin
   $fdisplay(slicefile,"%0d,request,0,294,%h,%h,%h,%h,%h,%h,%h",cycle,request.iv,request.ir,request.iv?request.id:294'b0,request.ov,request.ordy,request.ov?request.od:294'b0,request.empty);
   $fdisplay(slicefile,"%0d,response,0,261,%h,%h,%h,%h,%h,%h,%h",cycle,response.iv,response.ir,response.iv?response.id:261'b0,response.ov,response.ordy,response.ov?response.od:261'b0,response.empty);
   $fdisplay''')
s=s.replace('if(!$value$plusargs', '''slicefile=$fopen("context_slices.csv","w");$fdisplay(slicefile,"cycle,name,kind,width,iv,ir,id,ov,ordy,od,empty");
  if(!$value$plusargs''')
s=s.replace('always @(negedge clk)begin', 'reg held_response=0;always @(posedge clk)held_response<=!reset&&sv&&!sr;\n always @(negedge clk)begin')
s=s.replace('sv=0;sel=-1;', 'if(!held_response)begin sv=0;sel=-1;').replace('if(sel>=0)begin sv=1;stag=sel;sd=data[sel];end', 'if(sel>=0)begin sv=1;stag=sel;sd=data[sel];end end')
s=s.replace('TEST_PASS PORT_STRESS','TEST_PASS CONTEXT_PORT_STRESS')
(h/'tb_port_context.sv').write_text(s)
s=(h/'run_ops.tcl').read_text().replace('/backend/sim_ops_a','/backend/sim_port_b').replace('tb_context_ops.sv','tb_port_context.sv').replace('top tb_context_ops','top tb_port_stress')
(h/'run_port.tcl').write_text(s)
