`timescale 1ns/1ps
// Elastic synchronous-RAM hit pipeline: tag/read of request k+1 overlaps
// whole-line RMW/event publication of k. Miss/fill/eviction credits are finite.
module sparse_owner_pipe(input wire clk,rst,iv,output wire ir,input wire [31:0] node,
 input wire [63:0] pair,input wire fence,output reg fence_done,
 output wire update_valid,input wire update_ready,output wire [31:0] update_line,output wire [3:0] update_mask,
 output reg mem_valid,input wire mem_ready,output reg mem_write,output reg [31:0] mem_line,
 output reg [5:0] mem_id,output reg [255:0] mem_data,
 input wire rsp_valid,output wire rsp_ready,input wire [5:0] rsp_id,input wire [255:0] rsp_data,
 output wire idle,output reg error,output reg [31:0] accepted,retired,merges,hits,misses,raw_stall,
 output reg [5:0] mshr_peak,output reg [4:0] dirty_peak);
 localparam [63:0] INF=64'h7f8000007f800000;
 wire qv,qr,fifo_ir,rv,rr;wire [95:0] qd;wire [261:0] rd;wire [6:0] qc,rc;
 sparse_fifo #(.WIDTH(96)) request_fifo(clk,rst,iv&&!fence,fifo_ir,{node,pair},qv,qr,qd,qc);
 sparse_fifo #(.WIDTH(262)) response_fifo(clk,rst,rsp_valid,rsp_ready,{rsp_id,rsp_data},rv,rr,rd,rc);
 assign ir=fifo_ir&&!fence;
 wire event_v,event_r;wire [35:0] event_data,event_out;wire [6:0] event_count;
 sparse_fifo #(.WIDTH(36)) event_fifo(clk,rst,event_v,event_r,event_data,update_valid,update_ready,event_out,event_count);
 assign {update_line,update_mask}=event_out;
 (* ram_style="block" *) reg [255:0] data_ram[0:127];
 reg [31:0] tags[0:127];reg [127:0] valid,dirty,busy;reg [1:0] replacement[0:31];
 reg [31:0] ml[0:31],mcount[0:31];reg [6:0] slot_for_miss[0:31];reg [255:0] mc[0:31];reg [31:0] mv,ms,mg;
 reg [31:0] wl[0:15];(* ram_style="block" *) reg [255:0] wb[0:15];reg [15:0] wv,ws;
 reg sv,skind,sdirty;reg [6:0] sslot;reg [31:0] snode,sline,evict_line;reg [63:0] spair;reg [4:0] smiss;
 reg [255:0] ram_q,last_data;reg [6:0] last_slot;reg last_valid;
 reg flushing;reg [7:0] flush_index;reg command_turn;
 wire [31:0] qline={2'b0,qd[95:66]};
 integer hit,matching,fm,fw,victim,issue_m,issue_w,count_m,count_w;integer candidate;reg hazard;
 always @*begin
  hit=-1;matching=-1;fm=-1;fw=-1;victim=-1;issue_m=-1;issue_w=-1;count_m=0;count_w=0;candidate=0;hazard=0;
  for(integer i=0;i<32;i=i+1)begin
   if(mv[i])begin count_m=count_m+1;if(ml[i]==qline)matching=i;end else if(fm<0)fm=i;
   hazard=0;for(integer j=0;j<16;j=j+1)if(wv[j]&&wl[j]==ml[i])hazard=1;
   if(mv[i]&&mg[i]&&!ms[i]&&!hazard&&issue_m<0)issue_m=i;
  end
  for(integer i=0;i<16;i=i+1)begin if(wv[i])count_w=count_w+1;else if(fw<0)fw=i;if(wv[i]&&!ws[i]&&issue_w<0)issue_w=i;end
  for(integer w=0;w<4;w=w+1)begin
   candidate=(w<<5)|qline[7:3];
   if(valid[candidate]&&!busy[candidate]&&tags[candidate]==qline)hit=candidate;
   if(!valid[candidate]&&!busy[candidate]&&!(sv&&sslot==candidate)&&victim<0)victim=candidate;
  end
  if(victim<0)for(integer w=0;w<4;w=w+1)begin candidate=(((replacement[qline[7:3]]+w)%4)<<5)|qline[7:3];if(!busy[candidate]&&!(sv&&sslot==candidate)&&victim<0)victim=candidate;end
 end
 wire [255:0] base_data=last_valid&&last_slot==sslot?last_data:ram_q;
 reg [255:0] hit_data,fill_data;reg [3:0] hit_mask,fill_mask;
 always @*begin
  hit_data=base_data;hit_mask=0;
  if(spair<base_data[snode[1:0]*64+:64])begin hit_data[snode[1:0]*64+:64]=spair;hit_mask[snode[1:0]]=1;end
  fill_data=rd[255:0];fill_mask=0;
  for(integer j=0;j<4;j=j+1)if(mc[rd[260:256]][j*64+:64]<rd[j*64+:64])begin fill_data[j*64+:64]=mc[rd[260:256]][j*64+:64];fill_mask[j]=1;end
 end
 wire advance=!sv||(skind?(!sdirty||fw>=0):(hit_mask==0||event_r));
 wire fill_wait=rv&&!rd[261];
 wire fill_take=fill_wait&&!sv&&(fill_mask==0||event_r);
 assign rr=rd[261]||(!sv&&(fill_mask==0||event_r));
 assign qr=!flushing&&!fill_wait&&advance&&(matching>=0||hit>=0||(fm>=0&&victim>=0));
 wire dispatch=qv&&qr;
 wire hit_dispatch=dispatch&&matching<0&&hit>=0;
 wire miss_dispatch=dispatch&&matching<0&&hit<0;
 wire flush_dispatch=flushing&&flush_index<128&&dirty[flush_index[6:0]]&&advance;
 wire ram_re=hit_dispatch||miss_dispatch||flush_dispatch;
 wire [6:0] ram_ra=flush_dispatch?flush_index[6:0]:hit_dispatch?hit[6:0]:victim[6:0];
 wire hit_write=sv&&!skind&&advance&&hit_mask!=0;
 wire ram_we=hit_write||fill_take;
 wire [6:0] ram_wa=fill_take?slot_for_miss[rd[260:256]]:sslot;
 wire [255:0] ram_wd=fill_take?fill_data:hit_data;
 assign event_v=hit_write||(fill_take&&fill_mask!=0);
 assign event_data=fill_take?{ml[rd[260:256]],fill_mask}:{sline,hit_mask};
 assign idle=!sv&&!flushing&&qc==0&&!qv&&rc==0&&!rv&&mv==0&&wv==0&&!mem_valid&&event_count==0&&!update_valid;
 always @(posedge clk)begin
  if(ram_re)ram_q<=data_ram[ram_ra];
  if(ram_we)data_ram[ram_wa]<=ram_wd;
  if(rst)begin sv<=0;valid<=0;dirty<=0;busy<=0;mv<=0;ms<=0;mg<=0;wv<=0;ws<=0;mem_valid<=0;fence_done<=0;flushing<=0;flush_index<=0;last_valid<=0;error<=0;accepted<=0;retired<=0;hits<=0;misses<=0;merges<=0;raw_stall<=0;mshr_peak<=0;dirty_peak<=0;command_turn<=0;
   for(integer i=0;i<32;i=i+1)replacement[i]<=0;
  end else begin
   if(iv&&ir)accepted<=accepted+1;
   if(qv&&!qr)raw_stall<=raw_stall+1;
   if(count_m>mshr_peak)mshr_peak<=count_m;if(count_w>dirty_peak)dirty_peak<=count_w;
   if(ram_we)begin last_valid<=1;last_slot<=ram_wa;last_data<=ram_wd;end
   if(!mem_valid||mem_ready)begin
    mem_valid<=0;
    if(issue_w>=0&&(issue_m<0||!command_turn))begin mem_valid<=1;mem_write<=1;mem_line<=wl[issue_w];mem_id<=32+issue_w;mem_data<=wb[issue_w];ws[issue_w]<=1;command_turn<=1;end
    else if(issue_m>=0)begin mem_valid<=1;mem_write<=0;mem_line<=ml[issue_m];mem_id<=issue_m;mem_data<=0;ms[issue_m]<=1;command_turn<=0;end
   end
   if(rv&&rr&&rd[261])begin if(rd[261:256]>=48||!wv[rd[259:256]]||!ws[rd[259:256]])error<=1;else begin wv[rd[259:256]]<=0;ws[rd[259:256]]<=0;end end
   if(fill_take)begin
    if(!mv[rd[260:256]]||!ms[rd[260:256]])error<=1;
    valid[slot_for_miss[rd[260:256]]]<=1;busy[slot_for_miss[rd[260:256]]]<=0;dirty[slot_for_miss[rd[260:256]]]<=fill_mask!=0;
    mv[rd[260:256]]<=0;ms[rd[260:256]]<=0;mg[rd[260:256]]<=0;retired<=retired+mcount[rd[260:256]];
   end
   if(advance)begin
    sv<=0;
    if(sv)begin
     if(!skind)begin retired<=retired+1;if(hit_mask!=0)dirty[sslot]<=1;end
     else begin
      if(sdirty)begin wv[fw]<=1;ws[fw]<=0;wl[fw]<=evict_line;wb[fw]<=base_data;end
      if(!flushing)mg[smiss]<=1;
     end
    end
    if(hit_dispatch)begin sv<=1;skind<=0;sslot<=hit;snode<=qd[95:64];sline<=qline;spair<=qd[63:0];hits<=hits+1;end
    if(miss_dispatch)begin
     sv<=1;skind<=1;sslot<=victim;sdirty<=dirty[victim];evict_line<=tags[victim];smiss<=fm;
     mv[fm]<=1;ms[fm]<=0;mg[fm]<=0;ml[fm]<=qline;slot_for_miss[fm]<=victim;mcount[fm]<=1;mc[fm]<={4{INF}};mc[fm][qd[65:64]*64+:64]<=qd[63:0];
     valid[victim]<=0;dirty[victim]<=0;busy[victim]<=1;tags[victim]<=qline;replacement[qline[7:3]]<=victim[6:5]+1;misses<=misses+1;
    end
    if(flush_dispatch)begin sv<=1;skind<=1;sslot<=flush_index[6:0];sdirty<=1;evict_line<=tags[flush_index[6:0]];dirty[flush_index[6:0]]<=0;flush_index<=flush_index+1;end
   end
   if(dispatch&&matching>=0)begin if(qd[63:0]<mc[matching][qd[65:64]*64+:64])mc[matching][qd[65:64]*64+:64]<=qd[63:0];mcount[matching]<=mcount[matching]+1;merges<=merges+1;end
   if(!fence)fence_done<=0;
   if(fence&&!fence_done&&!flushing&&idle)begin flushing<=1;flush_index<=0;end
   if(flushing&&flush_index<128&&!dirty[flush_index[6:0]])flush_index<=flush_index+1;
   if(flushing&&flush_index==128&&!sv&&wv==0&&!mem_valid&&rc==0&&!rv&&event_count==0&&!update_valid)begin flushing<=0;fence_done<=1;end
  end
 end
endmodule
