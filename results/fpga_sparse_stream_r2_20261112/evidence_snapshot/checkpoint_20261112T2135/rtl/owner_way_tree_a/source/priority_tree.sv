`timescale 1ns/1ps
// Preserve exact four-way cache policy without a loop-carried victim chain:
// highest matching way, lowest invalid available way, otherwise first
// available way in circular replacement order. Masks are evaluated in parallel.
module r2_cache_way_select(input wire [3:0] matches,available,invalid,
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
 assign hit_valid=|matches;
 assign hit_way=~first4({matches[0],matches[1],matches[2],matches[3]});
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
