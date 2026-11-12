`timescale 1ns/1ps
// Four independent sector append ports consume a complete changed-line mask
// each cycle. Marks stay reserved until commit ACK, independently of cache tags.
module changed_queue_pipe #(parameter CAP=512,LIMIT=CAP,AW=$clog2(CAP))(
 input wire clk,rst,input wire ev,output wire er,input wire [31:0] line,input wire [3:0] mask,
 input wire commit_phase,output reg ov,input wire issue_ready,output reg [AW-1:0] index,
 input wire ack,input wire [AW-1:0] ack_index,
 output wire idle,output reg error,output reg [AW:0] peak,output wire [AW:0] occupancy);
 reg [CAP-1:0] marked;reg [AW:0] reserved;reg [1:0] rotate;
 wire [AW-3:0] group_index=line[AW:3];
 wire [3:0] qv,qi_ready;reg [3:0] qr;wire [4*(AW-2)-1:0] qdata;wire [4*(AW-1)-1:0] qcount;
 reg [3:0] fresh;integer additions,selected,n;reg all_ready;
 always @*begin
  additions=0;fresh=0;all_ready=1;qr=0;selected=-1;
  for(integer s=0;s<4;s=s+1)begin fresh[s]=mask[s]&&!marked[{group_index,s[1:0]}];if(fresh[s])begin additions=additions+1;if(!qi_ready[s])all_ready=0;end end
  for(integer s=0;s<4;s=s+1)begin n=(rotate+s)%4;if(qv[n]&&selected<0)selected=n;end
  if(commit_phase&&(!ov||issue_ready)&&selected>=0)qr[selected]=1;
 end
 assign er=!commit_phase&&all_ready&&reserved+additions<=LIMIT;
 assign idle=1;assign occupancy=reserved;
 for(genvar s=0;s<4;s=s+1)begin:sectors
  sparse_fifo #(.WIDTH(AW-2),.DEPTH(CAP/4)) fifo(clk,rst,ev&&er&&fresh[s],qi_ready[s],group_index,qv[s],qr[s],qdata[s*(AW-2)+:AW-2],qcount[s*(AW-1)+:AW-1]);
 end
 always @(posedge clk)begin
  if(rst)begin marked<=0;reserved<=0;rotate<=0;ov<=0;index<=0;peak<=0;error<=0;end else begin
   if(ev&&er)begin
    for(integer s=0;s<4;s=s+1)if(fresh[s])marked[{group_index,s[1:0]}]<=1;
    if(reserved+additions>peak)peak<=reserved+additions;
    if((line>>3)>=CAP/4)error<=1;
   end
   if(ack)begin if(!marked[ack_index])error<=1;marked[ack_index]<=0;end
   reserved<=reserved+((ev&&er)?additions:0)-(ack?1:0);
   if(commit_phase&&(!ov||issue_ready))begin ov<=selected>=0;if(selected>=0)begin index<={qdata[selected*(AW-2)+:AW-2],selected[1:0]};rotate<=selected+1;end end
   if(!commit_phase&&ov)error<=1;
   if(ev&&!commit_phase&&reserved+additions>LIMIT)error<=1;
  end
 end
endmodule
