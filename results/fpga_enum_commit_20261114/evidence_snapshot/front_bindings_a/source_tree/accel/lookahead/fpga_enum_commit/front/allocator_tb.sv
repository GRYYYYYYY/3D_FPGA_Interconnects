`timescale 1ns/1ps
module allocator_tb;
 reg clk=0;always #2.5 clk=~clk;reg reset=1;reg [255:0] free_context;reg[7:0]valid,nonempty;
 wire[7:0]accepted[2],allocated[2];wire[63:0]context_id[2];integer file_id,cycle=0;reg[31:0]random_state=32'h7319feab;integer used_groups;
 for(genvar m=0;m<2;m=m+1)begin:mode
  allocator_grouped dut(.clk,.reset,.lane_rr(m==1),.free_context,.valid,.nonempty,.accepted(accepted[m]),.allocated(allocated[m]),.context_id(context_id[m]));
 end
 initial begin
  file_id=$fopen("allocator_cycles.txt","w");free_context=0;valid=0;nonempty=0;repeat(4)@(negedge clk);reset=0;
  for(integer c=0;c<1024;c=c+1)begin
   for(integer i=0;i<256;i=i+1)begin random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};free_context[i]=random_state[9];end
   if(c%23==0)free_context=0;if(c%23==1)free_context=256'b1<<255;if(c%23==2)free_context={256{1'b1}};
   valid=(9'b1<<(c%9))-1;nonempty=random_state[7:0];if(c%17==0)nonempty=0;
   @(negedge clk);
  end
  $display("TEST_PASS allocator finite_grants=8 cycles=1024");$fclose(file_id);$finish;
 end
 always @(posedge clk)if(!reset)begin
  cycle=cycle+1;
  $fwrite(file_id,"%0d %064h %02h %02h %02h %02h %016h %02h %02h %016h\n",cycle,free_context,valid,nonempty,accepted[0],allocated[0],context_id[0],accepted[1],allocated[1],context_id[1]);
  for(integer m=0;m<2;m=m+1)begin
   used_groups=0;
   for(integer n=0;n<8;n=n+1)if(allocated[m][n])begin
    if(!accepted[m][n]||!free_context[context_id[m][n*8+:8]])$fatal(1,"invalid allocation");
    if(used_groups&(1<<(context_id[m][n*8+:8]/32)))$fatal(1,"more than one group write");
    used_groups=used_groups|(1<<(context_id[m][n*8+:8]/32));
   end
  end
 end
endmodule
