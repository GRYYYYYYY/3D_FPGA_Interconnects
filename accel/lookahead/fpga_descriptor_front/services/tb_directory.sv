`timescale 1ns/1ps
module tb_directory;
 logic clk=0;always #5 clk=~clk;
 logic reset=1,cv,cr,rv,rr,initialized;logic[1:0]cop,rop,rstatus;logic[11:0]cbucket,rbucket;logic[31:0]cnode,carg,rnode,rarg;logic[13:0]cptr,rptr,rnext,used,peak;logic[63:0]upper;
 df_directory_bank dut(.*);
 integer fd,n,cy=0;integer ev,er,eop,es,eb,en,ea,ep,ex,eu;logic[63:0]eupper;string vectors;
 initial begin
  cv=0;rr=0;cop=0;cbucket=0;cnode=0;carg=0;cptr=8192;
  if(!$value$plusargs("VECTORS=%s",vectors))vectors="directory.vec";
  fd=$fopen(vectors,"r");if(!fd)$fatal(1,"cannotopen vectors");
  repeat(2)@(posedge clk);@(negedge clk);reset=0;
  while(!$feof(fd))begin
   n=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",cv,cop,cbucket,cnode,carg,cptr,rr,er,ev,eop,es,eb,en,ea,ep,ex,eu,eupper);
   if(n!=18)$fatal(1,"parse cycle%0d n%0d",cy,n);
   #1;
   if(cr!==er[0]||rv!==ev[0]||used!==eu[13:0]||upper!==eupper)$fatal(1,"cycle%0d state ready%0d/%0d rv%0d/%0d used%0d/%0d upper%h/%h",cy,cr,er,rv,ev,used,eu,upper,eupper);
   if(rv&&(rop!==eop[1:0]||rstatus!==es[1:0]||rbucket!==eb[11:0]||rnode!==en||rarg!==ea||rptr!==ep[13:0]||rnext!==ex[13:0]))$fatal(1,"response cycle%0d node%h/%h ptr%h/%h next%h/%h",cy,rnode,en,rptr,ep,rnext,ex);
   @(posedge clk);@(negedge clk);cy=cy+1;
  end
  if(used!=0||peak!=8192)$fatal(1,"drainpeak");
  $display("TEST_PASS DIRECTORY cycles=%0d peak=%0d",cy,peak);$finish;
 end
 initial begin #10000000;$fatal(1,"watchdog");end
endmodule
