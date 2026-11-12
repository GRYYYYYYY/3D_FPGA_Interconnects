`timescale 1ns/1ps
module graph_tb #(parameter OWNERS=8,MAX_LINES=20000);
 reg clk=0;always #2.5 clk=~clk;
 reg rst=1,start=0;reg [31:0] nodes,jobs,cells,base_row,base_edge,base_node,base_cost,base_cell,base_job,base_label,base_prop,base_pending,base_closed,base_output;
 wire [31:0] mem_valid,mem_write;reg [31:0] mem_ready;wire [1023:0] mem_line,mem_mask;wire [8191:0] mem_data;wire [415:0] mem_id;
 reg [31:0] rsp_valid=0;wire [31:0] rsp_ready;reg [415:0] rsp_id;reg [8191:0] rsp_data;
 wire done,error;wire [31:0] qid,waves;wire [63:0] cycle;wire [7:0] state;wire [OWNERS*32-1:0] accepted,retired;
 graph_top #(.OWNERS(OWNERS)) dut(.*);
 reg [255:0] memory[0:MAX_LINES-1];reg [63:0] expected[0:65535];
 reg [63:0] occupied[0:31];reg pwrite[0:2047];reg [31:0] pline[0:2047],pmask[0:2047];
 reg [255:0] pdata[0:2047];reg [12:0] pid[0:2047];integer due[0:2047];
 integer bank_next[0:511],next_link[0:31],last_dir[0:31],last_service[0:31],sending[0:31],free_slot[0:31];
 integer base_latency=60,link_gap=2,bank_gap=8,turn_gap=4;
 integer tick=0,lines,rc,fd,logfd,txnfd,outfd,summaryfd,diff=0,occ,hwm=0;longint reads=0,writes=0;
 reg [7:0] prev_state=255;reg [31:0] prev_q=32'hffffffff;reg [31:0] held_valid=0;reg [333:0] held[0:31];
 string dir;
 always @*begin
 mem_ready=0;
 for(integer c=0;c<32;c=c+1)begin
 free_slot[c]=-1;for(integer k=63;k>=0;k=k-1)if(!occupied[c][k])free_slot[c]=k;
 mem_ready[c]=free_slot[c]>=0&&tick>=next_link[c]&&tick>=bank_next[c*16+((mem_line[c*32+:32]/32)%16)]&&
 ((mem_write[c]==last_dir[c])||tick-last_service[c]>=turn_gap);
 end end
 always @(posedge clk)begin
 tick<=tick+1;
 if(tick%100000==0)$display("PROGRESS cycle=%0d state=%0d q=%0d waves=%0d",tick,state,qid,waves);
 if(tick>300000000)$fatal(1,"watchdog state=%d q=%d wave=%d",state,qid,waves);
 if(error)$fatal(1,"DUT error state=%d q=%d wave=%d",state,qid,waves);
 if(state!=prev_state||qid!=prev_q)begin $fdisplay(logfd,"%0d,%0d,%0d,%0d",tick,qid,waves,state);prev_state<=state;prev_q<=qid;end
 for(integer c=0;c<32;c=c+1)begin
 if(held_valid[c]&&(!mem_valid[c]||{mem_write[c],mem_line[c*32+:32],mem_mask[c*32+:32],mem_id[c*13+:13],mem_data[c*256+:256]}!==held[c]))$fatal(1,"unstable command ch%0d",c);
 held_valid[c]<=mem_valid[c]&&!mem_ready[c];held[c]<={mem_write[c],mem_line[c*32+:32],mem_mask[c*32+:32],mem_id[c*13+:13],mem_data[c*256+:256]};
 if(mem_valid[c]&&mem_ready[c])begin
 if(mem_line[c*32+:32]>=lines||mem_line[c*32+:32]%32!=c)$fatal(1,"bad address/channel");
 for(integer k=0;k<64;k=k+1)if(occupied[c][k]&&pline[c*64+k]==mem_line[c*32+:32]&&(pwrite[c*64+k]||mem_write[c]))$fatal(1,"RAW ordering ch%0d",c);
 occupied[c][free_slot[c]]<=1;pline[c*64+free_slot[c]]<=mem_line[c*32+:32];pwrite[c*64+free_slot[c]]<=mem_write[c];
 pmask[c*64+free_slot[c]]<=mem_mask[c*32+:32];pdata[c*64+free_slot[c]]<=mem_write[c]?mem_data[c*256+:256]:memory[mem_line[c*32+:32]];
 pid[c*64+free_slot[c]]<=mem_id[c*13+:13];due[c*64+free_slot[c]]<=tick+base_latency;
 bank_next[c*16+((mem_line[c*32+:32]/32)%16)]<=tick+bank_gap;next_link[c]<=tick+link_gap;last_dir[c]<=mem_write[c];last_service[c]<=tick;
 if(mem_write[c])writes=writes+1;else reads=reads+1;
 $fdisplay(txnfd,"%0d,Q,%0d,%0d,%0d,%0d",tick,c,mem_id[c*13+:13],mem_write[c],mem_line[c*32+:32]);
 end
 if(rsp_valid[c]&&rsp_ready[c])begin
 if(pwrite[c*64+sending[c]])for(integer b=0;b<32;b=b+1)if(pmask[c*64+sending[c]][b])memory[pline[c*64+sending[c]]][b*8+:8]<=pdata[c*64+sending[c]][b*8+:8];
 occupied[c][sending[c]]<=0;rsp_valid[c]<=0;
 $fdisplay(txnfd,"%0d,R,%0d,%0d,%0d,%0d",tick,c,rsp_id[c*13+:13],pwrite[c*64+sending[c]],pline[c*64+sending[c]]);
 end
 if(!rsp_valid[c])begin
 integer chosen;chosen=-1;for(integer k=0;k<64;k=k+1)if(occupied[c][k]&&due[c*64+k]<=tick)chosen=k;
 if(chosen>=0)begin sending[c]<=chosen;rsp_valid[c]<=1;rsp_id[c*13+:13]<=pid[c*64+chosen];rsp_data[c*256+:256]<=pdata[c*64+chosen];end
 end
 end
 end
 initial begin
 if(!$value$plusargs("DIR=%s",dir))$fatal(1,"DIR missing");rc=$value$plusargs("LATENCY=%d",base_latency);
 fd=$fopen($sformatf("%s/config.txt",dir),"r");rc=$fscanf(fd,"%d %d %d %d\n",nodes,jobs,cells,lines);if(rc!=4||lines>MAX_LINES)$fatal(1,"configuration capacity");
 rc=$fscanf(fd,"%d %d %d %d %d %d %d %d %d %d %d",base_row,base_edge,base_node,base_cost,base_cell,base_job,base_label,base_prop,base_pending,base_closed,base_output);if(rc!=11)$fatal(1,"bases missing");$fclose(fd);
 $readmemh($sformatf("%s/memory.hex",dir),memory,0,lines-1);$readmemh($sformatf("%s/expected.hex",dir),expected,0,jobs*cells-1);
 if(^memory[base_job]===1'bx||^memory[base_row]===1'bx||^expected[0]===1'bx)$fatal(1,"runtime load failure");
 logfd=$fopen($sformatf("%s/states.csv",dir),"w");$fdisplay(logfd,"cycle,qid,waves,state");txnfd=$fopen($sformatf("%s/transactions.csv",dir),"w");$fdisplay(txnfd,"cycle,event,channel,id,write,line");
 outfd=$fopen($sformatf("%s/actual.hex",dir),"w");summaryfd=$fopen($sformatf("%s/summary.json",dir),"w");
 for(integer c=0;c<32;c=c+1)begin occupied[c]=0;next_link[c]=0;last_dir[c]=0;last_service[c]=-100;end
 for(integer b=0;b<512;b=b+1)bank_next[b]=0;
 repeat(4)@(negedge clk);rst=0;start=1;@(negedge clk);start=0;
 wait(done);@(negedge clk);
 for(integer c=0;c<32;c=c+1)if(occupied[c]!=0||rsp_valid[c]||mem_valid[c])$fatal(1,"early done memory outstanding");
 for(integer o=0;o<OWNERS;o=o+1)if(accepted[o*32+:32]!=retired[o*32+:32])$fatal(1,"lost candidates");
 for(integer x=0;x<jobs*cells;x=x+1)begin
 $fdisplay(outfd,"%016h",memory[base_output+x/4][(x%4)*64+:64]);
 if(memory[base_output+x/4][(x%4)*64+:64]!==expected[x])begin diff=diff+1;if(diff<10)$display("DIFF %0d actual=%h expected=%h",x,memory[base_output+x/4][(x%4)*64+:64],expected[x]);end
 end
 $fdisplay(summaryfd,"{\"owners\":%0d,\"jobs\":%0d,\"cycles\":%0d,\"waves\":%0d,\"latency_cycles\":%0d,\"reads32B\":%0d,\"writes32B\":%0d,\"compared_pairs\":%0d,\"differences\":%0d}",OWNERS,jobs,tick,waves,base_latency,reads,writes,jobs*cells,diff);
 if(diff)$fatal(1,"full output difference");
 $display("TEST_PASS complete batch jobs=%0d waves=%0d cycles=%0d",jobs,waves,tick);$fclose(logfd);$fclose(txnfd);$fclose(outfd);$fclose(summaryfd);$finish;
 end
endmodule
