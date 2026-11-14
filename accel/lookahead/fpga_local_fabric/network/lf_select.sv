`timescale 1ns/1ps
// RR decision contains only keys; wide payload never traverses the priority tree.
// Exactly one input is granted. Pointer advances on capture into a real hold.
module lf_select #(parameter N=32,W=$clog2(N))(
 input wire clk,reset,input wire [N-1:0] valid,input wire accept,
 output wire [N-1:0] grant,output wire any);
 localparam P=2**W;
 reg [W-1:0] cursor;
 wire [2*P-1:1] v;wire [W:0] key[2*P];
 for(genvar i=0;i<P;i=i+1)begin:leaf
  if(i<N)begin assign v[P+i]=valid[i];assign key[P+i]={i<cursor,W'(i)};end
  else begin assign v[P+i]=0;assign key[P+i]=0;end
 end
 for(genvar i=1;i<P;i=i+1)begin:tree
  wire left=v[2*i]&&(!v[2*i+1]||key[2*i]<key[2*i+1]);
  assign v[i]=v[2*i]||v[2*i+1];assign key[i]=left?key[2*i]:key[2*i+1];
 end
 assign any=v[1];
 for(genvar i=0;i<N;i=i+1)assign grant[i]=v[1]&&key[1][W-1:0]==i;
 always @(posedge clk)if(reset)cursor<=0;else if(accept&&any)cursor<=key[1][W-1:0]==N-1?0:key[1][W-1:0]+1;
endmodule
