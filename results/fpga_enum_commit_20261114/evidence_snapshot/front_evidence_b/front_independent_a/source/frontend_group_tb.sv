`timescale 1ns/1ps
module frontend_group_tb;
 reg clk=0;always #2.5 clk=~clk;reg reset=1,cfg_we=0;reg[3:0]cfg_idx=0;reg[63:0]cfg_cost=0;
 reg[239:0] parents[144];reg[31:0] edges[8192];reg[63:0] gold[8192],costs[16];
 reg[1:0]pv=0,mr=0,rv=0;wire[1:0]pr,mv,rr,idle,error,av;
 reg[63:0]pp[2],be[2],ee[2];reg[31:0]pn[2];reg[15:0]epoch[2],rt[2];reg[255:0]rd[2];
 wire[63:0]ml[2];wire[15:0]mt[2];reg[7:0] oready[2];wire[7:0]ovalid[2];wire[255:0]od[2];wire[511:0]op[2];wire[31:0]accepted[2],completed[2],emitted[2];wire[7:0]ac[2];
 integer cycle=0,next_parent[2],count[2],req_count[2],rsp_count[2],epoch_step[2],files[2];reg seen[2][8192];
 reg fvalid[2][32];integer due[2][32];reg[15:0]tags[2][32];reg[63:0]lines[2][32];integer outstanding[2];
 integer choice,freeflight,idx,phase;reg[239:0] token;
 for(genvar m=0;m<2;m=m+1)begin:mode
  frontend_group dut(.clk,.reset,.lane_rr(m==1),.pv(pv[m]),.pr(pr[m]),.pn(pn[m]),.pp(pp[m]),.begin_edge(be[m]),.end_edge(ee[m]),.epoch(epoch[m]),.cfg_we,.cfg_idx,.cfg_cost,.mv(mv[m]),.mr(mr[m]),.ml(ml[m]),.mt(mt[m]),.rv(rv[m]),.rr(rr[m]),.rt(rt[m]),.rd(rd[m]),.ov(ovalid[m]),.or_(oready[m]),.od(od[m]),.op(op[m]),.error(error[m]),.accepted(accepted[m]),.completed(completed[m]),.emitted(emitted[m]),.idle(idle[m]),.alloc_valid(av[m]),.alloc_context(ac[m]));
 end
 initial begin
  $readmemh("cost.hex",costs);$readmemh("parent.hex",parents);$readmemh("edge.hex",edges);$readmemh("gold.hex",gold);
  for(integer m=0;m<2;m=m+1)begin
   next_parent[m]=0;count[m]=0;req_count[m]=0;rsp_count[m]=0;outstanding[m]=0;epoch_step[m]=0;
   for(integer i=0;i<8192;i=i+1)seen[m][i]=0;
   for(integer i=0;i<32;i=i+1)fvalid[m][i]=0;
   if(m==0)files[m]=$fopen("first_free_cycles.txt","w");else files[m]=$fopen("lane_rr_cycles.txt","w");
  end
  repeat(4)@(negedge clk);reset=0;
  for(integer i=0;i<16;i=i+1)begin cfg_we=1;cfg_idx=i;cfg_cost=costs[i];@(negedge clk);end
  cfg_we=0;
  forever begin
   for(integer m=0;m<2;m=m+1)begin
    pv[m]=0;pn[m]=0;pp[m]=0;be[m]=0;ee[m]=0;epoch[m]=0;
    if(next_parent[m]<144&&(next_parent[m]<72||epoch_step[m]==1))begin
     token=parents[next_parent[m]];pv[m]=cycle%17!=4;epoch[m]=token[239:224];pn[m]=token[223:192];pp[m]=token[191:128];be[m]=token[127:64];ee[m]=token[63:0];
    end
    mr[m]=(cycle%19!=3)&&(outstanding[m]<32);rv[m]=0;rt[m]=0;rd[m]=0;
    choice=-1;for(integer i=0;i<32;i=i+1)if(fvalid[m][i]&&due[m][i]<=cycle&&cycle%23!=6)choice=i;
    if(choice>=0)begin rv[m]=1;rt[m]=tags[m][choice];for(integer k=0;k<8;k=k+1)rd[m][k*32+:32]=edges[lines[m][choice]*8+k];end
    for(integer l=0;l<8;l=l+1)oready[m][l]=!((cycle+7*l)%41<8 || (cycle>150&&cycle<220&&l==2));
   end
   @(negedge clk);
  end
 end
 always @(posedge clk)if(!reset)begin
  cycle=cycle+1;if(cycle>30000)$fatal(1,"watchdog");
  if(!cfg_we)for(integer m=0;m<2;m=m+1)begin
   $fwrite(files[m],"%0d %0d %0d %08h %016h %016h %016h %04h %0d %0d %016h %04h %0d %0d %04h %064h %02h %02h %064h %0128h %0d %02h\n",cycle,pv[m],pr[m],pn[m],pp[m],be[m],ee[m],epoch[m],mr[m],mv[m],ml[m],mt[m],rv[m],rr[m],rt[m],rd[m],oready[m],ovalid[m],od[m],op[m],av[m],ac[m]);
   if(error[m])$fatal(1,"DUT error mode=%0d",m);
   if(pv[m]&&pr[m])next_parent[m]=next_parent[m]+1;
   if(rv[m]&&rr[m])begin
    idx=-1;for(integer i=0;i<32;i=i+1)if(fvalid[m][i]&&tags[m][i]==rt[m])idx=i;
    if(idx<0)$fatal(1,"unknown tag");fvalid[m][idx]=0;outstanding[m]=outstanding[m]-1;rsp_count[m]=rsp_count[m]+1;
   end
   if(mv[m]&&mr[m])begin
    freeflight=-1;for(integer i=0;i<32;i=i+1)if(!fvalid[m][i]&&freeflight<0)freeflight=i;
    if(freeflight<0)$fatal(1,"credit overflow");fvalid[m][freeflight]=1;tags[m][freeflight]=mt[m];lines[m][freeflight]=ml[m];due[m][freeflight]=cycle+15+((req_count[m]*17+m)%13);outstanding[m]=outstanding[m]+1;req_count[m]=req_count[m]+1;
   end
   for(integer l=0;l<8;l=l+1)if(ovalid[m][l]&&oready[m][l])begin
    idx=od[m][l*32+:32];if(idx>=8192||gold[idx]!==op[m][l*64+:64]||seen[m][idx])$fatal(1,"pair/duplicate mode=%0d lane=%0d dst=%0d exp=%h actual=%h",m,l,idx,gold[idx],op[m][l*64+:64]);seen[m][idx]=1;count[m]=count[m]+1;
   end
   if(next_parent[m]==72&&idle[m]&&outstanding[m]==0)begin epoch_step[m]=1;$display("EPOCH_BOUNDARY mode=%0d cycle=%0d completed=%0d",m,cycle,completed[m]);end
  end
  if(next_parent[0]==144&&next_parent[1]==144&&idle[0]&&idle[1]&&outstanding[0]==0&&outstanding[1]==0)begin
   if(accepted[0]!=144||accepted[1]!=144||completed[0]!=144||completed[1]!=144||emitted[0]!=count[0]||emitted[1]!=count[1]||count[0]!=count[1]||req_count[0]!=rsp_count[0]||req_count[1]!=rsp_count[1])$fatal(1,"conservation");
   $display("TEST_PASS frontend_group two_epochs=2 parents=144 candidates=%0d cycles=%0d req_first=%0d req_rr=%0d",count[0],cycle,req_count[0],req_count[1]);$fclose(files[0]);$fclose(files[1]);$finish;
  end
 end
endmodule
