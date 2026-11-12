`timescale 1ns/1ps
module pop_units_tb;
 reg clk=0;always #5 clk=~clk;
 reg rst=1,iv=0,ar=0,br=0;wire ir,av,bv;reg [31:0] node=0;wire [31:0] an,bn;reg [63:0] pair=0;wire [63:0] ap,bp;wire idle;wire [31:0] accepted;
 r2_pop_fork fork_pop(clk,rst,iv,ir,node,pair,av,ar,an,ap,bv,br,bn,bp,idle,accepted);
 reg init=0,rv=0,export_en=0;wire rr;reg [11:0] index=0,export_index=0;reg [63:0] value=0;reg [5:0] qid=3,event_qid=3;reg [15:0] epoch=16'hffff,event_epoch=16'hffff;
 wire [63:0] result;wire reduce_idle,init_done,error;wire [31:0] recorded,retired,forwarded;
 r2_cell_reducer reducer(clk,rst,init,13'd4096,qid,epoch,rv,rr,index,value,event_qid,event_epoch,export_en,export_index,result,reduce_idle,init_done,error,recorded,retired,forwarded);
 reg [64:0] reference[0:4095];integer a=0,b=0,s=0,i,j,visits=0,updates=0,seed=20261112;reg [31:0] random_bits;
 always @(posedge clk)if(!rst)begin
  if(av&&ar)begin if(an!=a||ap!={32'h3f800000,a[31:0]})$fatal(1,"fork A duplicate/loss/payload %d %d",an,a);a=a+1;end
  if(bv&&br)begin if(bn!=b||bp!={32'h3f800000,b[31:0]})$fatal(1,"fork B duplicate/loss/payload");b=b+1;end
  if(iv&&ir)s=s+1;
  if(rv&&rr)begin if(!reference[index][64])visits=visits+1;if(!reference[index][64]||value<reference[index][63:0])reference[index]={1'b1,value};updates=updates+1;end
 end
 initial begin
  for(i=0;i<4096;i=i+1)reference[i]=0;
  repeat(3)@(negedge clk);rst=0;init=1;
  while(!init_done)@(negedge clk);init=0;
  // Both consumers stall independently; producer holds exactly until both accept.
  while(s<4000)begin iv=1;node=s;pair={32'h3f800000,s[31:0]};ar=($random(seed)&7)!=0;br=($random(seed)&3)==0;@(negedge clk);end
  iv=0;ar=1;br=1;repeat(3)@(negedge clk);
  if(a!=4000||b!=4000||accepted!=4000||!idle)$fatal(1,"fork drain");
  // Conflict-free and long same-cell runs exercise synchronous read/write forwarding.
  for(j=0;j<20000;j=j+1)begin
   rv=(j%29)!=0;index=j<4096?j:((j%64)<40?12'd17:($random(seed)&4095));random_bits=$random(seed);
   value={32'h3f800000+(random_bits&32'h00ffffff),32'h40000000+(j&1023)};
   @(negedge clk);
  end
  rv=0;repeat(4)@(negedge clk);
  if(error||!reduce_idle||recorded!=visits||retired!=updates||forwarded<1000)$fatal(1,"reducer counters/forwarding");
  export_en=1;
  for(j=0;j<4096;j=j+1)begin export_index=j;repeat(2)@(negedge clk);
   if(result!==(reference[j][64]?reference[j][63:0]:64'h7fc000007fc00000))$fatal(1,"whole-pair export %d got %h expected %h",j,result,reference[j]);
  end
  export_en=0;event_qid=4;rv=1;index=0;@(negedge clk);rv=0;repeat(2)@(negedge clk);if(!error)$fatal(1,"qid admission missing");
  $display("POP_UNITS_PASS fork=4000 updates=%0d unique=%0d forwarded=%0d",updates,visits,forwarded);$finish;
 end
 initial begin #10000000;$fatal(1,"watchdog");end
endmodule
