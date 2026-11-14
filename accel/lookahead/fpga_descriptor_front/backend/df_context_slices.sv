`timescale 1ns/1ps
// Registered, non-fallthrough, two-entry FIFO. Capacity and ready use pre-edge state.
module df_fifo2 #(parameter integer WIDTH=1)(input wire clk,reset,
 input wire iv,output wire ir,input wire [WIDTH-1:0] id,
 output wire ov,input wire ordy,output wire [WIDTH-1:0] od,output wire empty);
 (* ram_style="registers" *) reg [WIDTH-1:0] payload[0:1];reg rp,wp;reg [1:0] count;
 assign ir=count<2;assign ov=count!=0;assign od=payload[rp];assign empty=count==0;
 wire push=iv&&ir,pop=ov&&ordy;
 always @(posedge clk)begin
  if(reset)begin rp<=0;wp<=0;count<=0;end
  else begin
   if(push)begin payload[wp]<=id;wp<=!wp;end
   if(pop)rp<=!rp;
   case({push,pop})2'b10:count<=count+1;2'b01:count<=count-1;default:;endcase
  end
 end
endmodule
// Capturing a publication is not retirement. ACK returns only after real consume.
module df_ack_slice #(parameter integer WIDTH=1)(input wire clk,reset,
 input wire iv,output wire ir,input wire [WIDTH-1:0] id,
 output wire ov,input wire ordy,output wire [WIDTH-1:0] od,output wire empty);
 localparam IDLE=0,PENDING=1,ACK=2;
 reg [1:0] state;reg [WIDTH-1:0] payload;
 assign ir=state==ACK;assign ov=state==PENDING;assign od=payload;assign empty=state==IDLE;
 always @(posedge clk)begin
  if(reset)state<=IDLE;
  else case(state)
   IDLE:if(iv)begin payload<=id;state<=PENDING;end
   PENDING:if(ordy)state<=ACK;
   ACK:state<=IDLE;
   default:state<=IDLE;
  endcase
 end
endmodule
