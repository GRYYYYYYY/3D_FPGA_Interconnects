`timescale 1ns/1ps
// Positive normal/+0 FP32 addition, round-to-nearest-even, no contraction.
module pair_lane(input wire clk,rst,iv, output wire ir,
 input wire [31:0] dst,input wire [63:0] parent,cost,
 output reg ov,input wire or_,output reg [31:0] od,output reg [63:0] pair,output reg error);
 function automatic legal(input [31:0] x);
 legal=(x==0)||(!x[31]&&x[30:23]!=0&&x[30:23]!=255);
 endfunction
 function automatic [31:0] add(input [31:0] a,b);
 reg [31:0] hi,lo;reg [27:0] m,n,sum;reg [24:0] rounded;
 integer shift,ex,j;reg sticky;
 begin
 if(a==0)add=b;else if(b==0)add=a;else begin
 hi=a>=b?a:b;lo=a>=b?b:a;ex=hi[30:23];shift=ex-lo[30:23];
 m={1'b0,1'b1,hi[22:0],3'b0};n={1'b0,1'b1,lo[22:0],3'b0};sticky=0;
 for(j=0;j<28;j=j+1)if(j<shift)sticky=sticky|n[j];
 n=shift>=28?0:n>>shift;n[0]=n[0]|sticky;sum=m+n;
 if(sum[27])begin sum={1'b0,sum[27:1]};sum[0]=sum[0]|((m+n)&1);ex=ex+1;end
 rounded={1'b0,sum[26:3]}+(sum[2]&&(sum[1]||sum[0]||sum[3]));
 if(rounded[24])begin rounded=rounded>>1;ex=ex+1;end
 add=ex>=255?32'h7f800000:{1'b0,ex[7:0],rounded[22:0]};
 end end endfunction
 assign ir=!ov||or_;
 always @(posedge clk)if(rst)begin ov<=0;error<=0;end else if(ir)begin
 ov<=iv;if(iv)begin od<=dst;pair<={add(parent[63:32],cost[63:32]),add(parent[31:0],cost[31:0])};
 if(!legal(parent[63:32])||!legal(parent[31:0])||!legal(cost[63:32])||!legal(cost[31:0])||
 !legal(add(parent[63:32],cost[63:32]))||!legal(add(parent[31:0],cost[31:0])))error<=1;
 end end
endmodule
