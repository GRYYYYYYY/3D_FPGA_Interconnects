`timescale 1ns/1ps
module enum_tb;
 reg clk=0;always #2.5 clk=~clk;reg reset=1;integer cyc=0;
 wire [1:0] complete;integer trace,ticks;
 initial begin trace=$fopen("enum_trace.csv","w");ticks=$fopen("enum_ticks.csv","w");$fwrite(ticks,"time_ps,variant,reset,flush,iv,ir,node,pair,fv,fr,line,pairs,done,scan,scan_index,fifo_occupancy\n");$fwrite(trace,"time_ps,variant,wave,event,line,flag,data\n");end
 always @(posedge clk)begin cyc=cyc+1;if(cyc>30000)$fatal(1,"enum watchdog");end
 initial begin repeat(4)@(negedge clk);reset=0;wait(&complete);$display("TEST_PASS enum old/new full ways two waves backpressure");$finish;end
 for(genvar v=0;v<2;v=v+1)begin:g
  reg iv=0,flush=0;wire ir,done,fv,ff;wire fr;reg[31:0] node=0;reg[63:0] pair;
  wire scan_launch;wire[31:0] scan_index;wire[4:0] fifo_used;
  wire[31:0] line,accepted,retired,spill_count,enumerated;wire[3:0] mask;wire[255:0] pairs;
  reg finished=0;integer limit=64,wave=0,sent=0,count=0,total=0,j=0,k=0,last=-1,start=0,first=0,tail=0;reg [63:0] seen;
  assign complete[v]=finished;
  assign fr=wave!=1?1:((cyc-start>150)&&(cyc%13>=5));
  if(v==0)begin:o
   assign scan_launch=0;assign scan_index=0;assign fifo_used=0;
   inf_flat_bank #(.SET_BITS(4)) dut(.clk,.reset,.in_valid(iv),.in_ready(ir),.in_node(node),.in_pair(pair),.flush,.done,.frag_valid(fv),.frag_ready(fr),.frag_line(line),.frag_mask(mask),.frag_pairs(pairs),.frag_final(ff),.accepted,.retired,.spill_count,.enumerated);
  end else begin:n
   assign scan_launch=dut.enum_launch;assign scan_index=dut.enum_index;assign fifo_used=dut.fifo_occupancy;
   enum2_bank #(.SET_BITS(4)) dut(.clk,.reset,.in_valid(iv),.in_ready(ir),.in_node(node),.in_pair(pair),.flush,.done,.frag_valid(fv),.frag_ready(fr),.frag_line(line),.frag_mask(mask),.frag_pairs(pairs),.frag_final(ff),.accepted,.retired,.spill_count,.enumerated);
  end
  reg previous_done=0;
  always @(posedge clk)begin
   if(!finished)$fwrite(ticks,"%0t,%0d,%b,%b,%b,%b,%h,%h,%b,%b,%h,%h,%b,%b,%h,%h\n",$time,v,reset,flush,iv,ir,node,pair,fv,fr,line,pairs,done,scan_launch,scan_index,fifo_used);
   if(!reset&&iv&&ir)$fwrite(trace,"%0t,%0d,%0d,accept,%h,0,%h\n",$time,v,wave,node,pair);
   if(!reset&&fv&&fr)$fwrite(trace,"%0t,%0d,%0d,fragment,%h,%h,%h\n",$time,v,wave,line,mask,pairs);
   if(!reset&&done&&!previous_done)$fwrite(trace,"%0t,%0d,%0d,done,0,0,0\n",$time,v,wave);
   previous_done<=done;
  end
  if(v==1)begin:scan_monitor
   always @(posedge clk)if(!reset&&enum_tb.g[1].n.dut.enum_launch)$fwrite(trace,"%0t,1,%0d,scan,%h,0,0\n",$time,wave,enum_tb.g[1].n.dut.enum_index);
   always @(posedge clk)if(!reset&&enum_tb.g[1].n.dut.fifo_occupancy>16)$fatal(1,"fragment fifo overflow");
  end
  always @(posedge clk)if(fv&&fr)begin
   j=line/64;
   if(line%64||j<0||j>=64||seen[j]||!ff)$fatal(1,"enum fragment v=%0d wave=%0d line=%h",v,wave,line);
   if(mask!==(4'b1<<(j%4)))$fatal(1,"enum mask v=%0d j=%0d got=%h",v,j,mask);
   for(k=0;k<4;k=k+1)if(pairs[k*64+:64]!==((k==j%4)?(64'h3f80000040000000+j):64'h7f8000007f800000))$fatal(1,"enum payload v=%0d line=%h sec=%0d actual=%h",v,line,k,pairs[k*64+:64]);
   if(count==0)first=cyc;
   if(wave==0&&last>=0&&cyc-last!=(v==0?5:2))$fatal(1,"enum interval v=%0d dt=%0d",v,cyc-last);
   last=cyc;seen[j]=1;count=count+1;total=total+1;
  end
  initial begin
   wait(!reset);
   for(wave=0;wave<4;wave=wave+1)begin
    sent=0;count=0;seen=0;last=-1;limit=wave==2?0:(wave==3?1:64);
    while(sent<limit)begin
     @(negedge clk);iv=1;node=sent*256+sent%4;pair=64'h3f80000040000000+sent;
     @(posedge clk);if(ir)sent=sent+1;
    end
    @(negedge clk);iv=0;flush=1;start=cyc;
    wait(done);@(negedge clk);
    if(count!=limit||seen!==((limit==64)?64'hffffffffffffffff:((64'b1<<limit)-1)))$fatal(1,"enum coverage v=%0d count=%0d",v,count);
    $display("ENUM_RESULT variant=%0d wave=%0d first=%0d last=%0d done=%0d elapsed=%0d accepted=%0d",v,wave,first,last,cyc,cyc-start,accepted);
    flush=0;repeat(5)@(negedge clk);
   end
   if(total!=129||accepted!=129||retired!=129||enumerated!=129||spill_count!=0)$fatal(1,"enum conservation v=%0d",v);
   finished=1;
  end
 end
endmodule
