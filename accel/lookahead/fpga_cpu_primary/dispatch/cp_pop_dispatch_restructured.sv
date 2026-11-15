`timescale 1ns/1ps
// Bounded equivalent combinational restructuring; original remains immutable.
// Finite TAKE/member/reservation/POP controller. See interface.md for the
// distinction between directory drain, POP delivery and complete expansion.
module cp_pop_dispatch_restructured(
 input wire clk,reset,wave_start,input wire [11:0] bucket,
 output wire wave_ready,output reg pops_done,error,
 output reg [63:0] ctrl_valid,input wire [63:0] ctrl_ready,
 output reg [127:0] ctrl_op,output reg [767:0] ctrl_bucket,output reg [895:0] ctrl_ptr,
 input wire [63:0] ctrl_rsp_valid,output reg [63:0] ctrl_rsp_ready,
 input wire [127:0] ctrl_rsp_op,ctrl_rsp_status,input wire [767:0] ctrl_rsp_bucket,
 input wire [2047:0] ctrl_rsp_node,ctrl_rsp_arg,input wire [895:0] ctrl_rsp_ptr,ctrl_rsp_next,
 output wire [15:0] av,input wire [15:0] ar,tv,output reg [15:0] tr,input wire [255:0] at,
 output reg [15:0] pv,input wire [15:0] pr,output reg [255:0] pt,
 output reg [15:0] stale,output reg [511:0] pn,output reg [1023:0] pp,
 output wire [63:0] op_valid,input wire [63:0] op_ready,
 output wire [2047:0] op_node,output wire [191:0] op_code,
 output wire [4095:0] op_pair,output wire [16383:0] op_line,
 output wire [1791:0] op_arg,output wire [1279:0] op_cookie,
 input wire [63:0] result_valid,output reg [63:0] result_ready,
 input wire [2047:0] result_node,input wire [191:0] result_opcode,
 input wire [255:0] result_status,input wire [4095:0] old_label,
 input wire [1279:0] result_cookie,
 output reg [31:0] take_count,release_count,pop_admitted,pop_returned,pop_delivered,stale_delivered,
 output reg [7:0] outstanding
);
 localparam [13:0] NIL=14'd8192;
 localparam [1:0] IDLE=0,TAKE=1,RUN=2;
 localparam [2:0] D_IDLE=0,D_TAKE_SEND=1,D_TAKE_WAIT=2,D_RELEASE_SEND=3,D_RELEASE_WAIT=4;
 reg [1:0] mode;reg [11:0] wave_bucket;reg [5:0] bank_rotor;
 reg [2:0] ds[64];reg [13:0] detached[64];reg [63:0] take_seen,member_valid,bank_reserved;
 reg [31:0] member_node[64];reg [27:0] member_arg[64];
 // One launch and one captured token per group, independently owned banks.
 reg [15:0] launch_valid,launch_sent,capture_valid,capture_issued;
 reg [5:0] launch_bank[16],capture_bank[16];reg [15:0] capture_token[16];reg [3:0] group_rr;
 // At most8 real command holds, not an 8/cycle promise on an unbounded queue.
 reg [63:0] op_hold;reg [3:0] op_group[64];reg [15:0] op_token[64];
 // Full live cookie ledger. Valid persists until frontend POP handoff, not
 // merely until canonical response capture. Generation is never truncated.
 reg [127:0] live,returned;reg [15:0] live_token[128];reg [31:0] live_node[128];reg [5:0] live_bank[128];
 reg [5:0] result_rr[16];
 reg [15:0] assign_group,fill_group;reg [5:0] assign_bank[16];reg [3:0] next_group_rr;
 reg [63:0] bad_ctrl,bad_result;reg all_drained;
 wire [15:0] selected_valid;wire [5:0] selected_bank[16];
 wire [15:0] selected_token[16];wire [31:0] selected_node[16];
 wire [63:0] selected_label[16];wire [3:0] selected_status[16];
 integer request_count,hold_count,fill_count,token_count;
 integer admit_n,return_n,deliver_n,stale_n,take_n,release_n;
 integer g,b,k,j,bi,gi,chosen,idx;reg [15:0] used_groups;reg [63:0] used_banks;
 reg [19:0] cookie;reg [15:0] token;reg [3:0] group;
 assign wave_ready=mode==IDLE&&!error;
 assign av=launch_valid&~launch_sent&{16{!error}};
 assign op_valid=op_hold&{64{!error}};
 assign op_pair=0;assign op_line=0;
 for(genvar n=0;n<64;n=n+1)begin:bank_payload
  assign op_node[n*32+:32]=member_node[n];
  assign op_arg[n*28+:28]=member_arg[n];
  assign op_code[n*3+:3]=3'd2;
  assign op_cookie[n*20+:20]={op_group[n],op_token[n]};
 end
 // Static unpacking: no runtime index-times-20 cookie slicing.
 wire [19:0] rb_cookie[64];wire [31:0] rb_node[64];
 wire [63:0] rb_label[64];wire [3:0] rb_status[64];wire [2:0] rb_opcode[64];
 wire [63:0] metadata_bad;wire [63:0] group_ack[16],group_bad[16];
 for(genvar rb=0;rb<64;rb=rb+1)begin:return_unpack
  assign rb_cookie[rb]=result_cookie[rb*20+:20];
  assign rb_node[rb]=result_node[rb*32+:32];assign rb_label[rb]=old_label[rb*64+:64];
  assign rb_status[rb]=result_status[rb*4+:4];assign rb_opcode[rb]=result_opcode[rb*3+:3];
  assign metadata_bad[rb]=result_valid[rb]&&rb_opcode[rb]==2&&
   (rb_cookie[rb][7:0]>=8||(rb_status[rb]!=0&&rb_status[rb]!=1));
 end
 for(genvar rg=0;rg<16;rg=rg+1)begin:return_group
  wire [63:0] eligible,hi,lo;wire [63:0] hp[7],lp[7];wire [63:0] winner;
  wire any_hi=|hi;wire any_winner=|winner;
  reg [5:0] bank_mux;reg [15:0] token_mux;reg [31:0] node_mux;
  reg [63:0] label_mux;reg [3:0] status_mux;
  wire [2:0] slot=token_mux[2:0];
  wire ledger_bad=!live[rg*8+slot]||returned[rg*8+slot]||
   live_token[rg*8+slot]!=token_mux||live_bank[rg*8+slot]!=bank_mux||live_node[rg*8+slot]!=node_mux;
  for(genvar rb=0;rb<64;rb=rb+1)begin:eligible_bank
   assign eligible[rb]=result_valid[rb]&&rb_opcode[rb]==2&&
    rb_cookie[rb][19:16]==4'(rg)&&!metadata_bad[rb];
   assign hi[rb]=eligible[rb]&&(6'(rb)>=result_rr[rg]);
   assign lo[rb]=eligible[rb]&&(6'(rb)<result_rr[rg]);
  end
  assign hp[0]=hi;assign lp[0]=lo;
  for(genvar st=0;st<6;st=st+1)begin:prefix_or
   assign hp[st+1]=hp[st]|(hp[st]<<(1<<st));
   assign lp[st+1]=lp[st]|(lp[st]<<(1<<st));
  end
  assign winner=(any_hi?(hi&~(hp[6]<<1)):(lo&~(lp[6]<<1)))&{64{!error&&!pv[rg]}};
  always_comb begin
   bank_mux=0;token_mux=0;node_mux=0;label_mux=0;status_mux=0;
   for(integer rb=0;rb<64;rb=rb+1)begin
    bank_mux=bank_mux|({6{winner[rb]}}&6'(rb));
    token_mux=token_mux|({16{winner[rb]}}&rb_cookie[rb][15:0]);
    node_mux=node_mux|({32{winner[rb]}}&rb_node[rb]);
    label_mux=label_mux|({64{winner[rb]}}&rb_label[rb]);
    status_mux=status_mux|({4{winner[rb]}}&rb_status[rb]);
   end
  end
  assign selected_valid[rg]=any_winner&&!ledger_bad;
  assign selected_bank[rg]=bank_mux;assign selected_token[rg]=token_mux;
  assign selected_node[rg]=node_mux;assign selected_label[rg]=label_mux;assign selected_status[rg]=status_mux;
  assign group_ack[rg]=winner&{64{!ledger_bad}};
  assign group_bad[rg]=winner&{64{ledger_bad}};
 end
 // Independent immutable eligible masks and logarithmic-depth inclusive sums.
 wire [63:0] bank_eligible;wire [15:0] group_free;
 wire [6:0] bank_prefix[7][64];wire [4:0] group_prefix[5][16];
 reg [5:0] rank_bank[8];
 for(genvar n=0;n<64;n=n+1)begin:rank_bank_input
  wire [5:0] physical=bank_rotor+6'(n);
  assign bank_eligible[n]=member_valid[physical]&&!bank_reserved[physical];
  assign bank_prefix[0][n]={6'b0,bank_eligible[n]};
 end
 for(genvar st=0;st<6;st=st+1)begin:bank_rank_stage
  for(genvar n=0;n<64;n=n+1)begin:column
   if(n>=(1<<st))assign bank_prefix[st+1][n]=bank_prefix[st][n]+bank_prefix[st][n-(1<<st)];
   else assign bank_prefix[st+1][n]=bank_prefix[st][n];
  end
 end
 for(genvar n=0;n<16;n=n+1)begin:rank_group_input
  wire [3:0] physical=group_rr+4'(n);
  assign group_free[n]=!launch_valid[physical];assign group_prefix[0][n]={4'b0,group_free[n]};
 end
 for(genvar st=0;st<4;st=st+1)begin:group_rank_stage
  for(genvar n=0;n<16;n=n+1)begin:column
   if(n>=(1<<st))assign group_prefix[st+1][n]=group_prefix[st][n]+group_prefix[st][n-(1<<st)];
   else assign group_prefix[st+1][n]=group_prefix[st][n];
  end
 end
 always_comb begin
  for(integer r=0;r<8;r=r+1)begin
   rank_bank[r]=0;
   for(integer n=0;n<64;n=n+1)
    rank_bank[r]=rank_bank[r]|({6{bank_eligible[n]&&bank_prefix[6][n]==7'(r+1)}}&(bank_rotor+6'(n)));
  end
 end
 wire [4:0] grant_count=(bank_prefix[6][63]<group_prefix[4][15])?
  ((bank_prefix[6][63]<8)?5'(bank_prefix[6][63]):5'd8):
  ((group_prefix[4][15]<8)?group_prefix[4][15]:5'd8);
 wire [3:0] group_position[16];wire [4:0] group_rank[16];
 for(genvar n=0;n<16;n=n+1)begin:physical_group_rank
  assign group_position[n]=4'(n)-group_rr;
  assign group_rank[n]=group_prefix[4][group_position[n]];
 end
 always_comb begin
  ctrl_valid=0;ctrl_op=0;ctrl_bucket=0;ctrl_ptr=0;ctrl_rsp_ready=0;
  bad_ctrl=0;bad_result=metadata_bad;result_ready=0;tr=0;
  for(integer rg=0;rg<16;rg=rg+1)begin bad_result=bad_result|group_bad[rg];result_ready=result_ready|group_ack[rg];end
  assign_group=0;fill_group=0;used_groups=launch_valid;used_banks=bank_reserved;
  next_group_rr=group_rr;request_count=0;hold_count=0;fill_count=0;token_count=0;
  admit_n=0;return_n=0;deliver_n=0;stale_n=0;take_n=0;release_n=0;
  bi=0;gi=0;chosen=-1;idx=0;cookie=0;token=0;group=0;
  all_drained=mode==RUN&&(&take_seen)&&!(|member_valid)&&!(|bank_reserved)&&
   !(|launch_valid)&&!(|capture_valid)&&!(|op_hold)&&!(|live)&&!(|pv)&&outstanding==0;
  for(g=0;g<16;g=g+1)begin
   assign_bank[g]=0;
   if(selected_valid[g])return_n=return_n+1;
   if(pv[g]&&pr[g])begin deliver_n=deliver_n+1;if(stale[g])stale_n=stale_n+1;end
   // Pre-edge capture capacity. No consume/reuse shortcut.
   if(!error&&launch_valid[g]&&launch_sent[g]&&!capture_valid[g]&&token_count<8)begin
    tr[g]=1;if(tv[g])token_count=token_count+1;
   end
  end
  for(b=0;b<64;b=b+1)begin
   if(ds[b]!=D_IDLE||detached[b]!=NIL)all_drained=0;
   if(op_hold[b])hold_count=hold_count+1;
   if(op_valid[b]&&op_ready[b])admit_n=admit_n+1;
   if(!error&&(ds[b]==D_TAKE_SEND||ds[b]==D_RELEASE_SEND))begin
    ctrl_valid[b]=1;ctrl_op[b*2+:2]=ds[b]==D_TAKE_SEND?2'd1:2'd2;
    ctrl_bucket[b*12+:12]=ds[b]==D_TAKE_SEND?wave_bucket:12'd0;
    ctrl_ptr[b*14+:14]=ds[b]==D_TAKE_SEND?NIL:detached[b];
   end
   if(ctrl_valid[b]&&ctrl_ready[b])begin
    if(ds[b]==D_TAKE_SEND)take_n=take_n+1;else release_n=release_n+1;
   end
   if(mode!=IDLE&&ctrl_rsp_valid[b])begin
    if(ds[b]==D_TAKE_WAIT)begin
     bad_ctrl[b]=ctrl_rsp_op[b*2+:2]!=1||ctrl_rsp_status[b*2+:2]!=0||
      ctrl_rsp_bucket[b*12+:12]!=wave_bucket||ctrl_rsp_ptr[b*14+:14]>NIL;
    end else if(ds[b]==D_RELEASE_WAIT)begin
     bad_ctrl[b]=ctrl_rsp_op[b*2+:2]!=2||ctrl_rsp_status[b*2+:2]!=0||
      ctrl_rsp_ptr[b*14+:14]!=detached[b]||ctrl_rsp_next[b*14+:14]>NIL||
      ctrl_rsp_arg[b*32+28+:4]!=0||member_valid[b]||
      {ctrl_rsp_node[b*32+2+:5],ctrl_rsp_node[b*32+7]}!=6'(b);
    end else bad_ctrl[b]=1;
    ctrl_rsp_ready[b]=!error&&!bad_ctrl[b];
   end
  end
  if(!error&&mode==RUN)begin
   // Old finite model visits captured reservations in group order, max8.
   for(g=0;g<16;g=g+1)begin
    if(capture_valid[g]&&!capture_issued[g]&&hold_count+fill_count<8)begin
     fill_group[g]=1;fill_count=fill_count+1;
    end
   end
   // Match the first eight eligible banks/groups by rank, preserving rotor order.
   request_count=grant_count;
   for(integer ag=0;ag<16;ag=ag+1)begin
    if(!launch_valid[ag]&&group_rank[ag]!=0&&group_rank[ag]<=grant_count)begin
     assign_group[ag]=1;assign_bank[ag]=rank_bank[3'(group_rank[ag]-1'b1)];
     if(group_rank[ag]==grant_count)next_group_rr=4'(ag)+1'b1;
    end
   end
  end
 end
 always_ff @(posedge clk)begin
  if(reset)begin
   mode<=IDLE;wave_bucket<=0;bank_rotor<=0;group_rr<=0;pops_done<=0;error<=0;
   take_seen<=0;member_valid<=0;bank_reserved<=0;launch_valid<=0;launch_sent<=0;
   capture_valid<=0;capture_issued<=0;op_hold<=0;live<=0;returned<=0;
   pv<=0;pt<=0;stale<=0;pn<=0;pp<=0;outstanding<=0;
   take_count<=0;release_count<=0;pop_admitted<=0;pop_returned<=0;pop_delivered<=0;stale_delivered<=0;
   for(integer b0=0;b0<64;b0=b0+1)begin ds[b0]<=D_IDLE;detached[b0]<=NIL;member_node[b0]<=0;member_arg[b0]<=0;op_group[b0]<=0;op_token[b0]<=0;end
   for(integer g0=0;g0<16;g0=g0+1)begin launch_bank[g0]<=0;capture_bank[g0]<=0;capture_token[g0]<=0;result_rr[g0]<=0;end
   for(integer i0=0;i0<128;i0=i0+1)begin live_token[i0]<=0;live_node[i0]<=0;live_bank[i0]<=0;end
  end else begin
   bank_rotor<=bank_rotor+1'b1;
   if((|bad_ctrl)||(|bad_result)||hold_count>8||admit_n>8)error<=1;
   take_count<=take_count+take_n;release_count<=release_count+release_n;
   pop_admitted<=pop_admitted+admit_n;pop_returned<=pop_returned+return_n;
   pop_delivered<=pop_delivered+deliver_n;stale_delivered<=stale_delivered+stale_n;
   outstanding<=outstanding+8'(admit_n)-8'(deliver_n);
   if(wave_start&&wave_ready)begin
    mode<=TAKE;wave_bucket<=bucket;pops_done<=0;take_seen<=0;
    for(integer b0=0;b0<64;b0=b0+1)ds[b0]<=D_TAKE_SEND;
   end
   if(mode==TAKE&&(&take_seen))mode<=RUN;
   if(all_drained&&!error)begin mode<=IDLE;pops_done<=1;end
   for(integer b0=0;b0<64;b0=b0+1)begin
    if(ctrl_valid[b0]&&ctrl_ready[b0])ds[b0]<=ds[b0]==D_TAKE_SEND?D_TAKE_WAIT:D_RELEASE_WAIT;
    if(ctrl_rsp_valid[b0]&&ctrl_rsp_ready[b0])begin
     ds[b0]<=D_IDLE;
     if(ds[b0]==D_TAKE_WAIT)begin detached[b0]<=ctrl_rsp_ptr[b0*14+:14];take_seen[b0]<=1;end
     else begin
      detached[b0]<=ctrl_rsp_next[b0*14+:14];member_valid[b0]<=1;
      member_node[b0]<=ctrl_rsp_node[b0*32+:32];member_arg[b0]<=ctrl_rsp_arg[b0*32+:28];
     end
    end
    if(!error&&mode==RUN&&ds[b0]==D_IDLE&&!member_valid[b0]&&detached[b0]!=NIL)ds[b0]<=D_RELEASE_SEND;
    if(op_valid[b0]&&op_ready[b0])begin
     if(!member_valid[b0]||!bank_reserved[b0])error<=1;
     op_hold[b0]<=0;member_valid[b0]<=0;bank_reserved[b0]<=0;
    end
   end
   group_rr<=next_group_rr;
   for(integer g0=0;g0<16;g0=g0+1)begin
    if(capture_valid[g0]&&capture_issued[g0]&&op_valid[capture_bank[g0]]&&op_ready[capture_bank[g0]])begin:accepted_pop
     integer pos;pos=g0*8+capture_token[g0][2:0];
     if(live[pos])error<=1;
     live[pos]<=1;returned[pos]<=0;live_token[pos]<=capture_token[g0];live_bank[pos]<=capture_bank[g0];live_node[pos]<=member_node[capture_bank[g0]];
     capture_valid[g0]<=0;capture_issued[g0]<=0;
    end
    if(av[g0]&&ar[g0])launch_sent[g0]<=1;
    if(tv[g0]&&tr[g0])begin
     if(at[g0*16+:8]>=8)error<=1;
     capture_valid[g0]<=1;capture_issued[g0]<=0;capture_bank[g0]<=launch_bank[g0];capture_token[g0]<=at[g0*16+:16];
     launch_valid[g0]<=0;launch_sent[g0]<=0;
    end
    if(assign_group[g0])begin launch_valid[g0]<=1;launch_sent[g0]<=0;launch_bank[g0]<=assign_bank[g0];bank_reserved[assign_bank[g0]]<=1;end
    if(fill_group[g0])begin
     if(!member_valid[capture_bank[g0]]||op_hold[capture_bank[g0]])error<=1;
     op_hold[capture_bank[g0]]<=1;op_group[capture_bank[g0]]<=4'(g0);op_token[capture_bank[g0]]<=capture_token[g0];capture_issued[g0]<=1;
    end
    if(pv[g0]&&pr[g0])begin:delivered_pop
     integer pos;pos=g0*8+pt[g0*16+:3];
     if(!live[pos]||!returned[pos]||live_token[pos]!=pt[g0*16+:16])error<=1;
     pv[g0]<=0;live[pos]<=0;returned[pos]<=0;
    end
    if(selected_valid[g0])begin:capture_pop
     integer pos;pos=g0*8+selected_token[g0][2:0];
     pv[g0]<=1;pt[g0*16+:16]<=selected_token[g0];stale[g0]<=!selected_status[g0][0];
     pn[g0*32+:32]<=selected_node[g0];pp[g0*64+:64]<=selected_label[g0];
     returned[pos]<=1;result_rr[g0]<=selected_bank[g0]+6'd1;
    end
   end
  end
 end
endmodule
