`timescale 1ns/1ps
module tb_admin;
 reg clk=0;always #2.5 clk=~clk;reg reset=1;reg[2:0]phase=0;reg[31:0]node_count=257;reg[4:0]cost_count=7;reg[7:0]sample_index=173;
 reg[63:0]label_base=64'h200000,cost_base=64'h800000;
 wire[31:0]cv;reg[31:0]cr=0;wire[127:0]ck;wire[1023:0]cl,cid,cgen;wire[8191:0]cd;
 reg[31:0]rv=0;wire[31:0]rr;reg[127:0]rk=0;reg[1023:0]rid=0,rgen=0;reg[8191:0]rd=0;reg[63:0]rstatus=0;
 wire init_done,cost_done,error,cfg_we;wire[3:0]cfg_idx;wire[63:0]cfg_cost;wire[1:0]write_v,write_r,ack_v,ack_r;wire[127:0]write_line;wire[511:0]write_data;
 wire[31:0]init_issued,init_acked,cost_issued,cost_acked;
 cp_admin dut(.*);
 reg[15:0]iv=0;wire[15:0]ir;reg[239:0]icell=0;reg[1023:0]ipair=0;wire[7:0]ov;wire[7:0]first;wire out_init,out_idle,export_ready,export_done,out_error;
 reg export_start=0;wire[1:0]service_ack_r;reg pause_ack=1;wire[14:0]issued_count,acked_count;
 assign ack_r=service_ack_r&{2{!pause_ack}};
 df_output_service output_service(.clk,.reset,.iv,.ir,.icell,.ipair,.ov,.ordy(8'hff),.ocell(),.opair(),.first,.improved(),.init_done(out_init),.idle(out_idle),.export_start,.export_ready,.cells(16'd137),.output_base_line(64'h900000),.write_v,.write_r,.write_line,.write_data,.ack_v(ack_v&{2{!pause_ack}}),.ack_r(service_ack_r),.export_done,.error(out_error),.issued_count,.acked_count,.packing_occupancy());
 localparam[63:0]INF=64'h7f8000007f800000,MISSING=64'h7fc000007fc00000;
 reg[63:0]expected[137];reg[255:0]observed[35];reg[64:0]init_seen=0;reg[34:0]output_seen=0,ack_seen=0;reg[6:0]cfg_seen=0;
 reg[7:0]pending[32];reg[3:0]qkind[32][8];reg[31:0]qid[32][8],qgen[32][8],qline[32][8];reg[255:0]qdata[32][8];integer due[32][8],order[32][8],held[32],last_order[32];reg[31:0]consumed=0;
 integer cycle=0,requests=0,responses=0,ooos=0,cfg_writes=0,export_acks=0,collector_blocked=0;integer p,k,slot,index_,mode=0;reg inject=0,injected=0,expect_error=0;
 function automatic[63:0]cost(input integer i);begin cost=64'h123456789abcdef0^(64'h0102030405060708*i);end endfunction
 always @(negedge clk)begin
  for(integer port=0;port<32;port=port+1)begin
   cr[port]=!reset&&pending[port]!=8'hff&&((cycle+port)%11<8);
   if(reset)begin rv[port]=0;held[port]=-1;end
   else begin
    if(consumed[port])begin rv[port]=0;held[port]=-1;end
    if(!rv[port])begin
     for(integer s=7;s>=0;s=s-1)if(pending[port][s]&&due[port][s]<=cycle&&(held[port]<0||order[port][s]>order[port][held[port]]))held[port]=s;
     if(held[port]>=0)begin
      rv[port]=1;rk[port*4+:4]=qkind[port][held[port]];rid[port*32+:32]=qid[port][held[port]];rgen[port*32+:32]=qgen[port][held[port]];rd[port*256+:256]=qdata[port][held[port]];
      if(inject&&!injected&&qkind[port][held[port]]==9)begin
       if(mode==1)rgen[port*32+:32]=rgen[port*32+:32]^32'h80000000;
       if(mode==2)rid[port*32+:32]=rid[port*32+:32]^32'h80000000;
       if(mode==3)rk[port*4+:4]=15;
       injected=1;
      end
     end
    end
   end
  end
 end
 always @(posedge clk)begin
  cycle=cycle+1;consumed=0;
  if(cycle>30000)$fatal(1,"admin watchdog phase=%0d init=%b cost=%b export=%b",phase,init_done,cost_done,export_done);
  if(reset)begin for(integer port=0;port<32;port=port+1)pending[port]=0;end
  else begin
   if((error||out_error)&&!expect_error)$fatal(1,"unexpected admin/output error");
   for(integer port=0;port<32;port=port+1)begin
    if(rv[port]&&rr[port])begin
     if(held[port]<0||!pending[port][held[port]])$fatal(1,"response model duplicate");
     if(order[port][held[port]]<last_order[port])ooos=ooos+1;last_order[port]=order[port][held[port]];
     pending[port][held[port]]=0;responses=responses+1;consumed[port]=1;
    end
    if(cv[port]&&cr[port])begin
     if(cl[port*32+:5]!=port||cgen[port*32+:32]!=173)$fatal(1,"source owner/gen mismatch");
     slot=-1;for(integer s=7;s>=0;s=s-1)if(!pending[port][s])slot=s;if(slot<0)$fatal(1,"memory model credit overflow");
     pending[port][slot]=1;qkind[port][slot]=ck[port*4+:4];qid[port][slot]=cid[port*32+:32];qgen[port][slot]=cgen[port*32+:32];qline[port][slot]=cl[port*32+:32];qdata[port][slot]=0;order[port][slot]=requests;
     due[port][slot]=cycle+16+((cl[port*32+:32]&32)?0:29);requests=requests+1;
     case(ck[port*4+:4])
      0:begin index_=cid[port*32+:32];if(index_>=65||init_seen[index_]||cl[port*32+:32]!=label_base+index_||cd[port*256+:256]!=={4{INF}})$fatal(1,"INIT exact address/id/data");init_seen[index_]=1;end
      10:begin index_=cid[port*32+:32];if(index_>=2||cl[port*32+:32]!=cost_base+index_)$fatal(1,"cost exact address/id");for(integer s=0;s<4;s=s+1)qdata[port][slot][s*64+:64]=cost(index_*4+s);end
      9:begin
       index_=cl[port*32+:32]-32'h900000;if(index_>=35||output_seen[index_]||cid[port*32+:32]!=cl[port*32+:32])$fatal(1,"export exact id/address duplicate");
       output_seen[index_]=1;observed[index_]=cd[port*256+:256];
       for(integer s=0;s<4;s=s+1)begin
        if(index_*4+s<137)begin if(cd[port*256+s*64+:64]!==expected[index_*4+s])$fatal(1,"output payload beat=%0d sector=%0d",index_,s);end
        else if(cd[port*256+s*64+:64]!==MISSING)$fatal(1,"last partial beat padding");
       end
      end
      default:$fatal(1,"illegal admin kind");
     endcase
     // Negative transport boundary probe: deliver a real cost response through
     // the wrong admin source. Move the model queue too, preserving handshakes.
     if(mode==4&&!injected&&ck[port*4+:4]==10)begin
      if(port!=0||pending[1]!=0)$fatal(1,"cost port fault precondition");
      pending[0][slot]=0;pending[1][slot]=1;qkind[1][slot]=qkind[0][slot];
      qid[1][slot]=qid[0][slot];qgen[1][slot]=qgen[0][slot];qline[1][slot]=qline[0][slot];
      qdata[1][slot]=qdata[0][slot];order[1][slot]=order[0][slot];due[1][slot]=due[0][slot];injected=1;
     end
    end
   end
   if(cfg_we)begin if(cfg_idx>=7||cfg_seen[cfg_idx]||cfg_cost!==cost(cfg_idx))$fatal(1,"partial cost decode idx=%0d actual=%h",cfg_idx,cfg_cost);cfg_seen[cfg_idx]=1;cfg_writes=cfg_writes+1;end
   if(|(ack_v&~ack_r))collector_blocked=collector_blocked+1;
   if(!expect_error)for(integer a=0;a<2;a=a+1)if(ack_v[a]&&ack_r[a])begin
    index_=dut.ack_out[a*64+:32]-32'h900000;
    if(dut.ack_out[a*64+32+:32]!=173||index_<0||index_>=35||!output_seen[index_]||ack_seen[index_])$fatal(1,"collector exact ID/gen conservation");
    ack_seen[index_]=1;export_acks=export_acks+1;
   end
  end
 end
 task update_cell(input integer c);
 integer g;
 begin g=c%16;@(negedge clk);iv=16'b1<<g;icell[g*15+:15]=c;ipair[g*64+:64]=64'h3f80000040000000+c;do @(posedge clk);while(!ir[g]);expected[c]=64'h3f80000040000000+c;@(negedge clk);iv=0;end endtask
 initial begin
  if($value$plusargs("MODE=%d",mode))begin end
  for(integer port=0;port<32;port=port+1)begin pending[port]=0;held[port]=-1;last_order[port]=-1;end
  for(integer c=0;c<137;c=c+1)expected[c]=MISSING;
  repeat(5)@(negedge clk);reset=0;phase=1;
  wait(init_done);@(negedge clk);if(init_issued!=65||init_acked!=65||init_seen!=={65{1'b1}}||requests!=responses)$fatal(1,"INIT premature drain");
  phase=2;
  if(mode==4)begin
   expect_error=1;repeat(100)@(negedge clk);
   if(!injected||!error)$fatal(1,"wrong cost return port not rejected");
   $display("TEST_PASS admin_negative_cost_wrong_port rejected");$finish;
  end
  wait(cost_done);@(negedge clk);if(cost_issued!=2||cost_acked!=2||cfg_seen!==7'h7f||cfg_writes!=7)$fatal(1,"cost partial-beat decode/drain");phase=0;
  wait(out_init);for(integer c=0;c<137;c=c+1)if(c%7!=3)update_cell(c);wait(out_idle);@(negedge clk);phase=3;export_start=1;
  @(negedge clk);export_start=0;if(mode!=0)begin expect_error=1;inject=1;end
  repeat(130)@(negedge clk);pause_ack=0;
  if(mode!=0)begin
   repeat(10)@(negedge clk);if(!injected)$fatal(1,"negative test did not inject");
   if(!error)$fatal(1,"ADMIN_MISSED_INVALID_ACK mode=%0d (1=gen32,2=localID32,3=kind)",mode);
   $display("TEST_PASS admin_negative_ACK mode=%0d rejected",mode);$finish;
  end
  wait(export_done);@(negedge clk);
  if(output_seen!=={35{1'b1}}||ack_seen!=={35{1'b1}}||export_acks!=35||issued_count!=35||acked_count!=35||requests!=responses||ooos==0||collector_blocked==0)$fatal(1,"export final conservation OOO=%0d blocked=%0d",ooos,collector_blocked);
  $display("TEST_PASS admin32 INIT65 cost7_decode2beats export137cells35beats request=%0d ACK=%0d OOO=%0d collector_blocked=%0d",requests,responses,ooos,collector_blocked);$finish;
 end
endmodule
