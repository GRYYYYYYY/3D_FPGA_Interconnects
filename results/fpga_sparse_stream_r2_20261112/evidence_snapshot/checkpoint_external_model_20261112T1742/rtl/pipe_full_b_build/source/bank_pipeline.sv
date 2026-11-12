`timescale 1ns/1ps
// Local node bank, finite linked-member allocator, sparse active/closed traversal.
// Commands: 1=initialize sample, 2=pop selected bucket, 3=commit changed, 4=close.
module sparse_bank_pipe #(parameter POP_REDUCE=1,INIT_OUTSTANDING=16,BANK=0,NC=512,MC=1024,CLOSED_LIMIT=NC,NA=$clog2(NC),MA=$clog2(MC))(
 input wire clk,rst,input wire [2:0] command,input wire [11:0] bucket,input wire [31:0] source,
 output reg done,output reg has_bucket,output reg [11:0] min_bucket,output reg error,
 output reg pv,input wire pr,output reg [31:0] pn,output reg [63:0] pp,
 input wire cv,output reg ca,input wire [NA-1:0] ci,
 output wire issue_ready,output reg [NA-1:0] commit_index,
 output reg close_valid,input wire close_ready,output reg [31:0] close_node,output reg [63:0] close_pair,
 output reg mem_valid,input wire mem_ready,output reg mem_write,output reg [31:0] mem_line,output reg [255:0] mem_data,
 input wire rsp_valid,input wire [255:0] rsp_data,
 output reg [5:0] mem_id,input wire [5:0] rsp_id,
 output reg [31:0] active_count,commit_count,closed_count,stale_count,output reg [MA:0] member_peak);
 localparam [63:0] INF=64'h7f8000007f800000;
 localparam [31:0] NIL=32'hffffffff;
 (* ram_style="block" *) reg [63:0] labels[0:NC-1];
 (* ram_style="block" *) reg [31:0] pending[0:NC-1];
 (* ram_style="block" *) reg [63:0] directory[0:4095];
 (* ram_style="block" *) reg [31:0] member_header[0:MC-1],member_next[0:MC-1];
 reg [31:0] header_q,next_q;
 wire pool_iv,pool_ir,pool_ov,pool_or;wire [MA-1:0] pool_in,pool_out;wire [MA:0] pool_count;
 sparse_fifo #(.WIDTH(MA),.DEPTH(MC)) pool(clk,rst,pool_iv,pool_ir,pool_in,pool_ov,pool_or,pool_out,pool_count);


 (* ram_style="block" *) reg [NA-1:0] closed[0:NC-1];
 reg [15:0] context_valid,context_sent,context_ready;
 reg [NA-1:0] context_index[0:15];reg [63:0] context_value[0:15];reg [3:0] active_context;
 integer free_context,send_context,ready_context;
 always @*begin free_context=-1;send_context=-1;ready_context=-1;
  for(integer c=0;c<16;c=c+1)begin
   if(!context_valid[c]&&free_context<0)free_context=c;
   if(context_valid[c]&&!context_sent[c]&&send_context<0)send_context=c;
   if(context_valid[c]&&context_ready[c]&&ready_context<0)ready_context=c;
  end
 end
 assign issue_ready=command==3&&free_context>=0;
 reg [NC-1:0] closed_mark;reg [4095:0] bitmap;reg [63:0] groups;
 reg [MA:0] free_count;reg [NA:0] closed_wr,closed_rd;reg [(MA>NA?MA:NA):0] initidx;
 reg [63:0] label_q,directory_read;wire [63:0] dir_q=directory_read;wire [63:0] member_q={header_q,next_q};reg [31:0] pending_q;reg [NA-1:0] closed_q;
 reg [NA-1:0] idx;reg [11:0] key;reg [31:0] pointer,allocated,tail_ptr;reg [63:0] tail_value,new_label;
 reg [15:0] init_busy;integer init_free;reg [NA:0] init_sent,init_acked;
 wire group_valid,word_valid;wire [5:0] group_index,word_index;reg [5:0] selected_group;reg [63:0] selected_word;
 r2_first64 first_group(groups,group_valid,group_index);
 r2_first64 first_word(selected_word,word_valid,word_index);
 always @*begin init_free=-1;for(integer j=0;j<INIT_OUTSTANDING;j=j+1)if(!init_busy[j]&&init_free<0)init_free=j;end
 reg [15:0] version;reg [7:0] state;integer i,g,k;reg found;
 localparam IDLE=0,INIT=1,INITMEM=2,INITWAIT=3,SEED=4,POPHEAD=5,POPSTART=6,POPMEMBER=7,POPMETA=8,POPVALID=9,POPLABEL=10,POPEMIT=11,COMMIT=12,CREAD=13,CWAIT=14,CMETA=15,CWRITE=16,APPEND=17,ALLOC=18,TAILREAD=19,TAILWRITE=20,PUBLISH=21,CACK=22,CLOSE=23,CLOSEIDX=24,CLOSELABEL=25,CLOSEEMIT=26;
 function automatic [31:0] global_node(input [NA-1:0] n);global_node=((n>>2)<<5)|(BANK<<2)|(n&3);endfunction

 // Three overlapped commit domains: tagged proposal response selection,
 // synchronous label/pending read + allocation, directory RMW + publication.
 reg p0v,p1v;reg [3:0] p0ctx,p1ctx;reg [NA-1:0] p0idx,p1idx;reg [63:0] p0value,p1value;
 reg p1append,p1present;reg [15:0] p1version;reg [11:0] p1key;reg [MA-1:0] p1allocated;
 wire [63:0] pipeline_dir=directory_read;reg last_dir_valid;reg [11:0] last_dir_key;reg [63:0] last_dir_value;
 wire select_context=command==3&&ready_context>=0;
 wire [NA-1:0] read_node=select_context?context_index[ready_context]:idx;
 wire p0append=!pending_q[28]||pending_q[11:0]!=p0value[63:52];
 wire publish=command==3&&p1v;
 wire forwarded_dir=last_dir_valid&&last_dir_key==p1key;
 wire dir_present=forwarded_dir?1'b1:p1present;
 wire [63:0] previous_dir=forwarded_dir?last_dir_value:pipeline_dir;
 wire [63:0] published_dir={dir_present?previous_dir[63:32]:{{(32-MA){1'b0}},p1allocated},{{(32-MA){1'b0}},p1allocated}};
 assign pool_iv=(state==INIT&&initidx<MC)||state==POPMETA;
 assign pool_in=state==INIT?initidx[MA-1:0]:pointer[MA-1:0];
 assign pool_or=state==ALLOC||(command==3&&p0v&&p0append);
 wire member_new_we=(state==PUBLISH)||(publish&&p1append);
 wire [MA-1:0] member_new_index=publish?p1allocated:allocated[MA-1:0];
 wire [31:0] member_new_header=publish?{p1version,{{(16-NA){1'b0}},p1idx}}:{version,{{(16-NA){1'b0}},idx}};
 wire member_tail_we=(state==TAILWRITE)||(publish&&p1append&&dir_present);
 wire [MA-1:0] member_tail_index=publish?previous_dir[MA-1:0]:tail_ptr[MA-1:0];
 wire [31:0] member_tail_next=publish?{{(32-MA){1'b0}},p1allocated}:allocated;
 // One header write port; two next-link ports. POP reads share the new-entry
 // port in a disjoint phase, so no hidden third RAM port is required.
 always @(posedge clk)begin
  if(member_new_we)begin member_header[member_new_index]<=member_new_header;member_next[member_new_index]<=NIL;end
  else begin header_q<=member_header[pointer[MA-1:0]];next_q<=member_next[pointer[MA-1:0]];end
  if(member_tail_we)member_next[member_tail_index]<=member_tail_next;
  if(command!=3||(command==3&&p0v))directory_read<=directory[command==3?p0value[63:52]:key];
 end
 always @(posedge clk)begin
  // Explicit synchronous read ports. States below consume on following edges.
  label_q<=labels[read_node];pending_q<=pending[read_node];if(!POP_REDUCE)closed_q<=closed[closed_rd[NA-1:0]];
  if(rst)begin p0v<=0;p1v<=0;last_dir_valid<=0;has_bucket<=0;min_bucket<=0;init_busy<=0;init_sent<=0;init_acked<=0;context_valid<=0;context_sent<=0;context_ready<=0;commit_index<=0;mem_id<=0;state<=IDLE;done<=0;error<=0;pv<=0;close_valid<=0;ca<=0;mem_valid<=0;bitmap<=0;groups<=0;closed_mark<=0;closed_wr<=0;closed_rd<=0;free_count<=MC;member_peak<=0;active_count<=0;commit_count<=0;closed_count<=0;stale_count<=0;end else begin
   ca<=0;
   if(pool_iv&&!pool_ir)error<=1;if(pool_or&&!pool_ov)error<=1;
   if(command!=3)begin p0v<=0;p1v<=0;last_dir_valid<=0;end
   if(mem_valid&&mem_ready)mem_valid<=0;if(pv&&pr)pv<=0;if(close_valid&&close_ready)close_valid<=0;
   if(command==0)done<=0;
   if(command==3)begin
    p0v<=select_context;p1v<=p0v;
    if(select_context)begin p0ctx<=ready_context;p0idx<=context_index[ready_context];p0value<=context_value[ready_context];context_ready[ready_context]<=0;end
    if(p0v)begin
     if(p0value>=label_q)error<=1;
     p1ctx<=p0ctx;p1idx<=p0idx;p1value<=p0value;p1key<=p0value[63:52];p1version<=pending_q[27:12]+1;
     p1append<=p0append;p1present<=bitmap[p0value[63:52]];p1allocated<=pool_out;
     if(p0append)begin free_count<=free_count-1;if(!pool_ov)error<=1;if(MC-free_count+1>member_peak)member_peak<=MC-free_count+1;end
    end
    if(publish)begin
     labels[p1idx]<=p1value;commit_count<=commit_count+1;ca<=1;commit_index<=p1idx;context_valid[p1ctx]<=0;context_sent[p1ctx]<=0;
     if(p1append)begin
      pending[p1idx]<={3'b0,1'b1,p1version,p1key};directory[p1key]<=published_dir;bitmap[p1key]<=1;groups[p1key[11:6]]<=1;
      last_dir_valid<=1;last_dir_key<=p1key;last_dir_value<=published_dir;
     end
    end

    if(cv&&issue_ready)begin context_valid[free_context]<=1;context_sent[free_context]<=0;context_ready[free_context]<=0;context_index[free_context]<=ci;end
    if((!mem_valid||mem_ready)&&send_context>=0)begin
     mem_valid<=1;mem_write<=0;mem_line<=global_node(context_index[send_context])>>2;mem_id<=send_context;context_sent[send_context]<=1;
    end
    if(rsp_valid)begin
     if(rsp_id>=16||!context_valid[rsp_id[3:0]]||!context_sent[rsp_id[3:0]])error<=1;
     else begin context_ready[rsp_id[3:0]]<=1;context_value[rsp_id[3:0]]<=rsp_data[context_index[rsp_id[3:0]][1:0]*64+:64];end
    end
   end
   case(state)
   IDLE:if(command!=0&&!done)begin
    case(command)
    1:begin initidx<=0;closed_wr<=0;closed_rd<=0;bitmap<=0;groups<=0;closed_mark<=0;free_count<=MC;state<=INIT;end
    2:begin key<=bucket;state<=POPHEAD;end
    3:state<=COMMIT;
    4:begin closed_rd<=0;state<=CLOSE;end
    5:begin selected_group<=group_index;has_bucket<=group_valid;state<=28;end
    default:error<=1;endcase
   end
   INIT:begin

    if(initidx<NC)begin labels[initidx[NA-1:0]]<=global_node(initidx[NA-1:0])==source?64'b0:INF;pending[initidx[NA-1:0]]<=0;end
    if(initidx==(MC>NC?MC:NC)-1)begin initidx<=0;init_sent<=0;init_acked<=0;init_busy<=0;state<=INITMEM;end else initidx<=initidx+1;
   end
   INITMEM:begin
    if((!mem_valid||mem_ready)&&init_sent<NC/4&&init_free>=0)begin
     mem_valid<=1;mem_write<=1;mem_id<=init_free;mem_line<=(init_sent<<3)|BANK;mem_data<={4{INF}};
     for(i=0;i<4;i=i+1)if(((init_sent<<5)|(BANK<<2)|i)==source)mem_data[i*64+:64]<=0;
     init_busy[init_free]<=1;init_sent<=init_sent+1;
    end
    if(rsp_valid)begin if(rsp_id>=INIT_OUTSTANDING||!init_busy[rsp_id[3:0]])error<=1;else begin init_busy[rsp_id[3:0]]<=0;init_acked<=init_acked+1;end end
    if(init_acked==NC/4&&init_busy==0&&!mem_valid)begin idx<=((source>>5)<<2)|(source&3);state<=SEED;end
   end
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
   POPMETA:begin idx<=member_q[32+:NA];version<=member_q[63:48];tail_ptr<=member_q[31:0];free_count<=free_count+1;state<=POPVALID;end
   POPVALID:state<=POPLABEL;
   POPLABEL:begin
    if(!pending_q[28]||pending_q[27:12]!=version||pending_q[11:0]!=key)begin stale_count<=stale_count+1;pointer<=tail_ptr;state<=POPMEMBER;end
    else begin pending[idx]<=0;
     if(!POP_REDUCE&&!closed_mark[idx])begin if(closed_wr==CLOSED_LIMIT)error<=1;else begin closed[closed_wr[NA-1:0]]<=idx;closed_mark[idx]<=1;closed_wr<=closed_wr+1;end end
     pv<=1;pn<=global_node(idx);pp<=label_q;state<=POPEMIT;
    end
   end
   POPEMIT:if(pv&&pr)begin active_count<=active_count+1;pointer<=tail_ptr;state<=POPMEMBER;end
   COMMIT:if(context_valid==0&&!cv&&!mem_valid&&!p0v&&!p1v)begin done<=1;state<=IDLE;end
   CREAD:if(!mem_valid)begin mem_valid<=1;mem_write<=0;mem_line<=global_node(idx)>>2;state<=CWAIT;end
   CWAIT:if(rsp_valid)begin new_label<=rsp_data[idx[1:0]*64+:64];state<=CMETA;end
   CMETA:state<=CWRITE;
   CWRITE:begin
    if(new_label>=label_q)error<=1;
    labels[idx]<=new_label;commit_count<=commit_count+1;key<=new_label[63:52];version<=pending_q[27:12]+1;
    if(pending_q[28]&&pending_q[11:0]==new_label[63:52])state<=CACK;else state<=APPEND;
   end
   APPEND:if(free_count==0)error<=1;else state<=ALLOC;
   ALLOC:begin allocated<=pool_out;free_count<=free_count-1;tail_ptr<=dir_q[31:0];pointer<=dir_q[31:0];tail_value<=dir_q;
    if(MC-free_count+1>member_peak)member_peak<=MC-free_count+1;
    state<=bitmap[key]?TAILREAD:PUBLISH;
   end
   TAILREAD:state<=TAILWRITE;
   TAILWRITE:state<=PUBLISH;
   PUBLISH:begin

    directory[key]<={bitmap[key]?tail_value[63:32]:allocated,allocated};
    bitmap[key]<=1;groups[key[11:6]]<=1;pending[idx]<={3'b0,1'b1,version,key};state<=CACK;
   end
   CACK:begin
    if(command==1)begin done<=1;state<=IDLE;end else begin ca<=1;commit_index<=idx;context_valid[active_context]<=0;context_sent[active_context]<=0;state<=27;end
   end
   27:state<=COMMIT;
   28:begin selected_word<=bitmap[selected_group*64+:64];state<=29;end
   29:begin min_bucket<={selected_group,word_index};has_bucket<=has_bucket&&word_valid;done<=1;state<=IDLE;end
   CLOSE:if(POP_REDUCE||closed_rd==closed_wr)begin closed_wr<=0;done<=1;state<=IDLE;end else state<=CLOSEIDX;
   CLOSEIDX:begin idx<=closed_q;state<=CLOSELABEL;end
   CLOSELABEL:state<=CLOSEEMIT;
   CLOSEEMIT:if(!close_valid)begin close_valid<=1;close_node<=global_node(idx);close_pair<=label_q;end else if(close_ready)begin close_valid<=0;closed_mark[idx]<=0;closed_rd<=closed_rd+1;closed_count<=closed_count+1;state<=CLOSE;end
   default:error<=1;
   endcase
  end
 end
endmodule
