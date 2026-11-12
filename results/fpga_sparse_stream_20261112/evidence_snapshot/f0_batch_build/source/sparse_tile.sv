`timescale 1ns/1ps
module sparse_tile #(parameter MEMBER_CAP=1024,CHANGED_LIMIT=512,CLOSED_LIMIT=512)(input wire clk,rst,start,input wire [31:0] source,row_base,edge_base,cost_base,cell_base,
 input wire [6:0] cell_count,input wire [31:0] targets,input wire [4:0] cost_count,
 output reg done,output wire error,
 output wire [24:0] mem_valid,input wire [24:0] mem_ready,output wire [24:0] mem_write,
 output wire [799:0] mem_line,output wire [149:0] mem_id,output wire [6399:0] mem_data,
 input wire [24:0] rsp_valid,output wire [24:0] rsp_ready,input wire [149:0] rsp_id,input wire [6399:0] rsp_data,
 input wire [11:0] output_index,output reg [63:0] output_pair,
 output wire [7:0] issued,accepted,committed,output wire [255:0] commit_nodes,
 output reg [31:0] wave,output reg [4:0] phase,output wire [7:0] owner_error,
 output wire [255:0] active_counts,commit_counts,output wire [47:0] mshr_peaks,output wire [39:0] dirty_peaks);
 localparam IDLE=0,RESET_JOB=1,LOAD_COST=2,COST_WAIT=3,COST_WORDS=4,INIT=5,GAP=6,SELECT=7,POP=8,DRAIN=9,FENCE=10,COMMIT=11,DECIDE=12,CLOSE=13,FINISH=14;
 wire local_reset=rst||phase==RESET_JOB;
 reg [2:0] command;reg [11:0] bucket;wire [7:0] bank_done,has_bucket,bank_error;
 wire [95:0] minima;wire [7:0] pv,pr;wire [255:0] pn;wire [511:0] pp;
 wire [7:0] fv,fr,front_idle,front_error;wire [255:0] fn;wire [511:0] fp;
 wire [7:0] ov,ordy,owner_done,owner_idle,uv,ur,queue_idle,queue_error,cv,ca;wire [255:0] on,ul;wire [511:0] op;wire [31:0] um;wire [71:0] ci,commit_index;wire [7:0] commit_issue_ready;
 wire [7:0] close_valid;reg [7:0] close_ready;wire [255:0] close_nodes;wire [511:0] close_pairs;
 wire router_idle;wire [31:0] conflicts;
 reg cost_we;reg [3:0] cost_index;reg [63:0] cost_data;reg cost_loaded;reg [4:0] cost_pos;reg [255:0] cost_beat;
 reg ctl_valid,ctl_write;reg [31:0] ctl_line;reg [255:0] ctl_data;
 reg [31:0] recorded;reg [6:0] output_init;
 (* ram_style="block" *) reg [63:0] outputs[0:4095];
 reg [11:0] output_base;reg [6:0] next_job;reg [63:0] output_valid;
 reg [63:0] output_q;reg [5:0] target_cell;reg [63:0] target_pair;
 reg [3:0] close_state;reg [31:0] held_node;reg [63:0] held_pair;
 reg cell_cache_valid;reg [31:0] cell_cache_tag;reg [255:0] cell_cache;
 reg local_error;integer b,chosen;reg [11:0] next_min;reg any_min;
 assign error=local_error||(|owner_error)||(|bank_error)||(|front_error)||(|queue_error);
 assign issued=fv&fr;assign accepted=ov&ordy;assign committed=ca;
 assign mem_valid[24]=ctl_valid;assign mem_write[24]=ctl_write;assign mem_line[24*32+:32]=ctl_line;assign mem_id[24*6+:6]=0;assign mem_data[24*256+:256]=ctl_data;assign rsp_ready[24]=1;
 sparse_router router(clk,local_reset,fv,fr,fn,fp,ov,ordy,on,op,conflicts,router_idle);
 for(genvar n=0;n<8;n=n+1)begin:banks
  wire [31:0] bc0,bc1;wire [31:0] dummy0,dummy1,dummy2,dummy3,dummy4,dummy5;wire [10:0] member_peak;wire [9:0] changed_peak,changed_occupancy;
  wire [31:0] local_index=commit_index[n*9+:9];
  assign commit_nodes[n*32+:32]=((local_index>>2)<<5)|(n<<2)|(local_index&3);
  sparse_bank #(.BANK(n),.MC(MEMBER_CAP),.CLOSED_LIMIT(CLOSED_LIMIT)) bank(clk,local_reset,command,bucket,source,bank_done[n],has_bucket[n],minima[n*12+:12],bank_error[n],
   pv[n],pr[n],pn[n*32+:32],pp[n*64+:64],cv[n],ca[n],ci[n*9+:9],commit_issue_ready[n],commit_index[n*9+:9],close_valid[n],close_ready[n],close_nodes[n*32+:32],close_pairs[n*64+:64],
   mem_valid[16+n],mem_ready[16+n],mem_write[16+n],mem_line[(16+n)*32+:32],mem_data[(16+n)*256+:256],rsp_valid[16+n],rsp_data[(16+n)*256+:256],mem_id[(16+n)*6+:6],rsp_id[(16+n)*6+:6],
   active_counts[n*32+:32],commit_counts[n*32+:32],bc0,bc1,member_peak);
  assign rsp_ready[16+n]=1;
  wire [3:0] front_id;wire [31:0] f0,f1,f2,f3,f4;wire [2:0] fpeak;
  sparse_frontend front(clk,local_reset,pv[n],pr[n],pn[n*32+:32],pp[n*64+:64],row_base,edge_base,cost_we,cost_index,cost_data,
   mem_valid[8+n],mem_ready[8+n],mem_line[(8+n)*32+:32],front_id,rsp_valid[8+n],rsp_ready[8+n],rsp_id[(8+n)*6+:4],rsp_data[(8+n)*256+:256],
   fv[n],fr[n],fn[n*32+:32],fp[n*64+:64],front_idle[n],front_error[n],f0,f1,f2,f3,f4,fpeak);
  assign mem_id[(8+n)*6+:6]={2'b00,front_id};assign mem_write[8+n]=0;assign mem_data[(8+n)*256+:256]=0;
  sparse_owner_f0 owner(clk,local_reset,ov[n],ordy[n],on[n*32+:32],op[n*64+:64],phase==FENCE,owner_done[n],uv[n],ur[n],ul[n*32+:32],um[n*4+:4],
   mem_valid[n],mem_ready[n],mem_write[n],mem_line[n*32+:32],mem_id[n*6+:6],mem_data[n*256+:256],rsp_valid[n],rsp_ready[n],rsp_id[n*6+:6],rsp_data[n*256+:256],owner_idle[n],owner_error[n],dummy0,dummy1,dummy2,dummy3,dummy4,dummy5,mshr_peaks[n*6+:6],dirty_peaks[n*5+:5]);
  changed_queue #(.LIMIT(CHANGED_LIMIT)) changes(clk,local_reset,uv[n],ur[n],ul[n*32+:32],um[n*4+:4],phase==COMMIT,cv[n],commit_issue_ready[n],ci[n*9+:9],ca[n],commit_index[n*9+:9],queue_idle[n],queue_error[n],changed_peak,changed_occupancy);
 end
 always @*begin next_min=4095;any_min=0;for(integer k=0;k<8;k=k+1)if(has_bucket[k])begin any_min=1;if(minima[k*12+:12]<next_min)next_min=minima[k*12+:12];end
  chosen=-1;close_ready=0;for(integer k=0;k<8;k=k+1)if(close_valid[k]&&chosen<0)chosen=k;
  if(phase==CLOSE&&close_state==0&&chosen>=0)close_ready[chosen]=1;
 end
 always @(posedge clk)begin
  output_pair<=outputs[output_index];output_q<=outputs[output_base+target_cell];
  if(rst)begin phase<=IDLE;command<=0;done<=0;output_base<=0;next_job<=0;local_error<=0;cost_loaded<=0;cost_we<=0;ctl_valid<=0;wave<=0;output_valid<=0;close_state<=0;cell_cache_valid<=0;end else begin
   cost_we<=0;if(ctl_valid&&mem_ready[24])ctl_valid<=0;
   case(phase)
   IDLE:if(start)begin output_base<={next_job[5:0],6'b0};next_job<=next_job+1;done<=0;wave<=0;recorded<=0;output_valid<=0;output_init<=0;cell_cache_valid<=0;close_state<=0;phase<=RESET_JOB;if(next_job>=64||cell_count>64||cell_count==0||cost_count>16||cost_count==0||source>=4096)local_error<=1;end
   RESET_JOB:begin if(cost_loaded)begin command<=1;phase<=INIT;end else begin cost_pos<=0;phase<=LOAD_COST;end end
   LOAD_COST:if(!ctl_valid)begin ctl_valid<=1;ctl_write<=0;ctl_line<=cost_base+(cost_pos>>2);ctl_data<=0;phase<=COST_WAIT;end
   COST_WAIT:if(rsp_valid[24])begin cost_beat<=rsp_data[24*256+:256];phase<=COST_WORDS;end
   COST_WORDS:begin cost_we<=1;cost_index<=cost_pos;cost_data<=cost_beat[cost_pos[1:0]*64+:64];cost_pos<=cost_pos+1;
    if(cost_pos+1==cost_count)begin cost_loaded<=1;command<=1;phase<=INIT;end else if(cost_pos[1:0]==3)phase<=LOAD_COST;
   end
   INIT:begin
    if(output_init<cell_count)begin outputs[output_base+output_init[5:0]]<=64'h7fc000007fc00000;output_init<=output_init+1;end
    if(&bank_done)begin command<=0;phase<=GAP;end
   end
   GAP:phase<=SELECT;
   SELECT:if(!any_min||targets==0)phase<=FINISH;else begin bucket<=next_min;command<=2;wave<=wave+1;phase<=POP;end
   POP:if(&bank_done)begin command<=0;phase<=DRAIN;end
   DRAIN:if((&front_idle)&&router_idle)phase<=FENCE;
   FENCE:if((&owner_done)&&(&queue_idle))begin command<=3;phase<=COMMIT;end
   COMMIT:if(&bank_done)begin command<=0;phase<=DECIDE;end
   DECIDE:if(any_min&&next_min==bucket)phase<=SELECT;else begin command<=4;close_state<=0;phase<=CLOSE;end
   CLOSE:begin
    case(close_state)
    0:if(chosen>=0)begin held_node<=close_nodes[chosen*32+:32];held_pair<=close_pairs[chosen*64+:64];close_state<=1;end
      else if(&bank_done)begin command<=0;if(recorded==targets)phase<=FINISH;else phase<=GAP;end
    1:if(cell_cache_valid&&cell_cache_tag==cell_base+(held_node>>2))close_state<=3;else if(!ctl_valid)begin ctl_valid<=1;ctl_write<=0;ctl_line<=cell_base+(held_node>>2);close_state<=2;end
    2:if(rsp_valid[24])begin cell_cache<=rsp_data[24*256+:256];cell_cache_tag<=cell_base+(held_node>>2);cell_cache_valid<=1;close_state<=3;end
    3:begin
     if(cell_cache[held_node[1:0]*64+32+:32]==0||cell_cache[held_node[1:0]*64+:32]==32'hffffffff)close_state<=0;
     else begin if(cell_cache[held_node[1:0]*64+:32]>=cell_count)local_error<=1;target_cell<=cell_cache[held_node[1:0]*64+:6];target_pair<=held_pair;close_state<=4;end
    end
    4:close_state<=5;
    5:begin if(!output_valid[target_cell]||target_pair<output_q)outputs[output_base+target_cell]<=target_pair;if(!output_valid[target_cell])recorded<=recorded+1;output_valid[target_cell]<=1;close_state<=0;end
    default:local_error<=1;endcase
   end
   FINISH:begin done<=1;phase<=IDLE;end
   default:local_error<=1;endcase
  end
 end
endmodule
