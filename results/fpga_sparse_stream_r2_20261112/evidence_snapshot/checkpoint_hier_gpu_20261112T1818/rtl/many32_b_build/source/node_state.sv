`timescale 1ns/1ps
// Elastic synchronous-RAM hit pipeline: tag/read of request k+1 overlaps
// whole-line RMW/event publication of k. Miss/fill/eviction credits are finite.
// External backing contains two 128-bit node records per 32B line:
// {flags32 (bit0 changed), pending32, lexical_label64}. No full-node RTL arrays.
// Ops: READ=0, MARK_CHANGED=1, VALID_POP=2, COMMIT=3, CLEAR_CHANGED=4, SEED=5.
module r2_node_state #(parameter OWNER_BITS=3)(input wire clk,rst,iv,output wire ir,input wire [31:0] node,
 input wire [2:0] opcode,input wire [63:0] operand,input wire [31:0] argument,input wire [5:0] tag,
 input wire [31:0] state_base,node_count,input wire fence,output reg fence_done,
 output wire ov,input wire ordy,output wire [31:0] onode,output wire [5:0] otag,output wire [3:0] status,output wire [127:0] old_record,
 output reg mem_valid,input wire mem_ready,output reg mem_write,output reg [31:0] mem_line,
 output reg [5:0] mem_id,output reg [255:0] mem_data,
 input wire rsp_valid,output wire rsp_ready,input wire [5:0] rsp_id,input wire [255:0] rsp_data,
 output wire idle,output reg error,output reg [31:0] accepted,retired,merges,hits,misses,raw_stall,
 output reg [5:0] mshr_peak,output reg [4:0] dirty_peak);
 localparam [63:0] INF=64'h7f8000007f800000;
 wire qv,qr,fifo_ir,rv,rr;wire [136:0] qd;wire [31:0] qnode=qd[136:105];wire [261:0] rd;wire [6:0] qc,rc;
 sparse_fifo #(.WIDTH(137)) request_fifo(clk,rst,iv&&!fence,fifo_ir,{node,opcode,operand,argument,tag},qv,qr,qd,qc);
 sparse_fifo #(.WIDTH(262)) response_fifo(clk,rst,rsp_valid,rsp_ready,{rsp_id,rsp_data},rv,rr,rd,rc);
 assign ir=fifo_ir&&!fence;
 wire event_v,event_r;wire [169:0] event_data,event_out;wire [6:0] event_count;
 sparse_fifo #(.WIDTH(170)) event_fifo(clk,rst,event_v,event_r,event_data,ov,ordy,event_out,event_count);
 assign {onode,otag,status,old_record}=event_out;
 (* ram_style="block" *) reg [255:0] data_ram[0:127];
 reg [31:0] tags[0:127];reg [127:0] valid,dirty,busy;reg [1:0] replacement[0:31];
 reg [31:0] ml[0:31];reg [136:0] miss_request[0:31];reg [6:0] slot_for_miss[0:31];reg [31:0] mv,ms,mg;
 reg [31:0] wl[0:15];(* ram_style="block" *) reg [255:0] wb[0:15];reg [15:0] wv,ws,wg;reg [3:0] swrite;
 reg sv,skind,sdirty;reg [6:0] sslot;reg [31:0] snode,sline,evict_line;reg [136:0] srequest;reg [4:0] smiss;
 reg [255:0] ram_q,last_data;reg [6:0] last_slot;reg last_valid;
 reg flushing;reg [7:0] flush_index;reg command_turn;
 wire [31:0] qline=state_base+((((qnode>>(OWNER_BITS+2))<<1)|((qnode>>1)&1))<<OWNER_BITS)+((qnode>>2)&((1<<OWNER_BITS)-1));
 integer hit,matching,fm,fw,victim,issue_m,issue_w,count_m,count_w;integer candidate;
 reg [15:0] wait_write[0:31];wire [15:0] allocation_wait;
 wire write_ack=rv&&rr&&rd[261];
 wire [15:0] ack_mask=write_ack?(16'b1<<rd[259:256]):16'b0;
 for(genvar j=0;j<16;j=j+1)begin:write_dependencies
  assign allocation_wait[j]=wv[j]&&wl[j]==qline&&!ack_mask[j];
 end
 always @*begin
  hit=-1;matching=-1;fm=-1;fw=-1;victim=-1;issue_m=-1;issue_w=-1;count_m=0;count_w=0;candidate=0;
  for(integer i=0;i<32;i=i+1)begin
   if(mv[i])begin count_m=count_m+1;if(ml[i]==qline)matching=i;end else if(fm<0)fm=i;
   if(mv[i]&&mg[i]&&!ms[i]&&wait_write[i]==0&&issue_m<0)issue_m=i;
  end
  for(integer i=0;i<16;i=i+1)begin if(wv[i])count_w=count_w+1;else if(fw<0)fw=i;if(wv[i]&&wg[i]&&!ws[i]&&issue_w<0)issue_w=i;end
  for(integer w=0;w<4;w=w+1)begin
   candidate=(w<<5)|qline[OWNER_BITS+:5];
   if(valid[candidate]&&!busy[candidate]&&tags[candidate]==qline)hit=candidate;
   if(!valid[candidate]&&!busy[candidate]&&!(sv&&sslot==candidate)&&victim<0)victim=candidate;
  end
  if(victim<0)for(integer w=0;w<4;w=w+1)begin candidate=(((replacement[qline[OWNER_BITS+:5]]+w)%4)<<5)|qline[OWNER_BITS+:5];if(!busy[candidate]&&!(sv&&sslot==candidate)&&victim<0)victim=candidate;end
 end
 wire [255:0] base_data=last_valid&&last_slot==sslot?last_data:ram_q;
 // The operation returns the immutable old record and atomically computes a
 // replacement. Status bit0 is op-specific success/append/first-mark; bit3 error.
 function automatic [131:0] apply_record(input [136:0] req,input [127:0] old);
  reg [127:0] value;reg [3:0] result;reg [31:0] pend;reg [15:0] version;
  begin value=old;result=0;pend=old[95:64];version=pend[27:12]+1;
   case(req[104:102])
   0:result[0]=1;
   1:begin value[96]=1;result[0]=!old[96];end
   2:if(pend[28]&&pend[27:0]==req[33:6])begin value[95:64]=0;result[0]=1;end
   3:if(req[101:38]>=old[63:0])result[3]=1;else begin
    value[63:0]=req[101:38];
    if(!pend[28]||pend[11:0]!=req[101:90])begin value[95:64]={3'b0,1'b1,version,req[101:90]};result[0]=1;end
   end
   4:begin result[0]=old[96];value[96]=0;end
   5:begin value[63:0]=0;value[95:64]=32'h10001000;result[0]=1;end
   default:result[3]=1;
   endcase
   apply_record={result,value};
  end
 endfunction
 wire [127:0] hit_old=base_data[srequest[105]*128+:128];
 wire [136:0] fill_request=miss_request[rd[260:256]];
 wire [127:0] fill_old=rd[fill_request[105]*128+:128];
 wire [131:0] hit_result=apply_record(srequest,hit_old),fill_result=apply_record(fill_request,fill_old);
 reg [255:0] hit_data,fill_data;
 wire hit_changed=hit_result[127:0]!=hit_old,fill_changed=fill_result[127:0]!=fill_old;
 always @*begin hit_data=base_data;hit_data[srequest[105]*128+:128]=hit_result[127:0];fill_data=rd[255:0];fill_data[fill_request[105]*128+:128]=fill_result[127:0];end
 wire advance=!sv||skind||event_r;
 wire fill_wait=rv&&!rd[261];
 wire fill_take=fill_wait&&!sv&&event_r;
 assign rr=rd[261]||(!sv&&event_r);
 assign qr=!flushing&&!fill_wait&&advance&&(matching<0&&(hit>=0||(fm>=0&&victim>=0&&(!dirty[victim]||fw>=0))));
 wire dispatch=qv&&qr;
 wire hit_dispatch=dispatch&&matching<0&&hit>=0;
 wire miss_dispatch=dispatch&&matching<0&&hit<0;
 wire flush_dispatch=flushing&&flush_index<128&&dirty[flush_index[6:0]]&&advance&&fw>=0;
 wire ram_re=hit_dispatch||miss_dispatch||flush_dispatch;
 wire [6:0] ram_ra=flush_dispatch?flush_index[6:0]:hit_dispatch?hit[6:0]:victim[6:0];
 wire hit_write=sv&&!skind&&advance&&hit_changed;
 wire ram_we=hit_write||fill_take;
 wire [6:0] ram_wa=fill_take?slot_for_miss[rd[260:256]]:sslot;
 wire [255:0] ram_wd=fill_take?fill_data:hit_data;
 assign event_v=(sv&&!skind&&advance)||fill_take;
 assign event_data=fill_take?{fill_request[136:105],fill_request[5:0],fill_result[131:128],fill_old}:{srequest[136:105],srequest[5:0],hit_result[131:128],hit_old};
 assign idle=!sv&&!flushing&&qc==0&&!qv&&rc==0&&!rv&&mv==0&&wv==0&&!mem_valid&&event_count==0&&!ov;
 always @(posedge clk)begin
  if(ram_re)ram_q<=data_ram[ram_ra];
  if(ram_we)data_ram[ram_wa]<=ram_wd;
  if(rst)begin sv<=0;valid<=0;dirty<=0;busy<=0;mv<=0;ms<=0;mg<=0;wv<=0;ws<=0;wg<=0;mem_valid<=0;fence_done<=0;flushing<=0;flush_index<=0;last_valid<=0;error<=0;accepted<=0;retired<=0;hits<=0;misses<=0;merges<=0;raw_stall<=0;mshr_peak<=0;dirty_peak<=0;command_turn<=0;
   for(integer i=0;i<32;i=i+1)replacement[i]<=0;
  end else begin
   if(write_ack)for(integer i=0;i<32;i=i+1)wait_write[i]<=wait_write[i]&~ack_mask;
   if(iv&&ir)begin accepted<=accepted+1;if(node>=node_count)error<=1;end
   if(qv&&!qr)raw_stall<=raw_stall+1;
   if(count_m>mshr_peak)mshr_peak<=count_m;if(count_w>dirty_peak)dirty_peak<=count_w;
   if(ram_we)begin last_valid<=1;last_slot<=ram_wa;last_data<=ram_wd;end
   if(!mem_valid||mem_ready)begin
    mem_valid<=0;
    if(issue_w>=0&&(issue_m<0||!command_turn))begin mem_valid<=1;mem_write<=1;mem_line<=wl[issue_w];mem_id<=32+issue_w;mem_data<=wb[issue_w];ws[issue_w]<=1;command_turn<=1;end
    else if(issue_m>=0)begin mem_valid<=1;mem_write<=0;mem_line<=ml[issue_m];mem_id<=issue_m;mem_data<=0;ms[issue_m]<=1;command_turn<=0;end
   end
   if(rv&&rr&&rd[261])begin if(rd[261:256]>=48||!wv[rd[259:256]]||!ws[rd[259:256]])error<=1;else begin wv[rd[259:256]]<=0;ws[rd[259:256]]<=0;wg[rd[259:256]]<=0;end end
   if(fill_take)begin
    if(!mv[rd[260:256]]||!ms[rd[260:256]])error<=1;
    valid[slot_for_miss[rd[260:256]]]<=1;busy[slot_for_miss[rd[260:256]]]<=0;dirty[slot_for_miss[rd[260:256]]]<=fill_changed;
    mv[rd[260:256]]<=0;ms[rd[260:256]]<=0;mg[rd[260:256]]<=0;retired<=retired+1;if(fill_result[131])error<=1;
   end
   if(advance)begin
    sv<=0;
    if(sv)begin
     if(!skind)begin retired<=retired+1;if(hit_changed)dirty[sslot]<=1;if(hit_result[131])error<=1;end
     else begin
      if(sdirty)begin wb[swrite]<=base_data;wg[swrite]<=1;end
      if(!flushing)mg[smiss]<=1;
     end
    end
    if(hit_dispatch)begin sv<=1;skind<=0;sslot<=hit;snode<=qnode;sline<=qline;srequest<=qd;hits<=hits+1;end
    if(miss_dispatch)begin
     sv<=1;skind<=1;sslot<=victim;sdirty<=dirty[victim];evict_line<=tags[victim];smiss<=fm;
     if(dirty[victim])begin swrite<=fw;wv[fw]<=1;ws[fw]<=0;wg[fw]<=0;wl[fw]<=tags[victim];end
     wait_write[fm]<=allocation_wait;
     mv[fm]<=1;ms[fm]<=0;mg[fm]<=0;ml[fm]<=qline;slot_for_miss[fm]<=victim;miss_request[fm]<=qd;
     valid[victim]<=0;dirty[victim]<=0;busy[victim]<=1;tags[victim]<=qline;replacement[qline[OWNER_BITS+:5]]<=victim[6:5]+1;misses<=misses+1;
    end
    if(flush_dispatch)begin swrite<=fw;wv[fw]<=1;ws[fw]<=0;wg[fw]<=0;wl[fw]<=tags[flush_index[6:0]];sv<=1;skind<=1;sslot<=flush_index[6:0];sdirty<=1;evict_line<=tags[flush_index[6:0]];dirty[flush_index[6:0]]<=0;flush_index<=flush_index+1;end
   end
   if(!fence)fence_done<=0;
   if(fence&&!fence_done&&!flushing&&idle)begin flushing<=1;flush_index<=0;end
   if(flushing&&flush_index<128&&!dirty[flush_index[6:0]])flush_index<=flush_index+1;
   if(flushing&&flush_index==128&&!sv&&wv==0&&!mem_valid&&rc==0&&!rv&&event_count==0&&!ov)begin flushing<=0;fence_done<=1;end
  end
 end
`ifndef SYNTHESIS
 always @(posedge clk)if(!rst)begin
  for(integer i=0;i<32;i=i+1)for(integer j=0;j<16;j=j+1)
   if(mv[i]&&(wait_write[i][j] !== (wv[j]&&wl[j]==ml[i])))
    $fatal(1,"write dependency differs from address-based guard: mshr=%0d slot=%0d",i,j);
 end
`endif
endmodule
