`timescale 1ns/1ps
// Common C0/F1/F2/F3 network. Source class and source index are architectural
// constants; context/generation remain intact in ID_W.32physicalports default.
module df_memory_network #(parameter integer SOURCES=208,PORTS=32,ID_W=32,
 parameter integer SOURCE_W=$clog2(SOURCES),DEST_W=$clog2(PORTS*4))(
 input logic clk,reset,
 input logic[SOURCES-1:0] cv,output logic[SOURCES-1:0] cr,input logic[SOURCES-1:0] cw,
 input logic[SOURCES*2-1:0] cclass,input logic[SOURCES*32-1:0] cl,
 input logic[SOURCES*ID_W-1:0] cid,input logic[SOURCES*256-1:0] cd,
 output logic[SOURCES-1:0] rv,input logic[SOURCES-1:0] rr,
 output logic[SOURCES*ID_W-1:0] rid,output logic[SOURCES*256-1:0] rd,
 output logic[PORTS-1:0] mv,input logic[PORTS-1:0] mr,output logic[PORTS-1:0] mw,
 output logic[PORTS*32-1:0] ml,output logic[PORTS*5-1:0] mtag,output logic[PORTS*256-1:0] md,
 input logic[PORTS-1:0] sv,output logic[PORTS-1:0] sr,input logic[PORTS*5-1:0] stag,input logic[PORTS*256-1:0] sd,
 output logic[PORTS-1:0] port_error);
 localparam integer LOCAL_W=SOURCE_W+ID_W,REQ_W=1+32+LOCAL_W+256,RET_W=ID_W+256;
 wire[SOURCES-1:0] qv,qr;wire[SOURCES*REQ_W-1:0] qdata;wire[SOURCES*DEST_W-1:0] qdest;
 wire[PORTS*4-1:0] gv,gr,bv,br;wire[PORTS*4*REQ_W-1:0] gdata;
 wire[PORTS*4*RET_W-1:0] bdata;wire[PORTS*4*SOURCE_W-1:0] bdest;
 wire[SOURCES*RET_W-1:0] result;
 for(genvar s=0;s<SOURCES;s=s+1)begin:source
  wire[DEST_W+REQ_W-1:0] inword,outword;
  assign inword={DEST_W'((cl[s*32+:5]<<2)|cclass[s*2+:2]),cw[s],cl[s*32+:32],SOURCE_W'(s),cid[s*ID_W+:ID_W],cd[s*256+:256]};
  df_fifo #(.WIDTH(DEST_W+REQ_W),.DEPTH(4)) fifo(.clk,.reset,.iv(cv[s]),.ir(cr[s]),.idata(inword),.ov(qv[s]),.ordy(qr[s]),.odata(outword));
  assign {qdest[s*DEST_W+:DEST_W],qdata[s*REQ_W+:REQ_W]}=outword;
  assign {rid[s*ID_W+:ID_W],rd[s*256+:256]}=result[s*RET_W+:RET_W];
 end
 df_rr_router #(.INPUTS(SOURCES),.OUTPUTS(PORTS*4),.WIDTH(REQ_W),.DEST_W(DEST_W),.SEL_W(SOURCE_W)) request_router(.clk,.reset,.iv(qv),.ir(qr),.dest(qdest),.idata(qdata),.ov(gv),.ordy(gr),.odata(gdata));
 for(genvar p=0;p<PORTS;p=p+1)begin:port
  wire[3:0] tw;wire[127:0] tl;wire[4*LOCAL_W-1:0] ti,ri;wire[1023:0] td,trd;
  for(genvar c=0;c<4;c=c+1)begin:client
   assign {tw[c],tl[c*32+:32],ti[c*LOCAL_W+:LOCAL_W],td[c*256+:256]}=gdata[(p*4+c)*REQ_W+:REQ_W];
   assign bdest[(p*4+c)*SOURCE_W+:SOURCE_W]=ri[c*LOCAL_W+ID_W+:SOURCE_W];
   assign bdata[(p*4+c)*RET_W+:RET_W]={ri[c*LOCAL_W+:ID_W],trd[c*256+:256]};
  end
  wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;
  wire[293:0] reqword;wire[260:0] rspword;
  df_tagged_port #(.OWNER_ID(p),.ID_W(LOCAL_W)) fabric(.clk,.reset,.cv(gv[p*4+:4]),.cr(gr[p*4+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[p*4+:4]),.rr(br[p*4+:4]),.rid(ri),.rd(trd),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.error(port_error[p]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
  df_fifo #(.WIDTH(294),.DEPTH(2)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({pw,pl,pt,pd}),.ov(mv[p]),.ordy(mr[p]),.odata(reqword));
  assign {mw[p],ml[p*32+:32],mtag[p*5+:5],md[p*256+:256]}=reqword;
  df_fifo #(.WIDTH(261),.DEPTH(2)) response_slice(.clk,.reset,.iv(sv[p]),.ir(sr[p]),.idata({stag[p*5+:5],sd[p*256+:256]}),.ov(sv2),.ordy(sr2),.odata(rspword));
  assign {st,sd2}=rspword;
 end
 df_rr_router #(.INPUTS(PORTS*4),.OUTPUTS(SOURCES),.WIDTH(RET_W),.DEST_W(SOURCE_W),.SEL_W(DEST_W)) response_router(.clk,.reset,.iv(bv),.ir(br),.dest(bdest),.idata(bdata),.ov(rv),.ordy(rr),.odata(result));
endmodule
