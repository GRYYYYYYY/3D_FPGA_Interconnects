`timescale 1ns/1ps
module r2_cell_router(input wire clk,rst,input wire [7:0] iv,output reg [7:0] ir,input wire [943:0] id,
 output wire [7:0] ov,input wire [7:0] ordy,output wire [943:0] od,output wire idle);
 // Payload {qid6,epoch16,cell32,pair64}; cell bank = low three cell bits.
 wire [117:0] words[0:7];for(genvar w=0;w<8;w=w+1)assign words[w]=id[w*118+:118];
 wire [7:0] qr;reg [7:0] put;reg [943:0] data;reg [2:0] rr[0:7];wire [55:0] counts;integer l,chosen;
 always @*begin ir=0;put=0;data=0;for(integer b=0;b<8;b=b+1)begin chosen=-1;
  for(integer k=0;k<8;k=k+1)begin l=(rr[b]+k)%8;if(iv[l]&&words[l][66:64]==b&&chosen<0)chosen=l;end
  if(chosen>=0)begin put[b]=1;ir[chosen]=qr[b];data[b*118+:118]=words[chosen];end
 end end
 for(genvar b=0;b<8;b=b+1)begin:queues
  sparse_fifo #(.WIDTH(118)) fifo(clk,rst,put[b],qr[b],data[b*118+:118],ov[b],ordy[b],od[b*118+:118],counts[b*7+:7]);
 end
 assign idle=counts==0&&ov==0;
 always @(posedge clk)if(rst)begin for(integer b=0;b<8;b=b+1)rr[b]<=0;end else begin for(integer b=0;b<8;b=b+1)if(put[b]&&qr[b])rr[b]<=rr[b]+1;end
endmodule
