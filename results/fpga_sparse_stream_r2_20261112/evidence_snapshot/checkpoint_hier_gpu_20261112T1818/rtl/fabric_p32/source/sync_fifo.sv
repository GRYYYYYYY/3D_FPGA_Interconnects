`timescale 1ns/1ps
module sparse_fifo #(parameter WIDTH=96, DEPTH=64, AW=$clog2(DEPTH))(
 input wire clk,rst,iv,output wire ir,input wire [WIDTH-1:0] id,
 output reg ov,input wire ordy,output reg [WIDTH-1:0] od,output wire [AW:0] occupancy);
 (* ram_style="block" *) reg [WIDTH-1:0] payload[0:DEPTH-1];
 reg [AW-1:0] wp,rp;reg [AW:0] count;
 wire take=(!ov||ordy)&&count!=0;wire put=iv&&ir;
 assign occupancy=count+ov;
 assign ir=occupancy<DEPTH||(ov&&ordy);
 always @(posedge clk)begin
  if(put)payload[wp]<=id;
  if(take)od<=payload[rp];
  if(rst)begin wp<=0;rp<=0;count<=0;ov<=0;end else begin
   if(put)wp<=wp==DEPTH-1?0:wp+1;
   if(take)rp<=rp==DEPTH-1?0:rp+1;
   case({put,take})2'b10:count<=count+1;2'b01:count<=count-1;default:;endcase
   if(!ov||ordy)ov<=take;
  end
 end
endmodule
