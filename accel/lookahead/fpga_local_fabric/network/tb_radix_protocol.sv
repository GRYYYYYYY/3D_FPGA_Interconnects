`timescale 1ns/1ps
module tb_radix_protocol;
 reg clk=0;always #2.5 clk=~clk;reg reset=1;
 reg [207:0]cv=0,rr=0;wire[207:0]cr,rv;
 reg [831:0]ck=0;reg[6655:0]cl=0,cid=0,cgen=0;
 reg [40959:0]local_write_data=0;wire[831:0]rk;wire[6655:0]rid,rgen;
 wire[53247:0]rd;wire[415:0]rstatus;
 wire[31:0]mv,mw,sr,port_error;reg[31:0]mr=0,sv=0;
 wire[1023:0]ml;wire[159:0]mtag;wire[8191:0]md;
 reg[159:0]stag=0;reg[8191:0]sd=0;reg[63:0]sstatus=0;wire error;
 wire[5:0]internal_peak[32];lf_radix_network dut(.*);
assign internal_peak[0]=dut.port0.fabric.peak_credits;
assign internal_peak[1]=dut.port1.fabric.peak_credits;
assign internal_peak[2]=dut.port2.fabric.peak_credits;
assign internal_peak[3]=dut.port3.fabric.peak_credits;
assign internal_peak[4]=dut.port4.fabric.peak_credits;
assign internal_peak[5]=dut.port5.fabric.peak_credits;
assign internal_peak[6]=dut.port6.fabric.peak_credits;
assign internal_peak[7]=dut.port7.fabric.peak_credits;
assign internal_peak[8]=dut.port8.fabric.peak_credits;
assign internal_peak[9]=dut.port9.fabric.peak_credits;
assign internal_peak[10]=dut.port10.fabric.peak_credits;
assign internal_peak[11]=dut.port11.fabric.peak_credits;
assign internal_peak[12]=dut.port12.fabric.peak_credits;
assign internal_peak[13]=dut.port13.fabric.peak_credits;
assign internal_peak[14]=dut.port14.fabric.peak_credits;
assign internal_peak[15]=dut.port15.fabric.peak_credits;
assign internal_peak[16]=dut.port16.fabric.peak_credits;
assign internal_peak[17]=dut.port17.fabric.peak_credits;
assign internal_peak[18]=dut.port18.fabric.peak_credits;
assign internal_peak[19]=dut.port19.fabric.peak_credits;
assign internal_peak[20]=dut.port20.fabric.peak_credits;
assign internal_peak[21]=dut.port21.fabric.peak_credits;
assign internal_peak[22]=dut.port22.fabric.peak_credits;
assign internal_peak[23]=dut.port23.fabric.peak_credits;
assign internal_peak[24]=dut.port24.fabric.peak_credits;
assign internal_peak[25]=dut.port25.fabric.peak_credits;
assign internal_peak[26]=dut.port26.fabric.peak_credits;
assign internal_peak[27]=dut.port27.fabric.peak_credits;
assign internal_peak[28]=dut.port28.fabric.peak_credits;
assign internal_peak[29]=dut.port29.fabric.peak_credits;
assign internal_peak[30]=dut.port30.fabric.peak_credits;
assign internal_peak[31]=dut.port31.fabric.peak_credits;
 localparam COUNT=96;
 reg[31:0]response_accepted=0,blocked_request=0;reg[293:0]held_request[32];
 reg[207:0]blocked_return=0;reg[325:0]held_return[208];
 integer maximum_internal_credit=0;
 integer sent[208],received[208];reg seen[208][COUNT];
 reg busy[32][32];integer due[32][32];reg[31:0] line_[32][32];
 integer cycle=0,total=0,issues=0,responses=0,local_during_front_stall=0,ooo=0;
 integer chosen,pick,credits,peak_credits=0,oldest,fd;
 reg[31:0] line_value;reg[255:0] expected;
 function automatic[3:0] kind(input integer s,n);
  if(s<16)kind=2;else if(s<32)kind=n%2?1:11;else if(s<48)kind=3;
  else if(s<112)kind=4+n%3;else if(s<176)kind=7+n%2;
  else case(n%3)0:kind=0;1:kind=9;default:kind=10;endcase
 endfunction
 function automatic bit writing(input integer s,n);
  reg[3:0]k;begin k=kind(s,n);writing=k==0||k==6||k==8||k==9;end
 endfunction
 function automatic[31:0] addr(input integer s,n);
  integer p;begin p=s<48?(s+n*7)%32:s<112?(s-48)/2:s<176?(s-112)/2:s-176;
  addr=(s<<18)|(n<<6)|p;end
 endfunction
 function automatic[255:0] data(input[31:0]a,input bit wr);
  begin for(integer k=0;k<8;k=k+1)data[k*32+:32]=(a*32'h9e3779b9)^(32'hcafebabe+k*32'h10203041)^(wr?32'h12345678:32'h87654321);end
 endfunction
 initial begin
  fd=$fopen("network_trace.csv","w");$fdisplay(fd,"cycle,event,source_or_port,id_or_tag,line_or_kind");
  for(integer s=0;s<208;s=s+1)begin sent[s]=0;received[s]=0;for(integer n=0;n<COUNT;n=n+1)seen[s][n]=0;end
  for(integer p=0;p<32;p=p+1)for(integer t=0;t<32;t=t+1)begin busy[p][t]=0;due[p][t]=0;line_[p][t]=0;end
  repeat(5)@(negedge clk);reset=0;
  while(total<208*COUNT)begin
   for(integer s=0;s<208;s=s+1)begin
    cv[s]=sent[s]<COUNT;rr[s]=(s>=48||cycle>=900)&&((cycle+s*3)%17!=0);
    ck[s*4+:4]=kind(s,sent[s]);cid[s*32+:32]=32'hf0000000|(s<<16)|sent[s];cgen[s*32+:32]=32'ha5000000|sent[s];cl[s*32+:32]=addr(s,sent[s]);
    if(s>=48)local_write_data[(s-48)*256+:256]=data(addr(s,sent[s]),1);
   end
   for(integer p=0;p<32;p=p+1)begin
    mr[p]=(cycle+p)%11!=0;chosen=-1;oldest=-1;credits=0;
    for(integer t=0;t<32;t=t+1)if(busy[p][t])begin
     credits=credits+1;
     if(due[p][t]<=cycle)begin if(oldest<0||due[p][t]<due[p][oldest])oldest=t;chosen=t;end
    end
    if(credits>peak_credits)peak_credits=credits;
    if(!sv[p]||response_accepted[p])begin
     sv[p]=chosen>=0;
     if(chosen>=0)begin stag[p*5+:5]=chosen;sd[p*256+:256]=data(line_[p][chosen],0);sstatus[p*2+:2]=(line_[p][chosen]>>6)&3;end
    end
   end
   @(posedge clk);
   response_accepted=sv&sr;
   for(integer p=0;p<32;p=p+1)begin
    if(blocked_request[p]&&(!mv[p]||{mw[p],ml[p*32+:32],mtag[p*5+:5],md[p*256+:256]}!==held_request[p]))$fatal(1,"HELD_PHYSICAL_REQUEST");
    blocked_request[p]=mv[p]&&!mr[p];held_request[p]={mw[p],ml[p*32+:32],mtag[p*5+:5],md[p*256+:256]};
    if(internal_peak[p]>maximum_internal_credit)maximum_internal_credit=internal_peak[p];
   end
   for(integer s=0;s<208;s=s+1)begin
    if(blocked_return[s]&&(!rv[s]||{rk[s*4+:4],rid[s*32+:32],rgen[s*32+:32],rstatus[s*2+:2],rd[s*256+:256]}!==held_return[s]))$fatal(1,"HELD_SOURCE_RETURN");
    blocked_return[s]=rv[s]&&!rr[s];held_return[s]={rk[s*4+:4],rid[s*32+:32],rgen[s*32+:32],rstatus[s*2+:2],rd[s*256+:256]};
   end
   if(error||port_error)$fatal(1,"PROTOCOL_ERROR cycle=%0d",cycle);
   for(integer s=0;s<208;s=s+1)begin
    if(cv[s]&&cr[s])begin $fdisplay(fd,"%0d,accept,%0d,%0d,%0d",cycle,s,sent[s],cl[s*32+:32]);sent[s]=sent[s]+1;end
    if(rv[s]&&rr[s])begin
     pick=rid[s*32+:32]&65535;
     if(pick>=COUNT||pick>=sent[s]||seen[s][pick])$fatal(1,"RETURN_ID s=%0d id=%0d",s,pick);
     if(rid[s*32+:32]!=(32'hf0000000|(s<<16)|pick)||rgen[s*32+:32]!=(32'ha5000000|pick)||rk[s*4+:4]!=kind(s,pick))$fatal(1,"IDENTITY s=%0d",s);
     expected=writing(s,pick)?256'b0:data(addr(s,pick),0);
     if(rd[s*256+:256]!==expected||rstatus[s*2+:2]!=(pick&3))$fatal(1,"PAYLOAD_STATUS s=%0d id=%0d",s,pick);
     seen[s][pick]=1;received[s]=received[s]+1;total=total+1;
     if(s>=48&&cycle<900)local_during_front_stall=local_during_front_stall+1;
     $fdisplay(fd,"%0d,return,%0d,%0d,%0d",cycle,s,pick,rk[s*4+:4]);
    end
   end
   for(integer p=0;p<32;p=p+1)begin
    // Check/retire old response before assigning a distinct live request tag.
    if(sv[p]&&sr[p])begin
     pick=stag[p*5+:5];if(!busy[p][pick]||due[p][pick]>cycle)$fatal(1,"EARLY_OR_DUPLICATE_RESPONSE");
     for(integer t=0;t<32;t=t+1)if(busy[p][t]&&due[p][t]<due[p][pick])ooo=ooo+1;
     busy[p][pick]=0;responses=responses+1;
    end
    if(mv[p]&&mr[p])begin
     pick=mtag[p*5+:5];line_value=ml[p*32+:32];
     if(busy[p][pick]||line_value[4:0]!=p)$fatal(1,"TAG_OR_OWNER");
     if(mw[p]&&md[p*256+:256]!==data(line_value,1))$fatal(1,"WRITE_PAYLOAD");
     busy[p][pick]=1;line_[p][pick]=line_value;due[p][pick]=cycle+16+((line_value>>6)%23);
     issues=issues+1;$fdisplay(fd,"%0d,issue,%0d,%0d,%0d",cycle,p,pick,line_value);
    end
   end
   @(negedge clk);cycle=cycle+1;if(cycle>100000)$fatal(1,"WATCHDOG total=%0d",total);
  end
  if(issues!=total||responses!=total||local_during_front_stall==0||ooo==0)$fatal(1,"COVERAGE_OR_CONSERVATION");
  if(maximum_internal_credit!=32)$fatal(1,"32_CREDIT_COVERAGE max=%0d",maximum_internal_credit);$display("PROTOCOL_PASS held_req_return_stable=1 internal_credit_peak=%0d",maximum_internal_credit);
  $fclose(fd);$display("TEST_PASS full_sources=208 ports=32 requests=%0d cycles=%0d local_while_front_blocked=%0d external_credit_peak=%0d ooo=%0d",total,cycle,local_during_front_stall,peak_credits,ooo);$finish;
 end
endmodule
