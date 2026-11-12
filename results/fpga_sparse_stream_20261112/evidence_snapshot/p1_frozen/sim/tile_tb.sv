`timescale 1ns/1ps
module tile_tb;
 reg clk=0;always #2.5 clk=~clk;
 reg rst=1,start=0;reg [31:0] source,row_base,edge_base,cost_base,cell_base,targets;reg [6:0] cell_count;reg [4:0] cost_count;
 wire done,error;wire [24:0] mv,mw,rr;reg [24:0] mr=0,rv=0;wire [799:0] ma;wire [149:0] mi;wire [6399:0] md;reg [149:0] ri=0;reg [6399:0] rd=0;reg [5:0] oi=0;wire [63:0] op;
 sparse_tile dut(.clk(clk),.rst(rst),.start(start),.source(source),.row_base(row_base),.edge_base(edge_base),.cost_base(cost_base),.cell_base(cell_base),.cell_count(cell_count),.targets(targets),.cost_count(cost_count),.done(done),.error(error),.mem_valid(mv),.mem_ready(mr),.mem_write(mw),.mem_line(ma),.mem_id(mi),.mem_data(md),.rsp_valid(rv),.rsp_ready(rr),.rsp_id(ri),.rsp_data(rd),.output_index(oi),.output_pair(op));
 reg [255:0] memory[0:32767];reg [63:0] expected[0:4095];
 reg used[0:24][0:63],write_[0:24][0:63];reg [31:0] address[0:24][0:63];reg [5:0] id[0:24][0:63];reg [255:0] data[0:24][0:63];integer due[0:24][0:63],selected[0:24],free_slot[0:24],next_cmd[0:24];
 integer cycle=0,c,k,p,q,x,fd,nj,nn,ncells,ncost,rb,eb,cb,mb,stride,nlines,nread,src,nt,watch;
 string dir;
 initial begin
  if(!$value$plusargs("DIR=%s",dir))$fatal(1,"DIR required");
  $readmemh("memory.hex",memory);$readmemh("expected.hex",expected);
  fd=$fopen("config.txt","r");nread=$fscanf(fd,"%d %d %d %d %d %d %d %d %d %d\n",nj,nn,ncells,ncost,rb,eb,cb,mb,stride,nlines);
  for(c=0;c<25;c=c+1)begin selected[c]=-1;next_cmd[c]=0;for(k=0;k<64;k=k+1)used[c][k]=0;end
  row_base=rb;edge_base=eb;cost_base=cb;cell_count=ncells;cost_count=ncost;
  repeat(4)@(negedge clk);rst=0;
  for(q=0;q<nj;q=q+1)begin
   nread=$fscanf(fd,"%d %d\n",src,nt);source=src;targets=nt;cell_base=mb+q*stride;start=1;@(negedge clk);start=0;watch=0;
   while(!done)begin @(negedge clk);watch=watch+1;if(error)$fatal(1,"DUT error sample %d",q);if(watch>2000000)$fatal(1,"watchdog");end
   for(x=0;x<ncells;x=x+1)begin oi=x;repeat(2)@(negedge clk);if(op!==expected[q*ncells+x])$fatal(1,"output q=%d c=%d got=%h expected=%h",q,x,op,expected[q*ncells+x]);end
   $display("XSIM_SAMPLE_PASS sample=%0d cycle=%0d",q,cycle);
  end
  for(c=0;c<25;c=c+1)for(k=0;k<64;k=k+1)if(used[c][k])$fatal(1,"undrained memory");
  $display("XSIM_TILE_PASS jobs=%0d cycles_including_readback=%0d",nj,cycle);$finish;
 end
 always @(negedge clk)if(!rst)begin
  mr=0;rv=0;
  for(integer ch=0;ch<25;ch=ch+1)begin
   free_slot[ch]=-1;for(integer i=0;i<64;i=i+1)if(!used[ch][i]&&free_slot[ch]<0)free_slot[ch]=i;
   if(free_slot[ch]>=0&&cycle>=next_cmd[ch]&&(cycle+ch)%7!=0)mr[ch]=1;
   if(selected[ch]<0)for(integer i=63;i>=0;i=i-1)if(used[ch][i]&&due[ch][i]<=cycle&&selected[ch]<0)selected[ch]=i;
   if(selected[ch]>=0)begin rv[ch]=1;ri[ch*6+:6]=id[ch][selected[ch]];rd[ch*256+:256]=data[ch][selected[ch]];end
  end
 end
 always @(posedge clk)begin
  cycle=cycle+1;
  if(!rst)begin
   for(integer ch=0;ch<25;ch=ch+1)begin
    if(rv[ch]&&rr[ch])begin if(write_[ch][selected[ch]])memory[address[ch][selected[ch]]]=data[ch][selected[ch]];used[ch][selected[ch]]=0;selected[ch]=-1;end
    if(mv[ch]&&mr[ch])begin
     if(ma[ch*32+:32]>=nlines)$fatal(1,"address range");
     used[ch][free_slot[ch]]=1;write_[ch][free_slot[ch]]=mw[ch];address[ch][free_slot[ch]]=ma[ch*32+:32];id[ch][free_slot[ch]]=mi[ch*6+:6];data[ch][free_slot[ch]]=mw[ch]?md[ch*256+:256]:memory[ma[ch*32+:32]];due[ch][free_slot[ch]]=cycle+60+(ch+cycle)%7;next_cmd[ch]=cycle+2;
    end
   end
  end
 end
endmodule
