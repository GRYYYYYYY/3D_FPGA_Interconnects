`timescale 1ns/1ps
// One-hot grants preserve the existing first-after-cursor, then wrap policy.
// Handshake paths use prefix reductions directly instead of encoding the
// selected index and immediately decoding it across all destinations.
module r2_round_robin_grant64(input wire [63:0] eligible,after_cursor,
 output wire [63:0] grant);
 wire use_after=|after_cursor;
 for(genvar i=0;i<64;i=i+1)begin:grant_bits
  if(i==0)assign grant[i]=use_after?after_cursor[i]:eligible[i];
  else assign grant[i]=use_after?(after_cursor[i]&&!(|after_cursor[i-1:0])):
                                  (eligible[i]&&!(|eligible[i-1:0]));
 end
endmodule

// The external bank's 32 live contexts keep their original low-ID priority.
// Decode each state in parallel, then select through balanced trees. Counts
// have bounded widths at every adder level, including the all-32-live case.
module r2_bank_context_select(input wire [127:0] states,
 output wire signed [31:0] free_context,send_context,prop_context,publish_context,
 output wire [5:0] live_count,pop_count);
 wire [31:0] free_bits,send_bits,prop_bits,publish_bits,pop_bits;
 for(genvar i=0;i<32;i=i+1)begin:decode
  wire [3:0] state=states[i*4+:4];
  assign free_bits[i]=state==0;
  assign send_bits[i]=state==1||state==5||state==9||state==11;
  assign prop_bits[i]=state==3;
  assign publish_bits[i]=state==7;
  assign pop_bits[i]=state==1||state==2;
 end
 wire fv,sv,pv,av;wire [5:0] fi,si,pi,ai;
 r2_first64 free_select({32'b0,free_bits},fv,fi);
 r2_first64 send_select({32'b0,send_bits},sv,si);
 r2_first64 prop_select({32'b0,prop_bits},pv,pi);
 r2_first64 publish_select({32'b0,publish_bits},av,ai);
 assign free_context=fv?{27'b0,fi[4:0]}:32'hffffffff;
 assign send_context=sv?{27'b0,si[4:0]}:32'hffffffff;
 assign prop_context=pv?{27'b0,pi[4:0]}:32'hffffffff;
 assign publish_context=av?{27'b0,ai[4:0]}:32'hffffffff;
 r2_popcount32 live_sum(~free_bits,live_count);
 r2_popcount32 pop_sum(pop_bits,pop_count);
endmodule

module r2_popcount32(input wire [31:0] bits,output wire [5:0] count);
 wire [1:0] a[0:15];wire [2:0] b[0:7];wire [3:0] c[0:3];wire [4:0] d[0:1];
 for(genvar i=0;i<16;i=i+1)begin:l1 assign a[i]={1'b0,bits[2*i]}+{1'b0,bits[2*i+1]};end
 for(genvar i=0;i<8;i=i+1)begin:l2 assign b[i]={1'b0,a[2*i]}+{1'b0,a[2*i+1]};end
 for(genvar i=0;i<4;i=i+1)begin:l3 assign c[i]={1'b0,b[2*i]}+{1'b0,b[2*i+1]};end
 for(genvar i=0;i<2;i=i+1)begin:l4 assign d[i]={1'b0,c[2*i]}+{1'b0,c[2*i+1]};end
 assign count={1'b0,d[0]}+{1'b0,d[1]};
endmodule

// Preserve exact four-way cache policy without a loop-carried victim chain:
// highest matching way, lowest invalid available way, otherwise first
// available way in circular replacement order. Masks are evaluated in parallel.
module r2_cache_way_select(input wire [3:0] match_mask,available,invalid,
 input wire [1:0] cursor,output wire hit_valid,output wire [1:0] hit_way,
 output wire victim_valid,output wire [1:0] victim_way);
 function automatic [1:0] first4(input [3:0] mask);
  begin first4=(|mask[1:0])?{1'b0,!mask[0]}:{1'b1,!mask[2]};end
 endfunction
 wire [3:0] after_cursor;
 for(genvar w=0;w<4;w=w+1)begin:after_bits
  assign after_cursor[w]=available[w]&&(w>=cursor);
 end
 wire [3:0] choose=(|invalid)?invalid:(|after_cursor)?after_cursor:available;
 assign hit_valid=|match_mask;
 assign hit_way=~first4({match_mask[0],match_mask[1],match_mask[2],match_mask[3]});
 assign victim_valid=|choose;assign victim_way=first4(choose);
endmodule

// Balanced binary selection, not a serial 64-element priority-for loop.
module r2_first64(input wire [63:0] mask,output wire valid,output wire [5:0] index);
 wire [6:0] level0[0:63];
 for(genvar i=0;i<64;i=i+1)begin:leaves assign level0[i]={!mask[i],6'(i)};end
 wire [6:0] level1[0:31];
 for(genvar i=0;i<32;i=i+1)begin:level_1 assign level1[i]=!level0[2*i][6]?level0[2*i]:level0[2*i+1];end
 wire [6:0] level2[0:15];
 for(genvar i=0;i<16;i=i+1)begin:level_2 assign level2[i]=!level1[2*i][6]?level1[2*i]:level1[2*i+1];end
 wire [6:0] level3[0:7];
 for(genvar i=0;i<8;i=i+1)begin:level_3 assign level3[i]=!level2[2*i][6]?level2[2*i]:level2[2*i+1];end
 wire [6:0] level4[0:3];
 for(genvar i=0;i<4;i=i+1)begin:level_4 assign level4[i]=!level3[2*i][6]?level3[2*i]:level3[2*i+1];end
 wire [6:0] level5[0:1];
 for(genvar i=0;i<2;i=i+1)begin:level_5 assign level5[i]=!level4[2*i][6]?level4[2*i]:level4[2*i+1];end
 wire [6:0] level6[0:0];
 for(genvar i=0;i<1;i=i+1)begin:level_6 assign level6[i]=!level5[2*i][6]?level5[2*i]:level5[2*i+1];end
 assign valid=!level6[0][6];assign index=level6[0][5:0];
endmodule

module r2_min8(input wire clk,rst,input wire [7:0] valid,
 input wire [103:0] keys,input wire [63:0] epochs,
 output reg ov,output reg [12:0] key,output reg [7:0] epoch);
 reg [12:0] a[0:3],b[0:1];reg [7:0] ae[0:3],be[0:1];reg [3:0] av;reg [1:0] bv;
 always @(posedge clk)begin
  if(rst)begin av<=0;bv<=0;ov<=0;key<=13'h1fff;epoch<=0;end else begin
   for(integer i=0;i<4;i=i+1)begin
    a[i]<=keys[(2*i)*13+:13]<keys[(2*i+1)*13+:13]?keys[(2*i)*13+:13]:keys[(2*i+1)*13+:13];
    ae[i]<=epochs[(2*i)*8+:8];av[i]<=valid[2*i]&&valid[2*i+1]&&epochs[(2*i)*8+:8]==epochs[(2*i+1)*8+:8];
   end
   for(integer i=0;i<2;i=i+1)begin b[i]<=a[2*i]<a[2*i+1]?a[2*i]:a[2*i+1];be[i]<=ae[2*i];bv[i]<=av[2*i]&&av[2*i+1]&&ae[2*i]==ae[2*i+1];end
   key<=b[0]<b[1]?b[0]:b[1];epoch<=be[0];ov<=(&bv)&&be[0]==be[1];
  end
 end
endmodule
