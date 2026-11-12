`timescale 1ns/1ps
// Eight independent registered owner queues; conflict arbitration per owner.
module sparse_router(input wire clk,rst,input wire [7:0] iv,output reg [7:0] ir,
 input wire [255:0] nodes,input wire [511:0] pairs,
 output wire [7:0] ov,input wire [7:0] ordy,output wire [255:0] onodes,output wire [511:0] opairs,
 output reg [31:0] conflicts,output wire idle);
 wire [7:0] put_ready;reg [7:0] put;reg [767:0] data;reg [2:0] rr[0:7];integer o,k,l,chosen,requests;wire [55:0] counts;
 always @*begin
  ir=0;put=0;data=0;
  for(integer b=0;b<8;b=b+1)begin
   chosen=-1;
   for(integer p=0;p<8;p=p+1)begin l=(rr[b]+p)%8;if(iv[l]&&nodes[l*32+2+:3]==b&&chosen<0)chosen=l;end
   if(chosen>=0)begin put[b]=iv[chosen];ir[chosen]=put_ready[b];data[b*96+:96]={nodes[chosen*32+:32],pairs[chosen*64+:64]};end
  end
 end
 for(genvar b=0;b<8;b=b+1)begin:output_queues
  wire [95:0] q;
  sparse_fifo #(.WIDTH(96)) fifo(clk,rst,put[b],put_ready[b],data[b*96+:96],ov[b],ordy[b],q,counts[b*7+:7]);
  assign {onodes[b*32+:32],opairs[b*64+:64]}=q;
 end
 assign idle=counts==0&&ov==0;
 always @(posedge clk)if(rst)begin conflicts<=0;for(o=0;o<8;o=o+1)rr[o]<=0;end else begin
  requests=0;for(k=0;k<8;k=k+1)if(iv[k]&&!ir[k])requests=requests+1;
  conflicts<=conflicts+requests;
  for(o=0;o<8;o=o+1)if(put[o]&&put_ready[o])rr[o]<=rr[o]+1;
 end
endmodule
