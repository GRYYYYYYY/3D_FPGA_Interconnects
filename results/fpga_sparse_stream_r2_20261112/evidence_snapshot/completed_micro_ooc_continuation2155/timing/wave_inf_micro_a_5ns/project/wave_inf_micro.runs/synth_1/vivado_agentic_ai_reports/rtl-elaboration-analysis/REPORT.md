# RTL elaboration analysis

Errors: 0; critical warnings: 0; warnings:25. 24 identical RAM inference warnings refer to mem0..mem3 in the actual frozen wave_inf_bank.sv; one advisory concerns parallel synthesis scheduling.

Source inspected: [frozen RTL](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/wave_inf_micro_a_5ns/source/wave_inf_bank.sv:18). Read paths at73/79 and writes at57/64/85 describe multiple syntactic ports; state mutual exclusion was not enough for BRAM inference. This is an inference diagnosis to verify with the revised synthesis, not a claim of hardware timing.

[UG901 2022.2 memory inference](https://docs.amd.com/r/2022.2-English/ug901-vivado-synthesis/Memory-Inference-Capabilities), [single-clock simple dual port](https://docs.amd.com/r/2022.2-English/ug901-vivado-synthesis/Simple-Dual-Port-Block-RAM-with-Single-Clock-Verilog).

### Synth 8-6849: RAM port inference

Occurrences (all24):

|CSV S.No|Message|
|---|---|
|17|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem3_reg",trying to implement using LUTRAM|
|18|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem3_reg",trying to implement using LUTRAM|
|19|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem3_reg",trying to implement using LUTRAM|
|20|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem3_reg",trying to implement using LUTRAM|
|21|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem3_reg",trying to implement using LUTRAM|
|22|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem3_reg",trying to implement using LUTRAM|
|23|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem2_reg",trying to implement using LUTRAM|
|24|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem2_reg",trying to implement using LUTRAM|
|25|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem2_reg",trying to implement using LUTRAM|
|26|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem2_reg",trying to implement using LUTRAM|
|27|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem2_reg",trying to implement using LUTRAM|
|28|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem2_reg",trying to implement using LUTRAM|
|29|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem1_reg",trying to implement using LUTRAM|
|30|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem1_reg",trying to implement using LUTRAM|
|31|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem1_reg",trying to implement using LUTRAM|
|32|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem1_reg",trying to implement using LUTRAM|
|33|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem1_reg",trying to implement using LUTRAM|
|34|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem1_reg",trying to implement using LUTRAM|
|35|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem0_reg",trying to implement using LUTRAM|
|36|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem0_reg",trying to implement using LUTRAM|
|37|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem0_reg",trying to implement using LUTRAM|
|38|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem0_reg",trying to implement using LUTRAM|
|39|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem0_reg",trying to implement using LUTRAM|
|40|Infeasible attribute ram_style = "block" set for RAM "wave_inf_bank:/mem0_reg",trying to implement using LUTRAM|

Problematic code:
```diff
- rd[0]<=mem0[input_set];
- rd[0]<=mem0[scan_addr];
```

Recommended fix:
```diff
+ if(ram_read_enable) rd[0]<=mem0[ram_read_addr];
+ if(ram_write_enable[0]) mem0[ram_write_addr]<=ram_write_data;
```

Corrected code (includes equivalent changes for allfour ways and the occupied-list enumeration variant):
```systemverilog
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
```

> Copy this block into `wave_inf_bank.sv` before its control always_ff block, replacing all existing mem0..mem3 accesses at the frozen source locations57/64/73/79/85 with the muxed single-port interface. The complete reviewed patch below also removes those old accesses.

### Synth 8-7080: parallel synthesis criteria not met

CSV S.No13. Advisory, not an RTL fault. Source: [top module](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R2/results/fpga_sparse_stream_r2_20261112/timing/wave_inf_micro_a_5ns/source/wave_inf_bank.sv:100). No forced hierarchy or dont_touch is introduced.

Problematic code (none; current module retained):
```diff
 module wave_inf_owner #(parameter SET_BITS=10)(
```

Recommended fix (retain):
```diff
 module wave_inf_owner #(parameter SET_BITS=10)(
```

Corrected code:
```systemverilog
module wave_inf_owner #(parameter SET_BITS=10)(
```

> This unchanged declaration can be retained at `wave_inf_bank.sv` frozen line100; no RTL modification is required for the advisory.

All25 non-INFO messages accounted for:24 RAM occurrences plus1 scheduling advisory. No timing waiver.

## Complete patch for current occupied-list revision

```diff
--- accel/lookahead/fpga_sparse_stream_r2/rtl/wave_inf_bank.sv
+++ accel/lookahead/fpga_sparse_stream_r2/rtl/wave_inf_bank.sv
@@ -49,6 +49,30 @@
    in_ready=state==RUN&&!flush&&advance;
    scan_word=rd[scan_way];
  end
+ logic ram_read_enable;logic [SET_BITS-1:0] ram_read_addr,ram_write_addr;
+ logic [3:0] ram_write_enable;logic [291:0] ram_write_data;
+ always_comb begin
+   ram_read_enable=0;ram_read_addr=input_set;
+   ram_write_enable=0;ram_write_addr=stage_set;ram_write_data=update_word;
+   if(!reset)begin
+     if(state==RUN&&in_valid&&in_ready)ram_read_enable=1;
+     if(state==SCAN_READ)begin ram_read_enable=1;ram_read_addr=enum_slot[SET_BITS-1:0];end
+     if(state==INIT)begin ram_write_enable=4'b1111;ram_write_addr=init_addr;ram_write_data=0;end
+     if((state==RUN||state==DRAIN)&&advance&&stage_valid)ram_write_enable=4'b0001<<chosen;
+     if(state==SCAN_EMIT&&advance)begin ram_write_enable=4'b0001<<scan_way;ram_write_addr=scan_addr;ram_write_data=0;end
+   end
+ end
+ // One syntactic read and one write port per array. Mux state addresses BEFORE
+ // the RAM template; keep reset/control logic outside RAM read/write processes.
+ always_ff @(posedge clk)begin
+   if(ram_read_enable)begin
+     rd[0]<=mem0[ram_read_addr];rd[1]<=mem1[ram_read_addr];rd[2]<=mem2[ram_read_addr];rd[3]<=mem3[ram_read_addr];
+   end
+   if(ram_write_enable[0])mem0[ram_write_addr]<=ram_write_data;
+   if(ram_write_enable[1])mem1[ram_write_addr]<=ram_write_data;
+   if(ram_write_enable[2])mem2[ram_write_addr]<=ram_write_data;
+   if(ram_write_enable[3])mem3[ram_write_addr]<=ram_write_data;
+ end
  always_ff @(posedge clk)begin
    if(reset)begin
      state<=INIT;init_addr<=0;stage_valid<=0;last_write<=0;frag_valid<=0;done<=0;
@@ -57,14 +81,13 @@
      if(frag_valid&&frag_ready)frag_valid<=0;
      case(state)
      INIT:begin
-       mem0[init_addr]<=0;mem1[init_addr]<=0;mem2[init_addr]<=0;mem3[init_addr]<=0;victim[init_addr]<=0;
+       victim[init_addr]<=0;
        if(init_addr==SETS-1)state<=RUN;else init_addr<=init_addr+1;
      end
      RUN,DRAIN:if(advance)begin
        last_write<=stage_valid;
        if(stage_valid)begin
          retired<=retired+1;last_set<=stage_set;last_way<=chosen;last_word<=update_word;
-         case(chosen)0:mem0[stage_set]<=update_word;1:mem1[stage_set]<=update_word;2:mem2[stage_set]<=update_word;3:mem3[stage_set]<=update_word;endcase
          if(!hit)begin
            victim[stage_set]<=chosen+1;
            if(empty)begin occupied[used_slots]<={chosen,stage_set};used_slots<=used_slots+1;end
@@ -74,7 +97,6 @@
        stage_valid<=in_valid&&in_ready;
        if(in_valid&&in_ready)begin
          accepted<=accepted+1;stage_line<=in_node>>2;stage_sector<=in_node[1:0];stage_pair<=in_pair;stage_set<=input_set;
-         rd[0]<=mem0[input_set];rd[1]<=mem1[input_set];rd[2]<=mem2[input_set];rd[3]<=mem3[input_set];
        end
        if(state==RUN&&flush)state<=DRAIN;
        if(state==DRAIN&&!stage_valid)begin state<=used_slots==0?FINISH:LIST_READ;enum_index<=0;end
@@ -82,13 +104,11 @@
      LIST_READ:begin enum_slot<=occupied[enum_index];state<=SCAN_READ;end
      SCAN_READ:begin
        scan_addr<=enum_slot[SET_BITS-1:0];scan_way<=enum_slot[SET_BITS+1:SET_BITS];
-       rd[0]<=mem0[enum_slot[SET_BITS-1:0]];rd[1]<=mem1[enum_slot[SET_BITS-1:0]];rd[2]<=mem2[enum_slot[SET_BITS-1:0]];rd[3]<=mem3[enum_slot[SET_BITS-1:0]];
        state<=SCAN_EMIT;
      end
      SCAN_EMIT:if(advance)begin
        enumerated<=enumerated+1;
        if(scan_word[259:256]!=0)begin frag_valid<=1;frag_line<=scan_word[291:260];frag_mask<=scan_word[259:256];frag_pairs<=scan_word[255:0];end
-       case(scan_way)0:mem0[scan_addr]<=0;1:mem1[scan_addr]<=0;2:mem2[scan_addr]<=0;3:mem3[scan_addr]<=0;endcase
        if(enum_index+1==used_slots)state<=FINISH;
        else begin enum_index<=enum_index+1;state<=LIST_READ;end
      end
```
