`timescale 1ns/1ps
// Two contending ports; 3 four-beat bursts per direction/port, two credits.
// Deterministic downstream stalls exercise held R/W VALID and burst accounting.
module bounded_axi_tb;
  reg clk=0, reset_n=0, finish=0;
  always #2.5 clk=~clk;
  wire [1:0] arvalid, arready, awvalid, awready, mrvalid, mrready;
  wire [1:0] rvalid, rready, wvalid, wready, mwvalid, mwready, bvalid;
  wire [1:0] marvalid, mawvalid, rlast, mrlast, wlast;
  wire [1:0] marready, mawready;
  wire [1023:0] mem_rdata, rdata;
  wire drained;
  integer cycle=0;
  integer ar[2], aw[2], rb[2], mr[2], wb[2], br[2];
  integer i;
  genvar p;
  generate for(p=0;p<2;p=p+1) begin
    assign arvalid[p]=reset_n && ar[p]<3;
    assign marready[p]=cycle%7>2;
    assign mawready[p]=cycle%11>5;
    assign awvalid[p]=reset_n && aw[p]<3;
    // Delayed response keeps credit pool full long enough to stall requests.
    assign mrvalid[p]=reset_n && cycle>30 && mr[p]<4*ar[p];
    assign mrlast[p]=(mr[p]%4==3);
    assign mem_rdata[p*512+:512]={{480{1'b0}},mr[p]};
    assign rready[p]=(p==1 || rb[1]>0) && cycle%7!=0 && cycle%7!=1;
    assign wvalid[p]=reset_n && wb[p]<12;
    assign wlast[p]=(wb[p]%4==3);
    assign mwready[p]=cycle%11>3;
    assign bvalid[p]=reset_n && cycle%5==0 && br[p]<wb[p]/4;
  end endgenerate
  la_bounded_axi #(.PORTS(2),.BANKS(1),.PERIOD(4),.CREDITS(2),.TOTAL_READ_CREDITS(2),.TOTAL_WRITE_CREDITS(2),.MAX_CYCLES(1000)) dut(
    .clk(clk),.reset_n(reset_n),.finish(finish),.drained(drained),
    .arvalid(arvalid),.arready(arready),.mem_arvalid(marvalid),.mem_arready(marready),
    .awvalid(awvalid),.awready(awready),.mem_awvalid(mawvalid),.mem_awready(mawready),
    .mem_rvalid(mrvalid),.mem_rready(mrready),.rvalid(rvalid),.rready(rready),
    .wvalid(wvalid),.wready(wready),.mem_wvalid(mwvalid),.mem_wready(mwready),
    .mem_rlast(mrlast),.rlast(rlast),.mem_rdata(mem_rdata),.rdata(rdata),
    .mem_rid(64'b0),.mem_rresp(4'b0),
    .wlast(wlast),.bvalid(bvalid),.bready(2'b11),
    .arlen(16'h0303),.awlen(16'h0303));
  always @(posedge clk) begin
    if(!reset_n) begin
      cycle<=0;
      for(i=0;i<2;i=i+1) begin ar[i]<=0;aw[i]<=0;rb[i]<=0;mr[i]<=0;wb[i]<=0;br[i]<=0;end
    end else begin
      cycle<=cycle+1;
      for(i=0;i<2;i=i+1) begin
        if(arvalid[i]&&arready[i]) ar[i]<=ar[i]+1;
        if(awvalid[i]&&awready[i]) aw[i]<=aw[i]+1;
        if(mrvalid[i]&&mrready[i]) mr[i]<=mr[i]+1;
        if(rvalid[i]&&rready[i]) begin
          if(rdata[i*512+:512]!=rb[i]) $fatal(1,"read buffer data reordered/corrupted");
          rb[i]<=rb[i]+1;
        end
        if(wvalid[i]&&wready[i]) wb[i]<=wb[i]+1;
        if(bvalid[i]) br[i]<=br[i]+1;
      end
      if(rb[0]==12 && rb[1]==12 && wb[0]==12 && wb[1]==12 && drained) finish<=1;
    end
  end
  initial begin
    repeat(3) @(negedge clk); reset_n=1;
    wait(finish); repeat(3) @(negedge clk);
    for(i=0;i<2;i=i+1)
      if(ar[i]!=3 || aw[i]!=3 || br[i]!=3 || dut.credit_stalls[i]==0 ||
         dut.rpeak[i]<1 || dut.wpeak[i]<1 || dut.read_stalls[i]==0 || dut.write_stalls[i]==0)
        $fatal(1,"selftest did not cover credits/stalls/bursts");
    if(dut.total_rpeak!=2 || dut.total_wpeak!=2)$fatal(1,"global credit cap not exercised");
    $display("TEST_PASS bounded AXI arbitration, stalls, bursts, credits and drain");
    $finish;
  end
endmodule
