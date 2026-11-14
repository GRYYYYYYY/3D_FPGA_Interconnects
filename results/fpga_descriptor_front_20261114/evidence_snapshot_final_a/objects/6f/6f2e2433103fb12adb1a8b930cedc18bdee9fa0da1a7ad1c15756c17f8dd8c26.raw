`timescale 1ns/1ps
// Return ports are existing common-network MISC source holding registers.
// They carry only this sample's output-write ACKs, after network tag validation.
module df_output_context #(parameter integer GROUPS=16,AW=12,CW=AW+3,ACK_W=64)(
 input logic clk,reset,input logic[GROUPS-1:0] iv,output logic[GROUPS-1:0] ir,
 input logic[GROUPS*CW-1:0] icell,input logic[GROUPS*64-1:0] ipair,
 output logic[7:0] ov,input logic[7:0] ordy,
 output logic[8*CW-1:0] ocell,output logic[511:0] opair,
 output logic[7:0] first,improved,output logic init_done,idle,
 input logic export_start,output logic export_ready,input logic[CW:0] cells,
 input logic[63:0] output_base_line,
 output logic[1:0] write_v,input logic[1:0] write_r,
 output logic[127:0] write_line,output logic[511:0] write_data,
 input logic[31:0]return_v,output logic[31:0]return_r,
 input logic[32*ACK_W-1:0]return_id,
 output logic[1:0]ack_v,ack_r,output logic[2*ACK_W-1:0]ack_id,
 output logic export_done,error,
 output logic[CW-1:0] issued_count,acked_count,
 output logic[4:0]packing_occupancy);
 df_ack_collector #(.WIDTH(ACK_W)) collector(.clk(clk),.reset(reset),.iv(return_v),.ir(return_r),.idata(return_id),.ov(ack_v),.ordy(ack_r),.odata(ack_id));
 df_output_service #(.GROUPS(GROUPS),.AW(AW),.CW(CW)) core(.clk(clk),.reset(reset),.iv(iv),.ir(ir),.icell(icell),.ipair(ipair),.ov(ov),.ordy(ordy),.ocell(ocell),.opair(opair),.first(first),.improved(improved),.init_done(init_done),.idle(idle),.export_start(export_start),.export_ready(export_ready),.cells(cells),.output_base_line(output_base_line),.write_v(write_v),.write_r(write_r),.write_line(write_line),.write_data(write_data),.ack_v(ack_v),.ack_r(ack_r),.export_done(export_done),.error(error),.issued_count(issued_count),.acked_count(acked_count),.packing_occupancy(packing_occupancy));
endmodule
