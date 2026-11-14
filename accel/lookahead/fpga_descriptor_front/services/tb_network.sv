`timescale 1ns/1ps
module tb_network;
 localparam NS=8,NP=2,ID_W=32;
 logic clk=0;always #5 clk=~clk;logic reset=1;
 logic[NS-1:0]cv,cr,cw,rv,rr;logic[NS*2-1:0]cclass;logic[NS*32-1:0]cl,cid,rid;logic[NS*256-1:0]cd,rd;
 logic[NP-1:0]mv,mr,mw,sv,sr,port_error;logic[NP*32-1:0]ml;logic[NP*5-1:0]mtag,stag;logic[NP*256-1:0]md,sd;
 df_memory_network #(.SOURCES(NS),.PORTS(NP),.ID_W(ID_W))dut(.*);
 integer fd,n,cy=0,s,p;string vectors;logic[63:0]data,retdata;
 integer ecr[NS],erv[NS];logic[31:0]erid[NS];logic[63:0]erd[NS];
 integer emv[NP],emw[NP],emt[NP],esr[NP];logic[31:0]eml[NP];logic[63:0]emd[NP];
 initial begin
  cv=0;cw=0;cl=0;cid=0;cd=0;rr=0;mr=0;sv=0;stag=0;sd=0;
  for(s=0;s<NS;s=s+1)cclass[s*2+:2]=s/2;
  if(!$value$plusargs("VECTORS=%s",vectors))vectors="network.vec";fd=$fopen(vectors,"r");if(!fd)$fatal(1,"no vectors");
  repeat(2)@(posedge clk);@(negedge clk);reset=0;
  while(!$feof(fd))begin
   for(s=0;s<NS;s=s+1)begin
    n=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h ",cv[s],cw[s],cl[s*32+:32],cid[s*32+:32],data,rr[s],ecr[s],erv[s],erid[s],erd[s]);if(n!=10)$fatal(1,"parse source cycle%0d",cy);cd[s*256+:256]={4{data}};
   end
   for(p=0;p<NP;p=p+1)begin
    n=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h ",mr[p],sv[p],stag[p*5+:5],data,emv[p],emw[p],eml[p],emt[p],emd[p],esr[p]);if(n!=10)$fatal(1,"parse port");sd[p*256+:256]={4{data}};
   end
   #1;
   if(port_error!=0)$fatal(1,"porterror cycle%0d",cy);
   for(s=0;s<NS;s=s+1)begin
    if(cr[s]!==ecr[s][0]||rv[s]!==erv[s][0])$fatal(1,"cycle%0d source%0d cr%0d/%0d rv%0d/%0d",cy,s,cr[s],ecr[s],rv[s],erv[s]);
    if(rv[s]&&(rid[s*32+:32]!==erid[s]||rd[s*256+:256]!=={4{erd[s]}}))$fatal(1,"returnpayload cycle%0d source%0d id%h/%h",cy,s,rid[s*32+:32],erid[s]);
   end
   for(p=0;p<NP;p=p+1)begin
    if(mv[p]!==emv[p][0]||sr[p]!==esr[p][0])$fatal(1,"cycle%0d port%0d mv%0d/%0d sr%0d/%0d",cy,p,mv[p],emv[p],sr[p],esr[p]);
    if(mv[p]&&(mw[p]!==emw[p][0]||ml[p*32+:32]!==eml[p]||mtag[p*5+:5]!==emt[p][4:0]||md[p*256+:256]!=={4{emd[p]}}))$fatal(1,"physicalpayload cycle%0d port%0d line%h/%h tag%h/%h",cy,p,ml[p*32+:32],eml[p],mtag[p*5+:5],emt[p]);
   end
   @(posedge clk);@(negedge clk);cy=cy+1;
  end
  $display("TEST_PASS NETWORK cycles=%0d",cy);$finish;
 end
 initial begin #10000000;$fatal(1,"watchdog");end
endmodule
