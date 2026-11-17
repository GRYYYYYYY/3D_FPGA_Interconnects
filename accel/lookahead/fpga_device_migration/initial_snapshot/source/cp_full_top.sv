`timescale 1ns/1ps
// Production L1 core. Runtime resident jobs, complete per-sample initialization,
// true MIN/TAKE/RELEASE/POP, full fabric, deferred publication and output ACKs.
// External config is held stable from start through done. No platform shell.
module cp_full_top(
 input wire clk,reset,start,
 input wire cfg_job_we,input wire [7:0] cfg_job_index,
 input wire [31:0] cfg_job_source,cfg_job_targets,
 input wire [31:0] cfg_nodes,cfg_edges,input wire [15:0] cfg_cells,
 input wire [4:0] cfg_costs,input wire [8:0] cfg_jobs,
 input wire [63:0] cfg_label_base,cfg_scratch_base,cfg_descriptor_base,cfg_edge_base,cfg_cost_base,cfg_output_base,
 input wire [31:0] cfg_descriptor_stride,cfg_output_stride,
 output reg busy,done,error,output reg sample_done,output reg [7:0] sample_index,
 output wire [4:0] phase,output reg [63:0] cycles,output reg [31:0] waves,
 output reg [31:0] recorded,output reg [31:0] mem_requests,mem_responses,
 output wire [31:0] mv,input wire [31:0] mr,output wire [31:0] mw,
 output wire [1023:0] ml,output wire [159:0] mtag,output wire [8191:0] md,
 input wire [31:0] sv,output wire [31:0] sr,input wire [159:0] stag,
 input wire [8191:0] sd,input wire [63:0] sstatus
);
 localparam IDLE=0,SRST=1,LOAD=2,INIT=3,COST=4,SEED=5,SEED_WAIT=6,
  MIN_START=7,MIN_WAIT=8,WAVE_START=9,EXPAND=10,FLUSH=11,FINALIZE=12,
  REOPEN=13,REOPEN_WAIT=14,EXPORT_START=15,EXPORT_WAIT=16,COMPLETE=17,FAULT=18;
 reg [4:0] state;assign phase=state;
 wire core_reset=reset||state==SRST;
 (* ram_style="distributed" *) reg [63:0] jobs[256];reg [255:0] job_valid;
 reg [31:0] source_node,targets;reg [63:0] descriptor_base,output_base;
 reg [11:0] bucket;reg have_bucket;reg [15:0] epoch;
 reg [63:0] phase_cycles[19];
 wire [64:0] nlines=({33'b0,cfg_nodes}+3)>>2;
 wire [64:0] elines=({33'b0,cfg_edges}+7)>>3;
 wire [64:0] olines=({49'b0,cfg_cells}+3)>>2;
 wire config_bad=cfg_nodes==0||cfg_nodes>4194304||cfg_cells==0||cfg_cells>32768||cfg_costs==0||cfg_costs>16||cfg_jobs==0||cfg_jobs>256||
  |cfg_label_base[63:32]|||cfg_scratch_base[63:32]|||cfg_descriptor_base[63:32]|||cfg_edge_base[63:32]|||cfg_cost_base[63:32]|||cfg_output_base[63:32]||
  |cfg_label_base[4:0]|||cfg_scratch_base[4:0]|||cfg_descriptor_base[4:0]|||cfg_edge_base[4:0]|||cfg_cost_base[4:0]|||cfg_output_base[4:0]||
  |cfg_descriptor_stride[4:0]|||cfg_output_stride[4:0]||cfg_descriptor_stride<nlines||cfg_output_stride<olines||
  ({1'b0,cfg_label_base}+nlines>65'h100000000)||({1'b0,cfg_scratch_base}+nlines>65'h100000000)||
  ({1'b0,cfg_edge_base}+elines>65'h100000000)||({1'b0,cfg_cost_base}+4>65'h100000000);
 wire sample_bad=!job_valid[sample_index]||jobs[sample_index][63:32]>=cfg_nodes||jobs[sample_index][31:0]>cfg_cells||
  ({1'b0,descriptor_base}+nlines>65'h100000000)||({1'b0,output_base}+olines>65'h100000000);
 wire [207:0] ncv,ncr,nrv,nrr;wire [831:0] nck,nrk;wire [6655:0] ncl,nid,ngen,nrid,nrgen;
 wire [53247:0] nrd;wire [415:0] nstatus;wire [40959:0] nwdata;
 wire [31:0] port_error;wire network_error;
 lf_radix_network fabric(.clk,.reset(core_reset),.cv(ncv),.cr(ncr),.ck(nck),.cl(ncl),.cid(nid),.cgen(ngen),.local_write_data(nwdata),
  .rv(nrv),.rr(nrr),.rk(nrk),.rid(nrid),.rgen(nrgen),.rd(nrd),.rstatus(nstatus),.mv,.mr,.mw,.ml,.mtag,.md,.sv,.sr,.stag,.sd,.sstatus,.port_error,.error(network_error));
 reg [9:0] pending[208];reg pending_error;reg net_empty;
 always @*begin net_empty=!(|ncv)&&!(|nrv);for(integer s=0;s<208;s=s+1)if(pending[s]!=0)net_empty=0;end
 always @(posedge clk)begin
  if(core_reset)begin pending_error<=0;for(integer s=0;s<208;s=s+1)pending[s]<=0;end
  else for(integer s=0;s<208;s=s+1)begin
   case({ncv[s]&&ncr[s],nrv[s]&&nrr[s]})
    2'b10:begin pending[s]<=pending[s]+1'b1;if(pending[s]==1023)pending_error<=1;end
    2'b01:begin pending[s]<=pending[s]-1'b1;if(pending[s]==0)pending_error<=1;end
   endcase
  end
 end
 wire [63:0] bank_initialized,bank_done,bank_idle,bank_expansion_idle,bank_error,bank_overflow;
 wire [63:0] bc_valid,bc_ready,br_valid,br_ready;wire [127:0] bc_op,br_op,br_status;wire [767:0] bc_bucket,br_bucket;
 wire [895:0] bc_ptr,br_ptr,br_next;wire [2047:0] br_node,br_arg;
 wire [63:0] bo_valid,bo_ready,result_valid,result_ready;wire [2047:0] bo_node,result_node;
 wire [191:0] bo_code,result_opcode;wire [4095:0] bo_pair,result_label;wire [16383:0] bo_line;
 wire [1791:0] bo_arg;wire [1279:0] bo_cookie,result_cookie;wire [255:0] result_status;
 wire [63:0] candidate_v,candidate_r,bank_candidate_v,bank_candidate_r;wire [6143:0] candidate_data,bank_candidate_data;wire candidate_idle;
 cp_candidate_network candidates(.clk,.reset(core_reset),.idle(candidate_idle),.cv(candidate_v),.cr(candidate_r),.cd(candidate_data),.rv(bank_candidate_v),.rr(bank_candidate_r),.rd(bank_candidate_data));
 wire [63:0] dc_valid,dc_ready,dr_valid,dr_ready,do_valid,do_ready,dp_result_ready;
 wire [127:0] dc_op;wire [767:0] dc_bucket;wire [895:0] dc_ptr;
 wire [2047:0] do_node;wire [191:0] do_code;wire [4095:0] do_pair;wire [16383:0] do_line;wire [1791:0] do_arg;wire [1279:0] do_cookie;
 wire [15:0] av,ar,tv,tr,pv,pr,stale;wire [255:0] at,pt;wire [511:0] pn;wire [1023:0] pp;
 wire dispatch_ready,pops_done,dispatch_error;wire [7:0] pop_outstanding;
 wire [31:0] take_count,release_count,pop_admitted,pop_returned,pop_delivered,stale_delivered;
 cp_pop_dispatch_restructured dispatch(.clk,.reset(core_reset),.wave_start(state==WAVE_START),.bucket,.wave_ready(dispatch_ready),.pops_done,.error(dispatch_error),
  .ctrl_valid(dc_valid),.ctrl_ready(dc_ready),.ctrl_op(dc_op),.ctrl_bucket(dc_bucket),.ctrl_ptr(dc_ptr),
  .ctrl_rsp_valid(dr_valid),.ctrl_rsp_ready(dr_ready),.ctrl_rsp_op(br_op),.ctrl_rsp_status(br_status),.ctrl_rsp_bucket(br_bucket),.ctrl_rsp_node(br_node),.ctrl_rsp_arg(br_arg),.ctrl_rsp_ptr(br_ptr),.ctrl_rsp_next(br_next),
  .av,.ar,.tv,.tr,.at,.pv,.pr,.pt,.stale,.pn,.pp,
  .op_valid(do_valid),.op_ready(do_ready),.op_node(do_node),.op_code(do_code),.op_pair(do_pair),.op_line(do_line),.op_arg(do_arg),.op_cookie(do_cookie),
  .result_valid,.result_ready(dp_result_ready),.result_node,.result_opcode,.result_status,.old_label(result_label),.result_cookie,
  .take_count,.release_count,.pop_admitted,.pop_returned,.pop_delivered,.stale_delivered,.outstanding(pop_outstanding));
 wire min_ready,min_valid,min_empty;wire [11:0] min_bucket;wire [63:0] min_cmd,min_accept,min_bank_valid,min_bank_empty;
 wire selecting=state==MIN_START||state==MIN_WAIT;
 df_min_collect minimum(.clk,.reset(core_reset),.start(state==MIN_START),.ready(min_ready),.bank_ready(bc_ready),.bank_command(min_cmd),.bank_valid(min_bank_valid),.bank_accept(min_accept),.bank_empty(min_bank_empty),.bank_bucket(br_bucket),.ov(min_valid),.ordy(state==MIN_WAIT),.empty(min_empty),.minimum(min_bucket));
 wire [5:0] seed_bank={source_node[6:2],source_node[7]};
 for(genvar b=0;b<64;b=b+1)begin:banks
  assign bc_valid[b]=selecting?min_cmd[b]:dc_valid[b];
  assign bc_op[b*2+:2]=selecting?2'd3:dc_op[b*2+:2];
  assign bc_bucket[b*12+:12]=selecting?12'b0:dc_bucket[b*12+:12];
  assign bc_ptr[b*14+:14]=selecting?14'd8192:dc_ptr[b*14+:14];
  assign dc_ready[b]=bc_ready[b]&&!selecting;
  assign min_bank_valid[b]=br_valid[b]&&br_op[b*2+:2]==3;
  assign min_bank_empty[b]=br_status[b*2+:2]==1;
  assign dr_valid[b]=br_valid[b]&&!selecting;
  assign br_ready[b]=selecting?min_accept[b]:dr_ready[b];
  assign bo_valid[b]=(state==SEED&&seed_bank==b)||do_valid[b];
  assign bo_node[b*32+:32]=state==SEED?source_node:do_node[b*32+:32];
  assign bo_code[b*3+:3]=state==SEED?3'd5:do_code[b*3+:3];
  assign bo_pair[b*64+:64]=state==SEED?64'b0:do_pair[b*64+:64];
  assign bo_line[b*256+:256]=do_line[b*256+:256];
  assign bo_arg[b*28+:28]=state==SEED?28'b0:do_arg[b*28+:28];
  assign bo_cookie[b*20+:20]=state==SEED?20'b0:do_cookie[b*20+:20];
  assign do_ready[b]=bo_ready[b]&&state!=SEED;
  assign result_ready[b]=result_opcode[b*3+:3]==2?dp_result_ready[b]:1'b1;
  cp_backend_bank #(.BANK_ID(b)) bank(.clk,.reset(core_reset),.sample_clear(1'b0),.wave_restart(state==REOPEN),.flush(state==FLUSH),.node_count(cfg_nodes),.label_base(cfg_label_base),.scratch_base(cfg_scratch_base),
   .in_valid(bank_candidate_v[b]),.in_ready(bank_candidate_r[b]),.in_node(bank_candidate_data[b*96+64+:32]),.in_pair(bank_candidate_data[b*96+:64]),
   .op_valid(bo_valid[b]),.op_ready(bo_ready[b]),.op_node(bo_node[b*32+:32]),.op_code(bo_code[b*3+:3]),.op_pair(bo_pair[b*64+:64]),.op_line(bo_line[b*256+:256]),.op_arg(bo_arg[b*28+:28]),.op_cookie(bo_cookie[b*20+:20]),
   .result_valid(result_valid[b]),.result_ready(result_ready[b]),.result_node(result_node[b*32+:32]),.result_opcode(result_opcode[b*3+:3]),.result_status(result_status[b*4+:4]),.old_label(result_label[b*64+:64]),.result_cookie(result_cookie[b*20+:20]),
   .ctrl_valid(bc_valid[b]),.ctrl_ready(bc_ready[b]),.ctrl_op(bc_op[b*2+:2]),.ctrl_bucket(bc_bucket[b*12+:12]),.ctrl_ptr(bc_ptr[b*14+:14]),
   .ctrl_rsp_valid(br_valid[b]),.ctrl_rsp_ready(br_ready[b]),.ctrl_rsp_op(br_op[b*2+:2]),.ctrl_rsp_status(br_status[b*2+:2]),.ctrl_rsp_bucket(br_bucket[b*12+:12]),.ctrl_rsp_node(br_node[b*32+:32]),.ctrl_rsp_arg(br_arg[b*32+:32]),.ctrl_rsp_ptr(br_ptr[b*14+:14]),.ctrl_rsp_next(br_next[b*14+:14]),
   .can_valid(ncv[48+b]),.can_ready(ncr[48+b]),.can_kind(nck[(48+b)*4+:4]),.can_line(ncl[(48+b)*32+:32]),.can_id(nid[(48+b)*32+:32]),.can_gen(ngen[(48+b)*32+:32]),.can_data(nwdata[b*256+:256]),
   .can_rsp_valid(nrv[48+b]),.can_rsp_ready(nrr[48+b]),.can_rsp_kind(nrk[(48+b)*4+:4]),.can_rsp_id(nrid[(48+b)*32+:32]),.can_rsp_gen(nrgen[(48+b)*32+:32]),.can_rsp_status(nstatus[(48+b)*2+:2]),.can_rsp_data(nrd[(48+b)*256+:256]),
   .scr_valid(ncv[112+b]),.scr_ready(ncr[112+b]),.scr_kind(nck[(112+b)*4+:4]),.scr_line(ncl[(112+b)*32+:32]),.scr_id(nid[(112+b)*32+:32]),.scr_gen(ngen[(112+b)*32+:32]),.scr_data(nwdata[(64+b)*256+:256]),
   .scr_rsp_valid(nrv[112+b]),.scr_rsp_ready(nrr[112+b]),.scr_rsp_kind(nrk[(112+b)*4+:4]),.scr_rsp_id(nrid[(112+b)*32+:32]),.scr_rsp_gen(nrgen[(112+b)*32+:32]),.scr_rsp_status(nstatus[(112+b)*2+:2]),.scr_rsp_data(nrd[(112+b)*256+:256]),
   .initialized(bank_initialized[b]),.done(bank_done[b]),.idle(bank_idle[b]),.expansion_idle(bank_expansion_idle[b]),.error(bank_error[b]),.overflow(bank_overflow[b]));
 end
 wire [15:0] front_idle,front_error,yv,yr;wire [239:0] yc;wire [1023:0] yp;wire cost_cfg_we;wire [3:0] cost_cfg_idx;wire [63:0] cost_cfg_data;
 for(genvar g=0;g<16;g=g+1)begin:fronts
  wire dv,mv_,dr,rr_,drv,rv_,drr;wire [63:0] da,edge_line;wire [15:0] dt,mt;
  wire [127:0] od,ot;wire [255:0] op;wire [3:0] ov,or_;
  wire edge_legal=nstatus[g*2+:2]==0&&nrk[g*4+:4]==2&&nrid[g*32+8+:24]==0&&nrgen[g*32+8+:24]==0;
  wire desc_legal=nstatus[(16+g)*2+:2]==0&&nrk[(16+g)*4+:4]==11&&nrid[(16+g)*32+8+:24]==0&&nrgen[(16+g)*32+8+:24]==0;
  lf_front_context front(.clk,.reset(core_reset),.av(av[g]),.ar(ar[g]),.tv(tv[g]),.tr(tr[g]),.at(at[g*16+:16]),
   .pv(pv[g]),.pr(pr[g]),.pt(pt[g*16+:16]),.stale(stale[g]),.pn(pn[g*32+:32]),.pp(pp[g*64+:64]),.epoch,
   .format16(1'b0),.descriptor_base,.edge_base(cfg_edge_base),.edge_count(cfg_edges),.cells(cfg_cells),.cfg_we(cost_cfg_we),.cfg_idx(cost_cfg_idx),.cfg_cost(cost_cfg_data),
   .dv,.dr(ncr[16+g]&&da[63:32]==0),.da,.dt,.drv(nrv[16+g]&&desc_legal),.drr,.drt({nrgen[(16+g)*32+:8],nrid[(16+g)*32+:8]}),.drd(nrd[(16+g)*256+:256]),
   .mv(mv_),.mr(ncr[g]&&edge_line[63:32]==0),.ml(edge_line),.mt,.rv(nrv[g]&&edge_legal),.rr(rr_),.rt({nrgen[g*32+:8],nrid[g*32+:8]}),.rd(nrd[g*256+:256]),
   .yv(yv[g]),.yr(yr[g]),.yc(yc[g*15+:15]),.yp(yp[g*64+:64]),.ov,.or_,.od,.ot,.op,.error(front_error[g]),.idle(front_idle[g]));
  assign ncv[g]=mv_&&edge_line[63:32]==0;assign ncl[g*32+:32]=edge_line[31:0];assign nck[g*4+:4]=2;assign nid[g*32+:32]={24'b0,mt[7:0]};assign ngen[g*32+:32]={24'b0,mt[15:8]};assign nrr[g]=rr_||!edge_legal;
  assign ncv[16+g]=dv&&da[63:32]==0;assign ncl[(16+g)*32+:32]=da[31:0];assign nck[(16+g)*4+:4]=11;assign nid[(16+g)*32+:32]={24'b0,dt[7:0]};assign ngen[(16+g)*32+:32]={24'b0,dt[15:8]};assign nrr[16+g]=drr||!desc_legal;
  assign ncv[32+g]=0;assign ncl[(32+g)*32+:32]=0;assign nck[(32+g)*4+:4]=3;assign nid[(32+g)*32+:32]=0;assign ngen[(32+g)*32+:32]=0;assign nrr[32+g]=1;
  reg protocol_error;
  always @(posedge clk)if(core_reset)protocol_error<=0;else if((dv&&|da[63:32])||(mv_&&|edge_line[63:32])||(nrv[g]&&!edge_legal)||(nrv[16+g]&&!desc_legal)||nrv[32+g])protocol_error<=1;
  for(genvar l=0;l<4;l=l+1)begin:lanes
   assign candidate_v[g*4+l]=ov[l];assign or_[l]=candidate_r[g*4+l];assign candidate_data[(g*4+l)*96+:96]={od[l*32+:32],op[l*64+:64]};
  end
 end
 wire [15:0] fproto;
 for(genvar p=0;p<16;p=p+1)assign fproto[p]=fronts[p].protocol_error;
 wire output_init,output_idle,export_ready,export_done,output_error;wire [7:0] target_valid,target_first;wire [1:0] write_v,write_r,ack_v,ack_r;
 wire [127:0] write_line;wire [511:0] write_data;wire [14:0] output_issued,output_acked;
 df_output_service output_service(.clk,.reset(core_reset),.iv(yv),.ir(yr),.icell(yc),.ipair(yp),.ov(target_valid),.ordy(8'hff),.first(target_first),
  .init_done(output_init),.idle(output_idle),.export_start(state==EXPORT_START),.export_ready,.cells(cfg_cells),.output_base_line(output_base),
  .write_v,.write_r,.write_line,.write_data,.ack_v,.ack_r,.export_done,.error(output_error),.issued_count(output_issued),.acked_count(output_acked));
 wire admin_init,admin_cost,admin_error;wire [2:0] admin_phase=state==INIT?3'd1:state==COST?3'd2:(state==EXPORT_START||state==EXPORT_WAIT)?3'd3:3'd0;
 cp_admin admin(.clk,.reset(core_reset),.phase(admin_phase),.node_count(cfg_nodes),.cost_count(cfg_costs),.sample_index,.label_base(cfg_label_base),.cost_base(cfg_cost_base),
  .cv(ncv[207:176]),.cr(ncr[207:176]),.ck(nck[831:704]),.cl(ncl[6655:5632]),.cid(nid[6655:5632]),.cgen(ngen[6655:5632]),.cd(nwdata[40959:32768]),
  .rv(nrv[207:176]),.rr(nrr[207:176]),.rk(nrk[831:704]),.rid(nrid[6655:5632]),.rgen(nrgen[6655:5632]),.rd(nrd[53247:45056]),.rstatus(nstatus[415:352]),
  .init_done(admin_init),.cost_done(admin_cost),.error(admin_error),.cfg_we(cost_cfg_we),.cfg_idx(cost_cfg_idx),.cfg_cost(cost_cfg_data),.write_v,.write_r,.write_line,.write_data,.ack_v,.ack_r);
 integer new_targets,reqs,rsps;
 always @*begin
  new_targets=0;for(integer i=0;i<8;i=i+1)if(target_valid[i]&&target_first[i])new_targets=new_targets+1;
  reqs=0;rsps=0;for(integer i=0;i<32;i=i+1)begin if(mv[i]&&mr[i])reqs=reqs+1;if(sv[i]&&sr[i])rsps=rsps+1;end
 end
 wire datapath_error=network_error||pending_error||(|bank_error)||(|bank_overflow)||(|front_error)||(|fproto)||dispatch_error||admin_error||output_error;
 always @(posedge clk)begin
  if(reset)begin state<=IDLE;busy<=0;done<=0;error<=0;sample_done<=0;sample_index<=0;cycles<=0;waves<=0;recorded<=0;mem_requests<=0;mem_responses<=0;job_valid<=0;source_node<=0;targets<=0;descriptor_base<=0;output_base<=0;bucket<=0;have_bucket<=0;epoch<=0;for(integer i=0;i<19;i=i+1)phase_cycles[i]<=0;end
  else begin
   sample_done<=0;
   if(cfg_job_we&&!busy)begin jobs[cfg_job_index]<={cfg_job_source,cfg_job_targets};job_valid[cfg_job_index]<=1;end
   if(busy)begin cycles<=cycles+1;phase_cycles[state]<=phase_cycles[state]+1;mem_requests<=mem_requests+reqs;mem_responses<=mem_responses+rsps;end
   if(state==SRST)recorded<=0;else recorded<=recorded+new_targets;
   if(busy&&state!=SRST&&state!=LOAD&&state!=FAULT&&datapath_error)begin error<=1;state<=FAULT;end
   else case(state)
    IDLE:if(start)begin done<=0;error<=0;cycles<=0;waves<=0;mem_requests<=0;mem_responses<=0;sample_index<=0;descriptor_base<=cfg_descriptor_base;output_base<=cfg_output_base;
     for(integer i=0;i<19;i=i+1)phase_cycles[i]<=0;
     if(config_bad)begin error<=1;done<=1;end else begin busy<=1;state<=SRST;end
    end
    SRST:begin state<=LOAD;have_bucket<=0;epoch<=0;end
    LOAD:if(sample_bad)begin error<=1;state<=FAULT;end else begin source_node<=jobs[sample_index][63:32];targets<=jobs[sample_index][31:0];state<=INIT;end
    INIT:if((&bank_initialized)&&output_init&&admin_init&&net_empty)state<=COST;
    COST:if(admin_cost&&net_empty)state<=targets==0?EXPORT_START:SEED;
    SEED:if(bo_ready[seed_bank])state<=SEED_WAIT;
    SEED_WAIT:if((&bank_idle)&&net_empty)state<=MIN_START;
    MIN_START:if(min_ready)state<=MIN_WAIT;
    MIN_WAIT:if(min_valid)begin
     if(min_empty||(have_bucket&&min_bucket!=bucket&&recorded==targets))state<=EXPORT_START;
     else begin bucket<=min_bucket;have_bucket<=1;state<=WAVE_START;end
    end
    WAVE_START:if(dispatch_ready)begin state<=EXPAND;waves<=waves+1;epoch<=epoch+1'b1;end
    EXPAND:if(pops_done&&(&front_idle)&&candidate_idle&&(&bank_expansion_idle)&&net_empty&&output_idle)state<=FLUSH;
    FLUSH:state<=FINALIZE;
    FINALIZE:if((&bank_done)&&(&bank_idle)&&net_empty)state<=REOPEN;
    REOPEN:state<=REOPEN_WAIT;
    REOPEN_WAIT:if((&bank_expansion_idle)&&(&bank_initialized))state<=MIN_START;
    EXPORT_START:if(export_ready)state<=EXPORT_WAIT;
    EXPORT_WAIT:if(export_done&&net_empty&&(&bank_idle))begin sample_done<=1;state<=COMPLETE;end
    COMPLETE:if({1'b0,sample_index}+1>=cfg_jobs)begin busy<=0;done<=1;state<=IDLE;end else begin sample_index<=sample_index+1'b1;descriptor_base<=descriptor_base+cfg_descriptor_stride;output_base<=output_base+cfg_output_stride;state<=SRST;end
    FAULT:begin busy<=0;done<=1;state<=IDLE;end
    default:begin error<=1;state<=FAULT;end
   endcase
  end
 end
endmodule
