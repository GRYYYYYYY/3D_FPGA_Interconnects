`timescale 1ns/1ps
module df_output_bank #(parameter integer AW=12,CW=AW+3)(
 input logic clk,reset,input logic iv,output logic ir,
 input logic[CW-1:0] in_cell,input logic[63:0] pair,
 output logic ov,input logic ordy,output logic[CW-1:0] ocell,
 output logic[63:0] opair,output logic first,improved,
 output logic init_done,idle,
 input logic export_mode,ex_v,input logic[AW-1:0] ex_row,
 output logic[64:0] ex_data);
 localparam integer DEPTH=1<<AW;
 localparam logic[63:0] MISSING=64'h7fc000007fc00000;
 (* ram_style="block" *) logic[64:0] mem[DEPTH];
 logic[64:0] rd;
 logic initializing;logic[AW-1:0] init_address;
 logic s0v,s1v;logic[CW-1:0] s0cell,s1cell,last_cell;
 logic[63:0] s0pair,s1pair,last_pair;logic s1first,s1improved,last_valid;
 logic[64:0] forwarded;logic advance,take,read_en;logic[AW-1:0] read_address;
 assign advance=!ov||ordy;
 assign ir=!initializing&&!export_mode&&advance;
 assign take=iv&&ir;
 assign init_done=!initializing;
 assign idle=!initializing&&!s0v&&!s1v&&!ov;
 assign read_en=!initializing&&(export_mode?ex_v:take);
 assign read_address=export_mode?ex_row:in_cell[CW-1:3];
 assign ex_data=rd;
 always_comb begin
  forwarded=rd;
  if(s1v&&s1cell==s0cell)forwarded={1'b1,s1pair};
  else if(last_valid&&last_cell==s0cell)forwarded={1'b1,last_pair};
 end
 // One explicit write port, multiplexed before the RAM inference template.
 logic ram_we;logic[AW-1:0] ram_wa;logic[64:0] ram_wd;
 assign ram_we=!reset&&(initializing||(advance&&s1v));
 assign ram_wa=initializing?init_address:s1cell[CW-1:3];
 assign ram_wd=initializing?{1'b0,MISSING}:{1'b1,s1pair};
 always_ff @(posedge clk)begin
  if(ram_we)mem[ram_wa]<=ram_wd;
  if(!reset&&read_en)rd<=mem[read_address];
 end
 always_ff @(posedge clk)begin
  if(reset)begin initializing<=1;init_address<=0;s0v<=0;s1v<=0;ov<=0;last_valid<=0;end
  else if(initializing)begin
   s0v<=0;s1v<=0;ov<=0;last_valid<=0;
   if(init_address==DEPTH-1)initializing<=0;else init_address<=init_address+1'b1;
  end else if(advance)begin
   ov<=s1v;
   if(s1v)begin ocell<=s1cell;opair<=s1pair;first<=s1first;improved<=s1improved;last_valid<=1;last_cell<=s1cell;last_pair<=s1pair;end
   s1v<=s0v;
   if(s0v)begin s1cell<=s0cell;s1first<=!forwarded[64];s1improved<=!forwarded[64]||s0pair<forwarded[63:0];s1pair<=(!forwarded[64]||s0pair<forwarded[63:0])?s0pair:forwarded[63:0];end
   s0v<=take;if(take)begin s0cell<=in_cell;s0pair<=pair;end
  end
 end
endmodule
