`timescale 1ns/1ps
// One finite eight-lane group. Eight groups dispatch <=8 parents/cycle globally.
// Input is the completed header boundary; CSR/meta/pending are outside this DUT.
module df_edge_group #(parameter L=4,C=4,B=8)(
 input logic clk,reset,input logic lane_rr,
 input logic pv,output logic pr,input logic [31:0] pn,input logic [63:0] pp,begin_edge,end_edge,input logic [15:0] epoch,
 input logic [63:0] edge_base,input logic cfg_we,input logic [3:0] cfg_idx,input logic [63:0] cfg_cost,
 output logic mv,input logic mr,output logic [63:0] ml,output logic [15:0] mt,
 input logic rv,output logic rr,input logic [15:0] rt,input logic [255:0] rd,
 output wire [L-1:0] ov,input wire [L-1:0] or_,output wire [L*32-1:0] od,output wire [L*64-1:0] op,
 output wire [L*32-1:0] ot,output logic error,output logic [31:0] accepted,completed,emitted,output logic idle,
 output logic alloc_valid,output logic [7:0] alloc_context
);
 localparam E=L*C,S=L*B;
 logic live[E],inflight[E];logic [7:0] gen[E];logic [15:0] ep[E];
 logic [31:0] node[E],pos[E],last_edge[E];logic [29:0] nextbeat[E];logic [28:0] last_beat[E];logic [63:0] parent[E];
 logic [1:0] slot_state[S];logic [7:0] slot_context[S],slot_gen[S];logic [28:0] slot_beat[S];logic [255:0] payload[S];
 logic [2:0] head_slot[E],tail_slot[E],slot_next[S];logic [3:0] queued_slots[E];logic [L-1:0] pop_beat;
 logic [63:0] costs[16];logic [$clog2(L)-1:0] alloc_pointer;
 logic [1:0] consume_rr[L];logic [L-1:0] iv,ir,pending,fp_error;
 logic [L*32-1:0] candidate_dst;logic [L*64-1:0] candidate_parent,candidate_cost;
 integer allocation,request_context,request_slot;integer selected_context[L],selected_slot[L];
 logic [8:0] completed_pulse;logic [7:0] emitted_pulse;logic [3:0] completed_population,emitted_population;
 function automatic [3:0] pop8(input logic [7:0] p);logic [1:0] a,b,c,d;logic[2:0] e,f;begin a={1'b0,p[0]}+p[1];b={1'b0,p[2]}+p[3];c={1'b0,p[4]}+p[5];d={1'b0,p[6]}+p[7];e={1'b0,a}+b;f={1'b0,c}+d;pop8={1'b0,e}+f;end endfunction
 logic [L-1:0] completed_flags,emitted_flags;
 logic [63:0] request_beat;
 logic [L-1:0] lane_request_valid;logic [C-1:0] eligible[L];logic [B-1:0] available_slots[L];logic [1:0] lane_request_context[L];logic [2:0] lane_request_slot[L];logic [7:0] request_tag;
 logic [$clog2(L)-1:0] request_pointer;logic [C-1:0] context_available[L];logic [B-1:0] matching_slots[L][C];logic [2:0] context_slot[L][C];
 logic supported_offsets;
 logic select_held[L];logic [1:0] held_context[L];logic [2:0] held_slot[L];logic [1:0] selected_local[L];logic [2:0] selected_beat_local[L];integer completed_now,emitted_now;
 always_comb begin
  allocation=-1;
  if(lane_rr)begin
   for(integer k=0;k<L;k=k+1)for(integer c=0;c<C;c=c+1)
    if(allocation<0&&!live[((alloc_pointer+k)%L)*C+c])allocation=((alloc_pointer+k)%L)*C+c;
  end else for(integer i=0;i<E;i=i+1)if(allocation<0&&!live[i])allocation=i;
  supported_offsets=begin_edge[63:32]==0&&end_edge[63:32]==0&&begin_edge<=end_edge;pr=supported_offsets&&(begin_edge==end_edge||allocation>=0);
  alloc_valid=pv&&pr&&begin_edge<end_edge;alloc_context=allocation;
  // Parallel context eligibility then small lane-local selectors. Avoid a 32-way
  // serial chain that feeds its own wide dynamic context-state writeback.
  for(integer l=0;l<L;l=l+1)begin
   for(integer c=0;c<C;c=c+1)eligible[l][c]=live[l*C+c]&&!inflight[l*C+c]&&nextbeat[l*C+c]<=last_beat[l*C+c];
   for(integer s=0;s<B;s=s+1)available_slots[l][s]=slot_state[l*B+s]==0;
   lane_request_valid[l]=|eligible[l]&&|available_slots[l];
   lane_request_context[l]=0;lane_request_slot[l]=0;
   for(integer c=C-1;c>=0;c=c-1)if(eligible[l][c])lane_request_context[l]=c;
   for(integer s=B-1;s>=0;s=s-1)if(available_slots[l][s])lane_request_slot[l]=s;
  end
  request_context=-1;request_slot=-1;request_beat=0;request_tag=0;
  for(integer k=L-1;k>=0;k=k-1)if(lane_request_valid[(request_pointer+k)%L])begin
   request_context=((request_pointer+k)%L)*C+lane_request_context[(request_pointer+k)%L];request_slot=((request_pointer+k)%L)*B+lane_request_slot[(request_pointer+k)%L];
   request_beat=nextbeat[request_context];request_tag=gen[request_context];
  end
  rr=rv&&rt[7:0]<S&&slot_state[rt[7:0]]==1&&slot_gen[rt[7:0]]==rt[15:8];
  iv=0;pop_beat=0;candidate_dst=0;candidate_parent=0;candidate_cost=0;completed_now=0;emitted_now=0;completed_flags=0;emitted_flags=0;completed_population=pop8(completed_pulse[7:0])+completed_pulse[8];emitted_population=pop8(emitted_pulse);
  for(integer l=0;l<L;l=l+1)begin
   // Compute four independent slot matches before the four-context arbiter.
   for(integer c=0;c<C;c=c+1)begin
    for(integer s=0;s<B;s=s+1)matching_slots[l][c][s]=live[l*C+c]&&slot_state[l*B+s]==2&&queued_slots[l*C+c]!=0&&head_slot[l*C+c]==s;
    context_available[l][c]=|matching_slots[l][c];context_slot[l][c]=0;
    for(integer s=B-1;s>=0;s=s-1)if(matching_slots[l][c][s])context_slot[l][c]=s;
   end
   selected_local[l]=0;
   for(integer k=C-1;k>=0;k=k-1)if(context_available[l][(consume_rr[l]+k)%C])selected_local[l]=(consume_rr[l]+k)%C;
   if(select_held[l])selected_local[l]=held_context[l];
   selected_beat_local[l]=select_held[l]?held_slot[l]:context_slot[l][selected_local[l]];
   selected_context[l]=(|context_available[l])?l*C+selected_local[l]:-1;
   selected_slot[l]=l*B+selected_beat_local[l];
   if(selected_context[l]>=0)begin
    iv[l]=1;
    candidate_dst[l*32+:32]={4'b0,payload[l*B+selected_beat_local[l]][pos[l*C+selected_local[l]][2:0]*32+:28]};
    candidate_parent[l*64+:64]=parent[l*C+selected_local[l]];
    candidate_cost[l*64+:64]=costs[payload[l*B+selected_beat_local[l]][pos[l*C+selected_local[l]][2:0]*32+28+:4]];
    if(ir[l])begin pop_beat[l]=(pos[l*C+selected_local[l]]==last_edge[l*C+selected_local[l]])||pos[l*C+selected_local[l]][2:0]==7;emitted_flags[l]=1;if(pos[l*C+selected_local[l]]==last_edge[l*C+selected_local[l]])completed_flags[l]=1;end
   end
  end
  idle=!mv&&completed_pulse==0&&emitted_pulse==0;
  for(integer i=0;i<E;i=i+1)if(live[i])idle=0;
  for(integer s=0;s<S;s=s+1)if(slot_state[s]!=0)idle=0;
  for(integer l=0;l<L;l=l+1)if(pending[l])idle=0;
 end
 for(genvar l=0;l<L;l=l+1)begin:lanes
  df_pair_lane pair_unit(.clk,.rst(reset),.iv(iv[l]),.ir(ir[l]),.dst(candidate_dst[l*32+:32]),.parent(candidate_parent[l*64+:64]),.cost(candidate_cost[l*64+:64]),.ov(ov[l]),.or_(or_[l]),.od(od[l*32+:32]),.pair(op[l*64+:64]),.tag({ep[l*C+selected_local[l]][7:0],gen[l*C+selected_local[l]],8'(selected_slot[l]),7'(selected_context[l]),(pos[l*C+selected_local[l]]==last_edge[l*C+selected_local[l]])}),.ot(ot[l*32+:32]),.bad(fp_error[l]),.pending(pending[l]));
 end
 always_ff @(posedge clk)begin
  if(reset)begin
   mv<=0;ml<=0;mt<=0;alloc_pointer<=0;request_pointer<=0;accepted<=0;completed<=0;emitted<=0;error<=0;completed_pulse<=0;emitted_pulse<=0;
   for(integer i=0;i<E;i=i+1)begin live[i]<=0;inflight[i]<=0;gen[i]<=0;queued_slots[i]<=0;end
   for(integer s=0;s<S;s=s+1)slot_state[s]<=0;
   for(integer l=0;l<L;l=l+1)begin consume_rr[l]<=0;select_held[l]<=0;end
  end else begin
   if(cfg_we)costs[cfg_idx]<=cfg_cost;
   if(|(fp_error&ov))error<=1;if(pv&&!supported_offsets)error<=1;
   if(rv&&!rr)error<=1;
   if(pv&&pr)begin
    accepted<=accepted+1;
    if(begin_edge<end_edge)begin
     live[allocation]<=1;inflight[allocation]<=0;gen[allocation]<=gen[allocation]+1;
     parent[allocation]<=pp;node[allocation]<=pn;pos[allocation]<=begin_edge[31:0];last_edge[allocation]<=end_edge[31:0]-1;last_beat[allocation]<=(end_edge[31:0]-1)>>3;nextbeat[allocation]<=begin_edge[31:0]>>3;ep[allocation]<=epoch;
     if(lane_rr)alloc_pointer<=(allocation/C+1)%L;
    end
   end
   completed_pulse<={pv&&pr&&begin_edge==end_edge,8'(completed_flags)};emitted_pulse<=emitted_flags;completed<=completed+completed_population;emitted<=emitted+emitted_population;
   if(mv&&mr)mv<=0;
   if((!mv||mr)&&request_context>=0)begin
    request_pointer<=(request_context/C+1)%L;mv<=1;ml<=edge_base+request_beat;mt<={request_tag,8'(request_slot)};
    for(integer s=0;s<S;s=s+1)if(request_slot==s)begin slot_state[s]<=1;slot_context[s]<=request_context;slot_gen[s]<=request_tag;slot_beat[s]<=request_beat;end
    for(integer i=0;i<E;i=i+1)if(request_context==i)begin inflight[i]<=1;nextbeat[i]<=nextbeat[i]+1;end
   end
   // Linked indices into the existing finite beat slots. No extra data
   // FIFO capacity: each context owns an in-order chain of allocated slots.
   // D1 guarantees return order per context, while other contexts may return OOO.
   for(integer i=0;i<E;i=i+1)begin:queue_update
    logic push_,pop_;push_=(!mv||mr)&&request_context==i;pop_=pop_beat[i/C]&&selected_context[i/C]==i;
    if(push_)begin
     tail_slot[i]<=request_slot%B;
     if(queued_slots[i]!=0)slot_next[(i/C)*B+tail_slot[i]]<=request_slot%B;
     if(queued_slots[i]==0||(pop_&&queued_slots[i]==1))head_slot[i]<=request_slot%B;
    end
    if(pop_&&!(push_&&queued_slots[i]==1))head_slot[i]<=slot_next[(i/C)*B+head_slot[i]];
    case({push_,pop_})
     2'b10:queued_slots[i]<=queued_slots[i]+1;
     2'b01:queued_slots[i]<=queued_slots[i]-1;
     default:;
    endcase
   end
   if(rv&&rr)begin slot_state[rt[7:0]]<=2;payload[rt[7:0]]<=rd;inflight[slot_context[rt[7:0]]]<=0;end
   for(integer l=0;l<L;l=l+1)begin
    if(iv[l]&&!ir[l])begin select_held[l]<=1;held_context[l]<=selected_local[l];held_slot[l]<=selected_beat_local[l];end
    if(iv[l]&&ir[l])select_held[l]<=0;
   end
   for(integer l=0;l<L;l=l+1)if(iv[l]&&ir[l])begin
    pos[l*C+selected_local[l]]<=pos[l*C+selected_local[l]]+1;consume_rr[l]<=(selected_local[l]+1)%C;
    if(pos[l*C+selected_local[l]]==last_edge[l*C+selected_local[l]]||pos[l*C+selected_local[l]][2:0]==7)slot_state[l*B+selected_beat_local[l]]<=0;
    if(pos[l*C+selected_local[l]]==last_edge[l*C+selected_local[l]])live[l*C+selected_local[l]]<=0;
   end
  end
 end
endmodule
