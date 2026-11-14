`timescale 1ns/1ps
module df_candidate_network(input logic clk,reset,
 input logic[63:0] cv,output logic[63:0] cr,input logic[64*96-1:0] cd,
 output logic[63:0] rv,input logic[63:0] rr,output logic[64*96-1:0] rd);
 wire[63:0] qv,qr,gv,gr;wire[64*96-1:0] qd,gd;wire[64*6-1:0] dest;
 for(genvar i=0;i<64;i=i+1)begin:lane
  df_fifo #(.WIDTH(96),.DEPTH(4)) fifo(.clk,.reset,.iv(cv[i]),.ir(cr[i]),.idata(cd[i*96+:96]),.ov(qv[i]),.ordy(qr[i]),.odata(qd[i*96+:96]));
  // node is high32; bank=2*((node/4)&31)+(((node/4)>>5)&1).
  assign dest[i*6+:6]={qd[i*96+64+2+:5],qd[i*96+64+7]};
 end
 df_rr_router #(.INPUTS(64),.OUTPUTS(64),.WIDTH(96)) route(.clk,.reset,.iv(qv),.ir(qr),.dest(dest),.idata(qd),.ov(gv),.ordy(gr),.odata(gd));
 for(genvar i=0;i<64;i=i+1)begin:bank
  df_fifo #(.WIDTH(96),.DEPTH(16)) fifo(.clk,.reset,.iv(gv[i]),.ir(gr[i]),.idata(gd[i*96+:96]),.ov(rv[i]),.ordy(rr[i]),.odata(rd[i*96+:96]));
 end
endmodule
