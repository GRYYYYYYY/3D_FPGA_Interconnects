`timescale 1ns/1ps
module r2_parallel_router #(parameter I=32,O=32,W=96,KEY_BIT=66,KEY_BITS=5,IA=$clog2(I))(
 input wire clk,rst,input wire [I-1:0] iv,output reg [I-1:0] ir,input wire [I*W-1:0] id,
 output wire [O-1:0] ov,input wire [O-1:0] ordy,output wire [O*W-1:0] od,output wire idle);
 wire [W-1:0] words[0:I-1];for(genvar i=0;i<I;i=i+1)assign words[i]=id[i*W+:W];
 reg [IA-1:0] rotate[0:O-1];wire [O-1:0] chosen_valid,ready;wire [5:0] chosen[0:O-1];wire [O*7-1:0] counts;
 for(genvar o=0;o<O;o=o+1)begin:owners
  wire [63:0] eligible,after_cursor;wire lv,hv;wire [5:0] li,hi;
  for(genvar i=0;i<64;i=i+1)begin:inputs
   if(i<I)begin assign eligible[i]=iv[i]&&words[i][KEY_BIT+:KEY_BITS]==o;assign after_cursor[i]=eligible[i]&&i>=rotate[o];end
   else begin assign eligible[i]=0;assign after_cursor[i]=0;end
  end
  r2_first64 all_first(eligible,lv,li);r2_first64 after_first(after_cursor,hv,hi);
  assign chosen[o]=hv?hi:li;assign chosen_valid[o]=lv;
  sparse_fifo #(.WIDTH(W)) fifo(clk,rst,lv,ready[o],words[chosen[o]],ov[o],ordy[o],od[o*W+:W],counts[o*7+:7]);
  always @(posedge clk)if(rst)rotate[o]<=0;else if(lv&&ready[o])rotate[o]<=rotate[o]==I-1?0:rotate[o]+1;
 end
 always @*begin ir=0;for(integer o=0;o<O;o=o+1)if(chosen_valid[o])ir[chosen[o]]=ready[o];end
 assign idle=counts==0&&ov==0;
endmodule
