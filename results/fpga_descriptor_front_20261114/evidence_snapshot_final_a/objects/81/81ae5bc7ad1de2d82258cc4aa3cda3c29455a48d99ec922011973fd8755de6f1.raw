`timescale 1ns/1ps
// Two global RR winners, each feeding a real holding register. Neither a free
// input nor a new output can bypass that register on its acceptance edge.
module df_ack_collector #(parameter integer WIDTH=64)(
 input logic clk,reset,input logic[31:0]iv,output logic[31:0]ir,
 input logic[32*WIDTH-1:0]idata,output logic[1:0]ov,
 input logic[1:0]ordy,output logic[2*WIDTH-1:0]odata);
 logic[4:0]cursor,selected[2],start[2];logic[1:0]found,grant;
 logic[WIDTH-1:0]chosen[2];
 assign start[0]=cursor;
 assign start[1]=grant[0]?selected[0]+5'd1:cursor;
 for(genvar lane=0;lane<2;lane=lane+1)begin:pick
  wire[63:1]valid;wire[5:0]key[64];wire[WIDTH-1:0]data[64];
  for(genvar i=0;i<32;i=i+1)begin:leaf
   if(lane==0)assign valid[32+i]=iv[i];
   else assign valid[32+i]=iv[i]&&!(grant[0]&&selected[0]==i);
   assign key[32+i]={i<start[lane],5'(i)};assign data[32+i]=idata[i*WIDTH+:WIDTH];
  end
  for(genvar j=1;j<32;j=j+1)begin:tree
   wire left=valid[2*j]&&(!valid[2*j+1]||key[2*j]<key[2*j+1]);
   assign valid[j]=valid[2*j]||valid[2*j+1];assign key[j]=left?key[2*j]:key[2*j+1];assign data[j]=left?data[2*j]:data[2*j+1];
  end
  assign found[lane]=valid[1];assign selected[lane]=key[1][4:0];assign chosen[lane]=data[1];
  assign grant[lane]=(!ov[lane]||ordy[lane])&&found[lane];
  always_ff @(posedge clk)begin
   if(reset)ov[lane]<=0;
   else if(!ov[lane]||ordy[lane])begin ov[lane]<=found[lane];if(found[lane])odata[lane*WIDTH+:WIDTH]<=chosen[lane];end
  end
 end
 always_comb begin ir=0;for(integer k=0;k<2;k=k+1)if(grant[k])ir[selected[k]]=1;end
 always_ff @(posedge clk)begin
  if(reset)cursor<=0;
  else if(grant[1])cursor<=selected[1]+5'd1;
  else if(grant[0])cursor<=selected[0]+5'd1;
 end
endmodule
