`timescale 1ns/1ps
module sparse_tile #(parameter POP_REDUCE=1,MEMBER_CAP=1024,CHANGED_LIMIT=512,CLOSED_LIMIT=512,INIT_OUTSTANDING=16)(
 input wire clk,rst,start,input wire [31:0] row_base,edge_base,cost_base,job_base,
 input wire [6:0] jobs,input wire [15:0] cell_count,input wire [4:0] cost_count,
 output reg done,output wire error,
 output wire [7:0] physical_valid,input wire [7:0] physical_ready,output wire [7:0] physical_write,
 output wire [255:0] physical_line,output wire [47:0] physical_id,output wire [2047:0] physical_data,
 input wire [7:0] physical_rsp_valid,output wire [7:0] physical_rsp_ready,input wire [47:0] physical_rsp_id,input wire [2047:0] physical_rsp_data,
 output wire [7:0] issued,accepted,committed,output wire [255:0] commit_nodes,
 output reg [31:0] wave,output reg [5:0] phase,output reg [5:0] qid,output wire [7:0] owner_error,
 output wire [255:0] active_counts,commit_counts,output wire [47:0] mshr_peaks,output wire [39:0] dirty_peaks);
 wire [32:0] mem_valid,mem_ready,mem_write,rsp_valid,rsp_ready;
 wire [1055:0] mem_line;wire [197:0] mem_id,rsp_id;wire [8447:0] mem_data,rsp_data;
 wire fabric_idle,fabric_error;wire [31:0] fab_accepted,fab_returned;
 r2_shared_fabric fabric(clk,rst,mem_valid,mem_ready,mem_write,mem_line,mem_id,mem_data,rsp_valid,rsp_ready,rsp_id,rsp_data,
  physical_valid,physical_ready,physical_write,physical_line,physical_id,physical_data,physical_rsp_valid,physical_rsp_ready,physical_rsp_id,physical_rsp_data,fabric_idle,fabric_error,fab_accepted,fab_returned);
 reg [2:0] command;reg [7:0] command_epoch;wire [23:0] leaf_op;wire [63:0] leaf_epoch;wire [7:0] leaf_done;wire command_done;
 r2_control_tree control(clk,rst,command,command_epoch,leaf_done,leaf_op,leaf_epoch,command_done);
 reg [11:0] bucket;reg [15:0] bucket_epoch;
 reg [31:0] source,targets,cell_base,output_base;
 wire [7:0] bank_done,has_bucket,bank_error;wire [95:0] minima;
 wire [7:0] pv,pr;wire [255:0] pn;wire [511:0] pp;
 wire [7:0] fv,fr,front_idle,front_error;wire [255:0] fn;wire [511:0] fp;
 wire [7:0] ov,ordy,owner_done,owner_idle,uv,ur,queue_idle,queue_error,cv,ca;wire [255:0] on,ul;wire [511:0] op;wire [31:0] um;wire [71:0] ci,commit_index;wire [7:0] commit_issue_ready;
 wire [7:0] close_valid;wire [7:0] close_ready;wire [255:0] close_nodes;wire [511:0] close_pairs;
 wire router_idle;wire [31:0] conflicts;
 wire [7:0] meta_valid,meta_ready,meta_idle,meta_error,reduce_valid,reduce_ready,reduce_idle,reduce_init,reduce_error;
 wire [943:0] meta_payload,reduce_payload;wire [255:0] records;wire cell_router_idle;
 r2_cell_router cell_router(clk,rst||command==7,meta_valid,meta_ready,meta_payload,reduce_valid,reduce_ready,reduce_payload,cell_router_idle);
 reg [31:0] record_a[0:3],record_b[0:1],recorded;
 always @(posedge clk)begin for(integer i=0;i<4;i=i+1)record_a[i]<=records[2*i*32+:32]+records[(2*i+1)*32+:32];
  for(integer i=0;i<2;i=i+1)record_b[i]<=record_a[2*i]+record_a[2*i+1];recorded<=record_b[0]+record_b[1];end
 wire [103:0] min_keys;wire [7:0] min_valid;wire minimum_valid;wire [12:0] minimum;wire [7:0] minimum_epoch;
 r2_min8 minimum_tree(clk,rst,min_valid,min_keys,leaf_epoch,minimum_valid,minimum,minimum_epoch);
 reg cost_we;reg [3:0] cost_index;reg [63:0] cost_data;reg [4:0] cost_pos;reg [255:0] cost_beat;
 reg ctl_valid,ctl_write;reg [31:0] ctl_line;reg [5:0] ctl_id;reg [255:0] ctl_data;
 reg export_en;reg [11:0] export_index;wire [511:0] export_pairs;reg [511:0] export_hold;
 reg [15:0] output_sent,output_acked;reg [15:0] write_busy;integer free_write;
 always @*begin free_write=-1;for(integer i=0;i<16;i=i+1)if(!write_busy[i]&&free_write<0)free_write=i;end
 reg local_error,close_mode;reg [5:0] after_neutral;reg [3:0] closure_drain;reg [12:0] held_minimum;
 assign error=local_error||fabric_error||(|owner_error)||(|bank_error)||(|front_error)||(|queue_error)||(|meta_error)||(|reduce_error);
 assign issued=fv&fr;assign accepted=ov&ordy;assign committed=ca;
 assign mem_valid[32]=ctl_valid;assign mem_write[32]=ctl_write;assign mem_line[32*32+:32]=ctl_line;assign mem_id[32*6+:6]=ctl_id;assign mem_data[32*256+:256]=ctl_data;assign rsp_ready[32]=1;
 sparse_router router(clk,rst||command==7,fv,fr,fn,fp,ov,ordy,on,op,conflicts,router_idle);
 for(genvar n=0;n<8;n=n+1)begin:banks
  wire [2:0] leaf_command=leaf_op[n*3+:3];
  wire leaf_reset=rst||leaf_command==7;
  wire [2:0] bank_command=(leaf_command==4&&close_mode)?4:(leaf_command==1||leaf_command==2||leaf_command==3||leaf_command==5)?leaf_command:0;
  reg reset_seen;always @(posedge clk)reset_seen<=leaf_command==7;
  reg leaf_cost_we;reg [3:0] leaf_cost_index;reg [63:0] leaf_cost_data;
  always @(posedge clk)begin leaf_cost_we<=cost_we;leaf_cost_index<=cost_index;leaf_cost_data<=cost_data;end
  wire fav,far,mav,mar,fork_idle;wire [31:0] fan,man;wire [63:0] fap,mapair;wire [31:0] pop_count;
  if(POP_REDUCE)begin:online
   r2_pop_fork fork_pop(clk,leaf_reset,pv[n],pr[n],pn[n*32+:32],pp[n*64+:64],fav,far,fan,fap,mav,mar,man,mapair,fork_idle,pop_count);
   assign close_ready[n]=1;
  end else begin:closed_ablation
   assign fav=pv[n];assign pr[n]=far;assign fan=pn[n*32+:32];assign fap=pp[n*64+:64];
   assign mav=close_valid[n];assign close_ready[n]=mar;assign man=close_nodes[n*32+:32];assign mapair=close_pairs[n*64+:64];assign fork_idle=!pv[n];assign pop_count=0;
  end
  wire [31:0] mc;wire [63:0] mp;wire [5:0] mq;wire [15:0] me;wire [31:0] md0,md1,md2,md3;wire [4:0] meta_peak;
  r2_pop_metadata meta(clk,leaf_reset,cell_base,{16'b0,cell_count},qid,bucket_epoch,mav,mar,man,mapair,
   mem_valid[24+n],mem_ready[24+n],mem_line[(24+n)*32+:32],mem_id[(24+n)*6+:6],rsp_valid[24+n],rsp_ready[24+n],rsp_id[(24+n)*6+:6],rsp_data[(24+n)*256+:256],
   meta_valid[n],meta_ready[n],mc,mp,mq,me,meta_idle[n],meta_error[n],md0,md1,md2,md3,meta_peak);
  assign mem_write[24+n]=0;assign mem_data[(24+n)*256+:256]=0;
  assign meta_payload[n*118+:118]={mq,me,mc,mp};
  wire [12:0] entries=({1'b0,cell_count}+7)>>3;
  wire [31:0] retired,forwarded;
  r2_cell_reducer reducer(clk,leaf_reset,leaf_command==1,entries,qid,bucket_epoch,
   reduce_valid[n],reduce_ready[n],reduce_payload[n*118+67+:12],reduce_payload[n*118+:64],reduce_payload[n*118+112+:6],reduce_payload[n*118+96+:16],
   export_en,export_index,export_pairs[n*64+:64],reduce_idle[n],reduce_init[n],reduce_error[n],records[n*32+:32],retired,forwarded);
  assign leaf_done[n]=leaf_command==7?reset_seen:leaf_command==0?!bank_done[n]:leaf_command==1?(bank_done[n]&&reduce_init[n]):
   leaf_command==4?(front_idle[n]&&fork_idle&&(!close_mode||bank_done[n])):leaf_command==6?(owner_done[n]&&queue_idle[n]):bank_done[n];
  assign min_keys[n*13+:13]={!has_bucket[n],minima[n*12+:12]};
  assign min_valid[n]=leaf_command==5&&bank_done[n];

  wire [31:0] bc0,bc1;wire [31:0] dummy0,dummy1,dummy2,dummy3,dummy4,dummy5;wire [10:0] member_peak;wire [9:0] changed_peak,changed_occupancy;
  wire [31:0] local_index=commit_index[n*9+:9];
  assign commit_nodes[n*32+:32]=((local_index>>2)<<5)|(n<<2)|(local_index&3);
  sparse_bank #(.BANK(n),.MC(MEMBER_CAP),.CLOSED_LIMIT(CLOSED_LIMIT),.INIT_OUTSTANDING(INIT_OUTSTANDING),.POP_REDUCE(POP_REDUCE)) bank(clk,leaf_reset,bank_command,bucket,source,bank_done[n],has_bucket[n],minima[n*12+:12],bank_error[n],
   pv[n],pr[n],pn[n*32+:32],pp[n*64+:64],cv[n],ca[n],ci[n*9+:9],commit_issue_ready[n],commit_index[n*9+:9],close_valid[n],close_ready[n],close_nodes[n*32+:32],close_pairs[n*64+:64],
   mem_valid[16+n],mem_ready[16+n],mem_write[16+n],mem_line[(16+n)*32+:32],mem_data[(16+n)*256+:256],rsp_valid[16+n],rsp_data[(16+n)*256+:256],mem_id[(16+n)*6+:6],rsp_id[(16+n)*6+:6],
   active_counts[n*32+:32],commit_counts[n*32+:32],bc0,bc1,member_peak);
  assign rsp_ready[16+n]=1;
  wire [3:0] front_id;wire [31:0] f0,f1,f2,f3,f4;wire [2:0] fpeak;
  sparse_frontend front(clk,leaf_reset,fav,far,fan,fap,row_base,edge_base,leaf_cost_we,leaf_cost_index,leaf_cost_data,
   mem_valid[8+n],mem_ready[8+n],mem_line[(8+n)*32+:32],front_id,rsp_valid[8+n],rsp_ready[8+n],rsp_id[(8+n)*6+:4],rsp_data[(8+n)*256+:256],
   fv[n],fr[n],fn[n*32+:32],fp[n*64+:64],front_idle[n],front_error[n],f0,f1,f2,f3,f4,fpeak);
  assign mem_id[(8+n)*6+:6]={2'b00,front_id};assign mem_write[8+n]=0;assign mem_data[(8+n)*256+:256]=0;
  sparse_owner owner(clk,leaf_reset,ov[n],ordy[n],on[n*32+:32],op[n*64+:64],leaf_command==6,owner_done[n],uv[n],ur[n],ul[n*32+:32],um[n*4+:4],
   mem_valid[n],mem_ready[n],mem_write[n],mem_line[n*32+:32],mem_id[n*6+:6],mem_data[n*256+:256],rsp_valid[n],rsp_ready[n],rsp_id[n*6+:6],rsp_data[n*256+:256],owner_idle[n],owner_error[n],dummy0,dummy1,dummy2,dummy3,dummy4,dummy5,mshr_peaks[n*6+:6],dirty_peaks[n*5+:5]);
  changed_queue #(.LIMIT(CHANGED_LIMIT)) changes(clk,leaf_reset,uv[n],ur[n],ul[n*32+:32],um[n*4+:4],leaf_command==3,cv[n],commit_issue_ready[n],ci[n*9+:9],ca[n],commit_index[n*9+:9],queue_idle[n],queue_error[n],changed_peak,changed_occupancy);
 end

 // Each transition to an operation goes through an acknowledged neutral epoch.
 task neutral(input [5:0] destination);begin command<=0;command_epoch<=command_epoch+1;after_neutral<=destination;phase<=6;end endtask
 task launch(input [2:0] operation,input [5:0] waiting);begin command<=operation;command_epoch<=command_epoch+1;phase<=waiting;end endtask
 always @(posedge clk)begin
  if(rst)begin phase<=0;command<=7;command_epoch<=0;done<=0;local_error<=0;close_mode<=0;cost_we<=0;ctl_valid<=0;ctl_id<=0;wave<=0;qid<=0;bucket_epoch<=0;export_en<=0;write_busy<=0;output_sent<=0;output_acked<=0;closure_drain<=0;end
  else begin
   cost_we<=0;if(ctl_valid&&mem_ready[32])ctl_valid<=0;
   if(phase>=30&&phase<=37&&rsp_valid[32])begin
    if(rsp_id[32*6+:6]>=16||!write_busy[rsp_id[32*6+:4]])local_error<=1;
    else begin write_busy[rsp_id[32*6+:4]]<=0;output_acked<=output_acked+1;end
   end
   case(phase)
   0:if(start)begin done<=0;cost_pos<=0;qid<=0;phase<=1;if(jobs==0||jobs>64||cell_count==0||cell_count>32768||cost_count==0||cost_count>16)local_error<=1;end
   1:if(!ctl_valid)begin ctl_valid<=1;ctl_write<=0;ctl_id<=0;ctl_line<=cost_base+(cost_pos>>2);ctl_data<=0;phase<=2;end
   2:if(rsp_valid[32])begin cost_beat<=rsp_data[32*256+:256];phase<=3;end
   3:begin cost_we<=1;cost_index<=cost_pos;cost_data<=cost_beat[cost_pos[1:0]*64+:64];cost_pos<=cost_pos+1;
    if(cost_pos+1==cost_count)phase<=4;else if(cost_pos[1:0]==3)phase<=1;end
   4:if(!ctl_valid)begin ctl_valid<=1;ctl_write<=0;ctl_id<=0;ctl_line<=job_base+qid;phase<=5;end
   5:if(rsp_valid[32])begin
    source<=rsp_data[32*256+:32];targets<=rsp_data[32*256+32+:32];cell_base<=rsp_data[32*256+64+:32];output_base<=rsp_data[32*256+96+:32];wave<=0;bucket_epoch<=0;
    if(rsp_data[32*256+:32]>=4096||rsp_data[32*256+32+:32]>cell_count)local_error<=1;
    launch(7,7);
   end
   6:if(command_done)phase<=after_neutral;
   7:if(command_done)neutral(8);
   8:launch(1,9);
   9:if(command_done)neutral(10);
   10:launch(5,11);
   11:if(command_done&&minimum_valid&&minimum_epoch==command_epoch)begin
    if(wave==0)begin if(minimum[12]||targets==0)neutral(30);else begin bucket<=minimum[11:0];bucket_epoch<=bucket_epoch+1;neutral(12);end end
    else if(!minimum[12]&&minimum[11:0]==bucket)neutral(12);
    else begin held_minimum<=minimum;closure_drain<=0;if(POP_REDUCE)phase<=23;else begin close_mode<=1;neutral(25);end end
   end
   12:begin close_mode<=0;launch(2,13);wave<=wave+1;end
   13:if(command_done)neutral(14);
   14:launch(4,15);
   15:if(command_done&&router_idle)neutral(16);
   16:launch(6,17);
   17:if(command_done)neutral(18);
   18:launch(3,19);
   19:if(command_done)neutral(10);
   25:launch(4,26);
   26:if(command_done)phase<=23;
   23:begin
    if((&meta_idle)&&cell_router_idle&&(&reduce_idle)&&fabric_idle)begin if(closure_drain==7)phase<=24;else closure_drain<=closure_drain+1;end else closure_drain<=0;
   end
   24:if(recorded>targets)local_error<=1;else if(recorded==targets||held_minimum[12])neutral(30);else begin bucket<=held_minimum[11:0];bucket_epoch<=bucket_epoch+1;neutral(12);end
   30:begin output_sent<=0;output_acked<=0;write_busy<=0;export_index<=0;export_en<=1;phase<=31;end
   31:phase<=32;
   32:phase<=33;
   33:begin export_hold<=export_pairs;phase<=34;end
   34:if((!ctl_valid||mem_ready[32])&&free_write>=0)begin
    ctl_valid<=1;ctl_write<=1;ctl_id<=free_write;ctl_line<=output_base+output_sent;ctl_data<=export_hold[255:0];write_busy[free_write]<=1;output_sent<=output_sent+1;
    if(output_sent+1==(({1'b0,cell_count}+3)>>2))begin export_en<=0;phase<=37;end else phase<=35;
   end
   35:if((!ctl_valid||mem_ready[32])&&free_write>=0)begin
    ctl_valid<=1;ctl_write<=1;ctl_id<=free_write;ctl_line<=output_base+output_sent;ctl_data<=export_hold[511:256];write_busy[free_write]<=1;output_sent<=output_sent+1;
    if(output_sent+1==(({1'b0,cell_count}+3)>>2))begin export_en<=0;phase<=37;end else begin export_index<=export_index+1;phase<=31;end
   end
   37:if(output_acked==output_sent&&write_busy==0&&!ctl_valid&&fabric_idle)begin if(qid+1==jobs)begin done<=1;phase<=0;end else begin qid<=qid+1;phase<=4;end end
   default:local_error<=1;
   endcase
  end
 end
endmodule
