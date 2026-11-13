`timescale 1ns/1ps
module bank_context_tb;
 reg [127:0] states;reg [15:0] busy;
 wire signed [31:0] fc,sc,pc,ac;
 wire [5:0] lc,npc,ii;wire iv;
 r2_bank_context_select dut(states,fc,sc,pc,ac,lc,npc);
 r2_first64 init_dut({48'b0,~busy},iv,ii);
 integer i,j,a,b,k,cases,ef,es,ep,ea,el,en,ei,s;
 reg [31:0] random_state;
 task check;
  begin
   ef=-1;es=-1;ep=-1;ea=-1;el=0;en=0;ei=-1;
   for(k=0;k<32;k=k+1)begin
    s=states[k*4+:4];
    if(s==0&&ef<0)ef=k;
    if(s!=0)el=el+1;
    if(s==1||s==2)en=en+1;
    if((s==1||s==5||s==9||s==11)&&es<0)es=k;
    if(s==3&&ep<0)ep=k;
    if(s==7&&ea<0)ea=k;
   end
   for(k=0;k<16;k=k+1)if(!busy[k]&&ei<0)ei=k;
   #1;
   if(fc!==ef||sc!==es||pc!==ep||ac!==ea||lc!=el||npc!=en)
    $fatal(1,"bank context selection/count mismatch case=%0d",cases);
   if(iv!==(ei>=0)||(iv&&ii!=ei))$fatal(1,"initialization selection mismatch");
   cases=cases+1;
  end
 endtask
 initial begin
  cases=0;busy=0;states=0;random_state=32'h19681112;
  for(a=0;a<16;a=a+1)begin states={32{a[3:0]}};check();end
  // Every pair of context positions/states, including absent/free/send and
  // duplicate contenders. Unselected positions use FREE or occupied WAIT.
  for(b=0;b<2;b=b+1)for(i=0;i<32;i=i+1)for(j=0;j<32;j=j+1)
   for(a=0;a<256;a=a+1)begin
    states=b?{32{4'd4}}:128'b0;
    states[i*4+:4]=a[3:0];states[j*4+:4]=a[7:4];check();
   end
  for(i=0;i<100000;i=i+1)begin
   for(j=0;j<32;j=j+1)begin
    random_state=random_state^(random_state<<13);
    random_state=random_state^(random_state>>17);
    random_state=random_state^(random_state<<5);
    states[j*4+:4]=random_state[3:0];
   end
   busy=random_state[31:16];check();
  end
  for(i=0;i<65536;i=i+1)begin busy=i;check();end
  $display("BANK_CONTEXT_PASS cases=%0d",cases);$finish;
 end
endmodule
