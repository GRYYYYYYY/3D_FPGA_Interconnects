`timescale 1ns/1ps
// Verification-only interposer for the Vitis 2022.2 AESL functional RAM.
// A bank transfers one R or W beat per PERIOD clocks, with held grants under
// backpressure. Ports map round-robin to BANKS. This is a synthetic bound,
// NOT a board-calibrated DDR/HBM controller. Data/address channels pass through.
module la_bounded_axi #(
  parameter PORTS=4, BANKS=1, PERIOD=4, CREDITS=2, MIN_READ_LATENCY=1,
  parameter TOTAL_READ_CREDITS=8, TOTAL_WRITE_CREDITS=8,
  parameter MAX_CYCLES=200000000, DATA_BITS=512, ID_BITS=32
)(
  input wire clk, reset_n, finish,
  input wire [PORTS-1:0] arvalid, mem_arready, awvalid, mem_awready,
  input wire [PORTS-1:0] mem_rvalid, rready, wvalid, mem_wready,
  input wire [PORTS-1:0] mem_rlast, wlast, bvalid, bready,
  input wire [PORTS*DATA_BITS-1:0] mem_rdata,
  input wire [PORTS*ID_BITS-1:0] mem_rid,
  input wire [PORTS*2-1:0] mem_rresp,
  input wire [8*PORTS-1:0] arlen, awlen,
  output wire [PORTS-1:0] arready, mem_arvalid, awready, mem_awvalid,
  output wire [PORTS-1:0] rvalid, mem_rready, wready, mem_wvalid,
  output reg [PORTS-1:0] rlast,
  output reg [PORTS*DATA_BITS-1:0] rdata,
  output reg [PORTS*ID_BITS-1:0] rid,
  output reg [PORTS*2-1:0] rresp,
  output reg drained
);
  integer reads[PORTS], writes[PORTS], rpeak[PORTS], wpeak[PORTS];
  integer rr[BANKS], held[BANKS], cooldown[BANKS], chosen[BANKS];
  integer last_transfer[BANKS];
  integer read_head[PORTS], read_tail[PORTS], write_head[PORTS], write_tail[PORTS];
  integer read_left[PORTS][CREDITS], write_left[PORTS][CREDITS];
  integer read_at[PORTS][CREDITS];
  integer read_beats[PORTS], write_beats[PORTS], read_requests[PORTS], write_requests[PORTS];
  integer read_stalls[PORTS], write_stalls[PORTS], credit_stalls[PORTS];
  integer cycle=0, reported=0, done_cycle=-1, last_activity=0, fd;
  reg [PORTS-1:0] grant_r, grant_w;
  reg [PORTS-1:0] pending_r, pending_w;
  reg [PORTS-1:0] read_buffer_valid;
  reg [PORTS-1:0] permit_ar, permit_aw, held_ar, held_aw;
  integer admit_rr=0, sum_reads, sum_writes, reserved_reads, reserved_writes;
  integer free_reads, free_writes, admit_port, total_rpeak=0, total_wpeak=0;
  integer b, p, k, candidate;

  initial begin
    if(PORTS<1 || BANKS<1 || BANKS>PORTS || PERIOD<1 || CREDITS<1)
      $fatal(1,"invalid bounded memory configuration");
  end
  genvar g;
  generate for(g=0;g<PORTS;g=g+1) begin
    assign mem_arvalid[g] = arvalid[g] && permit_ar[g];
    assign arready[g] = mem_arready[g] && permit_ar[g];
    assign mem_awvalid[g] = awvalid[g] && permit_aw[g];
    assign awready[g] = mem_awready[g] && permit_aw[g];
    // Each return port owns one finite skid slot. Holding a blocked consumer's
    // RVALID must not reserve the shared bank and deadlock other read ports.
    assign rvalid[g] = read_buffer_valid[g];
    assign mem_rready[g] = (!read_buffer_valid[g] || rready[g]) && grant_r[g];
    assign mem_wvalid[g] = wvalid[g] && grant_w[g];
    assign wready[g] = mem_wready[g] && grant_w[g];
  end endgenerate

  // Admission reserves a global credit even while the RAM holds AR/AWREADY low.
  // This keeps VALID asserted and prevents simultaneous ports exceeding the pool.
  always @* begin
    sum_reads=0;sum_writes=0;reserved_reads=0;reserved_writes=0;
    for(integer j=0;j<PORTS;j=j+1) begin
      sum_reads=sum_reads+reads[j];sum_writes=sum_writes+writes[j];
      reserved_reads=reserved_reads+held_ar[j];reserved_writes=reserved_writes+held_aw[j];
    end
    free_reads=TOTAL_READ_CREDITS-sum_reads-reserved_reads;
    free_writes=TOTAL_WRITE_CREDITS-sum_writes-reserved_writes;
    permit_ar=held_ar;permit_aw=held_aw;
    for(integer j=0;j<PORTS;j=j+1) begin
      admit_port=(admit_rr+j)%PORTS;
      if(!held_ar[admit_port] && arvalid[admit_port] && reads[admit_port]<CREDITS && free_reads>0) begin
        permit_ar[admit_port]=1;free_reads=free_reads-1;
      end
      if(!held_aw[admit_port] && awvalid[admit_port] && writes[admit_port]<CREDITS && free_writes>0) begin
        permit_aw[admit_port]=1;free_writes=free_writes-1;
      end
    end
  end

  always @* begin
    grant_r=0; grant_w=0; drained=1;
    for(integer j=0;j<PORTS;j=j+1)
      if(reads[j]!=0 || writes[j]!=0) drained=0;
    for(integer bank=0;bank<BANKS;bank=bank+1) begin
      chosen[bank]=held[bank];
      if(held[bank]<0 && cooldown[bank]==0) begin
        for(integer offset=0;offset<2*PORTS;offset=offset+1) begin
          // candidate even=read, odd=write. Only this bank's ports compete.
          candidate=(rr[bank]+offset)%(2*PORTS);
          if(chosen[bank]<0 && (candidate/2)%BANKS==bank &&
             ((candidate%2==0 && mem_rvalid[candidate/2] &&
               (!read_buffer_valid[candidate/2] || rready[candidate/2])) ||
              (candidate%2==1 && wvalid[candidate/2] &&
               write_head[candidate/2]<write_tail[candidate/2])))
            chosen[bank]=candidate;
        end
      end
      if(chosen[bank]>=0) begin
        if(chosen[bank]%2==0) grant_r[chosen[bank]/2]=1;
        else grant_w[chosen[bank]/2]=1;
      end
    end
  end

  always @(posedge clk) begin
    if(!reset_n) begin
      cycle<=0; reported<=0; done_cycle<=-1; last_activity<=0;
      pending_r<=0; pending_w<=0; read_buffer_valid<=0;
      held_ar<=0;held_aw<=0;admit_rr<=0;total_rpeak<=0;total_wpeak<=0;
      for(p=0;p<PORTS;p=p+1) begin
        reads[p]<=0; writes[p]<=0; rpeak[p]<=0; wpeak[p]<=0;
        read_head[p]<=0; read_tail[p]<=0; write_head[p]<=0; write_tail[p]<=0;
        read_beats[p]<=0; write_beats[p]<=0; read_requests[p]<=0; write_requests[p]<=0;
        read_stalls[p]<=0; write_stalls[p]<=0; credit_stalls[p]<=0;
      end
      for(b=0;b<BANKS;b=b+1) begin
        rr[b]<=0; held[b]<=-1; cooldown[b]<=0; last_transfer[b]<=-PERIOD;
      end
    end else begin
      cycle<=cycle+1;
      admit_rr<=(admit_rr+1)%PORTS;
      held_ar<=permit_ar & arvalid & ~mem_arready;
      held_aw<=permit_aw & awvalid & ~mem_awready;
      if(sum_reads+reserved_reads>TOTAL_READ_CREDITS || sum_writes+reserved_writes>TOTAL_WRITE_CREDITS)
        $fatal(1,"global credit pool exceeded");
      if(sum_reads>total_rpeak)total_rpeak<=sum_reads;
      if(sum_writes>total_wpeak)total_wpeak<=sum_writes;
      if(cycle>MAX_CYCLES) $fatal(1,"bounded memory watchdog");
      if(cycle%1000000==0) $display("BOUNDED_MEMORY_PROGRESS cycle=%0d",cycle);
      for(b=0;b<BANKS;b=b+1) begin
        if(cooldown[b]>0) cooldown[b]<=cooldown[b]-1;
        if(chosen[b]>=0) begin
          k=chosen[b]/2;
          if((chosen[b]%2==0 && mem_rvalid[k] && mem_rready[k]) ||
             (chosen[b]%2==1 && mem_wvalid[k] && mem_wready[k])) begin
            if(cycle-last_transfer[b]<PERIOD) $fatal(1,"bank bandwidth exceeded");
            last_transfer[b]<=cycle; last_activity<=cycle;
            held[b]<=-1; rr[b]<=(chosen[b]+1)%(2*PORTS); cooldown[b]<=PERIOD-1;
          end else held[b]<=chosen[b];
        end
      end
      for(p=0;p<PORTS;p=p+1) begin
        if(mem_rvalid[p] && mem_rready[p]) begin
          read_buffer_valid[p]<=1;
          rdata[p*DATA_BITS+:DATA_BITS]<=mem_rdata[p*DATA_BITS+:DATA_BITS];
          rid[p*ID_BITS+:ID_BITS]<=mem_rid[p*ID_BITS+:ID_BITS];
          rresp[p*2+:2]<=mem_rresp[p*2+:2]; rlast[p]<=mem_rlast[p];
        end else if(rvalid[p] && rready[p]) read_buffer_valid[p]<=0;
        if(pending_r[p] && !rvalid[p]) $fatal(1,"RVALID lost while stalled");
        if(pending_w[p] && !mem_wvalid[p]) $fatal(1,"WVALID lost while stalled");
        pending_r[p]<=rvalid[p] && !rready[p];
        pending_w[p]<=mem_wvalid[p] && !mem_wready[p];
        if(reads[p]<0 || reads[p]>CREDITS || writes[p]<0 || writes[p]>CREDITS)
          $fatal(1,"outstanding credit violation");
        if(reads[p]>rpeak[p]) rpeak[p]<=reads[p];
        if(writes[p]>wpeak[p]) wpeak[p]<=writes[p];
        reads[p]<=reads[p]+(arvalid[p] && arready[p])-(rvalid[p] && rready[p] && rlast[p]);
        writes[p]<=writes[p]+(awvalid[p] && awready[p])-(bvalid[p] && bready[p]);
        if(arvalid[p] && arready[p]) begin
          read_left[p][read_tail[p]%CREDITS]<=1+arlen[p*8+:8];
          read_at[p][read_tail[p]%CREDITS]<=cycle;
          read_tail[p]<=read_tail[p]+1; read_requests[p]<=read_requests[p]+1;
        end
        if(awvalid[p] && awready[p]) begin
          write_left[p][write_tail[p]%CREDITS]<=1+awlen[p*8+:8];
          write_tail[p]<=write_tail[p]+1; write_requests[p]<=write_requests[p]+1;
        end
        if(rvalid[p] && rready[p]) begin
          k=read_head[p]%CREDITS;
          if(reads[p]==0 || rlast[p]!=(read_left[p][k]==1)) $fatal(1,"read burst mismatch");
          if(cycle-read_at[p][k]<MIN_READ_LATENCY) $fatal(1,"read latency below bound");
          read_left[p][k]<=read_left[p][k]-1;
          if(rlast[p]) read_head[p]<=read_head[p]+1;
          read_beats[p]<=read_beats[p]+1;
        end
        if(mem_wvalid[p] && mem_wready[p]) begin
          k=write_head[p]%CREDITS;
          if(wlast[p]!=(write_left[p][k]==1)) $fatal(1,"write burst mismatch");
          write_left[p][k]<=write_left[p][k]-1;
          if(wlast[p]) write_head[p]<=write_head[p]+1;
          write_beats[p]<=write_beats[p]+1;
        end
        if(bvalid[p] && bready[p]) begin
          if(writes[p]==0) $fatal(1,"write response without request");
          last_activity<=cycle;
        end
        if(mem_rvalid[p] && !mem_rready[p]) read_stalls[p]<=read_stalls[p]+1;
        if(wvalid[p] && !wready[p]) write_stalls[p]<=write_stalls[p]+1;
        if(held_ar[p] && !arvalid[p])$fatal(1,"ARVALID lost while reserved");
        if(held_aw[p] && !awvalid[p])$fatal(1,"AWVALID lost while reserved");
        if((arvalid[p] && !permit_ar[p]) || (awvalid[p] && !permit_aw[p]))
          credit_stalls[p]<=credit_stalls[p]+1;
      end
      if(finish && done_cycle<0) done_cycle<=cycle;
      if(finish && drained && !reported) begin
        fd=$fopen("bounded_memory.json","w");
        $fdisplay(fd,"{\"cycle\":%0d,\"done_observed\":%0d,\"last_activity\":%0d,\"max_total_reads\":%0d,\"max_total_writes\":%0d,\"drained\":true,\"ports\":[",cycle,done_cycle<0?cycle:done_cycle,last_activity,total_rpeak,total_wpeak);
        for(p=0;p<PORTS;p=p+1)
          $fdisplay(fd,"{\"port\":%0d,\"reads\":%0d,\"writes\":%0d,\"read_beats\":%0d,\"write_beats\":%0d,\"read_stall_cycles\":%0d,\"write_stall_cycles\":%0d,\"credit_stall_cycles\":%0d,\"max_reads\":%0d,\"max_writes\":%0d}%s",p,read_requests[p],write_requests[p],read_beats[p],write_beats[p],read_stalls[p],write_stalls[p],credit_stalls[p],rpeak[p],wpeak[p],p==PORTS-1?"":",");
        $fdisplay(fd,"]}"); $fclose(fd); reported<=1;
        $display("BOUNDED_MEMORY_PASS cycles=%0d",cycle);
      end
    end
  end
endmodule
