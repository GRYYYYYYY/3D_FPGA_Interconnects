// ALT_LINE_OWNER_REDUCE_V1. One runtime-fed owner, single clock.
// Pair encoding: {delay FP32, congestion FP32}; admitted nonnegative normal/+0.
module bounded_fifo #(parameter W=32, D=64, A=$clog2(D)) (
 input wire clk,rst,input wire iv,output wire ir,input wire [W-1:0] id,
 output wire ov,input wire or_,output wire [W-1:0] od,output reg [A:0] count);
 reg [W-1:0] mem[0:D-1]; reg [A-1:0] wp,rp;
 assign ir=count<D; assign ov=count!=0; assign od=mem[rp];
 always @(posedge clk) if(rst) begin wp<=0;rp<=0;count<=0;end else begin
 if(iv&&ir)begin mem[wp]<=id;wp<=wp+1'b1;end
 if(ov&&or_)rp<=rp+1'b1;
 case({iv&&ir,ov&&or_})2'b10:count<=count+1'b1;2'b01:count<=count-1'b1;default:;endcase
 end
endmodule

module owner_service #(parameter OWNER_BITS=0)(
 input wire clk,rst,input wire req_valid,output wire req_ready,
 input wire [23:0] req_line,input wire [1:0] req_sector,input wire [63:0] req_pair,
 input wire fence, output reg fence_done, output reg error,
 output reg mem_valid,input wire mem_ready,output reg mem_write,
 output reg [23:0] mem_line, output reg [255:0] mem_data,output reg [5:0] mem_id,
 input wire rsp_valid,output wire rsp_ready,input wire [5:0] rsp_id,input wire [255:0] rsp_data,
 output reg [31:0] accepted,retired,hits,merges,reads,writes,raw_stall,capacity_stall,fence_cycles,
 output reg [6:0] request_hwm,response_hwm,output reg [5:0] mshr_hwm,output reg [4:0] dirty_hwm
);
 localparam [63:0] INF=64'h7f8000007f800000;
 function automatic [63:0] best(input [63:0] a,b);
 begin best=(a[63:32]<b[63:32] || (a[63:32]==b[63:32] && a[31:0]<b[31:0]))?a:b;end endfunction
 function automatic legal(input [31:0] x);
 begin legal=(x==0)||(!x[31] && x[30:23]!=0 && x[30:23]!=255);end endfunction
 reg [255:0] data[0:127]; reg [23:0] tags[0:127];
 reg [127:0] valid,dirty,locked;reg [1:0] rr[0:31];
 reg [31:0] mv,ms;reg [23:0] ml[0:31];reg [6:0] slot[0:31];reg [255:0] acc[0:31];
 reg [15:0] dv,ds;reg [23:0] dl[0:15];reg [255:0] dd[0:15];
 reg initializing,draining,flushing;reg [7:0] scan;
 wire qi,qo,qp;wire [89:0] qdata;wire [6:0] qc;
 assign req_ready=qi&&!initializing&&!draining&&!fence&&!error;
 bounded_fifo #(.W(90)) requests(clk,rst,req_valid&&req_ready,qi,{req_line,req_sector,req_pair},qo,qp,qdata,qc);
 wire ro,rpop;wire [261:0] rd;wire [6:0] rc;
 bounded_fifo #(.W(262)) responses(clk,rst,rsp_valid,rsp_ready,{rsp_id,rsp_data},ro,rpop,rd,rc);
 wire [23:0] line=qdata[89:66];wire [1:0] sector=qdata[65:64];wire [63:0] pair=qdata[63:0];
 wire [4:0] setidx=line[OWNER_BITS+:5];
 integer i,w,match_m,free_m,free_d,hit,victim,send_m,send_d,raw,nm,nd;
 reg [6:0] idx;reg can_process;reg [255:0] filled;
 always @* begin
 match_m=-1;free_m=-1;free_d=-1;hit=-1;victim=-1;send_m=-1;send_d=-1;raw=0;nm=0;nd=0;
 for(i=31;i>=0;i=i-1)begin
 if(mv[i])begin nm=nm+1;if(ml[i]==line)match_m=i;if(!ms[i])send_m=i;end else free_m=i;
 end
 for(i=15;i>=0;i=i-1)begin
 if(dv[i])begin nd=nd+1;if(dl[i]==line)raw=1;if(!ds[i])send_d=i;end else free_d=i;
 end
 for(w=3;w>=0;w=w-1)begin
 idx={w[1:0],setidx};
 if(valid[idx]&&!locked[idx]&&tags[idx]==line)hit=idx;
 if(!valid[idx]&&!locked[idx])victim=idx;
 end
 if(victim<0&&!locked[{rr[setidx],setidx}])victim={rr[setidx],setidx};
 can_process=!raw && (match_m>=0 || hit>=0 || (free_m>=0 && victim>=0 && (!dirty[victim] || free_d>=0)));
 filled=0;
 for(w=0;w<4;w=w+1)filled[w*64+:64]=best(acc[rd[260:256]][w*64+:64],rd[w*64+:64]);
 end
 assign rpop=ro&&!initializing;
 assign qp=qo&&!initializing&&!flushing&&!ro&&can_process&&!error;
 always @(posedge clk)begin
 if(rst)begin
 initializing<=1;draining<=0;flushing<=0;scan<=0;valid<=0;dirty<=0;locked<=0;mv<=0;ms<=0;dv<=0;ds<=0;
 mem_valid<=0;fence_done<=0;error<=0;accepted<=0;retired<=0;hits<=0;merges<=0;reads<=0;writes<=0;
 raw_stall<=0;capacity_stall<=0;fence_cycles<=0;request_hwm<=0;response_hwm<=0;mshr_hwm<=0;dirty_hwm<=0;
 end else begin
 fence_done<=0;
 if(qc>request_hwm)request_hwm<=qc;if(rc>response_hwm)response_hwm<=rc;
 if(nm>mshr_hwm)mshr_hwm<=nm;if(nd>dirty_hwm)dirty_hwm<=nd;
 if(req_valid&&req_ready)accepted<=accepted+1;
 if(fence&&!initializing)draining<=1;
 if(draining)fence_cycles<=fence_cycles+1;
 if(mem_valid&&mem_ready)begin mem_valid<=0;if(mem_write)writes<=writes+1;else reads<=reads+1;end
 // Registered command holds stable through arbitrary memory backpressure.
 if(!initializing&&!mem_valid)begin
 if(send_d>=0)begin mem_valid<=1;mem_write<=1;mem_line<=dl[send_d];mem_data<=dd[send_d];mem_id<={1'b1,1'b0,send_d[3:0]};ds[send_d]<=1;end
 else if(send_m>=0)begin mem_valid<=1;mem_write<=0;mem_line<=ml[send_m];mem_data<=0;mem_id<={1'b0,send_m[4:0]};ms[send_m]<=1;end
 end
 if(initializing)begin
 rr[scan[4:0]]<=0;
 if(scan==127)begin initializing<=0;scan<=0;end else scan<=scan+1;
 end else if(ro)begin
 if(rd[261])begin
 if(!dv[rd[259:256]]||!ds[rd[259:256]])error<=1;
 dv[rd[259:256]]<=0;ds[rd[259:256]]<=0;
 end else begin
 if(!mv[rd[260:256]]||!ms[rd[260:256]])error<=1;
 data[slot[rd[260:256]]]<=filled;dirty[slot[rd[260:256]]]<=filled!=rd[255:0];locked[slot[rd[260:256]]]<=0;
 mv[rd[260:256]]<=0;ms[rd[260:256]]<=0;
 end
 end else if(flushing)begin
 if(scan<128)begin
 if(!dirty[scan[6:0]]||free_d>=0)begin
 if(valid[scan[6:0]]&&dirty[scan[6:0]])begin dv[free_d]<=1;ds[free_d]<=0;dl[free_d]<=tags[scan[6:0]];dd[free_d]<=data[scan[6:0]];end
 valid[scan[6:0]]<=0;dirty[scan[6:0]]<=0;scan<=scan+1;
 end
 end else if(dv==0&&!mem_valid&&rc==0)begin flushing<=0;draining<=0;fence_done<=!error;scan<=0;end
 end else if(qp)begin
 if(!legal(pair[63:32])||!legal(pair[31:0]))error<=1;
 retired<=retired+1;
 if(match_m>=0)begin acc[match_m][sector*64+:64]<=best(pair,acc[match_m][sector*64+:64]);merges<=merges+1;end
 else if(hit>=0)begin
 data[hit][sector*64+:64]<=best(pair,data[hit][sector*64+:64]);
 if(best(pair,data[hit][sector*64+:64])!=data[hit][sector*64+:64])dirty[hit]<=1;
 hits<=hits+1;
 end else begin
 if(valid[victim]&&dirty[victim])begin dv[free_d]<=1;ds[free_d]<=0;dl[free_d]<=tags[victim];dd[free_d]<=data[victim];end
 mv[free_m]<=1;ms[free_m]<=0;ml[free_m]<=line;slot[free_m]<=victim;
 acc[free_m]<={INF,INF,INF,INF};acc[free_m][sector*64+:64]<=pair;
 tags[victim]<=line;valid[victim]<=1;locked[victim]<=1;dirty[victim]<=0;rr[setidx]<=victim[6:5]+1'b1;
 end
 end else if(qo)begin if(raw)raw_stall<=raw_stall+1;else capacity_stall<=capacity_stall+1;end
 else if(draining&&mv==0&&!mem_valid)begin flushing<=1;scan<=0;end
 end
 end
endmodule
