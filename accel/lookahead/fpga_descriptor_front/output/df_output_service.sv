`timescale 1ns/1ps
module df_output_service #(parameter integer GROUPS=16,AW=12,CW=AW+3)(
 input logic clk,reset,input logic[GROUPS-1:0] iv,output logic[GROUPS-1:0] ir,
 input logic[GROUPS*CW-1:0] icell,input logic[GROUPS*64-1:0] ipair,
 output logic[7:0] ov,input logic[7:0] ordy,
 output logic[8*CW-1:0] ocell,output logic[511:0] opair,
 output logic[7:0] first,improved,output logic init_done,idle,
 input logic export_start,output logic export_ready,input logic[CW:0] cells,
 input logic[63:0] output_base_line,
 output logic[1:0] write_v,input logic[1:0] write_r,
 output logic[127:0] write_line,output logic[511:0] write_data,
 input logic[1:0] ack_v,output logic[1:0] ack_r,
 output logic export_done,output logic error,
 output logic[CW-1:0] issued_count,acked_count,
 output logic[4:0] packing_occupancy);
 localparam logic[63:0] MISSING=64'h7fc000007fc00000;
 localparam integer WIDTH=CW+64;
 logic[GROUPS*3-1:0] dest;logic[GROUPS*WIDTH-1:0] payload;
 logic[7:0] rv,rr,bank_init,bank_idle;logic[8*WIDTH-1:0] rdata;
 logic[GROUPS-1:0] routed_ready,routed_valid;
 logic exporting;logic[7:0] ex_v;logic[8*AW-1:0] ex_row;logic[8*65-1:0] ex_data;
 logic[CW:0] cell_limit;logic[CW-1:0] total_beats,next_beat,pack_first;
 logic[1:0] launch_count,pack_count;logic[63:0] base;
 logic[255:0] fifo_data[16];logic[CW-1:0] fifo_index[16];
 logic[3:0] rd_ptr,wr_ptr;logic[4:0] filled;logic[1:0] popped;
 integer available,remaining,which,line_index,bank_index,cell_index;
 logic[255:0] packed0,packed1;
 assign init_done=&bank_init;
 assign idle=init_done&&(&bank_idle)&&!(|rv)&&!exporting;
 assign export_ready=idle&&!(|iv)&&!export_done;
 assign routed_valid=iv&{GROUPS{init_done&&!exporting&&!export_start&&!export_done}};
 assign ir=routed_ready&{GROUPS{init_done&&!exporting&&!export_start&&!export_done}};
 for(genvar g=0;g<GROUPS;g=g+1)begin
  assign dest[g*3+:3]=icell[g*CW+:3];
  assign payload[g*WIDTH+:WIDTH]={icell[g*CW+:CW],ipair[g*64+:64]};
 end
 df_rr_router #(.INPUTS(GROUPS),.OUTPUTS(8),.WIDTH(WIDTH),.DEST_W(3),.SEL_W($clog2(GROUPS))) router(
  .clk(clk),.reset(reset),.iv(routed_valid),.ir(routed_ready),.dest(dest),.idata(payload),.ov(rv),.ordy(rr),.odata(rdata));
 for(genvar b=0;b<8;b=b+1)begin:banks
  df_output_bank #(.AW(AW),.CW(CW)) bank(.clk(clk),.reset(reset),.iv(rv[b]),.ir(rr[b]),
   .in_cell(rdata[b*WIDTH+64+:CW]),.pair(rdata[b*WIDTH+:64]),.ov(ov[b]),.ordy(ordy[b]),
   .ocell(ocell[b*CW+:CW]),.opair(opair[b*64+:64]),.first(first[b]),.improved(improved[b]),
   .init_done(bank_init[b]),.idle(bank_idle[b]),.export_mode(exporting),.ex_v(ex_v[b]),.ex_row(ex_row[b*AW+:AW]),.ex_data(ex_data[b*65+:65]));
 end
 assign packing_occupancy=filled+pack_count;
 assign write_v[0]=exporting&&filled!=0;
 // A single strict-prefix FIFO: second cannot overtake a rejected first.
 assign write_v[1]=exporting&&filled>1&&write_r[0];
 assign write_data[255:0]=fifo_data[rd_ptr];
 assign write_data[511:256]=fifo_data[4'(rd_ptr+1'b1)];
 assign write_line[63:0]=base+fifo_index[rd_ptr];
 assign write_line[127:64]=base+fifo_index[4'(rd_ptr+1'b1)];
 assign popped={1'b0,(write_v[0]&&write_r[0])}+{1'b0,(write_v[1]&&write_r[1])};
 assign ack_r={2{exporting}};
 always_comb begin
  available=16-filled-pack_count;remaining=total_beats-next_beat;launch_count=0;
  if(exporting&&remaining>0&&available>0)begin
   launch_count=1;if(remaining>1&&available>1)launch_count=2;
  end
  ex_v=0;ex_row=0;
  for(integer k=0;k<2;k=k+1)if(k<launch_count)begin
   line_index=next_beat+k;
   for(integer s=0;s<4;s=s+1)begin
    bank_index=(line_index%2)*4+s;ex_v[bank_index]=1;ex_row[bank_index*AW+:AW]=AW'(line_index/2);
   end
  end
  packed0={4{MISSING}};packed1={4{MISSING}};
  for(integer k=0;k<2;k=k+1)if(k<pack_count)begin
   line_index=pack_first+k;
   for(integer s=0;s<4;s=s+1)begin
    bank_index=(line_index%2)*4+s;cell_index=line_index*4+s;
    if(cell_index<cell_limit&&ex_data[bank_index*65+64])begin
     if(k==0)packed0[s*64+:64]=ex_data[bank_index*65+:64];else packed1[s*64+:64]=ex_data[bank_index*65+:64];
    end
   end
  end
 end
 always_ff @(posedge clk)begin
  if(reset)begin exporting<=0;export_done<=0;error<=0;filled<=0;pack_count<=0;rd_ptr<=0;wr_ptr<=0;next_beat<=0;total_beats<=0;issued_count<=0;acked_count<=0;cell_limit<=0;base<=0;end
  else if(export_start&&export_ready)begin
   exporting<=1;cell_limit<=cells;total_beats<=(cells+3)>>2;next_beat<=0;issued_count<=0;acked_count<=0;base<=output_base_line;
   if(cells>(1<<CW))error<=1;
  end else if(exporting)begin
   if(pack_count!=0)begin fifo_data[wr_ptr]<=packed0;fifo_index[wr_ptr]<=pack_first;end
   if(pack_count==2)begin fifo_data[4'(wr_ptr+1'b1)]<=packed1;fifo_index[4'(wr_ptr+1'b1)]<=pack_first+1'b1;end
   wr_ptr<=wr_ptr+pack_count;rd_ptr<=rd_ptr+popped;filled<=filled+pack_count-popped;
   pack_count<=launch_count;if(launch_count!=0)pack_first<=next_beat;next_beat<=next_beat+launch_count;
   issued_count<=issued_count+popped;acked_count<=acked_count+ack_v[0]+ack_v[1];
   if(acked_count+ack_v[0]+ack_v[1]>issued_count)error<=1;
   if(next_beat==total_beats&&pack_count==0&&filled==0&&acked_count==total_beats)begin exporting<=0;export_done<=1;end
  end
 end
endmodule
