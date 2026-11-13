// Wave-private positive-FP32 whole-pair fragment accumulator.
// Each way is a synchronous 1R1W RAM. One candidate per cycle in the hit path.
// Evicted fragments are handshaken to a finite external merge service; no free
// spill sort/fill is assumed. Flush enumerates only occupied finite slots and clears them.
module wave_inf_bank #(parameter SET_BITS=10)(
 input logic clk, reset,
 input logic in_valid, output logic in_ready,
 input logic [31:0] in_node, input logic [63:0] in_pair,
 input logic flush, output logic done,
 output logic frag_valid,input logic frag_ready,
 output logic [31:0] frag_line,output logic [3:0] frag_mask,
 output logic [255:0] frag_pairs,
 output logic [31:0] accepted,retired,spill_count,enumerated
);
 localparam SETS=1<<SET_BITS;
 localparam [63:0] INF=64'h7f8000007f800000;
 // {line[31:0], valid-sector mask[3:0], four complete pairs[255:0]}
 (* ram_style="block" *) logic [291:0] mem0[SETS],mem1[SETS],mem2[SETS],mem3[SETS];
 logic [291:0] rd[4],view[4],update_word;
 logic [1:0] victim[SETS];
 (* ram_style="block" *) logic [SET_BITS+1:0] occupied[4*SETS];
 logic [SET_BITS+2:0] used_slots,enum_index;
 logic [SET_BITS+1:0] enum_slot;
 logic [SET_BITS-1:0] init_addr,stage_set,scan_addr;
 logic [31:0] stage_line;
 logic [1:0] stage_sector,scan_way;
 logic [63:0] stage_pair;
 logic stage_valid,last_write;
 logic [SET_BITS-1:0] last_set;
 logic [1:0] last_way;
 logic [291:0] last_word;
 typedef enum logic[2:0]{INIT,RUN,DRAIN,LIST_READ,SCAN_READ,SCAN_EMIT,FINISH} state_t;
 state_t state;
 logic advance,hit,empty;logic [1:0] chosen;
 logic [291:0] scan_word;
 wire [SET_BITS-1:0] input_set=in_node[8+SET_BITS-1:8];
 always_comb begin
   for(integer w=0;w<4;w=w+1)begin
     view[w]=rd[w];
     if(last_write&&last_set==stage_set&&last_way==w)view[w]=last_word;
   end
   hit=0;empty=0;chosen=victim[stage_set];
   for(integer w=3;w>=0;w=w-1)if(view[w][259:256]==0)begin chosen=w;empty=1;end
   for(integer w=0;w<4;w=w+1)if(view[w][259:256]!=0&&view[w][291:260]==stage_line)begin chosen=w;hit=1;end
   update_word=hit?view[chosen]:{stage_line,4'b0,{4{INF}}};
   if(!update_word[256+stage_sector]||stage_pair<update_word[stage_sector*64+:64])update_word[stage_sector*64+:64]=stage_pair;
   update_word[256+stage_sector]=1;
   advance=!frag_valid||frag_ready;
   in_ready=state==RUN&&!flush&&advance;
   scan_word=rd[scan_way];
 end
 logic ram_read_enable;logic [SET_BITS-1:0] ram_read_addr,ram_write_addr;
 logic [3:0] ram_write_enable;logic [291:0] ram_write_data;
 always_comb begin
   ram_read_enable=0;ram_read_addr=input_set;
   ram_write_enable=0;ram_write_addr=stage_set;ram_write_data=update_word;
   if(!reset)begin
     if(state==RUN&&in_valid&&in_ready)ram_read_enable=1;
     if(state==SCAN_READ)begin ram_read_enable=1;ram_read_addr=enum_slot[SET_BITS-1:0];end
     if(state==INIT)begin ram_write_enable=4'b1111;ram_write_addr=init_addr;ram_write_data=0;end
     if((state==RUN||state==DRAIN)&&advance&&stage_valid)ram_write_enable=4'b0001<<chosen;
     if(state==SCAN_EMIT&&advance)begin ram_write_enable=4'b0001<<scan_way;ram_write_addr=scan_addr;ram_write_data=0;end
   end
 end
 // One syntactic read and one write port per array. Mux state addresses BEFORE
 // the RAM template; keep reset/control logic outside RAM read/write processes.
 always_ff @(posedge clk)begin
   if(ram_read_enable)begin
     rd[0]<=mem0[ram_read_addr];rd[1]<=mem1[ram_read_addr];rd[2]<=mem2[ram_read_addr];rd[3]<=mem3[ram_read_addr];
   end
   if(ram_write_enable[0])mem0[ram_write_addr]<=ram_write_data;
   if(ram_write_enable[1])mem1[ram_write_addr]<=ram_write_data;
   if(ram_write_enable[2])mem2[ram_write_addr]<=ram_write_data;
   if(ram_write_enable[3])mem3[ram_write_addr]<=ram_write_data;
 end
 always_ff @(posedge clk)begin
   if(reset)begin
     state<=INIT;init_addr<=0;stage_valid<=0;last_write<=0;frag_valid<=0;done<=0;
     accepted<=0;retired<=0;spill_count<=0;enumerated<=0;scan_addr<=0;scan_way<=0;used_slots<=0;enum_index<=0;
   end else begin
     if(frag_valid&&frag_ready)frag_valid<=0;
     case(state)
     INIT:begin
       victim[init_addr]<=0;
       if(init_addr==SETS-1)state<=RUN;else init_addr<=init_addr+1;
     end
     RUN,DRAIN:if(advance)begin
       last_write<=stage_valid;
       if(stage_valid)begin
         retired<=retired+1;last_set<=stage_set;last_way<=chosen;last_word<=update_word;
         if(!hit)begin
           victim[stage_set]<=chosen+1;
           if(empty)begin occupied[used_slots]<={chosen,stage_set};used_slots<=used_slots+1;end
           if(!empty)begin frag_valid<=1;frag_line<=view[chosen][291:260];frag_mask<=view[chosen][259:256];frag_pairs<=view[chosen][255:0];spill_count<=spill_count+1;end
         end
       end
       stage_valid<=in_valid&&in_ready;
       if(in_valid&&in_ready)begin
         accepted<=accepted+1;stage_line<=in_node>>2;stage_sector<=in_node[1:0];stage_pair<=in_pair;stage_set<=input_set;
       end
       if(state==RUN&&flush)state<=DRAIN;
       if(state==DRAIN&&!stage_valid)begin state<=used_slots==0?FINISH:LIST_READ;enum_index<=0;end
     end
     LIST_READ:begin enum_slot<=occupied[enum_index];state<=SCAN_READ;end
     SCAN_READ:begin
       scan_addr<=enum_slot[SET_BITS-1:0];scan_way<=enum_slot[SET_BITS+1:SET_BITS];
       state<=SCAN_EMIT;
     end
     SCAN_EMIT:if(advance)begin
       enumerated<=enumerated+1;
       if(scan_word[259:256]!=0)begin frag_valid<=1;frag_line<=scan_word[291:260];frag_mask<=scan_word[259:256];frag_pairs<=scan_word[255:0];end
       if(enum_index+1==used_slots)state<=FINISH;
       else begin enum_index<=enum_index+1;state<=LIST_READ;end
     end
     FINISH:if(!frag_valid)begin
       done<=1;
       if(!flush)begin done<=0;state<=RUN;used_slots<=0;last_write<=0;end
     end
     default:state<=INIT;
     endcase
   end
 end
endmodule

// Two genuinely independent candidate interfaces and RAM subbanks.
module wave_inf_owner #(parameter SET_BITS=10)(
 input logic clk,reset,input logic [1:0] in_valid,output logic [1:0] in_ready,
 input logic [63:0] in_node,input logic [127:0] in_pair,
 input logic flush,output logic [1:0] done,
 output logic [1:0] frag_valid,input logic [1:0] frag_ready,
 output logic [63:0] frag_line,output logic [7:0] frag_mask,output logic [511:0] frag_pairs,
 output logic [63:0] accepted,retired,spill_count,enumerated
);
 for(genvar b=0;b<2;b=b+1)begin:banks
   wave_inf_bank #(.SET_BITS(SET_BITS)) bank(.clk,.reset,.in_valid(in_valid[b]),.in_ready(in_ready[b]),
    .in_node(in_node[b*32+:32]),.in_pair(in_pair[b*64+:64]),.flush,.done(done[b]),
    .frag_valid(frag_valid[b]),.frag_ready(frag_ready[b]),.frag_line(frag_line[b*32+:32]),
    .frag_mask(frag_mask[b*4+:4]),.frag_pairs(frag_pairs[b*256+:256]),
    .accepted(accepted[b*32+:32]),.retired(retired[b*32+:32]),.spill_count(spill_count[b*32+:32]),.enumerated(enumerated[b*32+:32]));
 end
endmodule
