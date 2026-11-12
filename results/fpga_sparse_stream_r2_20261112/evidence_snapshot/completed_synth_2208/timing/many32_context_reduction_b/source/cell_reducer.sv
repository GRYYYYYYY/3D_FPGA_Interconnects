`timescale 1ns/1ps
// One accepted update/clock after filling the single RAM-read stage. Same-cell
// read/write collisions forward the last whole {seen,pair}, including first-visit.
module r2_cell_reducer #(parameter AW=12)(input wire clk,rst,init,
 input wire [AW:0] entries,input wire [5:0] qid,input wire [15:0] epoch,
 input wire iv,output wire ir,input wire [AW-1:0] index,input wire [63:0] pair,
 input wire [5:0] event_qid,input wire [15:0] event_epoch,
 input wire export_en,input wire [AW-1:0] export_index,output reg [63:0] export_pair,
 output wire idle,output reg init_done,output reg error,output reg [31:0] recorded,retired,forwarded);
 (* ram_style="block" *) reg [64:0] memory[0:(1<<AW)-1];
 reg [64:0] ram_q,last_data;reg [AW-1:0] saddr,last_addr;reg [63:0] spair;
 reg sv,last_valid,initializing;reg [AW:0] init_index;
 wire [64:0] baseline=last_valid&&last_addr==saddr?last_data:ram_q;
 wire [64:0] value={1'b1,(!baseline[64]||spair<baseline[63:0])?spair:baseline[63:0]};
 assign ir=init_done&&!initializing&&!init&&!export_en;
 assign idle=!sv&&!initializing;
 wire ram_re=(iv&&ir)||export_en;
 wire [AW-1:0] ram_ra=(iv&&ir)?index:export_index;
 wire init_write=initializing&&init_index<entries;
 wire ram_we=init_write||sv;
 wire [AW-1:0] ram_wa=init_write?init_index[AW-1:0]:saddr;
 wire [64:0] ram_wd=init_write?65'b0:value;
 always @(posedge clk)begin
  if(ram_re)ram_q<=memory[ram_ra];
  export_pair<=ram_q[64]?ram_q[63:0]:64'h7fc000007fc00000;
  if(ram_we)memory[ram_wa]<=ram_wd;
  if(rst)begin sv<=0;last_valid<=0;initializing<=0;init_index<=0;init_done<=0;error<=0;recorded<=0;retired<=0;forwarded<=0;end
  else begin
   sv<=iv&&ir;last_valid<=sv;
   if(init&&!init_done&&!initializing)begin initializing<=1;init_index<=0;recorded<=0;end
   if(initializing)begin
    if(init_index==entries)begin initializing<=0;init_done<=1;end else init_index<=init_index+1;
   end
   if(iv&&ir)begin saddr<=index;spair<=pair;if(index>=entries||event_qid!=qid||event_epoch!=epoch)error<=1;end
   if(sv)begin
    last_addr<=saddr;last_data<=value;retired<=retired+1;
    if(!baseline[64])recorded<=recorded+1;
    if(last_valid&&last_addr==saddr)forwarded<=forwarded+1;
   end
  end
 end
endmodule
