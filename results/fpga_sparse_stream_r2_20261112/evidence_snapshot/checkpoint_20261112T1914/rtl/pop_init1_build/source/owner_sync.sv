`timescale 1ns/1ps
// 4-way x 32-set cache. One registered tag/data transaction in progress,
// 32 concurrent line misses; 16 writebacks. No asynchronous payload read.
// mem response IDs 0..31 = fill, 32..47 = write acknowledgement.
module sparse_owner(input wire clk,rst,iv,output wire ir,input wire [31:0] node,
 input wire [63:0] pair,input wire fence,output reg fence_done,
 output reg update_valid,input wire update_ready,output reg [31:0] update_line,
 output reg [3:0] update_mask,
 output reg mem_valid,input wire mem_ready,output reg mem_write,output reg [31:0] mem_line,
 output reg [5:0] mem_id,output reg [255:0] mem_data,
 input wire rsp_valid,output wire rsp_ready,input wire [5:0] rsp_id,input wire [255:0] rsp_data,
 output wire idle,output reg error,
 output reg [31:0] accepted,retired,merges,hits,misses,raw_stall,
 output reg [5:0] mshr_peak,output reg [4:0] dirty_peak);
 localparam [63:0] INF=64'h7f8000007f800000;
 wire qv,qr,fifo_ir;
 assign ir=fifo_ir&&!fence;wire [95:0] qd;wire [6:0] qc;
 sparse_fifo #(.WIDTH(96)) request_fifo(clk,rst,iv&&!fence,fifo_ir,{node,pair},qv,qr,qd,qc);
 wire rv,rr;wire [261:0] rd;wire [6:0] rc;
 sparse_fifo #(.WIDTH(262)) response_fifo(clk,rst,rsp_valid,rsp_ready,{rsp_id,rsp_data},rv,rr,rd,rc);
 (* ram_style="block" *) reg [255:0] data_ram[0:127];
 reg [31:0] tags[0:127];reg [127:0] valid,dirty,busy;reg [1:0] replace_way[0:31];
 reg [31:0] mcount[0:31];reg [3:0] resume_state;
 reg [31:0] ml[0:31];reg [6:0] mw[0:31];reg [255:0] mc[0:31];reg [31:0] mv,ms;
 reg [31:0] wl[0:15];(* ram_style="block" *) reg [255:0] wb[0:15];reg [15:0] wv,ws;
 reg [3:0] state;localparam IDLE=0,TAG=1,READ=2,APPLY=3,ALLOC=4,FILL=5,EVENT=6,FLUSH=7,FREAD=8,FWRITE=9;
 reg [31:0] cur_node,cur_line;reg [63:0] cur_pair;reg [6:0] slot;
 reg [5:0] fillid;reg [255:0] filldata;
 reg [7:0] flush_index;reg flushing;
 reg ram_re,ram_we;reg [6:0] ram_ra,ram_wa;reg [255:0] ram_wd,ram_q;
 always @(posedge clk)begin if(ram_re)ram_q<=data_ram[ram_ra];if(ram_we)data_ram[ram_wa]<=ram_wd;end
 integer i,j,hit,matching,free_m,free_w,victim,count_m,count_w,issue_m,issue_w;
 reg [255:0] nextdata;reg [3:0] mask;reg hazard;
 function automatic [63:0] minpair(input [63:0] a,b);minpair=a<b?a:b;endfunction
 always @*begin
  hit=-1;matching=-1;free_m=-1;free_w=-1;victim=-1;count_m=0;count_w=0;issue_m=-1;issue_w=-1;
  for(integer k=0;k<32;k=k+1)begin
   if(mv[k])begin count_m=count_m+1;if(ml[k]==cur_line)matching=k;end else if(free_m<0)free_m=k;
   hazard=0;for(integer l=0;l<16;l=l+1)if(wv[l]&&wl[l]==ml[k])hazard=1;
   if(mv[k]&&!ms[k]&&!hazard&&issue_m<0)issue_m=k;
  end
  for(integer k=0;k<16;k=k+1)begin if(wv[k])count_w=count_w+1;else if(free_w<0)free_w=k;if(wv[k]&&!ws[k]&&issue_w<0)issue_w=k;end
  for(integer w=0;w<4;w=w+1)begin
   if(valid[{w[1:0],cur_line[7:3]}]&&tags[{w[1:0],cur_line[7:3]}]==cur_line)hit={w[1:0],cur_line[7:3]};
   if(!busy[{w[1:0],cur_line[7:3]}]&&!valid[{w[1:0],cur_line[7:3]}]&&victim<0)victim={w[1:0],cur_line[7:3]};
  end
  if(victim<0)for(integer w=0;w<4;w=w+1)if(!busy[{w[1:0],cur_line[7:3]}]&&victim<0)victim={w[1:0],cur_line[7:3]};
  ram_re=state==READ||state==FREAD;ram_ra=slot;ram_we=0;ram_wa=slot;ram_wd=ram_q;nextdata=ram_q;mask=0;
  if(state==APPLY)begin
   if(cur_pair<ram_q[cur_node[1:0]*64+:64])begin nextdata[cur_node[1:0]*64+:64]=cur_pair;mask[cur_node[1:0]]=1;ram_we=1;ram_wd=nextdata;end
  end
  if(state==FILL)begin
   nextdata=filldata;
   for(integer s=0;s<4;s=s+1)if(mc[fillid][s*64+:64]<filldata[s*64+:64])begin nextdata[s*64+:64]=mc[fillid][s*64+:64];mask[s]=1;end
   ram_we=1;ram_wa=mw[fillid];ram_wd=nextdata;
  end
 end
 assign qr=state==IDLE&&!rv&&!flushing&&!update_valid;
 assign rr=(rd[261]||(state==IDLE||state==10))&&!update_valid;
 assign idle=state==IDLE&&!qv&&qc==0&&!rv&&rc==0&&mv==0&&wv==0&&!mem_valid&&!update_valid;
 always @(posedge clk)begin
  if(rst)begin state<=IDLE;valid<=0;dirty<=0;busy<=0;mv<=0;ms<=0;wv<=0;ws<=0;update_valid<=0;mem_valid<=0;fence_done<=0;flushing<=0;flush_index<=0;error<=0;accepted<=0;retired<=0;hits<=0;misses<=0;merges<=0;raw_stall<=0;mshr_peak<=0;dirty_peak<=0;for(i=0;i<32;i=i+1)replace_way[i]<=0;end else begin
   if(iv&&ir&&!fence)accepted<=accepted+1;
   if(count_m>mshr_peak)mshr_peak<=count_m;if(count_w>dirty_peak)dirty_peak<=count_w;
   if(update_valid&&update_ready)update_valid<=0;
   // Elastic command register: replace a consumed command on the same edge.
   if(!mem_valid||mem_ready)begin
    mem_valid<=0;
    if(issue_w>=0)begin mem_valid<=1;mem_write<=1;mem_line<=wl[issue_w];mem_id<=32+issue_w;mem_data<=wb[issue_w];ws[issue_w]<=1;end
    else if(issue_m>=0)begin mem_valid<=1;mem_write<=0;mem_line<=ml[issue_m];mem_id<=issue_m;mem_data<=0;ms[issue_m]<=1;end
   end
   if(!fence)fence_done<=0;
   if(rv&&rr&&rd[261])begin
    if(rd[261:256]>=48||!wv[rd[259:256]])error<=1;
    else begin wv[rd[259:256]]<=0;ws[rd[259:256]]<=0;end
   end
   case(state)
   IDLE:begin
    if(rv&&!update_valid)begin
     if(!rd[261])begin fillid<=rd[261:256];filldata<=rd[255:0];if(!mv[rd[260:256]])error<=1;resume_state<=IDLE;state<=FILL;end
    end else if(qv&&qr)begin cur_node<=qd[95:64];cur_line<=qd[95:66];cur_pair<=qd[63:0];state<=TAG;end
    else if(fence&&qc==0&&!qv&&mv==0&&!update_valid&&!flushing&&!fence_done)begin flushing<=1;flush_index<=0;state<=FLUSH;end
    else if(flushing&&wv==0&&!mem_valid&&!update_valid)begin flushing<=0;fence_done<=1;end
   end
   10:begin
    if(rv&&rr&&!rd[261])begin fillid<=rd[261:256];filldata<=rd[255:0];resume_state<=TAG;state<=FILL;end
    else if(!rv)state<=TAG;
   end
   TAG:begin
    if(matching>=0)begin mc[matching][cur_node[1:0]*64+:64]<=minpair(mc[matching][cur_node[1:0]*64+:64],cur_pair);merges<=merges+1;mcount[matching]<=mcount[matching]+1;state<=IDLE;end
    else if(hit>=0&&!busy[hit])begin slot<=hit;hits<=hits+1;state<=READ;end
    else if(free_m>=0&&victim>=0&&(!dirty[victim]||free_w>=0))begin slot<=victim;state<=READ;end
    // Responses must be serviced while a tag cannot progress: replay this request.
    else begin raw_stall<=raw_stall+1;state<=10;end
   end
   READ:state<=hit>=0?APPLY:ALLOC;
   APPLY:begin
    if(mask!=0)begin resume_state<=IDLE;dirty[slot]<=1;update_valid<=1;update_line<=cur_line;update_mask<=mask;state<=EVENT;end else state<=IDLE;
    retired<=retired+1;
   end
   ALLOC:begin
    if(free_m<0||(dirty[slot]&&free_w<0))error<=1;
    else begin
     if(dirty[slot])begin wv[free_w]<=1;ws[free_w]<=0;wl[free_w]<=tags[slot];wb[free_w]<=ram_q;end
     mcount[free_m]<=1;mv[free_m]<=1;ms[free_m]<=0;ml[free_m]<=cur_line;mw[free_m]<=slot;mc[free_m]<={4{INF}};mc[free_m][cur_node[1:0]*64+:64]<=cur_pair;
     valid[slot]<=0;dirty[slot]<=0;busy[slot]<=1;tags[slot]<=cur_line;misses<=misses+1;state<=IDLE;
    end
   end
   FILL:begin retired<=retired+mcount[fillid];valid[mw[fillid]]<=1;busy[mw[fillid]]<=0;dirty[mw[fillid]]<=mask!=0;mv[fillid]<=0;ms[fillid]<=0;
    if(mask!=0)begin update_valid<=1;update_line<=ml[fillid];update_mask<=mask;state<=EVENT;end else state<=resume_state;
   end
   EVENT:if(update_valid&&update_ready)state<=resume_state;
   FLUSH:if(flush_index==128)state<=IDLE;else if(!dirty[flush_index])flush_index<=flush_index+1;else if(free_w>=0)begin slot<=flush_index;state<=FREAD;end
   FREAD:state<=FWRITE;
   FWRITE:begin wv[free_w]<=1;ws[free_w]<=0;wl[free_w]<=tags[slot];wb[free_w]<=ram_q;dirty[slot]<=0;flush_index<=flush_index+1;state<=FLUSH;end
   default:error<=1;
   endcase
  end
 end
endmodule
