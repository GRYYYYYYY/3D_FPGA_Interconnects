`timescale 1ns/1ps
// Four logical clients, ONE shared physical port. No TB-only arbitration.
module df_tagged_port #(parameter integer OWNER_ID=0,ID_W=32)(input logic clk,reset,
 input logic [3:0] cv,output logic [3:0] cr,input logic [3:0] cw,
 input logic [127:0] cl,input logic [4*ID_W-1:0] cid,input logic [1023:0] cd,
 output logic [3:0] rv,input logic [3:0] rr,output logic [4*ID_W-1:0] rid,output logic [1023:0] rd,
 output logic mv,input logic mr,output logic mw,output logic [31:0] ml,output logic [4:0] mtag,output logic [255:0] md,
 input logic sv,output logic sr,input logic [4:0] stag,input logic [255:0] sd,
 output logic idle,error,output logic [5:0] credits_used,peak_credits,
 output logic [31:0] client_accepted,physical_issued,physical_returned,client_returned);
 // q payload={write,line32,local_idID_W,data256}; four entries per client.
 (* ram_style="distributed" *) logic [288+ID_W:0] qmem[4][4];
 logic [1:0] qread[4],qwrite[4];logic [2:0] qcount[4];
 logic [3:0] enqueue,dequeue;logic [1:0] cursor,selected;logic selected_valid;
 logic [31:0] busy;logic [1:0] tag_client[32];logic [ID_W-1:0] tag_local[32];logic [4:0] free_tag;logic tag_valid;
 // Registered physical-response FIFO, then one register per client.
 logic [1:0] return_client[4];logic [ID_W-1:0] return_id[4];logic [255:0] return_data[4];
 logic [1:0] return_read,return_write;logic [2:0] return_count;
 logic return_push,return_pop,fill_request;logic [2:0] enqueues,deliveries;integer idx,n;
 always_comb begin
  selected=0;selected_valid=0;free_tag=0;tag_valid=0;credits_used=0;enqueues=0;deliveries=0;
  for(integer c=0;c<4;c=c+1)begin
   cr[c]=qcount[c]<4&&cl[c*32+:5]==OWNER_ID;
   enqueue[c]=cv[c]&&cr[c];enqueues=enqueues+enqueue[c];deliveries=deliveries+(rv[c]&&rr[c]);
  end
  for(integer t=0;t<32;t=t+1)begin
   credits_used=credits_used+busy[t];if(!tag_valid&&!busy[t])begin tag_valid=1;free_tag=t;end
  end
  for(integer c=0;c<4;c=c+1)begin idx=(cursor+c)&3;if(!selected_valid&&qcount[idx]!=0)begin selected=idx;selected_valid=1;end end
  fill_request=(!mv||mr)&&selected_valid&&tag_valid;
  dequeue=0;if(fill_request)dequeue[selected]=1;
  sr=return_count<4;
  return_push=sv&&sr&&busy[stag];
  return_pop=return_count!=0&&(!rv[return_client[return_read]]||rr[return_client[return_read]]);
  idle=busy==0&&!mv&&return_count==0&&rv==0;
  for(integer c=0;c<4;c=c+1)if(qcount[c]!=0)idle=0;
 end
 for(genvar c=0;c<4;c=c+1)begin:queues
  always_ff @(posedge clk)begin
   if(reset)begin qread[c]<=0;qwrite[c]<=0;qcount[c]<=0;end
   else begin
    if(enqueue[c])begin qmem[c][qwrite[c]]<={cw[c],cl[c*32+:32],cid[c*ID_W+:ID_W],cd[c*256+:256]};qwrite[c]<=qwrite[c]+1;end
    if(dequeue[c])qread[c]<=qread[c]+1;
    case({enqueue[c],dequeue[c]})2'b10:qcount[c]<=qcount[c]+1;2'b01:qcount[c]<=qcount[c]-1;default:;endcase
   end
  end
 end
 always_ff @(posedge clk)begin
  if(reset)begin
   cursor<=0;busy<=0;mv<=0;rv<=0;return_read<=0;return_write<=0;return_count<=0;error<=0;peak_credits<=0;
   client_accepted<=0;physical_issued<=0;physical_returned<=0;client_returned<=0;
  end else begin
   client_accepted<=client_accepted+enqueues;client_returned<=client_returned+deliveries;
   if(credits_used>peak_credits)peak_credits<=credits_used;
   for(integer c=0;c<4;c=c+1)begin
    if(cv[c]&&cl[c*32+:5]!=OWNER_ID)error<=1;
    if(rv[c]&&rr[c])rv[c]<=0;
   end
   if(!mv||mr)begin
    mv<=0;
    if(fill_request)begin
     mv<=1;{mw,ml}<=qmem[selected][qread[selected]][288+ID_W:256+ID_W];md<=qmem[selected][qread[selected]][255:0];mtag<=free_tag;
     busy[free_tag]<=1;tag_client[free_tag]<=selected;tag_local[free_tag]<=qmem[selected][qread[selected]][255+ID_W:256];cursor<=selected+1;
    end
   end
   if(mv&&mr)physical_issued<=physical_issued+1;
   if(sv&&sr)begin
    if(!busy[stag])error<=1;
    else begin
     physical_returned<=physical_returned+1;busy[stag]<=0;
     return_client[return_write]<=tag_client[stag];return_id[return_write]<=tag_local[stag];return_data[return_write]<=sd;return_write<=return_write+1;
    end
   end
   if(return_pop)begin
    rv[return_client[return_read]]<=1;rid[return_client[return_read]*ID_W+:ID_W]<=return_id[return_read];rd[return_client[return_read]*256+:256]<=return_data[return_read];return_read<=return_read+1;
   end
   case({return_push,return_pop})2'b10:return_count<=return_count+1;2'b01:return_count<=return_count-1;default:;endcase
  end
 end
endmodule
