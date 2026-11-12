`timescale 1ns/1ps
// Membership belongs to the node bank, not to cache tags or MSHRs.
// A first mark and physical append happen on the same edge, only with credit.
module changed_queue #(parameter CAP=512,LIMIT=CAP,AW=$clog2(CAP))(
 input wire clk,rst,input wire ev,output wire er,input wire [31:0] line,input wire [3:0] mask,
 input wire commit_phase,output reg ov,input wire issue_ready,output reg [AW-1:0] index,
 input wire ack,input wire [AW-1:0] ack_index,
 output wire idle,output reg error,output reg [AW:0] peak,output wire [AW:0] occupancy);
 (* ram_style="block" *) reg [AW-1:0] ids[0:CAP-1];
 reg [CAP-1:0] marked;reg [AW:0] wr,rd;reg busy;reg [3:0] todo;reg [AW-1:0] base;integer s;
 wire take=commit_phase&&(!ov||issue_ready)&&rd<wr;
 assign er=!busy&&!commit_phase;assign idle=!busy;assign occupancy=wr-rd+ov;
 always @(posedge clk)begin
  if(take)index<=ids[rd[AW-1:0]];
  if(rst)begin marked<=0;wr<=0;rd<=0;busy<=0;todo<=0;ov<=0;error<=0;peak<=0;end else begin
   if(!commit_phase&&!busy&&wr==rd&&!ov)begin wr<=0;rd<=0;end
   if(ev&&er)begin busy<=1;todo<=mask;base<={line[AW:3],2'b00};end
   if(busy)begin
    s=0;if(todo[0])s=0;else if(todo[1])s=1;else if(todo[2])s=2;else s=3;
    if(todo==0)busy<=0;else if(marked[base+s])todo[s]<=0;
    else if(wr<LIMIT)begin ids[wr[AW-1:0]]<=base+s;marked[base+s]<=1;wr<=wr+1;todo[s]<=0;if(wr+1>peak)peak<=wr+1;end
    else error<=1;
   end
   if(take)rd<=rd+1;
   if(commit_phase&&(!ov||issue_ready))ov<=take;
   if(ack)marked[ack_index]<=0;
  end
 end
endmodule
