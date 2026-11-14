`timescale 1ns/1ps
module tb_port_stress;
 reg clk=0;always #2.5 clk=~clk;reg reset=1;
 reg [3:0] cv=0,cw=0,rr=0;wire [3:0] cr,rv;reg [127:0] cl=0;reg [43:0] cid=0;reg [1023:0] cd=0;wire [43:0] rid;wire [1023:0] rd;
 wire mv,mw,sr,idle,error;reg mr=0,sv=0;wire [31:0] ml;wire [4:0] mtag;wire [255:0] md;reg [4:0] stag=0;reg [255:0] sd=0;wire [5:0] credits_used,peak_credits;wire [31:0] client_accepted,physical_issued,physical_returned,client_returned;
 wire c_mv,c_mr,c_mw,c_sv,c_sr;wire [31:0] c_ml;wire [4:0] c_mtag,c_stag;wire [255:0] c_md,c_sd;wire request_empty,response_empty,core_idle;
 ec_tagged_port dut(.clk,.reset,.cv,.cr,.cw,.cl,.cid,.cd,.rv,.rr,.rid,.rd,.mv(c_mv),.mr(c_mr),.mw(c_mw),.ml(c_ml),.mtag(c_mtag),.md(c_md),.sv(c_sv),.sr(c_sr),.stag(c_stag),.sd(c_sd),.idle(core_idle),.error,.credits_used,.peak_credits,.client_accepted,.physical_issued,.physical_returned,.client_returned);
 df_fifo2 #(.WIDTH(294)) request(.clk,.reset,.iv(c_mv),.ir(c_mr),.id({c_mw,c_ml,c_mtag,c_md}),.ov(mv),.ordy(mr),.od({mw,ml,mtag,md}),.empty(request_empty));
 df_fifo2 #(.WIDTH(261)) response(.clk,.reset,.iv(sv),.ir(sr),.id({stag,sd}),.ov(c_sv),.ordy(c_sr),.od({c_stag,c_sd}),.empty(response_empty));
 assign idle=core_idle&&request_empty&&response_empty;
 integer slicefile;integer cycle=0,sent[4],received[4],sel,k,tracefile;
 reg [31:0] pending=0;reg [255:0] data[32];integer due[32];reg [511:0] seen[4];string dir;
 reg hit_qfull=0,hit_backfull=0,hit_credits=0;integer reverse_returns=0;
 reg held_response=0;always @(posedge clk)held_response<=!reset&&sv&&!sr;
 always @(negedge clk)begin
  if(!reset)begin
   for(integer c=0;c<4;c=c+1)begin
    cv[c]=sent[c]<512;cw[c]=sent[c]%2;cl[c*32+:32]=(c*4096+sent[c])*32;cid[c*11+:11]=sent[c];cd[c*256+:256]={8{32'h01230000+c*4096+sent[c]}};
   end
   mr=cycle>=100&&(cycle%29<23);rr=cycle<350?0:4'(15^(cycle%4==0?1<<((cycle/4)%4):0));
   if(!held_response)begin sv=0;sel=-1;
   for(integer j=0;j<32;j=j+1)if(pending[j]&&due[j]<=cycle+1&&(sel<0||due[j]>due[sel]))sel=j;
   if(sel>=0)begin sv=1;stag=sel;sd=data[sel];end end
  end
 end
 wire [127:0] clean_cl;wire [43:0] clean_cid,clean_rid;wire [1023:0] clean_cd,clean_rd;
 for(genvar c=0;c<4;c=c+1)begin
  assign clean_cl[c*32+:32]=cv[c]?cl[c*32+:32]:0;
  assign clean_cid[c*11+:11]=cv[c]?cid[c*11+:11]:0;
  assign clean_cd[c*256+:256]=cv[c]?cd[c*256+:256]:0;
  assign clean_rid[c*11+:11]=rv[c]?rid[c*11+:11]:0;
  assign clean_rd[c*256+:256]=rv[c]?rd[c*256+:256]:0;
 end
 always @(posedge clk)begin
  cycle=cycle+1;
  if(cycle>20000)$fatal(1,"watchdog");
  if(!reset)begin
   $fdisplay(slicefile,"%0d,request,0,294,%h,%h,%h,%h,%h,%h,%h",cycle,request.iv,request.ir,request.iv?request.id:294'b0,request.ov,request.ordy,request.ov?request.od:294'b0,request.empty);
   $fdisplay(slicefile,"%0d,response,0,261,%h,%h,%h,%h,%h,%h,%h",cycle,response.iv,response.ir,response.iv?response.id:261'b0,response.ov,response.ordy,response.ov?response.od:261'b0,response.empty);
   $fdisplay(tracefile,"%0d,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h",cycle,cv,cr&cv,cw&cv,clean_cl,clean_cid,clean_cd,rv,rr,clean_rid,clean_rd,c_mv,c_mr,c_mv?c_mw:1'b0,c_mv?c_ml:32'b0,c_mv?c_mtag:5'b0,c_mv?c_md:256'b0,c_sv,c_sr,c_sv?c_stag:5'b0,c_sv?c_sd:256'b0,dut.cursor);
   for(integer c=0;c<4;c=c+1)begin
    if(cv[c]&&cr[c])sent[c]=sent[c]+1;
    if(rv[c]&&rr[c])begin
     k=rid[c*11+:11];if(k>=512||k>=sent[c]||seen[c][k])$fatal(1,"duplicate/unknown client localID");
     if(rd[c*256+:256]!==({8{32'h01230000+c*4096+k}}^256'h1234))$fatal(1,"response payload routing");seen[c][k]=1;received[c]=received[c]+1;
    end
   end
   if(sv&&sr)begin
    if(!pending[stag])$fatal(1,"unknown physicaltag");
    for(integer j=0;j<32;j=j+1)if(pending[j]&&due[j]<due[stag])reverse_returns=reverse_returns+1;
    pending[stag]=0;
   end
   if(mv&&mr)begin if(pending[mtag])$fatal(1,"physicaltag reused");pending[mtag]=1;data[mtag]=md^256'h1234;due[mtag]=cycle+16+(cycle*7+mtag)%9;end
   if(credits_used==32)hit_credits=1;
   if(dut.return_count==4)hit_backfull=1;
   if(dut.qcount[0]==4&&dut.qcount[1]==4&&dut.qcount[2]==4&&dut.qcount[3]==4)hit_qfull=1;
   if(error)$fatal(1,"fabricerror");
   if(received[0]==512&&received[1]==512&&received[2]==512&&received[3]==512&&idle)begin
    if(!hit_qfull||!hit_backfull||!hit_credits||pending!=0||client_accepted!=2048||physical_issued!=2048||physical_returned!=2048||client_returned!=2048||reverse_returns==0)$fatal(1,"saturation/drain coverage");
    $display("TEST_PASS CONTEXT_PORT_STRESS cycles=%0d requests=2048 qfull=%0d returnfull=%0d credit32=%0d reverse=%0d",cycle,hit_qfull,hit_backfull,hit_credits,reverse_returns);$fclose(tracefile);$finish;
   end
  end
 end
 initial begin
  slicefile=$fopen("context_slices.csv","w");$fdisplay(slicefile,"cycle,name,kind,width,iv,ir,id,ov,ordy,od,empty");
  if(!$value$plusargs("REPLAY_DIR=%s",dir))$fatal(1,"path");tracefile=$fopen($sformatf("%s/calibration_port_stress.csv",dir),"w");
  $fdisplay(tracefile,"cycle,cv,cr,cw,cl,cid,cd,rv,rr,rid,rd,mv,mr,mw,ml,mtag,md,sv,sr,stag,sd,cursor");
  for(integer c=0;c<4;c=c+1)begin sent[c]=0;received[c]=0;seen[c]=0;end
  repeat(4)@(negedge clk);reset=0;
 end
endmodule
