`timescale 1ns/1ps
module append_interval_env #(parameter MODE=0)(output reg finished=0);
 reg clk=0;always #2.5 clk=~clk;reg reset=1;wire cr,rv,initialized;reg cv=0;wire[1:0]rop,status;wire[11:0]bucket;wire[31:0]node,arg;wire[13:0]ptr,next_ptr,used,peak;wire[63:0]upper;
 integer cycle=0,sent=0,acked=0,last_accept=-1,last_ack=-1,min_ii=100,max_ii=0,min_ri=100,max_ri=0,fd;reg[1:0]wrapper=0;
 wire rr=1;wire[11:0]cbucket=(sent%3==1)?12'd1:12'd0;
 generate if(MODE==2)begin
  lf_directory d(.clk,.reset,.cv,.cr,.cop(2'b0),.cbucket,.cnode(32'(sent)),.carg(32'(sent)),.cptr(14'd8192),.rv,.rr,.rop,.rstatus(status),.rbucket(bucket),.rnode(node),.rarg(arg),.rptr(ptr),.rnext(next_ptr),.initialized,.drained(),.used,.peak,.upper,.ram_visible(),.visible_ptr());
 end else begin
  df_directory_bank d(.clk,.reset,.cv,.cr,.cop(2'b0),.cbucket,.cnode(32'(sent)),.carg(32'(sent)),.cptr(14'd8192),.rv,.rr,.rop,.rstatus(status),.rbucket(bucket),.rnode(node),.rarg(arg),.rptr(ptr),.rnext(next_ptr),.initialized,.used,.peak,.upper);
 end endgenerate
 always @(posedge clk)if(!reset)begin
  cycle=cycle+1;if(cycle>15000)$fatal(1,"INTERVAL_TIMEOUT");
  if(cv&&cr)begin
   if(last_accept>=0)begin if(cycle-last_accept<min_ii)min_ii=cycle-last_accept;if(cycle-last_accept>max_ii)max_ii=cycle-last_accept;end
   last_accept=cycle;$fdisplay(fd,"%0d,command,%0d",cycle,sent);sent=sent+1;if(MODE==1)wrapper=1;
  end
  if(rv&&rr)begin
   if(status!=0)$fatal(1,"APPEND_STATUS");
   if(last_ack>=0)begin if(cycle-last_ack<min_ri)min_ri=cycle-last_ack;if(cycle-last_ack>max_ri)max_ri=cycle-last_ack;end
   last_ack=cycle;$fdisplay(fd,"%0d,ACK,%0d",cycle,acked);acked=acked+1;
  end
 end
 // The baseline model's deferred wrapper has two feedback/control edges after
 // event ACK before the next command. This is an explicit reconstruction, not
 // a claim that the historical externally-stalled native test had this bank.
 always @(negedge clk)begin
  if(MODE==1)begin if(wrapper==3)wrapper=0;else if(wrapper==2)wrapper=3;else if(wrapper==1&&acked==sent)wrapper=2;end
  cv=!reset&&initialized&&sent<128&&(MODE!=1||wrapper==0);
 end
 initial begin
  fd=$fopen($sformatf("append_interval_%0d.csv",MODE),"w");$fdisplay(fd,"cycle,event,sequence");repeat(5)@(negedge clk);reset=0;
  wait(acked==128);@(negedge clk);
  if(sent!=128||used!=128||min_ii!=(MODE==0?6:MODE==1?8:2)||max_ii!=min_ii||min_ri!=min_ii||max_ri!=min_ii)$fatal(1,"INTERVAL_MISMATCH mode=%0d II=%0d/%0d RI=%0d/%0d",MODE,min_ii,max_ii,min_ri,max_ri);
  $display("APPEND_INTERVAL_PASS mode=%0d accepts128 ACK128 II=%0d retire_interval=%0d",MODE,min_ii,min_ri);$fclose(fd);finished=1;
 end
endmodule
module tb_append_intervals;
 wire a,b,c;append_interval_env #(.MODE(0))old_bank(a);append_interval_env #(.MODE(1))old_wrapper(b);append_interval_env #(.MODE(2))new_bank(c);
 initial begin wait(a&&b&&c);$display("TEST_PASS APPEND old_leaf_II6 reconstructed_old_wrapper_II8 new_actual_RAM_II2");$finish;end
endmodule
