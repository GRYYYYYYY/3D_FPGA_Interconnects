`timescale 1ns/1ps
module tb_leaf;
 parameter L=4;integer ef,tf;
 logic clk=0;always #2.5 clk=~clk;logic reset=1,av=0,ar,pv=0,pr,stale=0;logic[15:0]at,pt=0,epoch=0;
 logic[31:0]pn=0;logic[63:0]pp=0;logic mode16=0,cfg_we=0;logic[3:0]cfg_idx=0;logic[63:0]cfg_cost=0;
 logic dv,dr=0,drv=0,drr,mv,mr=0,rv=0,rr;logic[63:0]da,ml;logic[15:0]dt,drt=0,mt,rt=0;logic[255:0]drd=0,rd=0;
 logic yv,yr=0;logic[14:0]yc;logic[63:0]yp;logic[15:0]yt;wire[L-1:0]ov;logic[L-1:0]oready=0;wire[L*32-1:0]od,ot;wire[L*64-1:0]op;
 logic error,idle;logic[31:0]reserved,retired,desc_count,target_count,edge_parents,edge_completed,edge_emitted;
 logic[64:0]parents[128];logic[63:0]desc8[128],costs[16],gold[16384];logic[127:0]desc16[128];logic[31:0]edges[16384];
 integer cycle=0,next=0,phase=0,issued_d=0,issued_e=0,returned_d=0,returned_e=0,got=0,targets=0,stales=0,fd;
 logic have_token=0;logic[15:0]token;logic seen[16384];logic target_seen[128];logic flight[2][32];integer due[2][32];logic[15:0]tags[2][32];logic[63:0]lines[2][32];integer choice[2],idx,slot,occ[2];
 logic blocked_d=0,blocked_e=0,blocked_y=0;logic[79:0]hold_d,hold_e;logic[94:0]hold_y;
 logic[L-1:0]blocked_o=0;logic[127:0]hold_o[L];
 df_front_group #(.L(L)) dut(.clk,.reset,.av,.ar,.at,.pv,.pr,.pt,.stale,.pn,.pp,.epoch,.format16(mode16),.descriptor_base(64'd0),.edge_base(64'd1041696),.edge_count(32'hffffffff),.cells(16'd8),.cfg_we,.cfg_idx,.cfg_cost,
 .dv,.dr,.da,.dt,.drv,.drr,.drt,.drd,.mv,.mr,.ml,.mt,.rv,.rr,.rt,.rd,.yv,.yr,.yc,.yp,.yt,.ov,.or_(oready),.od,.op,.ot,.error,.idle,.reserved,.retired,.desc_count,.target_count,.edge_parents,.edge_completed,.edge_emitted);
 initial begin
  $readmemh("parent.hex",parents);$readmemh("desc8.hex",desc8);$readmemh("desc16.hex",desc16);$readmemh("cost.hex",costs);$readmemh("edge.hex",edges);$readmemh("gold.hex",gold);
  ef=$fopen("edge_cycles.txt","w");tf=$fopen("token_cycles.txt","w");fd=$fopen("leaf_cycles.txt","w");for(integer i=0;i<16384;i=i+1)seen[i]=0;for(integer i=0;i<128;i=i+1)target_seen[i]=0;
  for(integer c=0;c<2;c=c+1)begin occ[c]=0;for(integer i=0;i<32;i=i+1)flight[c][i]=0;end
  repeat(4)@(negedge clk);reset=0;
  for(integer i=0;i<16;i=i+1)begin cfg_we=1;cfg_idx=i;cfg_cost=costs[i];@(negedge clk);end cfg_we=0;
  forever begin
   av=0;pv=0;
   if(next<128&&(next<64||phase==1))begin
    if(!have_token)av=cycle%11!=3;else begin pv=1;pt=token;pn=next;pp=parents[next][63:0];stale=parents[next][64];epoch=next<64?1:2;end
   end
   // 16B representation on epoch2, no reset or cost reload.
   mode16=phase==1;
   dr=cycle%17!=2&&occ[0]<32;mr=cycle%19!=3&&occ[1]<32;
   drv=0;rv=0;drd=0;rd=0;drt=0;rt=0;
   for(integer c=0;c<2;c=c+1)begin
    choice[c]=-1;for(integer i=0;i<32;i=i+1)if(flight[c][i]&&due[c][i]<=cycle&&cycle%23!=4)choice[c]=i;
    if(choice[c]>=0)begin
     if(c==0)begin drv=1;drt=tags[c][choice[c]];for(integer k=0;k<4;k=k+1)if(phase==0)drd[k*64+:64]=desc8[lines[c][choice[c]]*4+k];else if(k<2)drd[k*128+:128]=desc16[lines[c][choice[c]]*2+k];end
     else begin rv=1;rt=tags[c][choice[c]];for(integer k=0;k<8;k=k+1)rd[k*32+:32]=edges[(lines[c][choice[c]]-1041696==64'h1fffffff ? 16376+k:(lines[c][choice[c]]-1041696)*8+k)];end
    end
   end
   yr=cycle%29>9;
   for(integer l=0;l<L;l=l+1)oready[l]=(cycle+7*l)%41>10&&!(cycle>250&&cycle<330);
   @(negedge clk);
  end
 end
 always @(posedge clk)if(!reset)begin
  cycle=cycle+1;if(cycle>60000)$fatal(1,"watchdog next=%0d retired=%0d got=%0d",next,retired,got);
  if(!cfg_we)begin
   $fwrite(ef,"%0d %0d %0d %08h %016h %016h %016h %04h %0d %0d %016h %04h %0d %0d %04h %064h %h %h %h %h %0d %02h %h\n",cycle,dut.ev,dut.er,dut.e_node,dut.e_pair,dut.e_begin,dut.e_end,dut.e_epoch,mr,mv,ml,mt,rv,rr,rt,rd,oready,ov,od,op,dut.alloc_valid,dut.alloc_context,ot);
   $fwrite(tf,"%0d %0d %0d %04h %0d %0d %04h %08h %016h %0d %0d %04h %0d %0d %016h %04h %0d %0d %04h %064h %0d %0d %04h %016h %04h %0d %0d %08h %016h %016h %016h %04h %0d %0d %0d %0d\n",cycle,av,ar,at,pv,pr,pt,pn,pp,stale,mode16,epoch,dv,dr,da,dt,drv,drr,drt,drd,yv,yr,yc,yp,yt,dut.ev,dut.er,dut.e_node,dut.e_pair,dut.e_begin,dut.e_end,dut.e_epoch,reserved,retired,desc_count,target_count);
   if(error)$fatal(1,"DUT error");
   if(blocked_d&&(!dv||{da,dt}!==hold_d))$fatal(1,"DESC unstable");
   if(blocked_e&&(!mv||{ml,mt}!==hold_e))$fatal(1,"EDGE unstable");
   if(blocked_y&&(!yv||{yc,yp,yt}!==hold_y))$fatal(1,"target unstable");
   blocked_d=dv&&!dr;hold_d={da,dt};blocked_e=mv&&!mr;hold_e={ml,mt};blocked_y=yv&&!yr;hold_y={yc,yp,yt};
   for(integer l=0;l<L;l=l+1)begin
    if(blocked_o[l]&&(!ov[l]||{od[l*32+:32],op[l*64+:64],ot[l*32+:32]}!==hold_o[l]))$fatal(1,"candidate unstable");
    blocked_o[l]=ov[l]&&!oready[l];hold_o[l]={od[l*32+:32],op[l*64+:64],ot[l*32+:32]};
   end
   $fwrite(fd,"%0d %0d %0d %h %0d %0d %h %h %h %0d %0d %0d %h %h %0d %0d %h %0d %0d %h %h %0d %0d %h %0d %0d %h %h %h %h %h %h %h\n",cycle,av,ar,at,pv,pr,pt,pn,pp,stale,dv,dr,da,dt,drv,drr,drt,mv,mr,ml,mt,rv,rr,rt,yv,yr,yc,yp,ov,oready,od,op,ot);
   if(av&&ar)begin token=at;have_token=1;end
   if(pv&&pr)begin next=next+1;have_token=0;if(stale)stales=stales+1;end
   for(integer c=0;c<2;c=c+1)begin
    if((c==0&&drv&&drr)||(c==1&&rv&&rr))begin
     flight[c][choice[c]]=0;occ[c]=occ[c]-1;if(c==0)returned_d=returned_d+1;else returned_e=returned_e+1;
    end
    if((c==0&&dv&&dr)||(c==1&&mv&&mr))begin
     slot=-1;for(integer i=0;i<32;i=i+1)if(!flight[c][i]&&slot<0)slot=i;
     if(slot<0)$fatal(1,"credit overflow");flight[c][slot]=1;tags[c][slot]=c==0?dt:mt;lines[c][slot]=c==0?da:ml;due[c][slot]=cycle+15+((cycle*17)%13);occ[c]=occ[c]+1;
     if(c==0)issued_d=issued_d+1;else issued_e=issued_e+1;
    end
   end
   if(yv&&yr)begin
    idx=-1;for(integer n=0;n<128;n=n+1)if(!target_seen[n]&&!parents[n][64]&&desc8[n][63]&&parents[n][63:0]==yp&&desc8[n][62:48]==yc&&n<next&&idx<0)idx=n;
    if(idx<0)$fatal(1,"target duplicate/mismatch");target_seen[idx]=1;targets=targets+1;
   end
   for(integer l=0;l<L;l=l+1)if(ov[l]&&oready[l])begin
    idx=od[l*32+:32];if(idx>=16384||seen[idx]||gold[idx]!==op[l*64+:64])$fatal(1,"candidate mismatch dst=%0d got=%h exp=%h",idx,op[l*64+:64],gold[idx]);seen[idx]=1;got=got+1;
   end
   if(next==64&&idle&&occ[0]==0&&occ[1]==0)begin phase=1;$display("EPOCH_DRAIN cycle=%0d",cycle);end
   if(next==128&&idle&&occ[0]==0&&occ[1]==0)begin
    for(integer n=0;n<128;n=n+1)if(!parents[n][64]&&desc8[n][63]&&!target_seen[n])$fatal(1,"missing target");
    for(integer n=0;n<16384;n=n+1)if(gold[n]!=0&&!seen[n])$fatal(1,"missing candidate %0d",n);
    if(reserved!=128||retired!=128||desc_count!=128-stales||edge_parents!=128-stales||edge_completed!=edge_parents||edge_emitted!=got||target_count!=targets||issued_d!=returned_d||issued_e!=returned_e)$fatal(1,"conservation");
    $display("TEST_PASS leaf L=%0d cycles=%0d parents=128 stale=%0d candidates=%0d targets=%0d DESC=%0d EDGE=%0d",L,cycle,stales,got,targets,issued_d,issued_e);$fclose(fd);$finish;
   end
  end
 end
endmodule
