`timescale 1ns/1ps
// Expand RMW is frozen from inf_flat_bank; finalize uses synchronous elastic reads.
// One targeted replacement: four narrow metadata RAMs and four flat URAM sectors.
// Entire in-flight set reservation covers read/select/payload/compare/writeback.
// Independent sets sustain II1; same-set requests backpressure until retirement.
module enum2_bank #(parameter SET_BITS=10)(
 input logic clk,reset,input logic in_valid,output logic in_ready,
 input logic [31:0] in_node,input logic [63:0] in_pair,
 input logic flush,output logic done,output logic frag_valid,input logic frag_ready,
 output logic [31:0] frag_line,output logic [3:0] frag_mask,output logic [255:0] frag_pairs,
 output logic frag_final,output logic [31:0] accepted,retired,spill_count,enumerated,scan_issued
);
 localparam S=1<<SET_BITS;localparam [63:0] INF=64'h7f8000007f800000;
 typedef enum logic[3:0]{INIT,RUN,DRAIN,ENUM_PIPE,FINISH} state_t;
 state_t state;
 (* ram_style="block" *) logic [SET_BITS+1:0] occupied[4*S];
 logic [1:0] replacement[S];logic [35:0] mq[4];logic [63:0] pq[4];
 logic [3:0] v;logic [SET_BITS-1:0] sets[4];logic [31:0] lines[4];logic [1:0] sectors[4],ways[4];logic [63:0] pairs[4];
 logic [3:0] masks[4];logic [31:0] victims[4];logic hits[4],empties[4];
 logic [255:0] old_pairs;logic [63:0] new_pair;
 logic [SET_BITS-1:0] init_addr;logic [SET_BITS+2:0] used,enum_index;logic [SET_BITS+1:0] enum_slot;
 logic [35:0] enum_meta;logic [255:0] enum_pairs;
 logic hit,empty;logic [1:0] chosen;logic [35:0] chosen_meta;
 logic raw_valid,raw_final;logic [31:0] raw_line;logic [3:0] raw_mask;logic [255:0] raw_pairs;wire raw_ready;
 wire [292:0] fifo_data;wire [4:0] fifo_occupancy;
 sparse_fifo #(.WIDTH(293),.DEPTH(16),.STYLE("distributed")) fragment_fifo(
 .clk,.rst(reset),.iv(raw_valid),.ir(raw_ready),.id({raw_final,raw_line,raw_mask,raw_pairs}),
 .ov(frag_valid),.ordy(frag_ready),.od(fifo_data),.occupancy(fifo_occupancy));
 assign {frag_final,frag_line,frag_mask,frag_pairs}=fifo_data;
 wire advance=!raw_valid||raw_ready;
 logic [3:0] ev;logic phase;logic [SET_BITS+1:0] eslot[4];logic [35:0] emeta;
 logic [31:0] eline;logic [3:0] emask;logic [255:0] epairs;
 wire enum_step=!ev[3]||advance;
 wire enum_launch=state==ENUM_PIPE&&enum_step&&!phase&&enum_index<used;
 wire [SET_BITS-1:0] input_set=in_node[8+:SET_BITS];logic hazard;
 always_comb begin
  hazard=0;for(integer i=0;i<4;i=i+1)if(v[i]&&sets[i]==input_set)hazard=1;
  in_ready=state==RUN&&!flush&&advance&&!hazard;
  hit=0;empty=0;chosen=replacement[sets[0]];
  for(integer w=3;w>=0;w=w-1)if(mq[w][3:0]==0)begin chosen=w;empty=1;end
  for(integer w=0;w<4;w=w+1)if(mq[w][3:0]!=0&&mq[w][35:4]==lines[0])begin chosen=w;hit=1;end
  chosen_meta=mq[chosen];
 end
 logic mr;logic [SET_BITS-1:0] ma,mwa;logic [3:0] mw;logic [35:0] md;
 logic pr;logic [SET_BITS+1:0] pa,pwa;logic [3:0] pe,pw;logic [63:0] pd;
 always_comb begin
  mr=0;ma=input_set;mw=0;mwa=sets[3];md={lines[3],(hits[3]?masks[3]:4'b0)|(4'b1<<sectors[3])};
  pr=0;pa={ways[1],sets[1]};pe=0;pw=0;pwa={ways[3],sets[3]};pd=new_pair;
  if(!reset)begin
   if(state==INIT)begin mw=15;mwa=init_addr;md=0;end
   if((state==RUN||state==DRAIN)&&advance)begin
    mr=in_valid&&in_ready;
    if(v[1])begin pr=1;pe=hits[1]?(4'b1<<sectors[1]):4'b1111;end
    if(v[3])begin mw=4'b1<<ways[3];pw=4'b1<<sectors[3];end
   end
   if(state==ENUM_PIPE&&enum_step)begin
    if(ev[0])begin mr=1;ma=eslot[0][SET_BITS-1:0];end
    if(ev[1])begin pr=1;pa=eslot[1];pe=15;end
    if(ev[3]&&advance)begin mw=4'b1<<eslot[3][SET_BITS+1:SET_BITS];mwa=eslot[3][SET_BITS-1:0];md=0;end
   end
  end
 end
 for(genvar w=0;w<4;w=w+1)begin:ram_columns
  (* ram_style="block" *) logic [35:0] meta[S];
  (* ram_style="ultra" *) logic [63:0] payload[4*S];
  always_ff @(posedge clk)begin
   if(mr)mq[w]<=meta[ma];if(mw[w])meta[mwa]<=md;
   if(pr&&pe[w])pq[w]<=payload[pa];if(pw[w])payload[pwa]<=pd;
  end
 end
 // Simple dual-port BRAM template: exact-depth addresses, no reset mux on read data.
 wire occupied_we=!reset&&(state==RUN||state==DRAIN)&&advance&&v[3]&&!hits[3]&&empties[3];
 always_ff @(posedge clk)begin
  if(occupied_we)occupied[used[SET_BITS+1:0]]<={ways[3],sets[3]};
  if(!reset&&enum_launch)eslot[0]<=occupied[enum_index[SET_BITS+1:0]];
 end
 always_ff @(posedge clk)begin
  if(reset)begin state<=INIT;init_addr<=0;v<=0;used<=0;enum_index<=0;done<=0;raw_valid<=0;raw_final<=0;accepted<=0;retired<=0;spill_count<=0;enumerated<=0;scan_issued<=0;ev<=0;phase<=0;end
  else begin
   if(raw_valid&&raw_ready)raw_valid<=0;
   case(state)
    INIT:begin replacement[init_addr]<=0;if(init_addr==S-1)state<=RUN;else init_addr<=init_addr+1;end
    RUN,DRAIN:if(advance)begin
     v<={v[2:0],in_valid&&in_ready};
     for(integer i=1;i<4;i=i+1)begin sets[i]<=sets[i-1];lines[i]<=lines[i-1];sectors[i]<=sectors[i-1];pairs[i]<=pairs[i-1];ways[i]<=ways[i-1];masks[i]<=masks[i-1];victims[i]<=victims[i-1];hits[i]<=hits[i-1];empties[i]<=empties[i-1];end
     if(in_valid&&in_ready)begin sets[0]<=input_set;lines[0]<=in_node>>2;sectors[0]<=in_node[1:0];pairs[0]<=in_pair;accepted<=accepted+1;end
     if(v[0])begin ways[1]<=chosen;masks[1]<=chosen_meta[3:0];victims[1]<=chosen_meta[35:4];hits[1]<=hit;empties[1]<=empty;end
     if(v[2])begin
      new_pair<=(!hits[2]||!masks[2][sectors[2]]||pairs[2]<pq[sectors[2]])?pairs[2]:pq[sectors[2]];
      for(integer j=0;j<4;j=j+1)old_pairs[j*64+:64]<=masks[2][j]?pq[j]:INF;
     end
     if(v[3])begin
      retired<=retired+1;
      if(!hits[3])begin
       replacement[sets[3]]<=ways[3]+1;
       if(empties[3])begin used<=used+1;end
       else begin raw_valid<=1;raw_final<=0;raw_line<=victims[3];raw_mask<=masks[3];raw_pairs<=old_pairs;spill_count<=spill_count+1;end
      end
     end
     if(state==RUN&&flush)state<=DRAIN;
     if(state==DRAIN&&v==0)begin enum_index<=0;state<=used==0?FINISH:ENUM_PIPE;ev<=0;phase<=0;end
    end
    ENUM_PIPE:if(enum_step)begin
     ev<={ev[2:0],enum_launch};phase<=!phase;
     if(enum_launch)begin enum_index<=enum_index+1;scan_issued<=scan_issued+1;end
     for(integer k=1;k<4;k=k+1)eslot[k]<=eslot[k-1];
     if(ev[1])emeta<=mq[eslot[1][SET_BITS+1:SET_BITS]];
     if(ev[2])begin
      eline<=emeta[35:4];emask<=emeta[3:0];
      for(integer k=0;k<4;k=k+1)epairs[k*64+:64]<=emeta[k]?pq[k]:INF;
     end
     if(ev[3])begin raw_valid<=1;raw_final<=1;raw_line<=eline;raw_mask<=emask;raw_pairs<=epairs;enumerated<=enumerated+1;end
     if(enum_index==used&&ev==0)state<=FINISH;
    end
    FINISH:if(!raw_valid&&fifo_occupancy==0)begin done<=1;if(!flush)begin done<=0;used<=0;state<=RUN;end end
    default:state<=INIT;
   endcase
  end
 end
endmodule
