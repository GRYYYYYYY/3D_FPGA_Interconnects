`timescale 1ns/1ps
// Eight referenced transactions, 32 maximum events. Enqueue never unlocks Tx.
module lf_journal(input wire clk,reset,
 input wire ev,output wire er,input wire[2:0] eslot,input wire[7:0] egen,input wire[3:0] emask,
 output wire[2:0] issue_slot,input wire[21:0] issue_node,input wire[111:0] issue_args,
 output wire cv,input wire cr,output wire[11:0] cbucket,output wire[31:0] cnode,carg,
 input wire av,output wire ar,input wire[1:0] astatus,
 output wire finish_valid,input wire finish_ready,output wire[2:0] finish_slot,output wire[7:0] finish_gen,
 output wire idle,output reg error,output reg[3:0] peak,output reg[5:0] event_peak,
 output wire[3:0] count,output wire[5:0] event_count);
 reg[2:0] slot[8];reg[7:0] gen[8];reg[3:0] mask[8],issued[8],acked[8];
 reg[2:0] head,tail,issue;reg[3:0] live,unissued;
 reg[5:0] events;reg[1:0] selected;wire[3:0] remain=mask[issue]&~issued[issue];
 wire mapping_ready,mapping_valid;wire[12:0] mapping;
 wire command_accept=cv&&cr;wire finish=finish_valid&&finish_ready;wire enqueue=ev&&er;
 wire issued_record=unissued!=0&&(remain==0||(command_accept&&remain==(4'b1<<selected)));
 assign count=live;assign event_count=events;assign idle=live==0&&!mapping_valid;
 assign er=live<8;assign issue_slot=slot[issue];
 always @*begin selected=0;for(integer k=3;k>=0;k=k-1)if(remain[k])selected=k;end
 assign cv=unissued!=0&&remain!=0&&mapping_ready;
 assign cnode={10'b0,issue_node[21:2],selected};assign carg={4'b0,issue_args[selected*28+:28]};assign cbucket=carg[11:0];
 // APPEND responses are strictly FIFO ordered. This FIFO proves their record/event correspondence.
 df_fifo #(.WIDTH(13),.DEPTH(32)) ack_map(.clk,.reset,.iv(command_accept),.ir(mapping_ready),.idata({gen[issue],issue,selected}),.ov(mapping_valid),.ordy(av),.odata(mapping));
 assign ar=mapping_valid;
 assign finish_valid=live!=0&&issued[head]==mask[head]&&acked[head]==mask[head];
 assign finish_slot=slot[head];assign finish_gen=gen[head];
 function automatic[2:0] popcount(input[3:0] x);popcount={2'b0,x[0]}+x[1]+x[2]+x[3];endfunction
 always @(posedge clk)begin
  if(reset)begin head<=0;tail<=0;issue<=0;live<=0;unissued<=0;events<=0;error<=0;peak<=0;event_peak<=0;end
  else begin
   if(live>peak)peak<=live;if(events>event_peak)event_peak<=events;
   case({enqueue,finish})2'b10:live<=live+1;2'b01:live<=live-1;default:;endcase
   case({enqueue,issued_record})2'b10:unissued<=unissued+1;2'b01:unissued<=unissued-1;default:;endcase
   events<=events+(enqueue?popcount(emask):0)-(finish?popcount(mask[head]):0);
   if(enqueue)begin slot[tail]<=eslot;gen[tail]<=egen;mask[tail]<=emask;issued[tail]<=0;acked[tail]<=0;tail<=tail+1;end
   if(command_accept)issued[issue]<=issued[issue]|(4'b1<<selected);
   if(issued_record)issue<=issue+1;
   if(av&&ar)begin
    if(astatus!=0||gen[mapping[4:2]]!=mapping[12:5]||!issued[mapping[4:2]][mapping[1:0]]||acked[mapping[4:2]][mapping[1:0]])error<=1;
    acked[mapping[4:2]]<=acked[mapping[4:2]]|(4'b1<<mapping[1:0]);
   end
   if(finish)head<=head+1;
  end
 end
endmodule
