`timescale 1ns/1ps
// Membership resides in the external node-state service. Each MARK reserves one
// of 32 response mailboxes before issue; no response or first-mark ID can vanish.
// The worklist is finite. A first mark beyond CAP raises an explicit batch error.
module r2_external_changed #(parameter CAP=1024,AW=$clog2(CAP),STYLE="block")(
 input wire clk,rst,input wire ev,output wire er,input wire [31:0] line,input wire [3:0] mask,
 input wire commit_phase,output wire cv,input wire cr,output wire [31:0] node,
 output reg mv,input wire mr,output reg [31:0] mn,output reg [4:0] mid,
 input wire rv,input wire [4:0] rid,input wire [31:0] rn,input wire first_mark,
 output wire mark_idle,output reg error,output reg [AW:0] peak,output wire [AW:0] occupancy,
 output reg [31:0] mark_requests,duplicates,unique_ids);
 wire [3:0] qv,qir;reg [3:0] qr;wire [31:0] qnode[0:3];wire [27:0] qcounts;
 reg [31:0] live,sent,ready;reg [31:0] context_node[0:31];reg [1:0] rotate;
 integer free_context,request_sector,publish_context,k;
 always @*begin
  free_context=-1;request_sector=-1;publish_context=-1;qr=0;
  for(integer i=0;i<32;i=i+1)begin if(!live[i]&&free_context<0)free_context=i;if(live[i]&&ready[i]&&publish_context<0)publish_context=i;end
  for(integer i=0;i<4;i=i+1)begin k=(rotate+i)%4;if(qv[k]&&request_sector<0)request_sector=k;end
  if((!mv||mr)&&free_context>=0&&request_sector>=0&&!commit_phase)qr[request_sector]=1;
 end
 assign er=!commit_phase&&((qir|~mask)==4'hf);
 for(genvar s=0;s<4;s=s+1)begin:requests
  sparse_fifo #(.WIDTH(32)) fifo(clk,rst,ev&&er&&mask[s],qir[s],{line[29:0],s[1:0]},qv[s],qr[s],qnode[s],qcounts[s*7+:7]);
 end
 wire list_ready;wire list_put=publish_context>=0;
 wire [31:0] list_data=publish_context>=0?context_node[publish_context]:0;
 sparse_fifo #(.WIDTH(32),.DEPTH(CAP),.STYLE(STYLE)) list(clk,rst,list_put,list_ready,list_data,cv,cr&&commit_phase,node,occupancy);
 assign mark_idle=qv==0&&qcounts==0&&!mv&&live==0;
 always @(posedge clk)begin
  if(rst)begin live<=0;sent<=0;ready<=0;mv<=0;error<=0;rotate<=0;peak<=0;mark_requests<=0;duplicates<=0;unique_ids<=0;end
  else begin
   if(occupancy>peak)peak<=occupancy;
   if(mv&&mr)sent[mid]<=1;
   if(!mv||mr)begin mv<=0;if(free_context>=0&&request_sector>=0&&!commit_phase)begin
    mv<=1;mid<=free_context;mn<=qnode[request_sector];live[free_context]<=1;sent[free_context]<=0;ready[free_context]<=0;context_node[free_context]<=qnode[request_sector];rotate<=request_sector+1;mark_requests<=mark_requests+1;
   end end
   if(rv)begin
    if(!live[rid]||!sent[rid]||ready[rid]||context_node[rid]!=rn)error<=1;
    else if(first_mark)ready[rid]<=1;else begin live[rid]<=0;sent[rid]<=0;duplicates<=duplicates+1;end
   end
   if(list_put&&list_ready)begin live[publish_context]<=0;sent[publish_context]<=0;ready[publish_context]<=0;unique_ids<=unique_ids+1;end
   if(list_put&&!list_ready&&!commit_phase)error<=1;
  end
 end
endmodule
