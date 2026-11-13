// One targeted replacement: four narrow metadata RAMs and four flat URAM sectors.
// Entire in-flight set reservation covers read/select/payload/compare/writeback.
// Independent sets sustain II1; same-set requests backpressure until retirement.
module inf_flat_bank #(parameter SET_BITS=10)(
 input logic clk,reset,input logic in_valid,output logic in_ready,
 input logic [31:0] in_node,input logic [63:0] in_pair,
 input logic flush,output logic done,output logic frag_valid,input logic frag_ready,
 output logic [31:0] frag_line,output logic [3:0] frag_mask,output logic [255:0] frag_pairs,
 output logic frag_final,output logic [31:0] accepted,retired,spill_count,enumerated
);
 localparam S=1<<SET_BITS;localparam [63:0] INF=64'h7f8000007f800000;
 typedef enum logic[3:0]{INIT,RUN,DRAIN,ENUM_READ,ENUM_META,ENUM_SELECT,ENUM_PAYLOAD,ENUM_SEND,FINISH} state_t;
 state_t state;
 (* ram_style="block" *) logic [SET_BITS+1:0] occupied[4*S];
 logic [1:0] replacement[S];logic [35:0] mq[4];logic [63:0] pq[4];
 logic [3:0] v;logic [SET_BITS-1:0] sets[4];logic [31:0] lines[4];logic [1:0] sectors[4],ways[4];logic [63:0] pairs[4];
 logic [3:0] masks[4];logic [31:0] victims[4];logic hits[4],empties[4];
 logic [255:0] old_pairs;logic [63:0] new_pair;
 logic [SET_BITS-1:0] init_addr;logic [SET_BITS+2:0] used,enum_index;logic [SET_BITS+1:0] enum_slot;
 logic [35:0] enum_meta;logic [255:0] enum_pairs;
 logic hit,empty;logic [1:0] chosen;logic [35:0] chosen_meta;
 wire advance=!frag_valid||frag_ready;
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
   if(state==ENUM_META)begin mr=1;ma=enum_slot[SET_BITS-1:0];end
   if(state==ENUM_SELECT)begin pr=1;pa=enum_slot;pe=15;end
   if(state==ENUM_SEND&&advance)begin mw=4'b1<<enum_slot[SET_BITS+1:SET_BITS];mwa=enum_slot[SET_BITS-1:0];md=0;end
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
 always_ff @(posedge clk)begin
  if(reset)begin state<=INIT;init_addr<=0;v<=0;used<=0;enum_index<=0;done<=0;frag_valid<=0;frag_final<=0;accepted<=0;retired<=0;spill_count<=0;enumerated<=0;end
  else begin
   if(frag_valid&&frag_ready)frag_valid<=0;
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
       if(empties[3])begin occupied[used]<={ways[3],sets[3]};used<=used+1;end
       else begin frag_valid<=1;frag_final<=0;frag_line<=victims[3];frag_mask<=masks[3];frag_pairs<=old_pairs;spill_count<=spill_count+1;end
      end
     end
     if(state==RUN&&flush)state<=DRAIN;
     if(state==DRAIN&&v==0)begin enum_index<=0;state<=used==0?FINISH:ENUM_READ;end
    end
    ENUM_READ:begin enum_slot<=occupied[enum_index];state<=ENUM_META;end
    ENUM_META:state<=ENUM_SELECT;
    ENUM_SELECT:begin enum_meta<=mq[enum_slot[SET_BITS+1:SET_BITS]];state<=ENUM_PAYLOAD;end
    ENUM_PAYLOAD:begin for(integer j=0;j<4;j=j+1)enum_pairs[j*64+:64]<=enum_meta[j]?pq[j]:INF;state<=ENUM_SEND;end
    ENUM_SEND:if(advance)begin
     frag_valid<=1;frag_final<=1;frag_line<=enum_meta[35:4];frag_mask<=enum_meta[3:0];frag_pairs<=enum_pairs;enumerated<=enumerated+1;
     if(enum_index+1==used)state<=FINISH;else begin enum_index<=enum_index+1;state<=ENUM_READ;end
    end
    FINISH:if(!frag_valid)begin done<=1;if(!flush)begin done<=0;used<=0;state<=RUN;end end
    default:state<=INIT;
   endcase
  end
 end
endmodule
module inf_flat_owner(input logic clk,reset,input logic [1:0] in_valid,output logic [1:0] in_ready,
 input logic [63:0] in_node,input logic [127:0] in_pair,input logic flush,output logic [1:0] done,
 output logic [1:0] frag_valid,input logic [1:0] frag_ready,output logic [1:0] frag_final,
 output logic [63:0] frag_line,output logic [7:0] frag_mask,output logic [511:0] frag_pairs,
 output logic [63:0] accepted,retired,spill_count,enumerated);
 for(genvar b=0;b<2;b=b+1)begin:banks
  inf_flat_bank bank(.clk,.reset,.in_valid(in_valid[b]),.in_ready(in_ready[b]),.in_node(in_node[b*32+:32]),.in_pair(in_pair[b*64+:64]),.flush,.done(done[b]),.frag_valid(frag_valid[b]),.frag_ready(frag_ready[b]),.frag_final(frag_final[b]),.frag_line(frag_line[b*32+:32]),.frag_mask(frag_mask[b*4+:4]),.frag_pairs(frag_pairs[b*256+:256]),.accepted(accepted[b*32+:32]),.retired(retired[b*32+:32]),.spill_count(spill_count[b*32+:32]),.enumerated(enumerated[b*32+:32]));
 end
endmodule
