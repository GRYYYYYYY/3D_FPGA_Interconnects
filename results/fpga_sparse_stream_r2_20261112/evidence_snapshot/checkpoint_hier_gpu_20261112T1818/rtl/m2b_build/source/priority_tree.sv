`timescale 1ns/1ps
// Balanced binary selection, not a serial 64-element priority-for loop.
module r2_first64(input wire [63:0] mask,output wire valid,output wire [5:0] index);
 wire [6:0] tree[1:127];
 for(genvar i=0;i<64;i=i+1)begin:leaves
  assign tree[64+i]={!mask[i],6'(i)};
 end
 for(genvar i=1;i<64;i=i+1)begin:branches
  assign tree[i]=!tree[2*i][6]?tree[2*i]:tree[2*i+1];
 end
 assign valid=!tree[1][6];assign index=tree[1][5:0];
endmodule

module r2_min8(input wire clk,rst,input wire [7:0] valid,
 input wire [103:0] keys,input wire [63:0] epochs,
 output reg ov,output reg [12:0] key,output reg [7:0] epoch);
 reg [12:0] a[0:3],b[0:1];reg [7:0] ae[0:3],be[0:1];reg [3:0] av;reg [1:0] bv;
 always @(posedge clk)begin
  if(rst)begin av<=0;bv<=0;ov<=0;key<=13'h1fff;epoch<=0;end else begin
   for(integer i=0;i<4;i=i+1)begin
    a[i]<=keys[(2*i)*13+:13]<keys[(2*i+1)*13+:13]?keys[(2*i)*13+:13]:keys[(2*i+1)*13+:13];
    ae[i]<=epochs[(2*i)*8+:8];av[i]<=valid[2*i]&&valid[2*i+1]&&epochs[(2*i)*8+:8]==epochs[(2*i+1)*8+:8];
   end
   for(integer i=0;i<2;i=i+1)begin b[i]<=a[2*i]<a[2*i+1]?a[2*i]:a[2*i+1];be[i]<=ae[2*i];bv[i]<=av[2*i]&&av[2*i+1]&&ae[2*i]==ae[2*i+1];end
   key<=b[0]<b[1]?b[0]:b[1];epoch<=be[0];ov<=(&bv)&&be[0]==be[1];
  end
 end
endmodule
