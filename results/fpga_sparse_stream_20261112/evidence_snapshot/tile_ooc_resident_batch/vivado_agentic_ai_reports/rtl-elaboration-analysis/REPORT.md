# RTL synthesis diagnostic review

Vivado2022.2, final resident-batch source snapshot. Log analysis only; synthesis succeeded. No RTL was changed to silence warnings. User-required physical evidence and the P3 fixed-structure decision take precedence over adding KEEP/DONT_TOUCH or making a new uncalibrated architecture.

The parser extracted 866 printed Synth messages: 318 WARNING, 548 INFO, zero ERROR and zero CRITICAL WARNING. The tool aggregate mentions 5028 warnings; repeated message suppression means that number is not the count of printed CSV rows. Every printed non-INFO row is accounted for below.

The bundled per-file splitter was executed but interprets this CSV layout incorrectly (429 apparent files). Its raw output is retained; this report uses Python csv.DictReader on the actual seven named columns. No subagent tool was used; file analysis was performed serially.

| Message ID | Printed warnings |
|---|---:|
| 3917 | 100 |
| 3936 | 9 |
| 4767 | 2 |
| 6014 | 38 |
| 6849 | 100 |
| 7129 | 69 |

### [Synth 8-3917] sparse_tile.sv:45 defined constant interface fields
File: [sparse_tile.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/sparse_tile.sv:45)

Read-only frontend ports drive mem_write/data constants; dedicated control transactions use fixed ID0; reserved interface bits remain defined. These are intentional constant connections, not floating outputs.

Source context (no deletion recommended):
```diff
   sparse_frontend front(clk,local_reset,pv[n],pr[n],pn[n*32+:32],pp[n*64+:64],row_base,edge_base,cost_we,cost_index,cost_data,
    mem_valid[8+n],mem_ready[8+n],mem_line[(8+n)*32+:32],front_id,rsp_valid[8+n],rsp_ready[8+n],rsp_id[(8+n)*6+:4],rsp_data[(8+n)*256+:256],
    fv[n],fr[n],fn[n*32+:32],fp[n*64+:64],front_idle[n],front_error[n],f0,f1,f2,f3,f4,fpeak);
   assign mem_id[(8+n)*6+:6]={2'b00,front_id};assign mem_write[8+n]=0;assign mem_data[(8+n)*256+:256]=0;
   sparse_owner owner(clk,local_reset,ov[n],ordy[n],on[n*32+:32],op[n*64+:64],phase==FENCE,owner_done[n],uv[n],ur[n],ul[n*32+:32],um[n*4+:4],
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
   sparse_frontend front(clk,local_reset,pv[n],pr[n],pn[n*32+:32],pp[n*64+:64],row_base,edge_base,cost_we,cost_index,cost_data,
    mem_valid[8+n],mem_ready[8+n],mem_line[(8+n)*32+:32],front_id,rsp_valid[8+n],rsp_ready[8+n],rsp_id[(8+n)*6+:4],rsp_data[(8+n)*256+:256],
    fv[n],fr[n],fn[n*32+:32],fp[n*64+:64],front_idle[n],front_error[n],f0,f1,f2,f3,f4,fpeak);
   assign mem_id[(8+n)*6+:6]={2'b00,front_id};assign mem_write[8+n]=0;assign mem_data[(8+n)*256+:256]=0;
   sparse_owner owner(clk,local_reset,ov[n],ordy[n],on[n*32+:32],op[n*64+:64],phase==FENCE,owner_done[n],uv[n],ur[n],ul[n*32+:32],um[n*4+:4],
```

Unchanged source context, paste-ready:
```systemverilog
  sparse_frontend front(clk,local_reset,pv[n],pr[n],pn[n*32+:32],pp[n*64+:64],row_base,edge_base,cost_we,cost_index,cost_data,
   mem_valid[8+n],mem_ready[8+n],mem_line[(8+n)*32+:32],front_id,rsp_valid[8+n],rsp_ready[8+n],rsp_id[(8+n)*6+:4],rsp_data[(8+n)*256+:256],
   fv[n],fr[n],fn[n*32+:32],fp[n*64+:64],front_idle[n],front_error[n],f0,f1,f2,f3,f4,fpeak);
  assign mem_id[(8+n)*6+:6]={2'b00,front_id};assign mem_write[8+n]=0;assign mem_data[(8+n)*256+:256]=0;
  sparse_owner owner(clk,local_reset,ov[n],ordy[n],on[n*32+:32],op[n*64+:64],phase==FENCE,owner_done[n],uv[n],ur[n],ul[n*32+:32],um[n*4+:4],
```
This block can be copied to `sparse_tile.sv` at line 43; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 85 | design sparse_tile has port mem_write[15] driven by constant 0 |
| 86 | design sparse_tile has port mem_write[14] driven by constant 0 |
| 87 | design sparse_tile has port mem_write[13] driven by constant 0 |
| 88 | design sparse_tile has port mem_write[12] driven by constant 0 |
| 89 | design sparse_tile has port mem_write[11] driven by constant 0 |
| 90 | design sparse_tile has port mem_write[10] driven by constant 0 |
| 91 | design sparse_tile has port mem_write[9] driven by constant 0 |
| 92 | design sparse_tile has port mem_write[8] driven by constant 0 |
| 93 | design sparse_tile has port mem_id[149] driven by constant 0 |
| 94 | design sparse_tile has port mem_id[148] driven by constant 0 |
| 95 | design sparse_tile has port mem_id[147] driven by constant 0 |
| 96 | design sparse_tile has port mem_id[146] driven by constant 0 |
| 97 | design sparse_tile has port mem_id[145] driven by constant 0 |
| 98 | design sparse_tile has port mem_id[144] driven by constant 0 |
| 99 | design sparse_tile has port mem_id[95] driven by constant 0 |
| 100 | design sparse_tile has port mem_id[94] driven by constant 0 |
| 101 | design sparse_tile has port mem_id[89] driven by constant 0 |
| 102 | design sparse_tile has port mem_id[88] driven by constant 0 |
| 103 | design sparse_tile has port mem_id[83] driven by constant 0 |
| 104 | design sparse_tile has port mem_id[82] driven by constant 0 |
| 105 | design sparse_tile has port mem_id[77] driven by constant 0 |
| 106 | design sparse_tile has port mem_id[76] driven by constant 0 |
| 107 | design sparse_tile has port mem_id[71] driven by constant 0 |
| 108 | design sparse_tile has port mem_id[70] driven by constant 0 |
| 109 | design sparse_tile has port mem_id[65] driven by constant 0 |
| 110 | design sparse_tile has port mem_id[64] driven by constant 0 |
| 111 | design sparse_tile has port mem_id[59] driven by constant 0 |
| 112 | design sparse_tile has port mem_id[58] driven by constant 0 |
| 113 | design sparse_tile has port mem_id[53] driven by constant 0 |
| 114 | design sparse_tile has port mem_id[52] driven by constant 0 |
| 115 | design sparse_tile has port mem_data[4095] driven by constant 0 |
| 116 | design sparse_tile has port mem_data[4094] driven by constant 0 |
| 117 | design sparse_tile has port mem_data[4093] driven by constant 0 |
| 118 | design sparse_tile has port mem_data[4092] driven by constant 0 |
| 119 | design sparse_tile has port mem_data[4091] driven by constant 0 |
| 120 | design sparse_tile has port mem_data[4090] driven by constant 0 |
| 121 | design sparse_tile has port mem_data[4089] driven by constant 0 |
| 122 | design sparse_tile has port mem_data[4088] driven by constant 0 |
| 123 | design sparse_tile has port mem_data[4087] driven by constant 0 |
| 124 | design sparse_tile has port mem_data[4086] driven by constant 0 |
| 125 | design sparse_tile has port mem_data[4085] driven by constant 0 |
| 126 | design sparse_tile has port mem_data[4084] driven by constant 0 |
| 127 | design sparse_tile has port mem_data[4083] driven by constant 0 |
| 128 | design sparse_tile has port mem_data[4082] driven by constant 0 |
| 129 | design sparse_tile has port mem_data[4081] driven by constant 0 |
| 130 | design sparse_tile has port mem_data[4080] driven by constant 0 |
| 131 | design sparse_tile has port mem_data[4079] driven by constant 0 |
| 132 | design sparse_tile has port mem_data[4078] driven by constant 0 |
| 133 | design sparse_tile has port mem_data[4077] driven by constant 0 |
| 134 | design sparse_tile has port mem_data[4076] driven by constant 0 |
| 135 | design sparse_tile has port mem_data[4075] driven by constant 0 |
| 136 | design sparse_tile has port mem_data[4074] driven by constant 0 |
| 137 | design sparse_tile has port mem_data[4073] driven by constant 0 |
| 138 | design sparse_tile has port mem_data[4072] driven by constant 0 |
| 139 | design sparse_tile has port mem_data[4071] driven by constant 0 |
| 140 | design sparse_tile has port mem_data[4070] driven by constant 0 |
| 141 | design sparse_tile has port mem_data[4069] driven by constant 0 |
| 142 | design sparse_tile has port mem_data[4068] driven by constant 0 |
| 143 | design sparse_tile has port mem_data[4067] driven by constant 0 |
| 144 | design sparse_tile has port mem_data[4066] driven by constant 0 |
| 145 | design sparse_tile has port mem_data[4065] driven by constant 0 |
| 146 | design sparse_tile has port mem_data[4064] driven by constant 0 |
| 147 | design sparse_tile has port mem_data[4063] driven by constant 0 |
| 148 | design sparse_tile has port mem_data[4062] driven by constant 0 |
| 149 | design sparse_tile has port mem_data[4061] driven by constant 0 |
| 150 | design sparse_tile has port mem_data[4060] driven by constant 0 |
| 151 | design sparse_tile has port mem_data[4059] driven by constant 0 |
| 152 | design sparse_tile has port mem_data[4058] driven by constant 0 |
| 153 | design sparse_tile has port mem_data[4057] driven by constant 0 |
| 154 | design sparse_tile has port mem_data[4056] driven by constant 0 |
| 155 | design sparse_tile has port mem_data[4055] driven by constant 0 |
| 156 | design sparse_tile has port mem_data[4054] driven by constant 0 |
| 157 | design sparse_tile has port mem_data[4053] driven by constant 0 |
| 158 | design sparse_tile has port mem_data[4052] driven by constant 0 |
| 159 | design sparse_tile has port mem_data[4051] driven by constant 0 |
| 160 | design sparse_tile has port mem_data[4050] driven by constant 0 |
| 161 | design sparse_tile has port mem_data[4049] driven by constant 0 |
| 162 | design sparse_tile has port mem_data[4048] driven by constant 0 |
| 163 | design sparse_tile has port mem_data[4047] driven by constant 0 |
| 164 | design sparse_tile has port mem_data[4046] driven by constant 0 |
| 165 | design sparse_tile has port mem_data[4045] driven by constant 0 |
| 166 | design sparse_tile has port mem_data[4044] driven by constant 0 |
| 167 | design sparse_tile has port mem_data[4043] driven by constant 0 |
| 168 | design sparse_tile has port mem_data[4042] driven by constant 0 |
| 169 | design sparse_tile has port mem_data[4041] driven by constant 0 |
| 170 | design sparse_tile has port mem_data[4040] driven by constant 0 |
| 171 | design sparse_tile has port mem_data[4039] driven by constant 0 |
| 172 | design sparse_tile has port mem_data[4038] driven by constant 0 |
| 173 | design sparse_tile has port mem_data[4037] driven by constant 0 |
| 174 | design sparse_tile has port mem_data[4036] driven by constant 0 |
| 175 | design sparse_tile has port mem_data[4035] driven by constant 0 |
| 176 | design sparse_tile has port mem_data[4034] driven by constant 0 |
| 177 | design sparse_tile has port mem_data[4033] driven by constant 0 |
| 178 | design sparse_tile has port mem_data[4032] driven by constant 0 |
| 179 | design sparse_tile has port mem_data[4031] driven by constant 0 |
| 180 | design sparse_tile has port mem_data[4030] driven by constant 0 |
| 181 | design sparse_tile has port mem_data[4029] driven by constant 0 |
| 182 | design sparse_tile has port mem_data[4028] driven by constant 0 |
| 183 | design sparse_tile has port mem_data[4027] driven by constant 0 |
| 184 | design sparse_tile has port mem_data[4026] driven by constant 0 |

### [Synth 8-3936] owner_sync.sv:81 
File: [owner_sync.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/owner_sync.sv:81)

Unused high bits are trimmed: pending uses29 bits and cur_node retains only sector bits while cur_line carries the line address. No missing functional consumer was found.

Source context (no deletion recommended):
```diff
     if(rv&&!update_valid)begin
      if(!rd[261])begin fillid<=rd[261:256];filldata<=rd[255:0];if(!mv[rd[260:256]])error<=1;resume_state<=IDLE;state<=FILL;end
     end else if(qv&&qr)begin cur_node<=qd[95:64];cur_line<=qd[95:66];cur_pair<=qd[63:0];state<=TAG;end
     else if(fence&&qc==0&&!qv&&mv==0&&!update_valid&&!flushing&&!fence_done)begin flushing<=1;flush_index<=0;state<=FLUSH;end
     else if(flushing&&wv==0&&!mem_valid&&!update_valid)begin flushing<=0;fence_done<=1;end
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
     if(rv&&!update_valid)begin
      if(!rd[261])begin fillid<=rd[261:256];filldata<=rd[255:0];if(!mv[rd[260:256]])error<=1;resume_state<=IDLE;state<=FILL;end
     end else if(qv&&qr)begin cur_node<=qd[95:64];cur_line<=qd[95:66];cur_pair<=qd[63:0];state<=TAG;end
     else if(fence&&qc==0&&!qv&&mv==0&&!update_valid&&!flushing&&!fence_done)begin flushing<=1;flush_index<=0;state<=FLUSH;end
     else if(flushing&&wv==0&&!mem_valid&&!update_valid)begin flushing<=0;fence_done<=1;end
```

Unchanged source context, paste-ready:
```systemverilog
    if(rv&&!update_valid)begin
     if(!rd[261])begin fillid<=rd[261:256];filldata<=rd[255:0];if(!mv[rd[260:256]])error<=1;resume_state<=IDLE;state<=FILL;end
    end else if(qv&&qr)begin cur_node<=qd[95:64];cur_line<=qd[95:66];cur_pair<=qd[63:0];state<=TAG;end
    else if(fence&&qc==0&&!qv&&mv==0&&!update_valid&&!flushing&&!fence_done)begin flushing<=1;flush_index<=0;state<=FLUSH;end
    else if(flushing&&wv==0&&!mem_valid&&!update_valid)begin flushing<=0;fence_done<=1;end
```
This block can be copied to `owner_sync.sv` at line 79; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 233 | Found unconnected internal register 'cur_node_reg' and it is trimmed from '32' to '2' bits. |

### [Synth 8-3936] sparse_bank.sv:45 
File: [sparse_bank.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/sparse_bank.sv:45)

Unused high bits are trimmed: pending uses29 bits and cur_node retains only sector bits while cur_line carries the line address. No missing functional consumer was found.

Source context (no deletion recommended):
```diff
  always @(posedge clk)begin
   // Explicit synchronous read ports. States below consume on following edges.
   label_q<=labels[idx];pending_q<=pending[idx];dir_q<=directory[key];member_q<=members[pointer[MA-1:0]];free_q<=free_ids[(free_count-1)&(MC-1)];closed_q<=closed[closed_rd[NA-1:0]];
   if(rst)begin context_valid<=0;context_sent<=0;context_ready<=0;commit_index<=0;mem_id<=0;state<=IDLE;done<=0;error<=0;pv<=0;close_valid<=0;ca<=0;mem_valid<=0;bitmap<=0;groups<=0;closed_mark<=0;closed_wr<=0;closed_rd<=0;free_count<=MC;member_peak<=0;active_count<=0;commit_count<=0;closed_count<=0;stale_count<=0;end else begin
    ca<=0;if(mem_valid&&mem_ready)mem_valid<=0;if(pv&&pr)pv<=0;if(close_valid&&close_ready)close_valid<=0;
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
  always @(posedge clk)begin
   // Explicit synchronous read ports. States below consume on following edges.
   label_q<=labels[idx];pending_q<=pending[idx];dir_q<=directory[key];member_q<=members[pointer[MA-1:0]];free_q<=free_ids[(free_count-1)&(MC-1)];closed_q<=closed[closed_rd[NA-1:0]];
   if(rst)begin context_valid<=0;context_sent<=0;context_ready<=0;commit_index<=0;mem_id<=0;state<=IDLE;done<=0;error<=0;pv<=0;close_valid<=0;ca<=0;mem_valid<=0;bitmap<=0;groups<=0;closed_mark<=0;closed_wr<=0;closed_rd<=0;free_count<=MC;member_peak<=0;active_count<=0;commit_count<=0;closed_count<=0;stale_count<=0;end else begin
    ca<=0;if(mem_valid&&mem_ready)mem_valid<=0;if(pv&&pr)pv<=0;if(close_valid&&close_ready)close_valid<=0;
```

Unchanged source context, paste-ready:
```systemverilog
 always @(posedge clk)begin
  // Explicit synchronous read ports. States below consume on following edges.
  label_q<=labels[idx];pending_q<=pending[idx];dir_q<=directory[key];member_q<=members[pointer[MA-1:0]];free_q<=free_ids[(free_count-1)&(MC-1)];closed_q<=closed[closed_rd[NA-1:0]];
  if(rst)begin context_valid<=0;context_sent<=0;context_ready<=0;commit_index<=0;mem_id<=0;state<=IDLE;done<=0;error<=0;pv<=0;close_valid<=0;ca<=0;mem_valid<=0;bitmap<=0;groups<=0;closed_mark<=0;closed_wr<=0;closed_rd<=0;free_count<=MC;member_peak<=0;active_count<=0;commit_count<=0;closed_count<=0;stale_count<=0;end else begin
   ca<=0;if(mem_valid&&mem_ready)mem_valid<=0;if(pv&&pr)pv<=0;if(close_valid&&close_ready)close_valid<=0;
```
This block can be copied to `sparse_bank.sv` at line 43; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 37 | Found unconnected internal register 'pending_q_reg' and it is trimmed from '32' to '29' bits. |
| 77 | Found unconnected internal register 'pending_q_reg' and it is trimmed from '32' to '29' bits. |
| 78 | Found unconnected internal register 'pending_q_reg' and it is trimmed from '32' to '29' bits. |
| 79 | Found unconnected internal register 'pending_q_reg' and it is trimmed from '32' to '29' bits. |
| 80 | Found unconnected internal register 'pending_q_reg' and it is trimmed from '32' to '29' bits. |
| 81 | Found unconnected internal register 'pending_q_reg' and it is trimmed from '32' to '29' bits. |
| 82 | Found unconnected internal register 'pending_q_reg' and it is trimmed from '32' to '29' bits. |
| 83 | Found unconnected internal register 'pending_q_reg' and it is trimmed from '32' to '29' bits. |

### [Synth 8-4767] frontend.sv:10 last
File: [frontend.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/frontend.sv:10)

pos/last are four small independently updated parent contexts. Concurrent emit, request and response operations need several logical update sites. Registers are intentional for these tiny context fields; forcing BRAM would require service arbitration and revalidation.

Source context (no deletion recommended):
```diff
  output reg [31:0] parents,edge_beats,row_beats,candidates,unused_sectors,output reg [2:0] context_peak);
  reg [2:0] state[0:3];localparam FREE=0,ROW=1,ROW_WAIT=2,ROW_NEXT=3,EDGE=4,EDGE_WAIT=5,EMIT=6,NEXT_WAIT=7;
  reg [31:0] node[0:3],pos[0:3],last[0:3];reg [63:0] parent[0:3];reg [255:0] beat[0:3];
  reg [63:0] costs[0:15];reg [1:0] rr;
  // One-line row metadata reuse; all fetches and cache misses counted.
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
  output reg [31:0] parents,edge_beats,row_beats,candidates,unused_sectors,output reg [2:0] context_peak);
  reg [2:0] state[0:3];localparam FREE=0,ROW=1,ROW_WAIT=2,ROW_NEXT=3,EDGE=4,EDGE_WAIT=5,EMIT=6,NEXT_WAIT=7;
  reg [31:0] node[0:3],pos[0:3],last[0:3];reg [63:0] parent[0:3];reg [255:0] beat[0:3];
  reg [63:0] costs[0:15];reg [1:0] rr;
  // One-line row metadata reuse; all fetches and cache misses counted.
```

Unchanged source context, paste-ready:
```systemverilog
 output reg [31:0] parents,edge_beats,row_beats,candidates,unused_sectors,output reg [2:0] context_peak);
 reg [2:0] state[0:3];localparam FREE=0,ROW=1,ROW_WAIT=2,ROW_NEXT=3,EDGE=4,EDGE_WAIT=5,EMIT=6,NEXT_WAIT=7;
 reg [31:0] node[0:3],pos[0:3],last[0:3];reg [63:0] parent[0:3];reg [255:0] beat[0:3];
 reg [63:0] costs[0:15];reg [1:0] rr;
 // One-line row metadata reuse; all fetches and cache misses counted.
```
This block can be copied to `frontend.sv` at line 8; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 42 | Trying to implement RAM 'last_reg' in registers. Block RAM or DRAM implementation is not possible; see log for reasons. |

### [Synth 8-4767] frontend.sv:10 pos
File: [frontend.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/frontend.sv:10)

pos/last are four small independently updated parent contexts. Concurrent emit, request and response operations need several logical update sites. Registers are intentional for these tiny context fields; forcing BRAM would require service arbitration and revalidation.

Source context (no deletion recommended):
```diff
  output reg [31:0] parents,edge_beats,row_beats,candidates,unused_sectors,output reg [2:0] context_peak);
  reg [2:0] state[0:3];localparam FREE=0,ROW=1,ROW_WAIT=2,ROW_NEXT=3,EDGE=4,EDGE_WAIT=5,EMIT=6,NEXT_WAIT=7;
  reg [31:0] node[0:3],pos[0:3],last[0:3];reg [63:0] parent[0:3];reg [255:0] beat[0:3];
  reg [63:0] costs[0:15];reg [1:0] rr;
  // One-line row metadata reuse; all fetches and cache misses counted.
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
  output reg [31:0] parents,edge_beats,row_beats,candidates,unused_sectors,output reg [2:0] context_peak);
  reg [2:0] state[0:3];localparam FREE=0,ROW=1,ROW_WAIT=2,ROW_NEXT=3,EDGE=4,EDGE_WAIT=5,EMIT=6,NEXT_WAIT=7;
  reg [31:0] node[0:3],pos[0:3],last[0:3];reg [63:0] parent[0:3];reg [255:0] beat[0:3];
  reg [63:0] costs[0:15];reg [1:0] rr;
  // One-line row metadata reuse; all fetches and cache misses counted.
```

Unchanged source context, paste-ready:
```systemverilog
 output reg [31:0] parents,edge_beats,row_beats,candidates,unused_sectors,output reg [2:0] context_peak);
 reg [2:0] state[0:3];localparam FREE=0,ROW=1,ROW_WAIT=2,ROW_NEXT=3,EDGE=4,EDGE_WAIT=5,EMIT=6,NEXT_WAIT=7;
 reg [31:0] node[0:3],pos[0:3],last[0:3];reg [63:0] parent[0:3];reg [255:0] beat[0:3];
 reg [63:0] costs[0:15];reg [1:0] rr;
 // One-line row metadata reuse; all fetches and cache misses counted.
```
This block can be copied to `frontend.sv` at line 8; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 43 | Trying to implement RAM 'pos_reg' in registers. Block RAM or DRAM implementation is not possible; see log for reasons. |

### [Synth 8-6014] changed_queue.sv:19 
File: [changed_queue.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/changed_queue.sv:19)

Scratch blocking temporaries and unused debug/replacement metadata are optimized away. The victim logic uses first free/available way; no round-robin replacement behavior is claimed. Allow optimization; do not retain dead state with DONT_TOUCH.

Source context (no deletion recommended):
```diff
    if(ev&&er)begin busy<=1;todo<=mask;base<={line[AW:3],2'b00};end
    if(busy)begin
     s=0;if(todo[0])s=0;else if(todo[1])s=1;else if(todo[2])s=2;else s=3;
     if(todo==0)busy<=0;else if(marked[base+s])todo[s]<=0;
     else if(wr<LIMIT)begin ids[wr[AW-1:0]]<=base+s;marked[base+s]<=1;wr<=wr+1;todo[s]<=0;if(wr+1>peak)peak<=wr+1;end
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
    if(ev&&er)begin busy<=1;todo<=mask;base<={line[AW:3],2'b00};end
    if(busy)begin
     s=0;if(todo[0])s=0;else if(todo[1])s=1;else if(todo[2])s=2;else s=3;
     if(todo==0)busy<=0;else if(marked[base+s])todo[s]<=0;
     else if(wr<LIMIT)begin ids[wr[AW-1:0]]<=base+s;marked[base+s]<=1;wr<=wr+1;todo[s]<=0;if(wr+1>peak)peak<=wr+1;end
```

Unchanged source context, paste-ready:
```systemverilog
   if(ev&&er)begin busy<=1;todo<=mask;base<={line[AW:3],2'b00};end
   if(busy)begin
    s=0;if(todo[0])s=0;else if(todo[1])s=1;else if(todo[2])s=2;else s=3;
    if(todo==0)busy<=0;else if(marked[base+s])todo[s]<=0;
    else if(wr<LIMIT)begin ids[wr[AW-1:0]]<=base+s;marked[base+s]<=1;wr<=wr+1;todo[s]<=0;if(wr+1>peak)peak<=wr+1;end
```
This block can be copied to `changed_queue.sv` at line 17; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 76 | Unused sequential element s_reg was removed. |

### [Synth 8-6014] frontend.sv:33 
File: [frontend.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/frontend.sv:33)

Scratch blocking temporaries and unused debug/replacement metadata are optimized away. The victim logic uses first free/available way; no round-robin replacement behavior is claimed. Allow optimization; do not retain dead state with DONT_TOUCH.

Source context (no deletion recommended):
```diff
    if(pv&&pr)begin state[free_ctx]<=ROW;node[free_ctx]<=pn;parent[free_ctx]<=pp;parents<=parents+1;end
    if(!emitv||emitr)begin emitv<=0;if(emit>=0)begin
     desc=beat[emit][pos[emit][2:0]*32+:32];emitv<=1;emitdst<={4'b0,desc[27:0]};emitparent<=parent[emit];emitcost<=costs[desc[31:28]];candidates<=candidates+1;rr<=emit+1;
     pos[emit]<=pos[emit]+1;
     if(pos[emit]+1==last[emit])state[emit]<=FREE;else if(pos[emit][2:0]==7)state[emit]<=EDGE;
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
    if(pv&&pr)begin state[free_ctx]<=ROW;node[free_ctx]<=pn;parent[free_ctx]<=pp;parents<=parents+1;end
    if(!emitv||emitr)begin emitv<=0;if(emit>=0)begin
     desc=beat[emit][pos[emit][2:0]*32+:32];emitv<=1;emitdst<={4'b0,desc[27:0]};emitparent<=parent[emit];emitcost<=costs[desc[31:28]];candidates<=candidates+1;rr<=emit+1;
     pos[emit]<=pos[emit]+1;
     if(pos[emit]+1==last[emit])state[emit]<=FREE;else if(pos[emit][2:0]==7)state[emit]<=EDGE;
```

Unchanged source context, paste-ready:
```systemverilog
   if(pv&&pr)begin state[free_ctx]<=ROW;node[free_ctx]<=pn;parent[free_ctx]<=pp;parents<=parents+1;end
   if(!emitv||emitr)begin emitv<=0;if(emit>=0)begin
    desc=beat[emit][pos[emit][2:0]*32+:32];emitv<=1;emitdst<={4'b0,desc[27:0]};emitparent<=parent[emit];emitcost<=costs[desc[31:28]];candidates<=candidates+1;rr<=emit+1;
    pos[emit]<=pos[emit]+1;
    if(pos[emit]+1==last[emit])state[emit]<=FREE;else if(pos[emit][2:0]==7)state[emit]<=EDGE;
```
This block can be copied to `frontend.sv` at line 31; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 38 | Unused sequential element desc_reg was removed. |

### [Synth 8-6014] frontend.sv:43 
File: [frontend.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/frontend.sv:43)

Scratch blocking temporaries and unused debug/replacement metadata are optimized away. The victim logic uses first free/available way; no round-robin replacement behavior is claimed. Allow optimization; do not retain dead state with DONT_TOUCH.

Source context (no deletion recommended):
```diff
      else if(state[fetch]==ROW_NEXT)begin mem_valid<=1;mem_line<=row_base+(node[fetch]>>2)+1;mem_id<={2'b01,fetch[1:0]};state[fetch]<=NEXT_WAIT;row_beats<=row_beats+1;end
      else if(row_valid&&row_tag==row_base+(node[fetch]>>2))begin
       a=row_cache[node[fetch][1:0]*64+:64];pos[fetch]<=a[31:0];if(a[63:32]!=0)local_error<=1;
       if(node[fetch][1:0]==3)state[fetch]<=ROW_NEXT;else begin b=row_cache[(node[fetch][1:0]+1)*64+:64];last[fetch]<=b[31:0];if(b[63:32]!=0||b<a)local_error<=1;state[fetch]<=a==b?FREE:EDGE;end
      end else begin mem_valid<=1;mem_line<=row_base+(node[fetch]>>2);mem_id<={2'b00,fetch[1:0]};state[fetch]<=ROW_WAIT;row_beats<=row_beats+1;end
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
      else if(state[fetch]==ROW_NEXT)begin mem_valid<=1;mem_line<=row_base+(node[fetch]>>2)+1;mem_id<={2'b01,fetch[1:0]};state[fetch]<=NEXT_WAIT;row_beats<=row_beats+1;end
      else if(row_valid&&row_tag==row_base+(node[fetch]>>2))begin
       a=row_cache[node[fetch][1:0]*64+:64];pos[fetch]<=a[31:0];if(a[63:32]!=0)local_error<=1;
       if(node[fetch][1:0]==3)state[fetch]<=ROW_NEXT;else begin b=row_cache[(node[fetch][1:0]+1)*64+:64];last[fetch]<=b[31:0];if(b[63:32]!=0||b<a)local_error<=1;state[fetch]<=a==b?FREE:EDGE;end
      end else begin mem_valid<=1;mem_line<=row_base+(node[fetch]>>2);mem_id<={2'b00,fetch[1:0]};state[fetch]<=ROW_WAIT;row_beats<=row_beats+1;end
```

Unchanged source context, paste-ready:
```systemverilog
     else if(state[fetch]==ROW_NEXT)begin mem_valid<=1;mem_line<=row_base+(node[fetch]>>2)+1;mem_id<={2'b01,fetch[1:0]};state[fetch]<=NEXT_WAIT;row_beats<=row_beats+1;end
     else if(row_valid&&row_tag==row_base+(node[fetch]>>2))begin
      a=row_cache[node[fetch][1:0]*64+:64];pos[fetch]<=a[31:0];if(a[63:32]!=0)local_error<=1;
      if(node[fetch][1:0]==3)state[fetch]<=ROW_NEXT;else begin b=row_cache[(node[fetch][1:0]+1)*64+:64];last[fetch]<=b[31:0];if(b[63:32]!=0||b<a)local_error<=1;state[fetch]<=a==b?FREE:EDGE;end
     end else begin mem_valid<=1;mem_line<=row_base+(node[fetch]>>2);mem_id<={2'b00,fetch[1:0]};state[fetch]<=ROW_WAIT;row_beats<=row_beats+1;end
```
This block can be copied to `frontend.sv` at line 41; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 39 | Unused sequential element a_reg was removed. |

### [Synth 8-6014] frontend.sv:44 
File: [frontend.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/frontend.sv:44)

Scratch blocking temporaries and unused debug/replacement metadata are optimized away. The victim logic uses first free/available way; no round-robin replacement behavior is claimed. Allow optimization; do not retain dead state with DONT_TOUCH.

Source context (no deletion recommended):
```diff
      else if(row_valid&&row_tag==row_base+(node[fetch]>>2))begin
       a=row_cache[node[fetch][1:0]*64+:64];pos[fetch]<=a[31:0];if(a[63:32]!=0)local_error<=1;
       if(node[fetch][1:0]==3)state[fetch]<=ROW_NEXT;else begin b=row_cache[(node[fetch][1:0]+1)*64+:64];last[fetch]<=b[31:0];if(b[63:32]!=0||b<a)local_error<=1;state[fetch]<=a==b?FREE:EDGE;end
      end else begin mem_valid<=1;mem_line<=row_base+(node[fetch]>>2);mem_id<={2'b00,fetch[1:0]};state[fetch]<=ROW_WAIT;row_beats<=row_beats+1;end
     end
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
      else if(row_valid&&row_tag==row_base+(node[fetch]>>2))begin
       a=row_cache[node[fetch][1:0]*64+:64];pos[fetch]<=a[31:0];if(a[63:32]!=0)local_error<=1;
       if(node[fetch][1:0]==3)state[fetch]<=ROW_NEXT;else begin b=row_cache[(node[fetch][1:0]+1)*64+:64];last[fetch]<=b[31:0];if(b[63:32]!=0||b<a)local_error<=1;state[fetch]<=a==b?FREE:EDGE;end
      end else begin mem_valid<=1;mem_line<=row_base+(node[fetch]>>2);mem_id<={2'b00,fetch[1:0]};state[fetch]<=ROW_WAIT;row_beats<=row_beats+1;end
     end
```

Unchanged source context, paste-ready:
```systemverilog
     else if(row_valid&&row_tag==row_base+(node[fetch]>>2))begin
      a=row_cache[node[fetch][1:0]*64+:64];pos[fetch]<=a[31:0];if(a[63:32]!=0)local_error<=1;
      if(node[fetch][1:0]==3)state[fetch]<=ROW_NEXT;else begin b=row_cache[(node[fetch][1:0]+1)*64+:64];last[fetch]<=b[31:0];if(b[63:32]!=0||b<a)local_error<=1;state[fetch]<=a==b?FREE:EDGE;end
     end else begin mem_valid<=1;mem_line<=row_base+(node[fetch]>>2);mem_id<={2'b00,fetch[1:0]};state[fetch]<=ROW_WAIT;row_beats<=row_beats+1;end
    end
```
This block can be copied to `frontend.sv` at line 42; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 40 | Unused sequential element b_reg was removed. |

### [Synth 8-6014] frontend.sv:49 
File: [frontend.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/frontend.sv:49)

Scratch blocking temporaries and unused debug/replacement metadata are optimized away. The victim logic uses first free/available way; no round-robin replacement behavior is claimed. Allow optimization; do not retain dead state with DONT_TOUCH.

Source context (no deletion recommended):
```diff
    end
    if(rsp_valid)begin
     s=rsp_id[1:0];
     if(rsp_id[3:2]==2)begin
      beat[s]<=rsp_data;state[s]<=EMIT;
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
    end
    if(rsp_valid)begin
     s=rsp_id[1:0];
     if(rsp_id[3:2]==2)begin
      beat[s]<=rsp_data;state[s]<=EMIT;
```

Unchanged source context, paste-ready:
```systemverilog
   end
   if(rsp_valid)begin
    s=rsp_id[1:0];
    if(rsp_id[3:2]==2)begin
     beat[s]<=rsp_data;state[s]<=EMIT;
```
This block can be copied to `frontend.sv` at line 47; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 41 | Unused sequential element s_reg was removed. |

### [Synth 8-6014] owner_sync.sv:62 
File: [owner_sync.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/owner_sync.sv:62)

Scratch blocking temporaries and unused debug/replacement metadata are optimized away. The victim logic uses first free/available way; no round-robin replacement behavior is claimed. Allow optimization; do not retain dead state with DONT_TOUCH.

Source context (no deletion recommended):
```diff
  assign idle=state==IDLE&&!qv&&qc==0&&!rv&&rc==0&&mv==0&&wv==0&&!mem_valid&&!update_valid;
  always @(posedge clk)begin
   if(rst)begin state<=IDLE;valid<=0;dirty<=0;busy<=0;mv<=0;ms<=0;wv<=0;ws<=0;update_valid<=0;mem_valid<=0;fence_done<=0;flushing<=0;flush_index<=0;error<=0;accepted<=0;retired<=0;hits<=0;misses<=0;merges<=0;raw_stall<=0;mshr_peak<=0;dirty_peak<=0;for(i=0;i<32;i=i+1)replace_way[i]<=0;end else begin
    if(iv&&ir&&!fence)accepted<=accepted+1;
    if(count_m>mshr_peak)mshr_peak<=count_m;if(count_w>dirty_peak)dirty_peak<=count_w;
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
  assign idle=state==IDLE&&!qv&&qc==0&&!rv&&rc==0&&mv==0&&wv==0&&!mem_valid&&!update_valid;
  always @(posedge clk)begin
   if(rst)begin state<=IDLE;valid<=0;dirty<=0;busy<=0;mv<=0;ms<=0;wv<=0;ws<=0;update_valid<=0;mem_valid<=0;fence_done<=0;flushing<=0;flush_index<=0;error<=0;accepted<=0;retired<=0;hits<=0;misses<=0;merges<=0;raw_stall<=0;mshr_peak<=0;dirty_peak<=0;for(i=0;i<32;i=i+1)replace_way[i]<=0;end else begin
    if(iv&&ir&&!fence)accepted<=accepted+1;
    if(count_m>mshr_peak)mshr_peak<=count_m;if(count_w>dirty_peak)dirty_peak<=count_w;
```

Unchanged source context, paste-ready:
```systemverilog
 assign idle=state==IDLE&&!qv&&qc==0&&!rv&&rc==0&&mv==0&&wv==0&&!mem_valid&&!update_valid;
 always @(posedge clk)begin
  if(rst)begin state<=IDLE;valid<=0;dirty<=0;busy<=0;mv<=0;ms<=0;wv<=0;ws<=0;update_valid<=0;mem_valid<=0;fence_done<=0;flushing<=0;flush_index<=0;error<=0;accepted<=0;retired<=0;hits<=0;misses<=0;merges<=0;raw_stall<=0;mshr_peak<=0;dirty_peak<=0;for(i=0;i<32;i=i+1)replace_way[i]<=0;end else begin
   if(iv&&ir&&!fence)accepted<=accepted+1;
   if(count_m>mshr_peak)mshr_peak<=count_m;if(count_w>dirty_peak)dirty_peak<=count_w;
```
This block can be copied to `owner_sync.sv` at line 60; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 44 | Unused sequential element replace_way_reg[0] was removed. |
| 45 | Unused sequential element replace_way_reg[1] was removed. |
| 46 | Unused sequential element replace_way_reg[2] was removed. |
| 47 | Unused sequential element replace_way_reg[3] was removed. |
| 48 | Unused sequential element replace_way_reg[4] was removed. |
| 49 | Unused sequential element replace_way_reg[5] was removed. |
| 50 | Unused sequential element replace_way_reg[6] was removed. |
| 51 | Unused sequential element replace_way_reg[7] was removed. |
| 52 | Unused sequential element replace_way_reg[8] was removed. |
| 53 | Unused sequential element replace_way_reg[9] was removed. |
| 54 | Unused sequential element replace_way_reg[10] was removed. |
| 55 | Unused sequential element replace_way_reg[11] was removed. |
| 56 | Unused sequential element replace_way_reg[12] was removed. |
| 57 | Unused sequential element replace_way_reg[13] was removed. |
| 58 | Unused sequential element replace_way_reg[14] was removed. |
| 59 | Unused sequential element replace_way_reg[15] was removed. |
| 60 | Unused sequential element replace_way_reg[16] was removed. |
| 61 | Unused sequential element replace_way_reg[17] was removed. |
| 62 | Unused sequential element replace_way_reg[18] was removed. |
| 63 | Unused sequential element replace_way_reg[19] was removed. |
| 64 | Unused sequential element replace_way_reg[20] was removed. |
| 65 | Unused sequential element replace_way_reg[21] was removed. |
| 66 | Unused sequential element replace_way_reg[22] was removed. |
| 67 | Unused sequential element replace_way_reg[23] was removed. |
| 68 | Unused sequential element replace_way_reg[24] was removed. |
| 69 | Unused sequential element replace_way_reg[25] was removed. |
| 70 | Unused sequential element replace_way_reg[26] was removed. |
| 71 | Unused sequential element replace_way_reg[27] was removed. |
| 72 | Unused sequential element replace_way_reg[28] was removed. |
| 73 | Unused sequential element replace_way_reg[29] was removed. |
| 74 | Unused sequential element replace_way_reg[30] was removed. |
| 75 | Unused sequential element replace_way_reg[31] was removed. |

### [Synth 8-6014] router.sv:23 
File: [router.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/router.sv:23)

Scratch blocking temporaries and unused debug/replacement metadata are optimized away. The victim logic uses first free/available way; no round-robin replacement behavior is claimed. Allow optimization; do not retain dead state with DONT_TOUCH.

Source context (no deletion recommended):
```diff
  assign idle=counts==0&&ov==0;
  always @(posedge clk)if(rst)begin conflicts<=0;for(o=0;o<8;o=o+1)rr[o]<=0;end else begin
   requests=0;for(k=0;k<8;k=k+1)if(iv[k]&&!ir[k])requests=requests+1;
   conflicts<=conflicts+requests;
   for(o=0;o<8;o=o+1)if(put[o]&&put_ready[o])rr[o]<=rr[o]+1;
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
  assign idle=counts==0&&ov==0;
  always @(posedge clk)if(rst)begin conflicts<=0;for(o=0;o<8;o=o+1)rr[o]<=0;end else begin
   requests=0;for(k=0;k<8;k=k+1)if(iv[k]&&!ir[k])requests=requests+1;
   conflicts<=conflicts+requests;
   for(o=0;o<8;o=o+1)if(put[o]&&put_ready[o])rr[o]<=rr[o]+1;
```

Unchanged source context, paste-ready:
```systemverilog
 assign idle=counts==0&&ov==0;
 always @(posedge clk)if(rst)begin conflicts<=0;for(o=0;o<8;o=o+1)rr[o]<=0;end else begin
  requests=0;for(k=0;k<8;k=k+1)if(iv[k]&&!ir[k])requests=requests+1;
  conflicts<=conflicts+requests;
  for(o=0;o<8;o=o+1)if(put[o]&&put_ready[o])rr[o]<=rr[o]+1;
```
This block can be copied to `router.sv` at line 21; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 84 | Unused sequential element requests_reg was removed. |

### [Synth 8-6849] sparse_bank.sv:17 labels
File: [sparse_bank.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/sparse_bank.sv:17)

The read is synchronous, but this array has multiple write-address sites / logical port requirements that this Vivado2022.2 synthesis does not map to BRAM. Actual LUTRAM allocation is accepted and charged in this fixed prototype. A future BRAM revision must centralize mutually exclusive write ports and, for outputs, explicitly provide two read ports (possibly replicated storage). An attribute alone is not a repair; no change to the validated RTL is made.

Source context (no deletion recommended):
```diff
  localparam [63:0] INF=64'h7f8000007f800000;
  localparam [31:0] NIL=32'hffffffff;
  (* ram_style="block" *) reg [63:0] labels[0:NC-1];
  (* ram_style="block" *) reg [31:0] pending[0:NC-1];
  (* ram_style="block" *) reg [63:0] directory[0:4095];
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
  localparam [63:0] INF=64'h7f8000007f800000;
  localparam [31:0] NIL=32'hffffffff;
  (* ram_style="block" *) reg [63:0] labels[0:NC-1];
  (* ram_style="block" *) reg [31:0] pending[0:NC-1];
  (* ram_style="block" *) reg [63:0] directory[0:4095];
```

Unchanged source context, paste-ready:
```systemverilog
 localparam [63:0] INF=64'h7f8000007f800000;
 localparam [31:0] NIL=32'hffffffff;
 (* ram_style="block" *) reg [63:0] labels[0:NC-1];
 (* ram_style="block" *) reg [31:0] pending[0:NC-1];
 (* ram_style="block" *) reg [63:0] directory[0:4095];
```
This block can be copied to `sparse_bank.sv` at line 15; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 376 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB4/labels_reg",trying to implement using LUTRAM |
| 377 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB4/labels_reg",trying to implement using LUTRAM |
| 378 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB4/labels_reg",trying to implement using LUTRAM |
| 379 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB4/labels_reg",trying to implement using LUTRAM |
| 380 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB4/labels_reg",trying to implement using LUTRAM |
| 381 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB4/labels_reg",trying to implement using LUTRAM |
| 530 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB4/labels_reg",trying to implement using LUTRAM |
| 531 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB4/labels_reg",trying to implement using LUTRAM |
| 532 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB4/labels_reg",trying to implement using LUTRAM |
| 533 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB4/labels_reg",trying to implement using LUTRAM |
| 534 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB4/labels_reg",trying to implement using LUTRAM |
| 535 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB4/labels_reg",trying to implement using LUTRAM |
| 554 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/labels_reg",trying to implement using LUTRAM |
| 555 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/labels_reg",trying to implement using LUTRAM |
| 556 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/labels_reg",trying to implement using LUTRAM |
| 557 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/labels_reg",trying to implement using LUTRAM |
| 558 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/labels_reg",trying to implement using LUTRAM |
| 559 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/labels_reg",trying to implement using LUTRAM |
| 613 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB4/labels_reg",trying to implement using LUTRAM |
| 614 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB4/labels_reg",trying to implement using LUTRAM |
| 615 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB4/labels_reg",trying to implement using LUTRAM |
| 616 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB4/labels_reg",trying to implement using LUTRAM |
| 617 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB4/labels_reg",trying to implement using LUTRAM |
| 618 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB4/labels_reg",trying to implement using LUTRAM |
| 649 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/labels_reg",trying to implement using LUTRAM |
| 650 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/labels_reg",trying to implement using LUTRAM |
| 651 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/labels_reg",trying to implement using LUTRAM |
| 652 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/labels_reg",trying to implement using LUTRAM |
| 653 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/labels_reg",trying to implement using LUTRAM |
| 654 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/labels_reg",trying to implement using LUTRAM |
| 678 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized4__GB2/labels_reg",trying to implement using LUTRAM |
| 679 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized4__GB2/labels_reg",trying to implement using LUTRAM |
| 680 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized4__GB2/labels_reg",trying to implement using LUTRAM |
| 681 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized4__GB2/labels_reg",trying to implement using LUTRAM |
| 682 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized4__GB2/labels_reg",trying to implement using LUTRAM |
| 683 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized4__GB2/labels_reg",trying to implement using LUTRAM |

### [Synth 8-6849] sparse_bank.sv:18 pending
File: [sparse_bank.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/sparse_bank.sv:18)

The read is synchronous, but this array has multiple write-address sites / logical port requirements that this Vivado2022.2 synthesis does not map to BRAM. Actual LUTRAM allocation is accepted and charged in this fixed prototype. A future BRAM revision must centralize mutually exclusive write ports and, for outputs, explicitly provide two read ports (possibly replicated storage). An attribute alone is not a repair; no change to the validated RTL is made.

Source context (no deletion recommended):
```diff
  localparam [31:0] NIL=32'hffffffff;
  (* ram_style="block" *) reg [63:0] labels[0:NC-1];
  (* ram_style="block" *) reg [31:0] pending[0:NC-1];
  (* ram_style="block" *) reg [63:0] directory[0:4095];
  (* ram_style="block" *) reg [63:0] members[0:MC-1];
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
  localparam [31:0] NIL=32'hffffffff;
  (* ram_style="block" *) reg [63:0] labels[0:NC-1];
  (* ram_style="block" *) reg [31:0] pending[0:NC-1];
  (* ram_style="block" *) reg [63:0] directory[0:4095];
  (* ram_style="block" *) reg [63:0] members[0:MC-1];
```

Unchanged source context, paste-ready:
```systemverilog
 localparam [31:0] NIL=32'hffffffff;
 (* ram_style="block" *) reg [63:0] labels[0:NC-1];
 (* ram_style="block" *) reg [31:0] pending[0:NC-1];
 (* ram_style="block" *) reg [63:0] directory[0:4095];
 (* ram_style="block" *) reg [63:0] members[0:MC-1];
```
This block can be copied to `sparse_bank.sv` at line 16; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 348 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB0/pending_reg",trying to implement using LUTRAM |
| 349 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB0/pending_reg",trying to implement using LUTRAM |
| 350 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB0/pending_reg",trying to implement using LUTRAM |
| 351 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB0/pending_reg",trying to implement using LUTRAM |
| 352 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB0/pending_reg",trying to implement using LUTRAM |
| 353 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB0/pending_reg",trying to implement using LUTRAM |
| 518 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB0/pending_reg",trying to implement using LUTRAM |
| 519 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB0/pending_reg",trying to implement using LUTRAM |
| 520 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB0/pending_reg",trying to implement using LUTRAM |
| 521 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB0/pending_reg",trying to implement using LUTRAM |
| 522 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB0/pending_reg",trying to implement using LUTRAM |
| 523 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB0/pending_reg",trying to implement using LUTRAM |
| 560 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/pending_reg",trying to implement using LUTRAM |
| 561 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/pending_reg",trying to implement using LUTRAM |
| 562 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/pending_reg",trying to implement using LUTRAM |
| 563 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/pending_reg",trying to implement using LUTRAM |
| 564 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/pending_reg",trying to implement using LUTRAM |
| 565 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/pending_reg",trying to implement using LUTRAM |
| 585 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB0/pending_reg",trying to implement using LUTRAM |
| 586 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB0/pending_reg",trying to implement using LUTRAM |
| 587 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB0/pending_reg",trying to implement using LUTRAM |
| 588 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB0/pending_reg",trying to implement using LUTRAM |
| 589 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB0/pending_reg",trying to implement using LUTRAM |
| 590 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB0/pending_reg",trying to implement using LUTRAM |
| 643 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/pending_reg",trying to implement using LUTRAM |
| 644 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/pending_reg",trying to implement using LUTRAM |
| 645 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/pending_reg",trying to implement using LUTRAM |
| 646 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/pending_reg",trying to implement using LUTRAM |
| 647 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/pending_reg",trying to implement using LUTRAM |
| 648 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/pending_reg",trying to implement using LUTRAM |

### [Synth 8-6849] sparse_bank.sv:21 free_ids
File: [sparse_bank.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/sparse_bank.sv:21)

The read is synchronous, but this array has multiple write-address sites / logical port requirements that this Vivado2022.2 synthesis does not map to BRAM. Actual LUTRAM allocation is accepted and charged in this fixed prototype. A future BRAM revision must centralize mutually exclusive write ports and, for outputs, explicitly provide two read ports (possibly replicated storage). An attribute alone is not a repair; no change to the validated RTL is made.

Source context (no deletion recommended):
```diff
  (* ram_style="block" *) reg [63:0] directory[0:4095];
  (* ram_style="block" *) reg [63:0] members[0:MC-1];
  (* ram_style="block" *) reg [MA-1:0] free_ids[0:MC-1];
  (* ram_style="block" *) reg [NA-1:0] closed[0:NC-1];
  reg [15:0] context_valid,context_sent,context_ready;
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
  (* ram_style="block" *) reg [63:0] directory[0:4095];
  (* ram_style="block" *) reg [63:0] members[0:MC-1];
  (* ram_style="block" *) reg [MA-1:0] free_ids[0:MC-1];
  (* ram_style="block" *) reg [NA-1:0] closed[0:NC-1];
  reg [15:0] context_valid,context_sent,context_ready;
```

Unchanged source context, paste-ready:
```systemverilog
 (* ram_style="block" *) reg [63:0] directory[0:4095];
 (* ram_style="block" *) reg [63:0] members[0:MC-1];
 (* ram_style="block" *) reg [MA-1:0] free_ids[0:MC-1];
 (* ram_style="block" *) reg [NA-1:0] closed[0:NC-1];
 reg [15:0] context_valid,context_sent,context_ready;
```
This block can be copied to `sparse_bank.sv` at line 19; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 370 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB4/free_ids_reg",trying to implement using LUTRAM |
| 371 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB4/free_ids_reg",trying to implement using LUTRAM |
| 372 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB4/free_ids_reg",trying to implement using LUTRAM |
| 373 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB4/free_ids_reg",trying to implement using LUTRAM |
| 374 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB4/free_ids_reg",trying to implement using LUTRAM |
| 375 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__GB4/free_ids_reg",trying to implement using LUTRAM |
| 536 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB4/free_ids_reg",trying to implement using LUTRAM |
| 537 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB4/free_ids_reg",trying to implement using LUTRAM |
| 538 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB4/free_ids_reg",trying to implement using LUTRAM |
| 539 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB4/free_ids_reg",trying to implement using LUTRAM |
| 540 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB4/free_ids_reg",trying to implement using LUTRAM |
| 541 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized0__GB4/free_ids_reg",trying to implement using LUTRAM |
| 566 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/free_ids_reg",trying to implement using LUTRAM |
| 567 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/free_ids_reg",trying to implement using LUTRAM |
| 568 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/free_ids_reg",trying to implement using LUTRAM |
| 569 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/free_ids_reg",trying to implement using LUTRAM |
| 570 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/free_ids_reg",trying to implement using LUTRAM |
| 571 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized1__GB2/free_ids_reg",trying to implement using LUTRAM |
| 607 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB4/free_ids_reg",trying to implement using LUTRAM |
| 608 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB4/free_ids_reg",trying to implement using LUTRAM |
| 609 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB4/free_ids_reg",trying to implement using LUTRAM |
| 610 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB4/free_ids_reg",trying to implement using LUTRAM |
| 611 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB4/free_ids_reg",trying to implement using LUTRAM |
| 612 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized2__GB4/free_ids_reg",trying to implement using LUTRAM |
| 655 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/free_ids_reg",trying to implement using LUTRAM |
| 656 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/free_ids_reg",trying to implement using LUTRAM |
| 657 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/free_ids_reg",trying to implement using LUTRAM |
| 658 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/free_ids_reg",trying to implement using LUTRAM |
| 659 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/free_ids_reg",trying to implement using LUTRAM |
| 660 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized3__GB4/free_ids_reg",trying to implement using LUTRAM |
| 684 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized4__GB2/free_ids_reg",trying to implement using LUTRAM |
| 685 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized4__GB2/free_ids_reg",trying to implement using LUTRAM |
| 686 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized4__GB2/free_ids_reg",trying to implement using LUTRAM |
| 687 | Infeasible attribute ram_style = "block" set for RAM "sparse_bank__parameterized4__GB2/free_ids_reg",trying to implement using LUTRAM |

### [Synth 8-7129] changed_queue.sv:5 unused address or ID high bits under admitted protocol
File: [changed_queue.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/changed_queue.sv:5)

Node IDs are admitted below4096; frontend response IDs use4 of6 bits, control ID is fixed0, and changed membership uses bank-local address bits. Responses must echo the issued transaction ID. Leave the common interface width and allow trimming; this does not validate malformed memory responses.

Source context (no deletion recommended):
```diff
 // A first mark and physical append happen on the same edge, only with credit.
 module changed_queue #(parameter CAP=512,LIMIT=CAP,AW=$clog2(CAP))(
  input wire clk,rst,input wire ev,output wire er,input wire [31:0] line,input wire [3:0] mask,
  input wire commit_phase,output reg ov,input wire issue_ready,output reg [AW-1:0] index,
  input wire ack,input wire [AW-1:0] ack_index,
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
 // A first mark and physical append happen on the same edge, only with credit.
 module changed_queue #(parameter CAP=512,LIMIT=CAP,AW=$clog2(CAP))(
  input wire clk,rst,input wire ev,output wire er,input wire [31:0] line,input wire [3:0] mask,
  input wire commit_phase,output reg ov,input wire issue_ready,output reg [AW-1:0] index,
  input wire ack,input wire [AW-1:0] ack_index,
```

Unchanged source context, paste-ready:
```systemverilog
// A first mark and physical append happen on the same edge, only with credit.
module changed_queue #(parameter CAP=512,LIMIT=CAP,AW=$clog2(CAP))(
 input wire clk,rst,input wire ev,output wire er,input wire [31:0] line,input wire [3:0] mask,
 input wire commit_phase,output reg ov,input wire issue_ready,output reg [AW-1:0] index,
 input wire ack,input wire [AW-1:0] ack_index,
```
This block can be copied to `changed_queue.sv` at line 3; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 185 | Port line[31] in module changed_queue is either unconnected or has no load |
| 186 | Port line[30] in module changed_queue is either unconnected or has no load |
| 187 | Port line[29] in module changed_queue is either unconnected or has no load |
| 188 | Port line[28] in module changed_queue is either unconnected or has no load |
| 189 | Port line[27] in module changed_queue is either unconnected or has no load |
| 190 | Port line[26] in module changed_queue is either unconnected or has no load |
| 191 | Port line[25] in module changed_queue is either unconnected or has no load |
| 192 | Port line[24] in module changed_queue is either unconnected or has no load |
| 193 | Port line[23] in module changed_queue is either unconnected or has no load |
| 194 | Port line[22] in module changed_queue is either unconnected or has no load |
| 195 | Port line[21] in module changed_queue is either unconnected or has no load |
| 196 | Port line[20] in module changed_queue is either unconnected or has no load |
| 197 | Port line[19] in module changed_queue is either unconnected or has no load |
| 198 | Port line[18] in module changed_queue is either unconnected or has no load |
| 199 | Port line[17] in module changed_queue is either unconnected or has no load |
| 200 | Port line[16] in module changed_queue is either unconnected or has no load |
| 201 | Port line[15] in module changed_queue is either unconnected or has no load |
| 202 | Port line[14] in module changed_queue is either unconnected or has no load |
| 203 | Port line[13] in module changed_queue is either unconnected or has no load |
| 204 | Port line[12] in module changed_queue is either unconnected or has no load |
| 205 | Port line[11] in module changed_queue is either unconnected or has no load |
| 206 | Port line[10] in module changed_queue is either unconnected or has no load |
| 207 | Port line[2] in module changed_queue is either unconnected or has no load |
| 208 | Port line[1] in module changed_queue is either unconnected or has no load |
| 209 | Port line[0] in module changed_queue is either unconnected or has no load |

### [Synth 8-7129] sparse_tile.sv:41 unused address or ID high bits under admitted protocol
File: [sparse_tile.sv](/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_SPARSE_STREAM_R1/results/fpga_sparse_stream_20261112/tile_ooc_resident_batch/source/rtl/sparse_tile.sv:41)

Node IDs are admitted below4096; frontend response IDs use4 of6 bits, control ID is fixed0, and changed membership uses bank-local address bits. Responses must echo the issued transaction ID. Leave the common interface width and allow trimming; this does not validate malformed memory responses.

Source context (no deletion recommended):
```diff
    mem_valid[16+n],mem_ready[16+n],mem_write[16+n],mem_line[(16+n)*32+:32],mem_data[(16+n)*256+:256],rsp_valid[16+n],rsp_data[(16+n)*256+:256],mem_id[(16+n)*6+:6],rsp_id[(16+n)*6+:6],
    active_counts[n*32+:32],commit_counts[n*32+:32],bc0,bc1,member_peak);
   assign rsp_ready[16+n]=1;
   wire [3:0] front_id;wire [31:0] f0,f1,f2,f3,f4;wire [2:0] fpeak;
   sparse_frontend front(clk,local_reset,pv[n],pr[n],pn[n*32+:32],pp[n*64+:64],row_base,edge_base,cost_we,cost_index,cost_data,
```

Recommended disposition (behavior unchanged):
```diff
+ // Reviewed: preserve this validated implementation; charge its actual inferred resources.
    mem_valid[16+n],mem_ready[16+n],mem_write[16+n],mem_line[(16+n)*32+:32],mem_data[(16+n)*256+:256],rsp_valid[16+n],rsp_data[(16+n)*256+:256],mem_id[(16+n)*6+:6],rsp_id[(16+n)*6+:6],
    active_counts[n*32+:32],commit_counts[n*32+:32],bc0,bc1,member_peak);
   assign rsp_ready[16+n]=1;
   wire [3:0] front_id;wire [31:0] f0,f1,f2,f3,f4;wire [2:0] fpeak;
   sparse_frontend front(clk,local_reset,pv[n],pr[n],pn[n*32+:32],pp[n*64+:64],row_base,edge_base,cost_we,cost_index,cost_data,
```

Unchanged source context, paste-ready:
```systemverilog
   mem_valid[16+n],mem_ready[16+n],mem_write[16+n],mem_line[(16+n)*32+:32],mem_data[(16+n)*256+:256],rsp_valid[16+n],rsp_data[(16+n)*256+:256],mem_id[(16+n)*6+:6],rsp_id[(16+n)*6+:6],
   active_counts[n*32+:32],commit_counts[n*32+:32],bc0,bc1,member_peak);
  assign rsp_ready[16+n]=1;
  wire [3:0] front_id;wire [31:0] f0,f1,f2,f3,f4;wire [2:0] fpeak;
  sparse_frontend front(clk,local_reset,pv[n],pr[n],pn[n*32+:32],pp[n*64+:64],row_base,edge_base,cost_we,cost_index,cost_data,
```
This block can be copied to `sparse_tile.sv` at line 39; it is unchanged context, not a BRAM-port rewrite. No source edit is required for the accepted disposition.

Occurrences:
| CSV S.No | Diagnostic |
|---|---|
| 210 | Port rsp_id[149] in module sparse_tile is either unconnected or has no load |
| 211 | Port rsp_id[148] in module sparse_tile is either unconnected or has no load |
| 212 | Port rsp_id[147] in module sparse_tile is either unconnected or has no load |
| 213 | Port rsp_id[146] in module sparse_tile is either unconnected or has no load |
| 214 | Port rsp_id[145] in module sparse_tile is either unconnected or has no load |
| 215 | Port rsp_id[144] in module sparse_tile is either unconnected or has no load |
| 216 | Port rsp_id[95] in module sparse_tile is either unconnected or has no load |
| 217 | Port rsp_id[94] in module sparse_tile is either unconnected or has no load |
| 218 | Port rsp_id[89] in module sparse_tile is either unconnected or has no load |
| 219 | Port rsp_id[88] in module sparse_tile is either unconnected or has no load |
| 220 | Port rsp_id[83] in module sparse_tile is either unconnected or has no load |
| 221 | Port rsp_id[82] in module sparse_tile is either unconnected or has no load |
| 222 | Port rsp_id[77] in module sparse_tile is either unconnected or has no load |
| 223 | Port rsp_id[76] in module sparse_tile is either unconnected or has no load |
| 224 | Port rsp_id[71] in module sparse_tile is either unconnected or has no load |
| 225 | Port rsp_id[70] in module sparse_tile is either unconnected or has no load |
| 226 | Port rsp_id[65] in module sparse_tile is either unconnected or has no load |
| 227 | Port rsp_id[64] in module sparse_tile is either unconnected or has no load |
| 228 | Port rsp_id[59] in module sparse_tile is either unconnected or has no load |
| 229 | Port rsp_id[58] in module sparse_tile is either unconnected or has no load |
| 230 | Port rsp_id[53] in module sparse_tile is either unconnected or has no load |
| 231 | Port rsp_id[52] in module sparse_tile is either unconnected or has no load |
| 315 | Port rsp_id[149] in module sparse_tile is either unconnected or has no load |
| 316 | Port rsp_id[148] in module sparse_tile is either unconnected or has no load |
| 317 | Port rsp_id[147] in module sparse_tile is either unconnected or has no load |
| 318 | Port rsp_id[146] in module sparse_tile is either unconnected or has no load |
| 319 | Port rsp_id[145] in module sparse_tile is either unconnected or has no load |
| 320 | Port rsp_id[144] in module sparse_tile is either unconnected or has no load |
| 321 | Port rsp_id[95] in module sparse_tile is either unconnected or has no load |
| 322 | Port rsp_id[94] in module sparse_tile is either unconnected or has no load |
| 323 | Port rsp_id[89] in module sparse_tile is either unconnected or has no load |
| 324 | Port rsp_id[88] in module sparse_tile is either unconnected or has no load |
| 325 | Port rsp_id[83] in module sparse_tile is either unconnected or has no load |
| 326 | Port rsp_id[82] in module sparse_tile is either unconnected or has no load |
| 327 | Port rsp_id[77] in module sparse_tile is either unconnected or has no load |
| 328 | Port rsp_id[76] in module sparse_tile is either unconnected or has no load |
| 329 | Port rsp_id[71] in module sparse_tile is either unconnected or has no load |
| 330 | Port rsp_id[70] in module sparse_tile is either unconnected or has no load |
| 331 | Port rsp_id[65] in module sparse_tile is either unconnected or has no load |
| 332 | Port rsp_id[64] in module sparse_tile is either unconnected or has no load |
| 333 | Port rsp_id[59] in module sparse_tile is either unconnected or has no load |
| 334 | Port rsp_id[58] in module sparse_tile is either unconnected or has no load |
| 335 | Port rsp_id[53] in module sparse_tile is either unconnected or has no load |
| 336 | Port rsp_id[52] in module sparse_tile is either unconnected or has no load |

### Vendor INFO [Synth 8-11241]

Vivado2022.2 data/verilog/src/unimacro/BRAM_SINGLE_MACRO.v:2170 references REGCCE in a library branch. The actual library source was inspected. The task does not instantiate BRAM_SINGLE_MACRO; RAM is inferred as RAMB36E2/RAMB18E2. No vendor library is modified, and this INFO is not evidence of an undriven user RTL signal.

Review priorities: retain owner payload/FIFO BRAM mapping; charge bank/output LUTRAM and its port/control cost; inspect routed timing before any clock claim. The current no-go extension gate is derived from service structure, not from warning count.
