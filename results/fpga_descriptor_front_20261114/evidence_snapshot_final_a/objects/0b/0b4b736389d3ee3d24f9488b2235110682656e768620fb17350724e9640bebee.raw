`timescale 1ns/1ps
// Start only at a directory wave fence: every bank externally quiescent.
// One MIN command/bank, one captured response/bank, then actual6stage tree.
module df_min_collect(input logic clk,reset,input logic start,output logic ready,
 input logic[63:0] bank_ready,output logic[63:0] bank_command,
 input logic[63:0] bank_valid,output logic[63:0] bank_accept,
 input logic[63:0] bank_empty,input logic[64*12-1:0] bank_bucket,
 output logic ov,input logic ordy,output logic empty,output logic[11:0] minimum);
 localparam IDLE=0,QUERY=1,FEED=2,RESULT=3;
 logic[1:0] state;logic[63:0] sent,seen,held_valid;logic[64*12-1:0]held_bucket;
 logic tree_iv,tree_ir,tree_ov;logic[63:0]seen_next;
 assign ready=state==IDLE&&(&bank_ready);
 assign bank_command=state==QUERY?~sent:64'b0;
 assign bank_accept=state==QUERY?(sent&~seen):64'b0;
 assign tree_iv=state==FEED;assign ov=state==RESULT&&tree_ov;
 df_min_tree tree(.clk,.reset,.iv(tree_iv),.ir(tree_ir),.valid(held_valid),.bucket(held_bucket),.ov(tree_ov),.ordy(ordy&&state==RESULT),.empty,.minimum);
 always_comb seen_next=seen|(bank_valid&bank_accept);
 always_ff @(posedge clk)begin
  if(reset)begin state<=IDLE;sent<=0;seen<=0;held_valid<=0;held_bucket<=0;end
  else case(state)
   IDLE:if(start&&ready)begin state<=QUERY;sent<=0;seen<=0;end
   QUERY:begin
    sent<=sent|(bank_command&bank_ready);seen<=seen_next;
    for(integer b=0;b<64;b=b+1)if(bank_valid[b]&&bank_accept[b])begin held_valid[b]<=!bank_empty[b];held_bucket[b*12+:12]<=bank_bucket[b*12+:12];end
    if(&seen_next)state<=FEED;
   end
   FEED:if(tree_ir)state<=RESULT;
   RESULT:if(tree_ov&&ordy)state<=IDLE;
  endcase
 end
endmodule
