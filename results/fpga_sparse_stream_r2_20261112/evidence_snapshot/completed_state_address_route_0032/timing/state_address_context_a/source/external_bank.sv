`timescale 1ns/1ps
// Sparse directory/member bank with finite cached external labels, pending and
// changed marks. No array is indexed by the full graph's node count.
module r2_external_bank #(parameter BANK=0,OWNER_BITS=3,MC=1024,CC=1024,MA=$clog2(MC),USE_URAM=0,REQUEST_STAGE=0)(
 input wire clk,rst,input wire [2:0] command,input wire [11:0] bucket,
 input wire [31:0] source,node_count,state_base,input wire upstream_fenced,
 output reg done,output reg has_bucket,output reg [11:0] min_bucket,output wire error,
 output wire pv,input wire pr,output wire [31:0] pn,output wire [63:0] pp,
 input wire ev,output wire er,input wire [31:0] event_line,input wire [3:0] event_mask,
 output wire mark_idle,output reg ca,output reg [31:0] commit_node,
 output reg mem_valid,input wire mem_ready,output reg mem_write,output reg [31:0] mem_line,
 output reg [255:0] mem_data,output reg [5:0] mem_id,
 input wire rsp_valid,input wire [5:0] rsp_id,input wire [255:0] rsp_data,
 output wire state_mem_valid,input wire state_mem_ready,output wire state_mem_write,
 output wire [31:0] state_mem_line,output wire [255:0] state_mem_data,output wire [5:0] state_mem_id,
 input wire state_rsp_valid,output wire state_rsp_ready,input wire [5:0] state_rsp_id,input wire [255:0] state_rsp_data,
 output reg [31:0] active_count,commit_count,stale_count,output reg [MA:0] member_peak);
 localparam [63:0] INF=64'h7f8000007f800000;
 localparam [31:0] NIL=32'hffffffff;
 localparam IDLE=0,INIT=1,SEED=2,POP_HEAD=3,POP_DIR=4,POP_READ=5,POP_CAPTURE=6,POP_DRAIN=7,
  COMMIT=8,FENCE=9,MIN_WORD=10,MIN_END=11;
 localparam FREE=0,POP_SEND=1,POP_WAIT=2,PROP_SEND=3,PROP_WAIT=4,COMMIT_SEND=5,COMMIT_WAIT=6,
  PUBLISH_READY=7,PUBLISH_WAIT=8,CLEAR_SEND=9,CLEAR_WAIT=10,SEED_SEND=11,SEED_WAIT=12;
 reg [3:0] state;reg local_error;assign error=local_error||changed_error||state_error;
 reg [31:0] cn[0:31];reg [63:0] cp[0:31];reg [27:0] carg[0:31];reg [3:0] cs[0:31];
 wire signed [31:0] free_context,send_context,prop_context,publish_context;
 wire [5:0] live_count,pop_count;wire [127:0] context_states;
 for(genvar ci=0;ci<32;ci=ci+1)begin:context_decode
  assign context_states[ci*4+:4]=cs[ci];
 end
 r2_bank_context_select context_select(context_states,free_context,send_context,
  prop_context,publish_context,live_count,pop_count);
 // Atomic changed marks are serviced in the same cache as POP and COMMIT.
 wire mv,mr,mrv,first_mark,changed_error,cv,cr;wire [31:0] mn,rn,changed_node;wire [4:0] mid,rid;
 wire [$clog2(CC):0] changed_peak,changed_count;wire [31:0] marks,duplicates,unique_ids;
 r2_external_changed #(.CAP(CC),.STYLE(USE_URAM?"ultra":"block")) changes(clk,rst,ev,er,event_line,event_mask,state==COMMIT,cv,cr,changed_node,
  mv,mr,mn,mid,mrv,rid,rn,first_mark,mark_idle,changed_error,changed_peak,changed_count,marks,duplicates,unique_ids);
 assign cr=state==COMMIT&&free_context>=0;
 reg sv;wire sr;reg [31:0] sn;reg [2:0] sop;reg [63:0] sval;reg [31:0] sarg;reg [4:0] sid;
 reg arb_hold,arb_selected,arb_turn;
 wire selected=arb_hold?arb_selected:(mv&&(!sv||arb_turn));
 wire niv=selected?mv:sv;wire nir;wire nov;wire [31:0] non;wire [5:0] notag;wire [3:0] nost;wire [127:0] nold;
 wire state_idle,state_error,state_done;reg state_fence;
 assign mr=selected&&nir;assign sr=!selected&&nir;
 assign mrv=nov&&notag[5];assign rid=notag[4:0];assign rn=non;assign first_mark=nost[0];
 wire bank_response=nov&&!notag[5];
 wire [31:0] ns0,ns1,ns2,ns3,ns4,ns5;wire [5:0] ns6;wire [4:0] ns7;
 r2_node_state #(.OWNER_BITS(OWNER_BITS),.REQUEST_STAGE(REQUEST_STAGE)) node_state(clk,rst,niv,nir,selected?mn:sn,selected?3'd1:sop,
  selected?64'b0:sval,selected?32'b0:sarg,{selected,selected?mid:sid},state_base,node_count,state_fence,state_done,
  nov,1'b1,non,notag,nost,nold,state_mem_valid,state_mem_ready,state_mem_write,state_mem_line,state_mem_id,state_mem_data,
  state_rsp_valid,state_rsp_ready,state_rsp_id,state_rsp_data,state_idle,state_error,ns0,ns1,ns2,ns3,ns4,ns5,ns6,ns7);
 always @(posedge clk)begin
  if(rst)begin arb_hold<=0;arb_turn<=0;arb_selected<=0;end
  else if(niv)begin if(nir)begin arb_hold<=0;arb_turn<=!selected;end else begin arb_hold<=1;arb_selected<=selected;end end
 end
 wire parent_iv,parent_ir;wire [95:0] parent_data;wire [6:0] parent_count;
 assign parent_iv=bank_response&&cs[notag[4:0]]==POP_WAIT&&nost[0];
 assign parent_data={non,nold[63:0]};
 sparse_fifo #(.WIDTH(96)) parents(clk,rst,parent_iv,parent_ir,parent_data,pv,pr,{pn,pp},parent_count);
 // Credit includes validation requests whose responses have not arrived yet.
 wire pop_credit=parent_count+pop_count<64;
 (* ram_style=(USE_URAM?"ultra":"block") *) reg [63:0] directory[0:4095];reg [63:0] directory_q;
 (* ram_style=(USE_URAM?"ultra":"block") *) reg [47:0] member_header[0:MC-1];
 (* ram_style=(USE_URAM?"ultra":"block") *) reg [MA-1:0] member_next[0:MC-1];
 reg [47:0] header_q;reg [MA-1:0] next_q,pop_tail;reg [31:0] pointer;reg [11:0] key;
 (* ram_style="distributed" *) reg [63:0] bitmap_words[0:63];
 reg [63:0] bitmap_q;reg [63:0] groups;wire [63:0] selected_word=bitmap_q;reg [5:0] selected_group;
 reg last_bitmap_valid;reg [5:0] last_bitmap_group;reg [63:0] last_bitmap_value;
 wire gv,wv;wire [5:0] gi,wi;
 r2_first64 first_group(groups,gv,gi);r2_first64 first_word(selected_word,wv,wi);
 wire pool_iv,pool_ir,pool_ov,pool_or;wire [MA-1:0] pool_in,pool_out;wire [MA:0] pool_count;
 reg [MA:0] pool_init;reg pool_initialized;
 sparse_fifo #(.WIDTH(MA),.DEPTH(MC),.STYLE(USE_URAM?"ultra":"block")) pool(clk,rst,pool_iv,pool_ir,pool_in,pool_ov,pool_or,pool_out,pool_count);
 wire pop_capture=state==POP_CAPTURE&&free_context>=0&&pop_credit&&pool_ir;
 wire append_select=publish_context>=0&&pool_ov;
 assign pool_iv=(state==INIT&&pool_init<MC)||pop_capture;
 assign pool_in=state==INIT?pool_init[MA-1:0]:pointer[MA-1:0];
 assign pool_or=append_select;
 // A POP snapshots both directory endpoints. The tail terminates the list;
 // its next word is never consumed. Thus next links need only one write port
 // (the previous tail) and one synchronous read, without a new-entry NIL write.
 reg av;reg [4:0] actx;reg [MA-1:0] aid;reg [11:0] akey;reg [31:0] anode;reg [15:0] aversion;reg apresent;
 reg last_valid;reg [11:0] last_key;reg [63:0] last_dir;
 wire forwarded=last_valid&&last_key==akey;
 wire [63:0] publication_bitmap=(last_bitmap_valid&&last_bitmap_group==akey[11:6])?last_bitmap_value:bitmap_q;
 wire present=forwarded||publication_bitmap[akey[5:0]];wire [63:0] old_dir=forwarded?last_dir:directory_q;
 wire [31:0] extended_id={{(32-MA){1'b0}},aid};
 wire [63:0] new_dir={present?old_dir[63:32]:extended_id,extended_id};
 wire bitmap_init=state==INIT&&pool_init<64;
 wire bitmap_clear=state==POP_DIR;
 wire bitmap_write=bitmap_init||bitmap_clear||av;
 wire [5:0] bitmap_wa=bitmap_init?pool_init[5:0]:bitmap_clear?key[11:6]:akey[11:6];
 wire [63:0] bitmap_new=bitmap_init?64'b0:bitmap_clear?(bitmap_q&~(64'b1<<key[5:0])):(publication_bitmap|(64'b1<<akey[5:0]));
 wire bitmap_read=append_select||state==POP_HEAD||state==MIN_WORD;
 wire [5:0] bitmap_ra=append_select?cp[publish_context][63:58]:state==POP_HEAD?key[11:6]:selected_group;
 always @(posedge clk)begin
  if(bitmap_write)bitmap_words[bitmap_wa]<=bitmap_new;
  if(bitmap_read)bitmap_q<=bitmap_words[bitmap_ra];
  if(av)directory[akey]<=new_dir;
  if(append_select||state==POP_HEAD)directory_q<=directory[append_select?cp[publish_context][63:52]:key];
  if(av)member_header[aid]<={aversion,anode};else header_q<=member_header[pointer[MA-1:0]];
 end
 always @(posedge clk)begin
  if(av&&present)member_next[old_dir[MA-1:0]]<=aid;
  if(!av)next_q<=member_next[pointer[MA-1:0]];
 end
 reg [31:0] init_sent,init_acked;reg [15:0] init_busy;
 wire signed [31:0] init_free;wire init_free_valid;wire [5:0] init_free_index;
 wire [31:0] groups_per_bank=(node_count+((1<<(OWNER_BITS+2))-1))>>(OWNER_BITS+2);
 wire [31:0] init_total=groups_per_bank*3;
 wire [31:0] state_i=init_sent-groups_per_bank;
 wire [31:0] init_node=((state_i>>1)<<(OWNER_BITS+2))|(BANK<<2)|((state_i&1)<<1);
 r2_first64 init_select({48'b0,~init_busy},init_free_valid,init_free_index);
 assign init_free=init_free_valid?{28'b0,init_free_index[3:0]}:32'hffffffff;
 always @(posedge clk)begin
  if(rst)begin
   state<=IDLE;done<=0;local_error<=0;has_bucket<=0;min_bucket<=0;groups<=0;last_bitmap_valid<=0;pointer<=NIL;key<=0;
   sv<=0;av<=0;state_fence<=0;last_valid<=0;mem_valid<=0;mem_id<=0;mem_write<=0;mem_line<=0;mem_data<=0;
   ca<=0;commit_node<=0;active_count<=0;commit_count<=0;stale_count<=0;member_peak<=0;
   pool_initialized<=0;pool_init<=0;init_sent<=0;init_acked<=0;init_busy<=0;
   for(integer i=0;i<32;i=i+1)cs[i]<=FREE;
  end else begin
   ca<=0;av<=0;
   if(pool_initialized&&MC-pool_count>member_peak&&state!=INIT)member_peak<=MC-pool_count;
   if(parent_iv&&!parent_ir)local_error<=1;
   if(command==0)done<=0;
   if(mem_valid&&mem_ready)mem_valid<=0;
   if(sv&&sr)sv<=0;
   if((!sv||sr)&&send_context>=0)begin
    sv<=1;sid<=send_context;sn<=cn[send_context];sval<=cp[send_context];sarg<={4'b0,carg[send_context]};
    case(cs[send_context])
     POP_SEND:begin sop<=2;cs[send_context]<=POP_WAIT;end
     COMMIT_SEND:begin sop<=3;cs[send_context]<=COMMIT_WAIT;end
     CLEAR_SEND:begin sop<=4;cs[send_context]<=CLEAR_WAIT;end
     SEED_SEND:begin sop<=5;cs[send_context]<=SEED_WAIT;end
     default:local_error<=1;
    endcase
   end
   if(bank_response)begin
    if(nost[3]||cn[notag[4:0]]!=non)local_error<=1;
    case(cs[notag[4:0]])
     POP_WAIT:begin cs[notag[4:0]]<=FREE;if(nost[0])active_count<=active_count+1;else stale_count<=stale_count+1;end
     COMMIT_WAIT:begin
      carg[notag[4:0]]<={nold[91:76]+16'd1,cp[notag[4:0]][63:52]};
      cs[notag[4:0]]<=nost[0]?PUBLISH_READY:CLEAR_SEND;
     end
     CLEAR_WAIT:begin if(!nost[0])local_error<=1;cs[notag[4:0]]<=FREE;ca<=1;commit_node<=non;commit_count<=commit_count+1;end
     SEED_WAIT:begin cs[notag[4:0]]<=PUBLISH_READY;carg[notag[4:0]]<=28'h0001000;end
     default:local_error<=1;
    endcase
   end
   if(append_select)begin
    av<=1;actx<=publish_context;aid<=pool_out;akey<=cp[publish_context][63:52];
    anode<=cn[publish_context];aversion<=carg[publish_context][27:12];apresent<=0;
    cs[publish_context]<=PUBLISH_WAIT;
   end else if(publish_context>=0&&!pool_ov)local_error<=1;
   if(av)begin
    last_bitmap_valid<=1;last_bitmap_group<=akey[11:6];last_bitmap_value<=bitmap_new;groups[akey[11:6]]<=1;last_valid<=1;last_key<=akey;last_dir<=new_dir;
    cs[actx]<=state==SEED?FREE:CLEAR_SEND;
   end
   if(state==COMMIT)begin
    if(cv&&cr)begin cn[free_context]<=changed_node;cs[free_context]<=PROP_SEND;end
    if((!mem_valid||mem_ready)&&prop_context>=0)begin mem_valid<=1;mem_write<=0;mem_line<=cn[prop_context]>>2;mem_id<=prop_context;cs[prop_context]<=PROP_WAIT;end
    if(rsp_valid)begin
     if(rsp_id>=32||cs[rsp_id[4:0]]!=PROP_WAIT)local_error<=1;
     else begin cp[rsp_id[4:0]]<=rsp_data[cn[rsp_id[4:0]][1:0]*64+:64];cs[rsp_id[4:0]]<=COMMIT_SEND;end
    end
   end
   case(state)
    IDLE:if(command!=0&&!done)case(command)
     1:begin state<=INIT;last_bitmap_valid<=0;groups<=0;last_valid<=0;pool_initialized<=0;pool_init<=0;init_sent<=0;init_acked<=0;init_busy<=0;end
     2:begin key<=bucket;last_valid<=0;last_bitmap_valid<=0;state<=POP_HEAD;end
     3:state<=COMMIT;
     4:done<=1;
     5:begin has_bucket<=gv;selected_group<=gi;state<=MIN_WORD;end
     6:state<=FENCE;
     default:local_error<=1;
    endcase
    INIT:begin
     if(pool_init<MC&&pool_ir)pool_init<=pool_init+1;
     if((!mem_valid||mem_ready)&&init_sent<init_total&&init_free>=0)begin
      mem_valid<=1;mem_write<=1;mem_id<=init_free;init_busy[init_free]<=1;init_sent<=init_sent+1;
      if(init_sent<groups_per_bank)begin
       mem_line<=(init_sent<<OWNER_BITS)|BANK;mem_data<={4{INF}};
       for(integer s=0;s<4;s=s+1)if(((init_sent<<(OWNER_BITS+2))|(BANK<<2)|s)==source)mem_data[s*64+:64]<=0;
      end else begin
       mem_line<=state_base+(state_i<<OWNER_BITS)+BANK;mem_data<={2{64'b0,INF}};
      end
     end
     if(rsp_valid)begin if(rsp_id>=16||!init_busy[rsp_id[3:0]])local_error<=1;else begin init_busy[rsp_id[3:0]]<=0;init_acked<=init_acked+1;end end
     if(pool_init==MC&&init_acked==init_total&&init_busy==0&&!mem_valid)begin
      pool_initialized<=1;state<=SEED;
      if(((source>>2)&((1<<OWNER_BITS)-1))==BANK)begin cn[0]<=source;cp[0]<=0;cs[0]<=SEED_SEND;end
     end
    end
    SEED:if(live_count==0&&!sv&&!av)begin state_fence<=1;if(state_done)begin state_fence<=0;done<=1;state<=IDLE;end end
    POP_HEAD:state<=POP_DIR;
    POP_DIR:begin
     pointer<=bitmap_q[key[5:0]]?directory_q[63:32]:NIL;
     pop_tail<=directory_q[MA-1:0];
     if(bitmap_new==0)groups[key[11:6]]<=0;
     state<=POP_READ;
    end
    POP_READ:if(pointer==NIL)state<=POP_DRAIN;else state<=POP_CAPTURE;
    POP_CAPTURE:if(pop_capture)begin
     cn[free_context]<=header_q[31:0];carg[free_context]<={header_q[47:32],key};cs[free_context]<=POP_SEND;
     pointer<=pointer[MA-1:0]==pop_tail?NIL:{{(32-MA){1'b0}},next_q};state<=POP_READ;
    end
    POP_DRAIN:if(live_count==0&&!sv&&parent_count==0&&!pv)begin done<=1;state<=IDLE;end
    COMMIT:if(!cv&&live_count==0&&!sv&&!av&&!mem_valid)begin state_fence<=1;if(state_done)begin state_fence<=0;done<=1;state<=IDLE;end end
    FENCE:if(upstream_fenced&&mark_idle)begin state_fence<=1;if(state_done)begin state_fence<=0;done<=1;state<=IDLE;end end
    MIN_WORD:state<=MIN_END;
    MIN_END:begin min_bucket<={selected_group,wi};has_bucket<=has_bucket&&wv;done<=1;state<=IDLE;end
    default:local_error<=1;
   endcase
  end
 end
endmodule
