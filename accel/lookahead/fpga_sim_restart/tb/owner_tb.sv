`timescale 1ns/1ps
module owner_tb #(parameter OWNER_BITS=0, N=2048);
 reg clk=0;always #2.5 clk=~clk;
 reg rst=1,req_valid=0,fence=0;wire req_ready,fence_done,error;
 reg [23:0] req_line;reg [1:0] req_sector;reg [63:0] req_pair;
 wire mem_valid,mem_write;reg mem_ready;wire [23:0] mem_line;wire [255:0] mem_data;wire [5:0] mem_id;
 reg rsp_valid=0;wire rsp_ready;reg [5:0] rsp_id;reg [255:0] rsp_data;
 wire [31:0] accepted,retired,hits,merges,reads,writes,raw_stall,capacity_stall,fence_cycles;
 wire [6:0] request_hwm,response_hwm;wire [5:0] mshr_hwm;wire [4:0] dirty_hwm;
 owner_service #(.OWNER_BITS(OWNER_BITS)) dut(.*);
 localparam DEPTH=64;
 reg [255:0] memory[0:N-1];reg [255:0] expected[0:N*2-1];
 reg [63:0] occupied=0;reg pending_write[0:63];reg [23:0] pending_line[0:63];
 reg [255:0] pending_data[0:63];reg [5:0] pending_id[0:63];integer due[0:63];integer bank_next[0:15];
 integer cycle=0,free_slot,chosen=-1,sending=-1,i,bank,occupied_count,max_outstanding=0;
 integer base_latency=600,write_latency=800; // stress scenario, separately named; 5 ns/cycle
 integer next_link=0,last_dir=0,last_service=-1000;
 integer actionfd,txnfd,logfd,tracefd,outfd,stimfd,n,op,l,s,phase=0,diffs=0,totalaccepted=0;
 reg [63:0] p;string dir;
 reg was_stalled=0;reg [286:0] held_cmd;
 always @* begin
 free_slot=-1;occupied_count=0;
 for(integer j=63;j>=0;j=j-1)if(!occupied[j])free_slot=j;else occupied_count=occupied_count+1;
 bank=(mem_line/32)%16;
 // One declared physical channel, 32B shared read/write link, 4 GB/s.
 // 8ns link gap quantized conservatively to 2 cycles => actual 3.2 GB/s.
 mem_ready=free_slot>=0&&cycle>=next_link&&cycle>=bank_next[bank]&&
 ((mem_write==last_dir)||(cycle-last_service>=4))&&cycle%19!=0;
 end
 always @(posedge clk)begin
 cycle<=cycle+1;
 if(was_stalled && (!mem_valid || {mem_write,mem_line,mem_data,mem_id}!==held_cmd))$fatal(1,"command changed while stalled");
 was_stalled<=mem_valid&&!mem_ready;held_cmd<={mem_write,mem_line,mem_data,mem_id};
 if(cycle>1000000)$fatal(1,"watchdog");
 if(error)$fatal(1,"DUT protocol/numeric error cycle=%0d",cycle);
 if(occupied_count>max_outstanding)max_outstanding<=occupied_count;
 if(mem_valid&&mem_ready)begin
 if(mem_line>=N)$fatal(1,"out of range");
 for(integer j=0;j<64;j=j+1)if(occupied[j]&&pending_line[j]==mem_line&&(pending_write[j]||mem_write))$fatal(1,"RAW ordering violated");
 $fdisplay(txnfd,"%0d,request,%0d,%0d,%0d,%064h",cycle,mem_id,mem_write,mem_line,mem_data);
 occupied[free_slot]<=1;pending_line[free_slot]<=mem_line;pending_write[free_slot]<=mem_write;
 pending_data[free_slot]<=mem_write?mem_data:memory[mem_line];pending_id[free_slot]<=mem_id;
 due[free_slot]<=cycle+(mem_write?write_latency:base_latency)+(mem_line%7);
 bank_next[bank]<=cycle+8;next_link<=cycle+2;last_dir<=mem_write;last_service<=cycle;
 end
 if(rsp_valid&&rsp_ready)begin
 $fdisplay(txnfd,"%0d,response,%0d,%0d,%0d,%064h",cycle,rsp_id,pending_write[sending],pending_line[sending],rsp_data);
 if(pending_write[sending])memory[pending_line[sending]]<=pending_data[sending];
 occupied[sending]<=0;rsp_valid<=0;sending<=-1;
 end
 if(!rsp_valid&&cycle%13!=0)begin
 chosen=-1;for(integer j=0;j<64;j=j+1)if(occupied[j]&&due[j]<=cycle)chosen=j;
 if(chosen>=0)begin rsp_valid<=1;sending<=chosen;rsp_id<=pending_id[chosen];rsp_data<=pending_data[chosen];end
 end
 if(dut.qp)$fdisplay(actionfd,"%0d,reduce,%0d,%0d,%0d,%0d",cycle,dut.line,dut.victim,dut.hit,dut.match_m);
 if(dut.rpop&&!dut.rd[261])$fdisplay(actionfd,"%0d,fill,%0d,%0d,-1,-1",cycle,dut.ml[dut.rd[260:256]],dut.slot[dut.rd[260:256]]);
 if(logfd)$fdisplay(logfd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",cycle,req_valid,req_ready,mem_valid,mem_ready,mem_write,rsp_valid,rsp_ready,dut.qc,dut.rc,dut.nm,dut.nd,accepted,retired,fence_done);
 end
 initial begin
 if(!$value$plusargs("DIR=%s",dir))dir=".";
 n=$value$plusargs("READ_CYCLES=%d",base_latency);n=$value$plusargs("WRITE_CYCLES=%d",write_latency);
 logfd=$fopen($sformatf("%0s/cycles.csv",dir),"w");$fdisplay(logfd,"cycle,req_valid,req_ready,mem_valid,mem_ready,write,rsp_valid,rsp_ready,req_occupancy,rsp_occupancy,mshr,dirty,accepted,retired,fence_done");
 actionfd=$fopen($sformatf("%0s/actions.csv",dir),"w");$fdisplay(actionfd,"cycle,event,line,slot,hit,mshr");
 txnfd=$fopen($sformatf("%0s/transactions.csv",dir),"w");$fdisplay(txnfd,"cycle,event,id,write,line,data");
 tracefd=$fopen($sformatf("%0s/summary.jsonl",dir),"w");outfd=$fopen($sformatf("%0s/actual.hex",dir),"w");
 stimfd=$fopen($sformatf("%0s/stimulus.txt",dir),"r");if(!stimfd)$fatal(1,"missing stimulus");
 $readmemh($sformatf("%0s/expected.hex",dir),expected);
 for(i=0;i<N;i=i+1)memory[i]={4{64'h7f8000007f800000}};
 n=$fopen($sformatf("%0s/initial.hex",dir),"r");
 if(n)begin $fclose(n);$readmemh($sformatf("%0s/initial.hex",dir),memory);end
 for(i=0;i<16;i=i+1)bank_next[i]=0;
 repeat(4)@(negedge clk);rst=0;
 while(!$feof(stimfd))begin
 n=$fscanf(stimfd,"%d %h %h %h\n",op,l,s,p);
 if(n!=4)$fatal(1,"malformed stimulus");
 if(op==0)begin
 req_valid=1;req_line=l;req_sector=s;req_pair=p;
 @(posedge clk);while(!req_ready)@(posedge clk);
 @(negedge clk);req_valid=0;
 end else if(op==1)begin
 @(negedge clk);fence=1;@(negedge clk);fence=0;
 wait(fence_done);@(negedge clk);
 if(occupied!=0||rsp_valid||accepted!=retired)$fatal(1,"early fence");
 for(i=0;i<N;i=i+1)begin
 $fdisplay(outfd,"%064h",memory[i]);
 if(memory[i]!==expected[phase*N+i])begin diffs=diffs+1;$display("DIFF phase=%0d line=%0d actual=%h expected=%h",phase,i,memory[i],expected[phase*N+i]);end
 end
 $fdisplay(tracefd,"{\"phase\":%0d,\"cycle\":%0d,\"accepted\":%0d,\"retired\":%0d,\"hits\":%0d,\"merges\":%0d,\"reads32B\":%0d,\"writes32B\":%0d,\"raw_stall\":%0d,\"capacity_stall\":%0d,\"fence_cycles\":%0d,\"request_hwm\":%0d,\"response_hwm\":%0d,\"mshr_hwm\":%0d,\"dirty_hwm\":%0d,\"memory_outstanding_hwm\":%0d,\"diff_words\":%0d}",phase,cycle,accepted,retired,hits,merges,reads,writes,raw_stall,capacity_stall,fence_cycles,request_hwm,response_hwm,mshr_hwm,dirty_hwm,max_outstanding,diffs);
 phase=phase+1;
 end else if(op==2)begin
 if(occupied!=0)$fatal(1,"unsafe reset");
 @(negedge clk);rst=1;repeat(4)@(negedge clk);rst=0;
 end else $fatal(1,"unknown opcode");
 end
 if(diffs)$fatal(1,"whole memory mismatch count=%0d",diffs);
 if(phase!=2)$fatal(1,"missing phases");
 $display("TEST_PASS whole memory exact; cycles=%0d phases=%0d",cycle,phase);
 $fclose(actionfd);$fclose(txnfd);$fclose(logfd);$fclose(tracefd);$fclose(outfd);$finish;
 end
endmodule
