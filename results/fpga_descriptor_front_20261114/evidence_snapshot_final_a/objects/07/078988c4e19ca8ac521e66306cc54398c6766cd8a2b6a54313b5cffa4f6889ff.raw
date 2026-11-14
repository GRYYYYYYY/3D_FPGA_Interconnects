`timescale 1ns/1ps
module df_fifo #(parameter integer WIDTH=32,DEPTH=4,PTR_W=$clog2(DEPTH))(
 input logic clk,reset,input logic iv,output logic ir,input logic[WIDTH-1:0] idata,
 output logic ov,input logic ordy,output logic[WIDTH-1:0] odata);
 (* ram_style="distributed" *) logic[WIDTH-1:0] mem[DEPTH];
 logic[PTR_W-1:0] rd,wr;logic[PTR_W:0] count;
 assign ir=count<DEPTH;assign ov=count!=0;assign odata=mem[rd];
 always_ff @(posedge clk)begin
  if(reset)begin rd<=0;wr<=0;count<=0;end
  else begin
   if(iv&&ir)begin mem[wr]<=idata;wr<=wr==DEPTH-1?0:wr+1;end
   if(ov&&ordy)rd<=rd==DEPTH-1?0:rd+1;
   case({iv&&ir,ov&&ordy})2'b10:count<=count+1;2'b01:count<=count-1;default:;endcase
  end
 end
endmodule
