`timescale 1ns/1ps
module tb_reject;parameter L=4;
 logic clk=0;always #2.5 clk=~clk;logic reset=1,av=0,ar,pv=0,pr;logic[15:0]at,pt=0;logic mode=0,dv,dr=1,drv=0,drr;logic[63:0]da;logic[15:0]dt,drt=0;logic[255:0]drd=0;logic error,idle;logic mv,mr=0,rv=0,rr,yv;logic[63:0]ml,yp;logic[15:0]mt,yt;logic[14:0]yc;wire[3:0]ov;wire[127:0]od,ot;wire[255:0]op;logic[31:0]reserved,retired,dc,tc,ep,ec,ee;integer cyc=0,caseidx;
 df_front_group dut(.clk,.reset,.av,.ar,.at,.pv,.pr,.pt,.stale(1'b0),.pn(32'd0),.pp(64'h3f8000003f800000),.epoch(16'd1),.format16(mode),.descriptor_base(64'd123456),.edge_base(64'd1041696),.edge_count(32'hffffffff),.cells(16'd8),.cfg_we(1'b0),.cfg_idx(4'd0),.cfg_cost(64'd0),.dv,.dr,.da,.dt,.drv,.drr,.drt,.drd,.mv,.mr,.ml,.mt,.rv,.rr,.rt(16'd0),.rd(256'd0),.yv,.yr(1'b1),.yc,.yp,.yt,.ov,.or_(4'b1111),.od,.op,.ot,.error,.idle,.reserved,.retired,.desc_count(dc),.target_count(tc),.edge_parents(ep),.edge_completed(ec),.edge_emitted(ee));
 task test_case(input integer k,input logic fmt,input logic[127:0]raw,input logic should_fail);
 begin
  reset=1;av=0;pv=0;drv=0;mode=fmt;repeat(3)@(negedge clk);reset=0;av=1;
  do @(posedge clk);while(!ar);pt=at;@(negedge clk);av=0;pv=1;
  do @(posedge clk);while(!pr);@(negedge clk);pv=0;
  do @(posedge clk);while(!dv);if(da!=123456)$fatal(1,"descriptor base lost");drt=dt;
  @(negedge clk);drd={128'd0,raw};drv=1;do @(posedge clk);while(!drr);@(negedge clk);drv=0;
  repeat(12)@(negedge clk);
  if(should_fail)begin if(!error||ep!=0||tc!=0||mv||yv)$fatal(1,"invalid descriptor escaped k=%0d",k);end
  else begin if(error||ep!=1||!mv||ml!=1041696)$fatal(1,"fallback degree decode failed k=%0d ep=%d mv=%b",k,ep,mv);end
  $display("REJECT_CASE_PASS k=%0d error=%b",k,error);
 end endtask
 initial begin
  test_case(0,0,128'h000000000000000000000020fffffff0,1); // begin+degree overflow
  test_case(1,0,128'h00000000000000008009000000000000,1); // valid cell9>=8
  test_case(2,0,128'h00000000000000000001000000000000,1); // invalid cell bits nonzero
  test_case(3,1,128'h00000002000000000000000100000000,1); // reserved flags bit1
  test_case(4,1,128'h00000001ffffffff0000000100000000,1); // negative validcell
  test_case(5,1,128'h00000000000000000000000000000001,1); // end<begin
  test_case(6,1,128'h00000000000000000001000000000000,0); // valid degree65536 exact fallback decode, firstrequest only
  $display("TEST_PASS descriptor_reject invalid=6 fallback65536_firstrequest=1");$finish;
 end
 always @(posedge clk)begin cyc=cyc+1;if(cyc>1000)$fatal(1,"watchdog");end
endmodule
