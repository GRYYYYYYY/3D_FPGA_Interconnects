`timescale 1ns/1ps
// TESTBENCH ONLY. Sparse runtime input; finite real physical tags/ports.
// No expected/golden data is read by this module. At reset only transport state
// resets; backing memory persists, so DUT initialization cannot be bypassed.
module cp_sparse_memory #(
 parameter integer PORT_ROWS=512,
 parameter integer LATENCY_CYCLES=16, ISSUE_CYCLES=1,
 parameter integer JITTER_CYCLES=0, STALL_PERIOD=0, STALL_OPEN=0
)(
 input wire clk,reset,
 input wire [31:0] mv,mw,output reg [31:0] mr,
 input wire [1023:0] ml,input wire [159:0] mtag,input wire [8191:0] md,
 output reg [31:0] sv,input wire [31:0] sr,
 output reg [159:0] stag,output reg [8191:0] sd,output reg [63:0] status,
 output reg idle,output integer issued,returned,peak_credits,out_of_order
);
 reg [255:0] memory[0:32*PORT_ROWS-1];reg initialized[0:32*PORT_ROWS-1];
 reg [31:0] busy[0:31],write_pending[0:31];
 reg [31:0] address_pending[0:31][0:31];reg [255:0] data_pending[0:31][0:31];
 integer due[0:31][0:31],order_id[0:31][0:31],next_issue[0:31],live[0:31];
 reg [31:0] consumed;integer cycle=0,sequence_next=0;
 integer service_latency=LATENCY_CYCLES,service_issue=ISSUE_CYCLES,service_jitter=JITTER_CYCLES,service_period=STALL_PERIOD,service_open=STALL_OPEN;
 task automatic configure_service(input integer latency,issue_gap,jitter,stall_period,stall_open);
  begin
   if(!idle||latency<1||issue_gap<1||jitter<0||stall_period<0||stall_open<0||stall_open>stall_period)$fatal(1,"MEM_SERVICE_RECONFIG");
   service_latency=latency;service_issue=issue_gap;service_jitter=jitter;service_period=stall_period;service_open=stall_open;
  end
 endtask
 reg [31:0] cfg[0:21];integer max_line=-1,label_begin=0,scratch_begin=0,output_begin=0,label_lines=0,output_lines=0;
 function automatic integer index(input reg[31:0] line);
  begin index=(line[4:0]*PORT_ROWS)+(line>>5);end
 endfunction
 function automatic reg writable(input reg[31:0] line);
  begin writable=(line>=label_begin&&line<label_begin+label_lines)||
   (line>=scratch_begin&&line<scratch_begin+label_lines)||
   (line>=output_begin&&line<output_begin+output_lines);end
 endfunction
 task automatic load_native(input string directory);
  integer fd,rc,line_number;reg[31:0] address;reg[255:0] word;string filename;
  begin
   if(!idle)$fatal(1,"MEM_LOAD_WHILE_BUSY");
   filename=$sformatf("%s/config.hex",directory);$readmemh(filename,cfg);
   if(cfg[0]!==32'h43504631||cfg[1]!==1||cfg[20]>PORT_ROWS)$fatal(1,"MEM_FIXTURE_CONFIG");
   max_line=cfg[19];label_begin=cfg[14];scratch_begin=cfg[15];output_begin=cfg[16];label_lines=(cfg[2]+3)/4;output_lines=cfg[6]*cfg[17];
   for(integer i=0;i<32*PORT_ROWS;i=i+1)begin initialized[i]=0;memory[i]={8{32'hdeadc0de}};end
   filename=$sformatf("%s/input/lines.txt",directory);fd=$fopen(filename,"r");if(!fd)$fatal(1,"MEM_FIXTURE_OPEN %s",directory);line_number=0;
   while(!$feof(fd))begin
    rc=$fscanf(fd,"%h %h\n",address,word);
    if(rc==2)begin
     if(address>max_line||(address>>5)>=PORT_ROWS||writable(address)||initialized[index(address)])$fatal(1,"MEM_FIXTURE_LINE %0d addr=%h",line_number,address);
     memory[index(address)]=word;initialized[index(address)]=1;line_number=line_number+1;
    end else if(rc!=-1)$fatal(1,"MEM_FIXTURE_PARSE line=%0d rc=%0d",line_number,rc);
   end
   $fclose(fd);$display("MEM_FIXTURE_LOADED %s lines=%0d maximum=%0d",directory,line_number,max_line);
  end
 endtask
 function automatic reg[255:0] peek(input reg[31:0] address);
  begin
   if(address>max_line||(address>>5)>=PORT_ROWS||!initialized[index(address)])$fatal(1,"MEM_PEEK_UNINITIALIZED %h",address);
   peek=memory[index(address)];
  end
 endfunction
 initial begin
  mr=0;sv=0;stag=0;sd=0;status=0;consumed=0;idle=1;issued=0;returned=0;peak_credits=0;out_of_order=0;
  if(LATENCY_CYCLES<1||ISSUE_CYCLES<1||JITTER_CYCLES<0||STALL_PERIOD<0||STALL_OPEN<0||STALL_OPEN>STALL_PERIOD)$fatal(1,"MEM_SERVICE_CONFIG");
  for(integer p=0;p<32;p=p+1)begin busy[p]=0;write_pending[p]=0;next_issue[p]=0;live[p]=0;end
  for(integer i=0;i<32*PORT_ROWS;i=i+1)initialized[i]=0;
 end
 always @(posedge clk)begin:edge_update
  integer tag,idx;reg[31:0] previous;
  if(reset)begin
   cycle=0;consumed=0;sequence_next=0;issued=0;returned=0;peak_credits=0;out_of_order=0;
   for(integer p=0;p<32;p=p+1)begin busy[p]=0;write_pending[p]=0;next_issue[p]=0;live[p]=0;end
  end else begin
   cycle=cycle+1;consumed=sv&sr;
   for(integer p=0;p<32;p=p+1)begin
    previous=busy[p];
    if(sv[p]&&sr[p])begin
     tag=stag[p*5+:5];if(!previous[tag])$fatal(1,"MEM_UNKNOWN_ACK p=%0d tag=%0d",p,tag);
     if(cycle<due[p][tag])$fatal(1,"MEM_EARLY_ACK");
     for(integer k=0;k<32;k=k+1)if(previous[k]&&order_id[p][k]<order_id[p][tag])begin out_of_order=out_of_order+1;break;end
     if(write_pending[p][tag])begin idx=index(address_pending[p][tag]);memory[idx]=data_pending[p][tag];initialized[idx]=1;end
     busy[p][tag]=0;live[p]=live[p]-1;returned=returned+1;
    end
    if(mv[p]&&mr[p])begin
     tag=mtag[p*5+:5];
     if(previous[tag]||live[p]>=32)$fatal(1,"MEM_TAG_REUSE_OR_CREDIT p=%0d tag=%0d",p,tag);
     if(ml[p*32+:5]!=p||(ml[p*32+:32]>>5)>=PORT_ROWS||ml[p*32+:32]>max_line)$fatal(1,"MEM_ADDRESS_OWNER_RANGE p=%0d line=%h",p,ml[p*32+:32]);
     if(mw[p]&&!writable(ml[p*32+:32]))$fatal(1,"MEM_WRITE_READONLY");
     busy[p][tag]=1;write_pending[p][tag]=mw[p];address_pending[p][tag]=ml[p*32+:32];data_pending[p][tag]=md[p*256+:256];order_id[p][tag]=sequence_next;sequence_next=sequence_next+1;
     due[p][tag]=cycle+service_latency+(service_jitter?((tag*7+p*3)%service_jitter):0);
     next_issue[p]=cycle+service_issue;live[p]=live[p]+1;issued=issued+1;if(live[p]>peak_credits)peak_credits=live[p];
    end
   end
  end
 end
 // Drives after accepted-edge accounting. Use captured consumed, never the
 // current negedge sr, to preserve a stalled response even if sr changes here.
 always @(negedge clk)begin:drive
  integer sel;idle=1;
  for(integer p=0;p<32;p=p+1)begin
   mr[p]=!reset&&live[p]<32&&cycle+1>=next_issue[p]&&(!service_period||((cycle+1+p)%service_period)<service_open);
   if(reset)begin sv[p]=0;stag[p*5+:5]=0;sd[p*256+:256]=0;status[p*2+:2]=0;end
   else if(!sv[p]||consumed[p])begin
    sel=-1;
    for(integer k=0;k<32;k=k+1)if(busy[p][k]&&due[p][k]<=cycle+1&&(sel<0||order_id[p][k]>order_id[p][sel]))sel=k;
    sv[p]=sel>=0;
    if(sel>=0)begin
     stag[p*5+:5]=sel;status[p*2+:2]=0;
     if(write_pending[p][sel])sd[p*256+:256]=0;
     else begin
      if(!initialized[index(address_pending[p][sel])])$fatal(1,"MEM_READ_UNINITIALIZED p=%0d line=%h",p,address_pending[p][sel]);
      sd[p*256+:256]=memory[index(address_pending[p][sel])];
     end
    end
   end
   if(live[p]||sv[p])idle=0;
  end
 end
endmodule
