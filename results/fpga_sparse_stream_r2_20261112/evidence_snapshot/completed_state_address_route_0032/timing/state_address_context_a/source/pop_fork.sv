`timescale 1ns/1ps
// Each consumer receives exactly once; the producer holds the payload until both ACK.
module r2_pop_fork(input wire clk,rst,iv,output wire ir,
 input wire [31:0] node,input wire [63:0] pair,
 output wire av,input wire ar,output wire [31:0] an,output wire [63:0] ap,
 output wire bv,input wire br,output wire [31:0] bn,output wire [63:0] bp,
 output wire idle,output reg [31:0] accepted);
 reg sent_a,sent_b;
 assign av=iv&&!sent_a;assign bv=iv&&!sent_b;
 assign an=node;assign bn=node;assign ap=pair;assign bp=pair;
 assign ir=(sent_a||ar)&&(sent_b||br);
 assign idle=!iv&&!sent_a&&!sent_b;
 always @(posedge clk)begin
  if(rst)begin sent_a<=0;sent_b<=0;accepted<=0;end
  else if(iv&&ir)begin sent_a<=0;sent_b<=0;accepted<=accepted+1;end
  else begin if(av&&ar)sent_a<=1;if(bv&&br)sent_b<=1;end
 end
endmodule
