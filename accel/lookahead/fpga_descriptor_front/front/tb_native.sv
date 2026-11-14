`timescale 1ns/1ps
module tb_native;
 parameter L=4;
 logic clk=0;always #2.5 clk=~clk;logic reset=1,av=0,ar,pv=0,pr,stale=0;logic[15:0]at,pt=0,epoch=0;
 logic[31:0]pn=0;logic[63:0]pp=0;logic mode16=0,cfg_we=0;logic[3:0]cfg_idx=0;logic[63:0]cfg_cost=0;
 logic dv,dr=0,drv=0,drr,mv,mr=0,rv=0,rr;logic[63:0]da,ml;logic[15:0]dt,drt=0,mt,rt=0;logic[255:0]drd=0,rd=0;
 logic yv,yr=0;logic[14:0]yc;logic[63:0]yp;logic[15:0]yt;wire[L-1:0]ov;logic[L-1:0]oready=0;wire[L*32-1:0]od,ot;wire[L*64-1:0]op;
 logic error,idle;logic[31:0]reserved,retired,desc_count,target_count,edge_parents,edge_completed,edge_emitted;
 logic[31:0]nodes[128];logic[319:0]native_beats[512];logic[95:0]native_gold[4096];logic[63:0]native_config[4];integer lookup,baseidx;logic[64:0]parents[128];logic[63:0]desc8[128],costs[16],gold[16384];logic[127:0]desc16[128];logic[31:0]edges[16384];
 integer cycle=0,next=0,phase=0,issued_d=0,issued_e=0,returned_d=0,returned_e=0,got=0,targets=0,stales=0,fd;
 logic cmd_pending=0,tv;logic[255:0]stats;
 assign reserved=stats[31:0];assign retired=stats[63:32];assign desc_count=stats[95:64];assign target_count=stats[127:96];assign edge_parents=stats[159:128];assign edge_completed=stats[191:160];assign edge_emitted=stats[223:192];
 logic have_token=0;logic[15:0]token;logic seen[16384];logic target_seen[128];logic flight[2][32];integer due[2][32];logic[15:0]tags[2][32];logic[63:0]lines[2][32];integer choice[2],idx,slot,occ[2];
 logic blocked_d=0,blocked_e=0,blocked_y=0;logic[79:0]hold_d,hold_e;logic[94:0]hold_y;
 logic[L-1:0]blocked_o=0;logic[127:0]hold_o[L];
 df_front_context #(.L(L)) dut(.clk,.reset,.av,.ar,.tv,.tr(1'b1),.at,.pv,.pr,.pt,.stale,.pn,.pp,.epoch,.format16(mode16),.descriptor_base(native_config[2]),.edge_base(native_config[3]),.edge_count(32'hffffffff),.cells(16'd32768),.cfg_we,.cfg_idx,.cfg_cost,
 .dv,.dr,.da,.dt,.drv,.drr,.drt,.drd,.mv,.mr,.ml,.mt,.rv,.rr,.rt,.rd,.yv,.yr,.yc,.yp,.yt,.ov,.or_(oready),.od,.op,.ot,.error,.idle,.stats);
 initial begin
  $readmemh("node.hex",nodes);$readmemh("native_beats.hex",native_beats);$readmemh("native_gold.hex",native_gold);$readmemh("native_config.hex",native_config);$readmemh("parent.hex",parents);$readmemh("desc8.hex",desc8);$readmemh("desc16.hex",desc16);$readmemh("cost.hex",costs);
  fd=$fopen("leaf_cycles.txt","w");for(integer i=0;i<16384;i=i+1)seen[i]=0;for(integer i=0;i<128;i=i+1)target_seen[i]=0;
  for(integer c=0;c<2;c=c+1)begin occ[c]=0;for(integer i=0;i<32;i=i+1)flight[c][i]=0;end
  repeat(4)@(negedge clk);reset=0;
  for(integer i=0;i<16;i=i+1)begin cfg_we=1;cfg_idx=i;cfg_cost=costs[i];@(negedge clk);end cfg_we=0;
  forever begin
   av=0;pv=0;
   if(next<128)begin
    if(!have_token)av=!cmd_pending&&cycle%11!=3;else begin pv=1;pt=token;pn=nodes[next];pp=parents[next][63:0];stale=parents[next][64];epoch=phase+1;end
   end
   // 16B representation on epoch2, no reset or cost reload.
   mode16=phase==1;
   dr=cycle%17!=2&&occ[0]<32;mr=cycle%19!=3&&occ[1]<32;
   drv=0;rv=0;drd=0;rd=0;drt=0;rt=0;
   for(integer c=0;c<2;c=c+1)begin
    choice[c]=-1;for(integer i=0;i<32;i=i+1)if(flight[c][i]&&due[c][i]<=cycle&&cycle%23!=4)choice[c]=i;
    if(choice[c]>=0)begin
     if(c==0)begin drv=1;drt=tags[c][choice[c]];for(integer n=0;n<128;n=n+1)begin if(phase==0&&native_config[2]+(nodes[n]>>2)==lines[c][choice[c]])drd[nodes[n][1:0]*64+:64]=desc8[n];if(phase==1&&native_config[2]+(nodes[n]>>1)==lines[c][choice[c]])drd[nodes[n][0]*128+:128]=desc16[n];end end
     else begin rv=1;rt=tags[c][choice[c]];lookup=-1;for(integer b=0;b<512;b=b+1)if(b<native_config[0]&&native_config[3]+native_beats[b][319:256]==lines[c][choice[c]])lookup=b;if(lookup<0)$fatal(1,"unknown native beat %h",lines[c][choice[c]]);rd=native_beats[lookup][255:0];end
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
   if(av&&ar)cmd_pending=1;
   if(tv)begin token=at;have_token=1;cmd_pending=0;end
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
    idx=-1;for(integer n=0;n<4096;n=n+1)if(n<native_config[1]&&!seen[n]&&native_gold[n]=={od[l*32+:32],op[l*64+:64]}&&idx<0)idx=n;
    if(idx<0)$fatal(1,"native candidate mismatch dst=%0d pair=%h",od[l*32+:32],op[l*64+:64]);seen[idx]=1;got=got+1;
   end

   if(next==128&&idle&&occ[0]==0&&occ[1]==0)begin
    for(integer n=0;n<128;n=n+1)if(!parents[n][64]&&desc8[n][63]&&!target_seen[n])$fatal(1,"missing target");
    for(integer n=0;n<4096;n=n+1)if(n<native_config[1]&&!seen[n])$fatal(1,"missing candidate %0d",n);
    if(reserved!=128*(phase+1)||retired!=128*(phase+1)||desc_count!=128*(phase+1)||edge_parents!=128*(phase+1)||edge_completed!=edge_parents||edge_emitted!=got||target_count!=targets||issued_d!=returned_d||issued_e!=returned_e)$fatal(1,"conservation");
    $display("NATIVE_EPOCH_PASS phase=%0d cycles=%0d candidates=%0d",phase,cycle,got);
    if(phase==0)begin phase=1;next=0;for(integer n=0;n<16384;n=n+1)seen[n]=0;for(integer n=0;n<128;n=n+1)target_seen[n]=0;end
    else begin $display("TEST_PASS native L=%0d cycles=%0d candidates=%0d DESC=%0d EDGE=%0d",L,cycle,got,issued_d,issued_e);$fclose(fd);$finish;end
   end
  end
 end
endmodule
