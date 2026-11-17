`timescale 1ns/1ps
// CPU_PRIMARY candidate-only 64x64, 96-bit router.
// Preserve the historical valid/key RR tree, selected index, ready and holds.
// Only payload evaluation changes: static 3x32-bit input words selected by
// the existing 6-bit root index. No extra state, latency, ports or capacity.
module cp_candidate_wordmux_router(
 input logic clk,reset,input logic[63:0] iv,output logic[63:0] ir,
 input logic[64*6-1:0] dest,input logic[64*96-1:0] idata,
 output logic[63:0] ov,input logic[63:0] ordy,
 output logic[64*96-1:0] odata);
 localparam integer INPUTS=64,OUTPUTS=64,WIDTH=96,DEST_W=6,SEL_W=6;
 localparam integer LEAVES=2**SEL_W;
 logic[SEL_W-1:0] cursor[OUTPUTS],selected[OUTPUTS];logic[OUTPUTS-1:0] found;
 logic[WIDTH-1:0] selected_data[OUTPUTS];
 wire[31:0] word0[INPUTS],word1[INPUTS],word2[INPUTS];
 for(genvar i=0;i<INPUTS;i=i+1)begin:payload_words
  assign word0[i]=idata[i*96+:32];
  assign word1[i]=idata[i*96+32+:32];
  assign word2[i]=idata[i*96+64+:32];
 end
 for(genvar o=0;o<OUTPUTS;o=o+1)begin:outputs
  wire[2*LEAVES-1:1] valid;
  wire[SEL_W:0] key[2*LEAVES];
  for(genvar i=0;i<LEAVES;i=i+1)begin:leaf
   if(i<INPUTS)begin
    assign valid[LEAVES+i]=iv[i]&&dest[i*DEST_W+:DEST_W]==o;
    assign key[LEAVES+i]={i<cursor[o],SEL_W'(i)};
   end else begin assign valid[LEAVES+i]=0;assign key[LEAVES+i]=0;end
  end
  for(genvar j=1;j<LEAVES;j=j+1)begin:tree
   wire left_wins=valid[2*j]&&(!valid[2*j+1]||key[2*j]<key[2*j+1]);
   assign valid[j]=valid[2*j]||valid[2*j+1];
   assign key[j]=left_wins?key[2*j]:key[2*j+1];
  end
  assign found[o]=valid[1];assign selected[o]=key[1][SEL_W-1:0];
  assign selected_data[o]={word2[selected[o]],word1[selected[o]],word0[selected[o]]};
  always_ff @(posedge clk)begin
   if(reset)begin ov[o]<=0;cursor[o]<=0;end
   else if(!ov[o]||ordy[o])begin
    ov[o]<=found[o];
    if(found[o])begin odata[o*WIDTH+:WIDTH]<=selected_data[o];cursor[o]<=selected[o]==INPUTS-1?0:selected[o]+1;end
   end
  end
 end
 always_comb begin
  ir=0;
  for(integer o=0;o<OUTPUTS;o=o+1)if((!ov[o]||ordy[o])&&found[o])ir[selected[o]]=1;
 end
endmodule
