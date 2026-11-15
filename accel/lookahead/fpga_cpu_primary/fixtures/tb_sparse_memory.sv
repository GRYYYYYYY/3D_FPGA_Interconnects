`timescale 1ns/1ps
module tb_sparse_memory;
 reg clk=0;always #2.5 clk=~clk;reg reset=1;
 reg[31:0]mv=0,mw=0,sr=0;wire[31:0]mr,sv;reg[1023:0]ml=0;reg[159:0]mtag=0;reg[8191:0]md=0;wire[159:0]stag;wire[8191:0]sd;wire[63:0]status;wire idle;
 integer issued,returned,peak_credits,out_of_order;
 cp_sparse_memory #(.PORT_ROWS(512),.LATENCY_CYCLES(16),.ISSUE_CYCLES(1),.JITTER_CYCLES(17),.STALL_PERIOD(19),.STALL_OPEN(14)) memory(.clk,.reset,.mv,.mw,.mr,.ml,.mtag,.md,.sv,.sr,.stag,.sd,.status,.idle,.issued,.returned,.peak_credits,.out_of_order);
 integer stage=0,cycle=0,total_requested=0,total_returned=0,hold_checks=0;
 integer requested[32],completed[32],birth[32][32];reg[31:0]expected_valid[32];reg[255:0]expected[32][32],row_value[32],cost_value[4];
 reg[31:0]last_sv=0,last_sr=0;reg[159:0]last_tag=0;reg[8191:0]last_data=0;reg[63:0]last_status=0;
 reg[31:0]cfg[22];string directory,negative="none";
 function automatic reg[255:0] pattern(input integer p);
  begin pattern={32'hcafe0000|32'(p),32'h3f800000,32'hdead0000|32'(p),32'h40000000,32'hacdc0000|32'(p),32'h40400000,32'h12340000|32'(p),32'h40800000};end
 endfunction
 always @(negedge clk)begin
  #0.2;mv=0;mw=0;sr=0;ml=0;mtag=0;md=0;
  if(!reset)for(integer p=0;p<32;p=p+1)begin
   sr[p]=stage!=0&&((cycle+p*3)%17<9);
   if(stage==0&&requested[p]<32)begin mv[p]=1;ml[p*32+:32]=p;mtag[p*5+:5]=requested[p];md[p*256+:256]=pattern(p);end
   if(stage==2&&requested[p]<33)begin mv[p]=1;mw[p]=1;ml[p*32+:32]=cfg[14]+p;mtag[p*5+:5]=0;md[p*256+:256]=pattern(p);end
   if(stage==3&&requested[p]<34)begin mv[p]=1;ml[p*32+:32]=cfg[14]+p;mtag[p*5+:5]=0;md[p*256+:256]=~pattern(p);end
   if(stage==4&&p<(cfg[4]+3)/4&&requested[p]<35)begin mv[p]=1;ml[p*32+:32]=cfg[18]+p;mtag[p*5+:5]=0;md[p*256+:256]=~pattern(p);end
   if(stage==9&&p==0&&requested[p]<(negative=="reuse"?2:1))begin
    mv[p]=1;mtag[4:0]=0;sr[p]=0;
    if(negative=="range")ml[31:0]=((cfg[19]>>5)+1)*32;
    else if(negative=="owner")ml[31:0]=1;
    else if(negative=="uninitialized")ml[31:0]=cfg[14];
    else if(negative=="readonly")begin ml[31:0]=0;mw[0]=1;end
    else ml[31:0]=0;
   end
  end
 end
 always @(posedge clk)begin:check
  integer tag;
  if(!reset)begin
   cycle=cycle+1;if(cycle>10000)$fatal(1,"WATCHDOG stage=%0d req=%0d ret=%0d",stage,total_requested,total_returned);
   for(integer p=0;p<32;p=p+1)begin
    if(last_sv[p]&&!last_sr[p])begin
     if(!sv[p]||stag[p*5+:5]!==last_tag[p*5+:5]||sd[p*256+:256]!==last_data[p*256+:256]||status[p*2+:2]!==last_status[p*2+:2])$fatal(1,"HELD_RESPONSE_CHANGED");hold_checks=hold_checks+1;
    end
    if(sv[p]&&sr[p])begin
     tag=stag[p*5+:5];if(!expected_valid[p][tag]||sd[p*256+:256]!==expected[p][tag]||status[p*2+:2]!==0)$fatal(1,"ACK_DATA_STATUS p=%0d tag=%0d data=%h expected=%h",p,tag,sd[p*256+:256],expected[p][tag]);
     if(cycle-birth[p][tag]<16)$fatal(1,"LATENCY_FLOOR");expected_valid[p][tag]=0;completed[p]=completed[p]+1;total_returned=total_returned+1;
    end
    if(mv[p]&&mr[p])begin
     tag=mtag[p*5+:5];if(expected_valid[p][tag]&&stage!=9)$fatal(1,"TB_DUPLICATE_TAG");expected_valid[p][tag]=1;expected[p][tag]=mw[p]?0:(stage==3?pattern(p):(stage==4?cost_value[p]:row_value[p]));birth[p][tag]=cycle;requested[p]=requested[p]+1;total_requested=total_requested+1;
    end
   end
   last_sv=sv;last_sr=sr;last_tag=stag;last_data=sd;last_status=status;
  end
 end
 initial begin:run
  integer fd,rc,count;reg[31:0]address;reg[255:0]value;string filename;
  for(integer p=0;p<32;p=p+1)begin requested[p]=0;completed[p]=0;expected_valid[p]=0;end
  if(!$value$plusargs("DIR=%s",directory))$fatal(1,"MISSING_DIR");rc=$value$plusargs("NEG=%s",negative);
  #0.1;memory.load_native(directory);filename=$sformatf("%s/config.hex",directory);$readmemh(filename,cfg);
  filename=$sformatf("%s/input/lines.txt",directory);fd=$fopen(filename,"r");count=0;
  while(!$feof(fd))begin rc=$fscanf(fd,"%h %h\n",address,value);if(rc==2)begin if(address<32)begin row_value[address]=value;count=count+1;end if(address>=cfg[18]&&address<cfg[18]+(cfg[4]+3)/4)cost_value[address-cfg[18]]=value;end end
  $fclose(fd);if(count!=32)$fatal(1,"ROWS_FOR_ALL_PORTS");repeat(4)@(posedge clk);@(negedge clk);#0.1;if(negative!="none")stage=9;reset=0;
  if(negative!="none")begin repeat(200)@(posedge clk);$fatal(1,"NEGATIVE_NOT_REJECTED %s",negative);end
  wait(total_requested==1024);repeat(80)@(posedge clk);if(peak_credits!=32)$fatal(1,"DID_NOT_FILL32_CREDITS");@(negedge clk);#0.1;stage=1;
  wait(total_returned==1024);@(negedge clk);#0.1;stage=2;
  wait(total_returned==1056);@(negedge clk);#0.1;stage=3;
  wait(total_returned==1088);@(negedge clk);#0.1;stage=4;wait(total_returned==1088+(cfg[4]+3)/4);@(negedge clk);#0.1;stage=5;repeat(3)@(posedge clk);
  if(!idle||issued!=1088+(cfg[4]+3)/4||returned!=1088+(cfg[4]+3)/4||out_of_order==0||hold_checks==0)$fatal(1,"FINAL_CONSERVATION");
  for(integer p=0;p<32;p=p+1)if(expected_valid[p]||memory.peek(cfg[14]+p)!==pattern(p))$fatal(1,"FINAL_BACKING");
  $display("TEST_PASS sparse32port real_data actual_cost_load held OOO requests=%0d returns=%0d peak=%0d OOO=%0d held=%0d cycles=%0d",issued,returned,peak_credits,out_of_order,hold_checks,cycle);$finish;
 end
endmodule
