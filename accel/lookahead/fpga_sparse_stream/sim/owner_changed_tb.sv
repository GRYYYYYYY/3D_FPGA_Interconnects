`timescale 1ns/1ps
// Semantic component composition test, not the 512-node tile configuration.
// CAP4096 admits 768 owner-local lines, forcing eviction of the 128-line cache.
module owner_changed_tb(input wire clk,rst,iv,output wire ir,input wire [31:0] node,
 input wire [63:0] pair,input wire fence,output wire fence_done,
 output wire update_valid,input wire update_ready,output wire [31:0] update_line,output wire [3:0] update_mask,
 output wire mem_valid,input wire mem_ready,output wire mem_write,output wire [31:0] mem_line,
 output wire [5:0] mem_id,output wire [255:0] mem_data,
 input wire rsp_valid,output wire rsp_ready,input wire [5:0] rsp_id,input wire [255:0] rsp_data,
 output wire idle,error,output wire [31:0] accepted,retired,merges,hits,misses,raw_stall,
 output wire [5:0] mshr_peak,output wire [4:0] dirty_peak,
 input wire commit_phase,commit_ready,commit_ack,input wire [11:0] ack_index,
 output wire commit_valid,output wire [11:0] commit_index,output wire [12:0] occupancy,
 output wire [4095:0] marked_debug);
 wire uv,er,owner_done,owner_error,queue_idle,queue_error;wire [12:0] peak;
 sparse_owner owner(clk,rst,iv,ir,node,pair,fence,owner_done,uv,er&&update_ready,update_line,update_mask,
  mem_valid,mem_ready,mem_write,mem_line,mem_id,mem_data,rsp_valid,rsp_ready,rsp_id,rsp_data,
  idle,owner_error,accepted,retired,merges,hits,misses,raw_stall,mshr_peak,dirty_peak);
 changed_queue #(.CAP(4096)) changes(clk,rst,uv&&update_ready,er,update_line,update_mask,
  commit_phase,commit_valid,commit_ready,commit_index,commit_ack,ack_index,queue_idle,queue_error,peak,occupancy);
 assign update_valid=uv&&er;
 assign fence_done=owner_done&&queue_idle;
 assign error=owner_error||queue_error;
 // Read-only assertion visibility; no testbench value drives membership state.
 assign marked_debug=changes.marked;
endmodule
