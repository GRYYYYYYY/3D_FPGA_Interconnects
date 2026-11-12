`timescale 1ns/1ps
// Sixteen bounded contexts retain the immutable POP pair until tagged metadata returns.
module r2_pop_metadata(input wire clk,rst,input wire [31:0] base,cell_count,input wire [5:0] qid,input wire [15:0] epoch,
 input wire iv,output wire ir,input wire [31:0] node,input wire [63:0] pair,
 output reg mv,input wire mr,output reg [31:0] line,output reg [5:0] id,
 input wire rv,output wire rr,input wire [5:0] rid,input wire [255:0] rd,
 output reg ov,input wire ordy,output reg [31:0] cell_index,output reg [63:0] opair,output reg [5:0] oqid,output reg [15:0] oepoch,
 output wire idle,output reg error,output reg [31:0] accepted,reads,targets,skipped,output reg [4:0] peak);
 reg [15:0] live,sent,ready;
 reg [31:0] nodes[0:15];reg [63:0] pairs[0:15],metadata[0:15];reg [5:0] qids[0:15];reg [15:0] epochs[0:15];
 integer f,s,e,used;reg [3:0] rotate;
 always @*begin f=-1;s=-1;e=-1;used=0;for(integer i=0;i<16;i=i+1)begin
  if(!live[i]&&f<0)f=i;if(live[i])used=used+1;if(live[i]&&!sent[i]&&s<0)s=i;
  if(live[(rotate+i)%16]&&ready[(rotate+i)%16]&&e<0)e=(rotate+i)%16;
 end end
 assign ir=f>=0;assign rr=1;assign idle=live==0&&!mv&&!ov;
 always @(posedge clk)begin
  if(rst)begin live<=0;sent<=0;ready<=0;mv<=0;ov<=0;error<=0;accepted<=0;reads<=0;targets<=0;skipped<=0;peak<=0;rotate<=0;end else begin
   if(used>peak)peak<=used;
   if(iv&&ir)begin live[f]<=1;sent[f]<=0;ready[f]<=0;nodes[f]<=node;pairs[f]<=pair;qids[f]<=qid;epochs[f]<=epoch;accepted<=accepted+1;end
   if(!mv||mr)begin mv<=0;if(s>=0)begin mv<=1;line<=base+(nodes[s]>>2);id<=s;sent[s]<=1;reads<=reads+1;end end
   if(rv)begin if(rid>=16||!live[rid[3:0]]||!sent[rid[3:0]]||ready[rid[3:0]])error<=1;
    else begin ready[rid[3:0]]<=1;metadata[rid[3:0]]<=rd[nodes[rid[3:0]][1:0]*64+:64];end end
   if(!ov||ordy)begin ov<=0;if(e>=0)begin
    live[e]<=0;ready[e]<=0;rotate<=e+1;
    if(metadata[e][63:32]==0||metadata[e][31:0]==32'hffffffff)skipped<=skipped+1;
    else begin ov<=1;cell_index<=metadata[e][31:0];opair<=pairs[e];oqid<=qids[e];oepoch<=epochs[e];targets<=targets+1;if(metadata[e][31:0]>=cell_count)error<=1;end
   end end
  end
 end
endmodule
