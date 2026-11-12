`timescale 1ns/1ps
// Local node bank, finite linked-member allocator, sparse active/closed traversal.
// Commands: 1=initialize sample, 2=pop selected bucket, 3=commit changed, 4=close.
module sparse_bank #(parameter BANK=0,NC=512,MC=1024,CLOSED_LIMIT=NC,NA=$clog2(NC),MA=$clog2(MC))(
 input wire clk,rst,input wire [2:0] command,input wire [11:0] bucket,input wire [31:0] source,
 output reg done,output wire has_bucket,output reg [11:0] min_bucket,output reg error,
 output reg pv,input wire pr,output reg [31:0] pn,output reg [63:0] pp,
 input wire cv,output reg ca,input wire [NA-1:0] ci,
 output reg close_valid,input wire close_ready,output reg [31:0] close_node,output reg [63:0] close_pair,
 output reg mem_valid,input wire mem_ready,output reg mem_write,output reg [31:0] mem_line,output reg [255:0] mem_data,
 input wire rsp_valid,input wire [255:0] rsp_data,
 output reg [31:0] active_count,commit_count,closed_count,stale_count,output reg [MA:0] member_peak);
 localparam [63:0] INF=64'h7f8000007f800000;
 localparam [31:0] NIL=32'hffffffff;
 (* ram_style="block" *) reg [63:0] labels[0:NC-1];
 (* ram_style="block" *) reg [31:0] pending[0:NC-1];
 (* ram_style="block" *) reg [63:0] directory[0:4095];
 (* ram_style="block" *) reg [63:0] members[0:MC-1];
 (* ram_style="block" *) reg [MA-1:0] free_ids[0:MC-1];
 (* ram_style="block" *) reg [NA-1:0] closed[0:NC-1];
 reg [NC-1:0] closed_mark;reg [4095:0] bitmap;reg [63:0] groups;
 reg [MA:0] free_count;reg [NA:0] closed_wr,closed_rd;reg [(MA>NA?MA:NA):0] initidx;
 reg [63:0] label_q,dir_q,member_q;reg [31:0] pending_q;reg [MA-1:0] free_q;reg [NA-1:0] closed_q;
 reg [NA-1:0] idx;reg [11:0] key;reg [31:0] pointer,allocated,tail_ptr;reg [63:0] tail_value,new_label;
 reg [15:0] version;reg [7:0] state;integer i,g,k;reg found;
 localparam IDLE=0,INIT=1,INITMEM=2,INITWAIT=3,SEED=4,POPHEAD=5,POPSTART=6,POPMEMBER=7,POPMETA=8,POPVALID=9,POPLABEL=10,POPEMIT=11,COMMIT=12,CREAD=13,CWAIT=14,CMETA=15,CWRITE=16,APPEND=17,ALLOC=18,TAILREAD=19,TAILWRITE=20,PUBLISH=21,CACK=22,CLOSE=23,CLOSEIDX=24,CLOSELABEL=25,CLOSEEMIT=26;
 function automatic [31:0] global_node(input [NA-1:0] n);global_node=((n>>2)<<5)|(BANK<<2)|(n&3);endfunction
 assign has_bucket=groups!=0;
 always @*begin min_bucket=0;found=0;g=0;for(integer a=0;a<64;a=a+1)if(groups[a]&&!found)begin g=a;found=1;end found=0;for(integer b=0;b<64;b=b+1)if(bitmap[g*64+b]&&!found)begin min_bucket=g*64+b;found=1;end end
 always @(posedge clk)begin
  // Explicit synchronous read ports. States below consume on following edges.
  label_q<=labels[idx];pending_q<=pending[idx];dir_q<=directory[key];member_q<=members[pointer[MA-1:0]];free_q<=free_ids[(free_count-1)&(MC-1)];closed_q<=closed[closed_rd[NA-1:0]];
  if(rst)begin state<=IDLE;done<=0;error<=0;pv<=0;close_valid<=0;ca<=0;mem_valid<=0;bitmap<=0;groups<=0;closed_mark<=0;closed_wr<=0;closed_rd<=0;free_count<=MC;member_peak<=0;active_count<=0;commit_count<=0;closed_count<=0;stale_count<=0;end else begin
   ca<=0;if(mem_valid&&mem_ready)mem_valid<=0;if(pv&&pr)pv<=0;if(close_valid&&close_ready)close_valid<=0;
   if(command==0)done<=0;
   case(state)
   IDLE:if(command!=0&&!done)begin
    case(command)
    1:begin initidx<=0;closed_wr<=0;closed_rd<=0;bitmap<=0;groups<=0;closed_mark<=0;free_count<=MC;state<=INIT;end
    2:begin key<=bucket;state<=POPHEAD;end
    3:state<=COMMIT;
    4:begin closed_rd<=0;state<=CLOSE;end
    default:error<=1;endcase
   end
   INIT:begin
    if(initidx<MC)free_ids[initidx[MA-1:0]]<=initidx[MA-1:0];
    if(initidx<NC)begin labels[initidx[NA-1:0]]<=global_node(initidx[NA-1:0])==source?64'b0:INF;pending[initidx[NA-1:0]]<=0;end
    if(initidx==(MC>NC?MC:NC)-1)begin initidx<=0;state<=INITMEM;end else initidx<=initidx+1;
   end
   INITMEM:if(!mem_valid)begin
    mem_valid<=1;mem_write<=1;mem_line<=(initidx<<3)|BANK;mem_data<={4{INF}};
    for(i=0;i<4;i=i+1)if(((initidx<<5)|(BANK<<2)|i)==source)mem_data[i*64+:64]<=0;
    state<=INITWAIT;
   end
   INITWAIT:if(rsp_valid)begin if(initidx==NC/4-1)begin idx<=((source>>5)<<2)|(source&3);state<=SEED;end else begin initidx<=initidx+1;state<=INITMEM;end end
   SEED:begin if(source[4:2]==BANK)begin key<=0;version<=1;new_label<=0;state<=APPEND;end else begin state<=IDLE;done<=1;end end
   POPHEAD:state<=POPSTART;
   POPSTART:begin
    if(!bitmap[key])begin done<=1;state<=IDLE;end else begin
     pointer<=dir_q[63:32];bitmap[key]<=0;
     if((bitmap[key[11:6]*64+:64]&~(64'b1<<key[5:0]))==0)groups[key[11:6]]<=0;
     state<=POPMEMBER;
    end
   end
   POPMEMBER:if(pointer==NIL)begin state<=IDLE;done<=1;end else state<=POPMETA;
   POPMETA:begin idx<=member_q[32+:NA];version<=member_q[63:48];tail_ptr<=member_q[31:0];free_ids[free_count[MA-1:0]]<=pointer[MA-1:0];free_count<=free_count+1;state<=POPVALID;end
   POPVALID:state<=POPLABEL;
   POPLABEL:begin
    if(!pending_q[28]||pending_q[27:12]!=version||pending_q[11:0]!=key)begin stale_count<=stale_count+1;pointer<=tail_ptr;state<=POPMEMBER;end
    else begin pending[idx]<=0;
     if(!closed_mark[idx])begin if(closed_wr==CLOSED_LIMIT)error<=1;else begin closed[closed_wr[NA-1:0]]<=idx;closed_mark[idx]<=1;closed_wr<=closed_wr+1;end end
     pv<=1;pn<=global_node(idx);pp<=label_q;state<=POPEMIT;
    end
   end
   POPEMIT:if(pv&&pr)begin active_count<=active_count+1;pointer<=tail_ptr;state<=POPMEMBER;end
   COMMIT:if(cv)begin idx<=ci;state<=CREAD;end else begin done<=1;state<=IDLE;end
   CREAD:if(!mem_valid)begin mem_valid<=1;mem_write<=0;mem_line<=global_node(idx)>>2;state<=CWAIT;end
   CWAIT:if(rsp_valid)begin new_label<=rsp_data[idx[1:0]*64+:64];state<=CMETA;end
   CMETA:state<=CWRITE;
   CWRITE:begin
    if(new_label>=label_q)error<=1;
    labels[idx]<=new_label;commit_count<=commit_count+1;key<=new_label[63:52];version<=pending_q[27:12]+1;
    if(pending_q[28]&&pending_q[11:0]==new_label[63:52])state<=CACK;else state<=APPEND;
   end
   APPEND:if(free_count==0)error<=1;else state<=ALLOC;
   ALLOC:begin allocated<=free_q;free_count<=free_count-1;tail_ptr<=dir_q[31:0];pointer<=dir_q[31:0];tail_value<=dir_q;
    if(MC-free_count+1>member_peak)member_peak<=MC-free_count+1;
    state<=bitmap[key]?TAILREAD:PUBLISH;
   end
   TAILREAD:state<=TAILWRITE;
   TAILWRITE:begin members[tail_ptr[MA-1:0]]<={member_q[63:32],allocated};state<=PUBLISH;end
   PUBLISH:begin
    members[allocated[MA-1:0]]<={version,{{(16-NA){1'b0}},idx},NIL};
    directory[key]<={bitmap[key]?tail_value[63:32]:allocated,allocated};
    bitmap[key]<=1;groups[key[11:6]]<=1;pending[idx]<={3'b0,1'b1,version,key};state<=CACK;
   end
   CACK:begin
    if(command==1)begin done<=1;state<=IDLE;end else begin ca<=1;state<=27;end
   end
   27:state<=COMMIT;
   CLOSE:if(closed_rd==closed_wr)begin closed_wr<=0;done<=1;state<=IDLE;end else state<=CLOSEIDX;
   CLOSEIDX:begin idx<=closed_q;state<=CLOSELABEL;end
   CLOSELABEL:state<=CLOSEEMIT;
   CLOSEEMIT:if(!close_valid)begin close_valid<=1;close_node<=global_node(idx);close_pair<=label_q;end else if(close_ready)begin close_valid<=0;closed_mark[idx]<=0;closed_rd<=closed_rd+1;closed_count<=closed_count+1;state<=CLOSE;end
   default:error<=1;
   endcase
  end
 end
endmodule
