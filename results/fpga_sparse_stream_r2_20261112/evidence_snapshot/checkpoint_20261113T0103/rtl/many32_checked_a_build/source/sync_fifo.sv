`timescale 1ns/1ps
module sparse_fifo #(parameter WIDTH=96, DEPTH=64, AW=$clog2(DEPTH),STYLE="block",REGISTERED_READY=1,OUTPUT_STAGE=0)(
 input wire clk,rst,iv,output wire ir,input wire [WIDTH-1:0] id,
 output wire ov,input wire ordy,output wire [WIDTH-1:0] od,output wire [AW:0] occupancy);
 (* ram_style=STYLE *) reg [WIDTH-1:0] payload[0:DEPTH-1];
 reg [AW-1:0] wp,rp;reg [AW:0] count;
 reg read_valid;reg [WIDTH-1:0] read_data;wire read_ready;
 wire take=(!read_valid||read_ready)&&count!=0;wire put=iv&&ir;
 // Admission counts every live word, including both output stages. The optional
 // FF after the synchronous RAM does not enlarge the configured FIFO capacity.
 if(OUTPUT_STAGE)begin:output_stage
  reg valid;reg [WIDTH-1:0] data;
  assign read_ready=!valid||ordy;
  assign ov=valid;assign od=data;
  assign occupancy=count+read_valid+valid;
  always @(posedge clk)begin
   if(read_ready)begin valid<=read_valid;if(read_valid)data<=read_data;end
   if(rst)valid<=0;
  end
 end else begin:direct_output
  assign ov=read_valid;assign od=read_data;assign read_ready=ordy;
  assign occupancy=count+read_valid;
 end
 assign ir=occupancy<DEPTH||(!REGISTERED_READY&&ov&&ordy);
 always @(posedge clk)begin
  if(put)payload[wp]<=id;
  if(take)read_data<=payload[rp];
  if(rst)begin wp<=0;rp<=0;count<=0;read_valid<=0;end else begin
   if(put)wp<=wp==DEPTH-1?0:wp+1;
   if(take)rp<=rp==DEPTH-1?0:rp+1;
   case({put,take})2'b10:count<=count+1;2'b01:count<=count-1;default:;endcase
   if(!read_valid||read_ready)read_valid<=take;
  end
 end
endmodule
