`timescale 1ns/1ps
// Reachable-state behavioral miter plus independent cyclic-scan scoreboard.
// No force/deposit. Every pending producer holds its full tuple until accepted,
// except synchronous reset, which explicitly starts a new protocol epoch.
module tb_candidate_wordmux_miter;
 logic clk=0,reset=1;
 logic[63:0] iv=0,ordy=0;
 logic[383:0] dest=0;
 logic[6143:0] idata=0;
 wire[63:0] old_ir,new_ir,old_ov,new_ov;
 wire[6143:0] old_data,new_data;
 df_rr_router reference(.clk,.reset,.iv,.ir(old_ir),.dest,.idata,
  .ov(old_ov),.ordy,.odata(old_data));
 cp_candidate_wordmux_router dut(.clk,.reset,.iv,.ir(new_ir),.dest,.idata,
  .ov(new_ov),.ordy,.odata(new_data));
 logic[63:0] model_ov=0,expected_ir,last_accept=0;
 logic[6143:0] model_data='x;
 integer model_cursor[64],winner[64];
 integer cursor_dest[64][64],input_dest[64][64];
 integer held[64],replaced[64],cleared[64],filled[64],reset_occupied[64];
 logic[95:0] seen_one[64],seen_zero[64];
 logic[63:0] prior_pending=0;
 logic[383:0] prior_dest=0;
 logic[6143:0] prior_data=0;
 integer edges=0,accepted=0,delivered=0,resets=0,wrap_select=0,wrap_cursor=0;
 integer seed=32'h41c64e6d,initial_seed,random_cycles=8000;
 integer phase=0;
 bit initialized=0;

 function automatic logic[31:0] rng();
  seed=seed^(seed<<13);seed=seed^(seed>>17);seed=seed^(seed<<5);
  return seed;
 endfunction
 function automatic logic[95:0] payload(input integer lane,serial);
  // Distinct words and nonzero high bits catch word order and truncation.
  return {32'h80000000^(32'(serial)*32'h9e3779b9)^32'(lane),
          32'h5a5a0000^(32'(serial)<<6)^32'(lane),
          32'ha5a50000^(32'(serial)*32'h01010101)^(32'(lane)<<24)};
 endfunction

 task automatic tick;
  integer o,i,k;
  begin
   #2;
   if(!reset)for(i=0;i<64;i=i+1)if(prior_pending[i])begin
    if(!iv[i]||dest[i*6+:6]!==prior_dest[i*6+:6]||
       idata[i*96+:96]!==prior_data[i*96+:96])
     $fatal(1,"producer changed pending tuple edge=%0d phase=%0d i=%0d",edges,phase,i);
   end
   expected_ir=0;
   for(o=0;o<64;o=o+1)begin
    winner[o]=-1;
    for(k=0;k<64;k=k+1)begin
     i=(model_cursor[o]+k)%64;
     if(winner[o]<0&&iv[i]&&dest[i*6+:6]==o)winner[o]=i;
    end
    if((!model_ov[o]||ordy[o])&&winner[o]>=0)expected_ir[winner[o]]=1;
   end
   if(initialized)begin
    if(old_ir!==new_ir||old_ir!==expected_ir||old_ov!==new_ov||
       old_ov!==model_ov||old_data!==new_data||old_data!==model_data)
     $fatal(1,"pre-edge interface mismatch edge=%0d phase=%0d",edges,phase);
    for(o=0;o<64;o=o+1)begin
     if(reference.cursor[o]!==dut.cursor[o]||reference.cursor[o]!==6'(model_cursor[o])||
        reference.found[o]!==dut.found[o]||reference.selected[o]!==dut.selected[o]||
        reference.found[o]!==1'(winner[o]>=0))
      $fatal(1,"pre-edge arbiter mismatch edge=%0d phase=%0d o=%0d",edges,phase,o);
     if(winner[o]>=0)begin
      if(dut.selected[o]!==6'(winner[o])||
         reference.selected_data[o]!==idata[winner[o]*96+:96]||
         dut.selected_data[o]!==idata[winner[o]*96+:96])
       $fatal(1,"selected payload mismatch edge=%0d o=%0d winner=%0d",edges,o,winner[o]);
     end
    end
   end
   last_accept=reset?64'b0:expected_ir;
   if(reset)begin
    resets=resets+1;
    for(o=0;o<64;o=o+1)begin
     if(model_ov[o])reset_occupied[o]=reset_occupied[o]+1;
     model_cursor[o]=0;
    end
    model_ov=0; // Original odata is not reset, including an occupied reset.
   end else begin
    for(o=0;o<64;o=o+1)begin
     if(model_ov[o]&&ordy[o])delivered=delivered+1;
     if(model_ov[o]&&!ordy[o])held[o]=held[o]+1;
     else begin
      if(winner[o]>=0)begin
       if(model_ov[o])replaced[o]=replaced[o]+1;else filled[o]=filled[o]+1;
       i=winner[o];accepted=accepted+1;
       cursor_dest[o][model_cursor[o]]=cursor_dest[o][model_cursor[o]]+1;
       input_dest[o][i]=input_dest[o][i]+1;
       if(i<model_cursor[o])wrap_select=wrap_select+1;
       if(i==63)wrap_cursor=wrap_cursor+1;
       model_data[o*96+:96]=idata[i*96+:96];
       seen_one[o]=seen_one[o]|idata[i*96+:96];
       seen_zero[o]=seen_zero[o]|~idata[i*96+:96];
       model_cursor[o]=(i+1)%64;
      end else if(model_ov[o])cleared[o]=cleared[o]+1;
      model_ov[o]=(winner[o]>=0);
     end
    end
   end
   prior_pending=reset?64'b0:(iv&~expected_ir);
   prior_dest=dest;prior_data=idata;
   #2;clk=1;#0.1;
   edges=edges+1;initialized=1;
   if(old_ov!==new_ov||old_ov!==model_ov||old_data!==new_data||old_data!==model_data)
    $fatal(1,"post-edge interface mismatch edge=%0d phase=%0d",edges,phase);
   for(o=0;o<64;o=o+1)
    if(reference.cursor[o]!==dut.cursor[o]||dut.cursor[o]!==6'(model_cursor[o]))
     $fatal(1,"post-edge cursor mismatch edge=%0d o=%0d",edges,o);
   #0.9;clk=0;
  end
 endtask

 task automatic drain;
  integer n;
  begin
   ordy='1;n=0;
   while(iv!=0&&n<128)begin tick();iv=iv&~last_accept;n=n+1;end
   if(iv!=0)$fatal(1,"drain timeout");
   tick();tick();
   if(new_ov!=0)$fatal(1,"output not drained");
  end
 endtask

 initial begin : stimulus
  integer i,o,c,b,n;
  logic[31:0] r;
  if($value$plusargs("SEED=%d",seed))begin end
  initial_seed=seed;
  for(o=0;o<64;o=o+1)begin
   model_cursor[o]=0;held[o]=0;replaced[o]=0;cleared[o]=0;filled[o]=0;reset_occupied[o]=0;
   seen_one[o]=0;seen_zero[o]=0;
   for(i=0;i<64;i=i+1)begin cursor_dest[o][i]=0;input_dest[o][i]=0;end
  end
  tick();reset=0;ordy='1;
  repeat(8)tick();
  // 4096 individually accepted source/destination pairs. All 64 cursor values
  // at each destination are reached by normal handshakes, no state backdoor.
  phase=1;
  for(i=0;i<64;i=i+1)for(o=0;o<64;o=o+1)begin
   iv=64'b1<<i;dest[i*6+:6]=6'(o);idata[i*96+:96]=payload(i,i*64+o);
   tick();if(last_accept!==iv)$fatal(1,"single not accepted");iv=0;
  end
  drain();
  // Full 64-way contention, all destinations, exactly one service per input.
  phase=2;
  for(o=0;o<64;o=o+1)begin
   iv='1;
   for(i=0;i<64;i=i+1)begin dest[i*6+:6]=6'(o);idata[i*96+:96]=payload(i,8192+o);end
   for(c=0;c<64;c=c+1)begin
    tick();if(last_accept!==(64'b1<<c))$fatal(1,"RR sweep o=%0d c=%0d",o,c);
    iv=iv&~last_accept;
   end
   drain();
  end
  // Every payload bit individually set and cleared at all 64 destinations.
  // A permutation gives 64 simultaneous independent winners each cycle.
  phase=3;
  for(b=0;b<96;b=b+1)begin
   for(n=0;n<2;n=n+1)begin
    iv='1;
    for(i=0;i<64;i=i+1)begin
     dest[i*6+:6]=6'((i+b)%64);
     idata[i*96+:96]=n?(~(96'b1<<b)):(96'b1<<b);
    end
    tick();if(last_accept!=='1)$fatal(1,"parallel bit sweep blocked");iv=0;
   end
  end
  drain();
  // Fill while downstream not ready, then hold all outputs with new requests
  // pending, consume+replace at all outputs and reset occupied/stalled holds.
  phase=4;
  iv='1;ordy=0;
  for(i=0;i<64;i=i+1)begin dest[i*6+:6]=6'(i);idata[i*96+:96]=payload(i,12000);end
  tick();if(last_accept!=='1)$fatal(1,"empty hold must load without ordy");
  for(i=0;i<64;i=i+1)idata[i*96+:96]=payload(i,12001);
  repeat(17)begin tick();if(last_accept!=0)$fatal(1,"blocked accept");end
  ordy='1;tick();if(last_accept!=='1)$fatal(1,"consume replace bubble");iv=0;
  // Synchronous reset retains the last data while invalidating all holds.
  ordy=0;reset=1;tick();tick();reset=0;iv=0;tick();
  drain();
  // Deterministic seeded valid/ready traffic, maintaining pending tuples.
  // Long global congestion, hotspot, sparse and permutation destinations;
  // periodic reset while occupied covers a fresh epoch with pending inputs.
  phase=5;
  for(n=0;n<random_cycles;n=n+1)begin
   if(n!=0&&n%997==0)begin reset=1;tick();reset=0;iv=0;end
   for(i=0;i<64;i=i+1)begin
    r=rng();ordy[i]=(n%127>=19)&&(r[2:0]<3);
    if(!iv[i])begin
     r=rng();iv[i]=(r[2:0]!=0);
     if(iv[i])begin
      r=rng();
      case((n/137)%3)
       0:dest[i*6+:6]=6'((n/137)%64);
       1:dest[i*6+:6]=r[5:0];
       2:dest[i*6+:6]=6'((i+n/137)%64);
      endcase
      idata[i*96+:96]={rng(),rng(),rng()};
     end
    end
   end
   tick();iv=iv&~last_accept;
  end
  drain();phase=6;
  for(o=0;o<64;o=o+1)begin
   for(i=0;i<64;i=i+1)
    if(cursor_dest[o][i]==0||input_dest[o][i]==0)
     $fatal(1,"missing cursor/source destination coverage o=%0d i=%0d",o,i);
   if(held[o]==0||replaced[o]==0||cleared[o]==0||filled[o]==0||reset_occupied[o]==0||
      seen_one[o]!=='1||seen_zero[o]!=='1)$fatal(1,"missing behavioral coverage o=%0d",o);
  end
  if(wrap_select==0||wrap_cursor==0)$fatal(1,"missing wrap coverage");
  $display("COVERAGE cursor_dest=4096/4096 input_dest=4096/4096 payload_bit_value_dest=12288/12288 per_output_hold_replace_clear_fill_reset=64/64");
  $display("MITER_EDGES %0d accepted=%0d delivered=%0d resets=%0d wrap_select=%0d wrap_cursor=%0d seed=%0d",edges,accepted,delivered,resets,wrap_select,wrap_cursor,initial_seed);
  $display("TEST_PASS tb_candidate_wordmux_miter");$finish;
 end
 initial begin #2000000;$fatal(1,"watchdog phase=%0d edge=%0d",phase,edges);end
endmodule
