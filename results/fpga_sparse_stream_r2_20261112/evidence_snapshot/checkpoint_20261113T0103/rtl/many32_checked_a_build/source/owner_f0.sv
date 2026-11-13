`timescale 1ns/1ps
// Cache/merge disabled control: same64-entry interfaces,32 independent line
// transactions and16 writes, explicit same-line serialization until write ACK.
module sparse_owner_f0 #(parameter REQUEST_STAGE=0)(input wire clk,rst,iv,output wire ir,input wire [31:0] node,
 input wire [63:0] pair,input wire fence,output reg fence_done,
 output reg update_valid,input wire update_ready,output reg [31:0] update_line,output reg [3:0] update_mask,
 output reg mem_valid,input wire mem_ready,output reg mem_write,output reg [31:0] mem_line,
 output reg [5:0] mem_id,output reg [255:0] mem_data,
 input wire rsp_valid,output wire rsp_ready,input wire [5:0] rsp_id,input wire [255:0] rsp_data,
 output wire idle,output reg error,output reg [31:0] accepted,retired,merges,hits,misses,raw_stall,
 output reg [5:0] mshr_peak,output reg [4:0] dirty_peak);
 wire qv,qr,fifo_ir,rv,rr;wire [95:0] qd;wire [261:0] rd;wire [6:0] qc,rc;
 sparse_fifo #(.WIDTH(96),.OUTPUT_STAGE(REQUEST_STAGE)) requests(clk,rst,iv&&!fence,fifo_ir,{node,pair},qv,qr,qd,qc);
 sparse_fifo #(.WIDTH(262)) responses(clk,rst,rsp_valid,rsp_ready,{rsp_id,rsp_data},rv,rr,rd,rc);
 assign ir=fifo_ir&&!fence;
 reg [31:0] mv,ms,mready;reg [31:0] nodes[0:31];reg [63:0] candidates[0:31];
 (* ram_style="block" *) reg [255:0] fills[0:31];reg [255:0] fill_q;
 reg [15:0] wv,ws;reg [4:0] wm[0:15];(* ram_style="block" *) reg [255:0] writes[0:15];
 reg [2:0] state;reg [4:0] selected;integer fm,fw,fetch,write_cmd,apply,mc,wc,k;reg collision;
 always @*begin
  fm=-1;fw=-1;fetch=-1;write_cmd=-1;apply=-1;mc=0;wc=0;collision=0;
  for(integer n=0;n<32;n=n+1)begin
   if(mv[n])begin mc=mc+1;if(nodes[n][31:2]==qd[95:66])collision=1;end else if(fm<0)fm=n;
   if(mv[n]&&!ms[n]&&fetch<0)fetch=n;
   if(mv[n]&&mready[n]&&apply<0)apply=n;
  end
  for(integer n=0;n<16;n=n+1)begin if(wv[n])wc=wc+1;else if(fw<0)fw=n;if(wv[n]&&!ws[n]&&write_cmd<0)write_cmd=n;end
 end
 assign qr=state==0&&!rv&&!update_valid&&fm>=0&&!collision;
 assign rr=state==0&&!update_valid;
 assign idle=state==0&&qc==0&&!qv&&rc==0&&!rv&&mv==0&&wv==0&&!mem_valid&&!update_valid;
 always @(posedge clk)begin
  if(state==1)fill_q<=fills[selected];
  if(rv&&rr&&!rd[261])fills[rd[260:256]]<=rd[255:0];
  if(rst)begin state<=0;mv<=0;ms<=0;mready<=0;wv<=0;ws<=0;update_valid<=0;mem_valid<=0;fence_done<=0;error<=0;accepted<=0;retired<=0;merges<=0;hits<=0;misses<=0;raw_stall<=0;mshr_peak<=0;dirty_peak<=0;end else begin
   if(iv&&ir)accepted<=accepted+1;
   if(mc>mshr_peak)mshr_peak<=mc;if(wc>dirty_peak)dirty_peak<=wc;
   if(update_valid&&update_ready)update_valid<=0;
   if(!mem_valid||mem_ready)begin mem_valid<=0;
    if(write_cmd>=0)begin mem_valid<=1;mem_write<=1;mem_line<=nodes[wm[write_cmd]]>>2;mem_id<=32+write_cmd;mem_data<=writes[write_cmd];ws[write_cmd]<=1;end
    else if(fetch>=0)begin mem_valid<=1;mem_write<=0;mem_line<=nodes[fetch]>>2;mem_id<=fetch;mem_data<=0;ms[fetch]<=1;end
   end
   if(!fence)fence_done<=0;else if(idle)fence_done<=1;
   case(state)
   0:begin
    if(rv&&rr)begin
     if(rd[261])begin
      if(rd[261:256]>=48||!wv[rd[259:256]])error<=1;
      else begin
       update_valid<=1;update_line<=nodes[wm[rd[259:256]]]>>2;update_mask<=4'b1<<nodes[wm[rd[259:256]]][1:0];
       mv[wm[rd[259:256]]]<=0;ms[wm[rd[259:256]]]<=0;wv[rd[259:256]]<=0;ws[rd[259:256]]<=0;retired<=retired+1;
      end
     end else begin if(!mv[rd[260:256]])error<=1;else mready[rd[260:256]]<=1;end
    end else if(qv&&qr)begin nodes[fm]<=qd[95:64];candidates[fm]<=qd[63:0];mv[fm]<=1;ms[fm]<=0;mready[fm]<=0;misses<=misses+1;end
    else if(apply>=0&&fw>=0&&!update_valid)begin selected<=apply;mready[apply]<=0;state<=1;end
    if(qv&&collision)raw_stall<=raw_stall+1;
   end
   1:state<=2;
   2:begin
    if(candidates[selected]<fill_q[nodes[selected][1:0]*64+:64])begin
     writes[fw]<=fill_q;writes[fw][nodes[selected][1:0]*64+:64]<=candidates[selected];wv[fw]<=1;ws[fw]<=0;wm[fw]<=selected;
    end else begin mv[selected]<=0;ms[selected]<=0;retired<=retired+1;end
    state<=0;
   end
   default:error<=1;
   endcase
  end
 end
endmodule
