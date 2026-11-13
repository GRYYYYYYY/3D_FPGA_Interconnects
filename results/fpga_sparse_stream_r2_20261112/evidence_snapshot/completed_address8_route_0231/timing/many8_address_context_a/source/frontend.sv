`timescale 1ns/1ps
// Four parent contexts, tagged out-of-order reads, whole 32B edge beats.
module sparse_frontend(input wire clk,rst,input wire pv,output wire pr,input wire [31:0] pn,input wire [63:0] pp,
 input wire [31:0] row_base,edge_base,input wire cost_we,input wire [3:0] cost_index,input wire [63:0] cost_data,
 output reg mem_valid,input wire mem_ready,output reg [31:0] mem_line,output reg [3:0] mem_id,
 input wire rsp_valid,output wire rsp_ready,input wire [3:0] rsp_id,input wire [255:0] rsp_data,
 output wire ov,input wire ordy,output wire [31:0] dst,output wire [63:0] pair,output wire idle,output wire error,
 output reg [31:0] parents,edge_beats,row_beats,candidates,unused_sectors,output reg [2:0] context_peak);
 reg [2:0] state[0:3];localparam FREE=0,ROW=1,ROW_WAIT=2,ROW_NEXT=3,EDGE=4,EDGE_WAIT=5,EMIT=6,NEXT_WAIT=7;
 reg [31:0] node[0:3],pos[0:3],last[0:3];reg [63:0] parent[0:3];reg [255:0] beat[0:3];
 reg [63:0] costs[0:15];reg [1:0] rr;
 // One-line row metadata reuse; all fetches and cache misses counted.
 reg row_valid;reg [31:0] row_tag;reg [255:0] row_cache;
 reg emitv;reg [31:0] emitdst;reg [63:0] emitparent,emitcost;wire emitr,lane_pending,lane_error;reg local_error;
 pair_lane arithmetic(clk,rst,emitv,emitr,emitdst,emitparent,emitcost,ov,ordy,dst,pair,lane_error,lane_pending);
 assign error=lane_error||local_error;
 integer free_ctx,fetch,emit,used,i,s,n;reg [31:0] desc;reg [63:0] a,b;
 always @*begin
  free_ctx=-1;fetch=-1;emit=-1;used=0;
  for(integer c=0;c<4;c=c+1)begin
   if(state[c]==FREE&&free_ctx<0)free_ctx=c;if(state[c]!=FREE)used=used+1;
   if((state[c]==ROW||state[c]==ROW_NEXT||state[c]==EDGE)&&fetch<0)fetch=c;
   n=(rr+c)%4;if(state[n]==EMIT&&emit<0)emit=n;
  end
 end
 assign pr=free_ctx>=0;assign rsp_ready=1;assign idle=used==0&&!mem_valid&&!emitv&&!lane_pending;
 always @(posedge clk)begin
  if(cost_we)costs[cost_index]<=cost_data;
  if(rst)begin for(i=0;i<4;i=i+1)state[i]<=FREE;mem_valid<=0;emitv<=0;rr<=0;row_valid<=0;local_error<=0;parents<=0;edge_beats<=0;row_beats<=0;candidates<=0;unused_sectors<=0;context_peak<=0;end else begin
   if(used>context_peak)context_peak<=used;
   if(pv&&pr)begin state[free_ctx]<=ROW;node[free_ctx]<=pn;parent[free_ctx]<=pp;parents<=parents+1;end
   if(!emitv||emitr)begin emitv<=0;if(emit>=0)begin
    desc=beat[emit][pos[emit][2:0]*32+:32];emitv<=1;emitdst<={4'b0,desc[27:0]};emitparent<=parent[emit];emitcost<=costs[desc[31:28]];candidates<=candidates+1;rr<=emit+1;
    pos[emit]<=pos[emit]+1;
    if(pos[emit]+1==last[emit])state[emit]<=FREE;else if(pos[emit][2:0]==7)state[emit]<=EDGE;
   end end
   if(!mem_valid||mem_ready)begin
    mem_valid<=0;
    if(fetch>=0)begin
     if(state[fetch]==EDGE)begin mem_valid<=1;mem_line<=edge_base+(pos[fetch]>>3);mem_id<={2'b10,fetch[1:0]};state[fetch]<=EDGE_WAIT;edge_beats<=edge_beats+1;end
     else if(state[fetch]==ROW_NEXT)begin mem_valid<=1;mem_line<=row_base+(node[fetch]>>2)+1;mem_id<={2'b01,fetch[1:0]};state[fetch]<=NEXT_WAIT;row_beats<=row_beats+1;end
     else if(row_valid&&row_tag==row_base+(node[fetch]>>2))begin
      a=row_cache[node[fetch][1:0]*64+:64];pos[fetch]<=a[31:0];if(a[63:32]!=0)local_error<=1;
      if(node[fetch][1:0]==3)state[fetch]<=ROW_NEXT;else begin b=row_cache[(node[fetch][1:0]+1)*64+:64];last[fetch]<=b[31:0];if(b[63:32]!=0||b<a)local_error<=1;state[fetch]<=a==b?FREE:EDGE;end
     end else begin mem_valid<=1;mem_line<=row_base+(node[fetch]>>2);mem_id<={2'b00,fetch[1:0]};state[fetch]<=ROW_WAIT;row_beats<=row_beats+1;end
    end
   end
   if(rsp_valid)begin
    s=rsp_id[1:0];
    if(rsp_id[3:2]==2)begin
     beat[s]<=rsp_data;state[s]<=EMIT;
     unused_sectors<=unused_sectors+pos[s][2:0]+((last[s]>>3)==(pos[s]>>3)?8-last[s][2:0]:0);
    end else if(rsp_id[3:2]==1)begin last[s]<=rsp_data[31:0];if(rsp_data[63:32]!=0||rsp_data[31:0]<pos[s])local_error<=1;state[s]<=rsp_data[31:0]==pos[s]?FREE:EDGE;end
    else begin
     row_valid<=1;row_tag<=row_base+(node[s]>>2);row_cache<=rsp_data;
     a=rsp_data[node[s][1:0]*64+:64];pos[s]<=a[31:0];if(a[63:32]!=0)local_error<=1;
     if(node[s][1:0]==3)state[s]<=ROW_NEXT;else begin b=rsp_data[(node[s][1:0]+1)*64+:64];last[s]<=b[31:0];if(b[63:32]!=0||b<a)local_error<=1;state[s]<=a==b?FREE:EDGE;end
    end
   end
  end
 end
endmodule
