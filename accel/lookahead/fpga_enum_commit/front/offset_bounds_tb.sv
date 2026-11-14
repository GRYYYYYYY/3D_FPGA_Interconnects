`timescale 1ns/1ps
module offset_bounds_tb;
 reg clk=0;always #2.5 clk=~clk;reg reset=1,pv=0,rv=0,cfg_we=0;reg[63:0]begin_edge=0,end_edge=0;wire pr,mv,rr,error,idle,av;wire[63:0]ml;wire[15:0]mt;reg[15:0]rt=0;reg[255:0]rd=0;wire[7:0]ov;wire[255:0]od;wire[511:0]op;wire[31:0]accepted,completed,emitted;wire[7:0]ac;
 frontend_group dut(.clk,.reset,.lane_rr(1'b1),.pv,.pr,.pn(32'b0),.pp(64'h3f8000003f800000),.begin_edge,.end_edge,.epoch(16'd1),.cfg_we,.cfg_idx(4'b0),.cfg_cost(64'b0),.mv,.mr(1'b1),.ml,.mt,.rv,.rr,.rt,.rd,.ov,.or_(8'hff),.od,.op,.error,.accepted,.completed,.emitted,.idle,.alloc_valid(av),.alloc_context(ac));
 integer cycles=0,seen=0;
 always @(posedge clk)begin
  cycles=cycles+1;if(cycles>1000)$fatal(1,"watchdog");
  for(integer l=0;l<8;l=l+1)if(ov[l])begin if(op[l*64+:64]!==64'h3f8000003f800000||od[l*32+:32]!=1)$fatal(1,"boundary candidate mismatch");seen=seen+1;end
 end
 initial begin
  repeat(4)@(negedge clk);reset=0;cfg_we=1;@(negedge clk);cfg_we=0;
  begin_edge=64'hfffffffe;end_edge=64'hffffffff;pv=1;@(posedge clk);if(!pr)$fatal(1,"legal32 offset rejected");@(negedge clk);pv=0;
  wait(mv);if(ml!==64'h1fffffff)$fatal(1,"ceil/boundary beat wrong %h",ml);rt=mt;@(posedge clk);repeat(16)@(negedge clk);rd[6*32+:32]=1;rv=1;@(posedge clk);if(!rr)$fatal(1,"return rejected");@(negedge clk);rv=0;
  wait(idle);@(negedge clk);if(error||accepted!=1||completed!=1||emitted!=1||seen!=1)$fatal(1,"valid bound conservation");
  begin_edge=64'h100000000;end_edge=64'h100000001;pv=1;#0.1;if(pr)$fatal(1,"unsupported upper bits accepted");@(posedge clk);@(negedge clk);pv=0;
  if(!error||accepted!=1||completed!=1||emitted!=1||mv)$fatal(1,"unsupported-domain error contract");
  $display("TEST_PASS offset_bounds legal32_max_and_upper32_rejection");$finish;
 end
endmodule
