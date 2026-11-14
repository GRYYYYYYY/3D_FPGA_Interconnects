#!/usr/bin/env python3
"""Generate only legal connections. Local wide payload never enters global fabric."""
from pathlib import Path
import json
p=Path(__file__).resolve().parent
S=208; ID=74; NAR=106; REQ=363; RET=332
lines=['`timescale 1ns/1ps', '''module lf_network(
 input wire clk,reset,input wire [207:0] cv,output wire [207:0] cr,
 input wire [208*4-1:0] ck,input wire [208*32-1:0] cl,cid,cgen,
 input wire [160*256-1:0] local_write_data,
 output wire [207:0] rv,input wire [207:0] rr,
 output wire [208*4-1:0] rk,output wire [208*32-1:0] rid,rgen,
 output wire [208*256-1:0] rd,output wire [208*2-1:0] rstatus,
 output wire [31:0] mv,input wire [31:0] mr,output wire [31:0] mw,
 output wire [32*32-1:0] ml,output wire [32*5-1:0] mtag,output wire [32*256-1:0] md,
 input wire [31:0] sv,output wire [31:0] sr,input wire [32*5-1:0] stag,
 input wire [32*256-1:0] sd,input wire [32*2-1:0] sstatus,
 output wire [31:0] port_error,output reg error);
 wire [207:0] qv,qr,legal,write_,rlegal;
 wire [73:0] qi[208],ai[208],ri[208];wire [31:0] ql[208];
 wire [255:0] qd[160],raw_rd[208];wire qw[160];
 wire [127:0] gv,gr,bv,br;wire [362:0] gd[128];
 wire [331:0] bd[128];wire [5:0] dest[128];
 wire [207:0] source_accept;
 always @(posedge clk)if(reset)error<=0;else if(|(cv&~legal)|||(rv&~rlegal)|||port_error)error<=1;
''']
def emit(s):lines.append(s)
for s in range(S):
 emit(f'''lf_adapter #(.SOURCE({s})) a{s}(.kind(ck[{s*4}+:4]),.local_id(cid[{s*32}+:32]),.generation(cgen[{s*32}+:32]),.line(cl[{s*32}+:32]),.legal(legal[{s}]),.write(write_[{s}]),.packed_id(ai[{s}]),.returned_id(ri[{s}]),.returned_data(raw_rd[{s}]),.returned_kind(rk[{s*4}+:4]),.returned_local(rid[{s*32}+:32]),.returned_gen(rgen[{s*32}+:32]),.read_data(rd[{s*256}+:256]),.returned_legal(rlegal[{s}]));
 assign cr[{s}]=source_accept[{s}]&&legal[{s}];''')
 if s<48:
  emit(f'''df_fifo #(.WIDTH(106),.DEPTH(4)) q{s}(.clk,.reset,.iv(cv[{s}]&&legal[{s}]),.ir(source_accept[{s}]),.idata({{cl[{s*32}+:32],ai[{s}]}}),.ov(qv[{s}]),.ordy(qr[{s}]),.odata({{ql[{s}],qi[{s}]}}));''')
 else:
  emit(f'''df_fifo #(.WIDTH(363),.DEPTH(4)) q{s}(.clk,.reset,.iv(cv[{s}]&&legal[{s}]),.ir(source_accept[{s}]),.idata({{write_[{s}],cl[{s*32}+:32],ai[{s}],local_write_data[{(s-48)*256}+:256]}}),.ov(qv[{s}]),.ordy(qr[{s}]),.odata({{qw[{s-48}],ql[{s}],qi[{s}],qd[{s-48}]}}));''')
request_connections=[]; req_ready=[[] for _ in range(S)]
for port in range(32):
 for cls in range(4):
  sources=list(range(16)) if cls==0 else list(range(16,48))+[176+port] if cls==1 else [48+2*port,49+2*port] if cls==2 else [112+2*port,113+2*port]
  n=len(sources);o=port*4+cls;request_connections.append({'port':port,'class':cls,'sources':sources})
  emit(f'begin:req{o}\nwire [{n-1}:0] eligible,grant;wire any;wire accept=!gv[{o}]||gr[{o}]; reg [362:0] hold;reg valid;wire [105:0] narrow[{n}];wire [105:0] selected_narrow;')
  for i,s in enumerate(sources):
   emit(f'assign eligible[{i}]=qv[{s}]'+(f'&&ql[{s}][4:0]=={port};' if s<48 else ';'))
   emit(f'assign narrow[{i}]={{106{{grant[{i}]}}}}&{{ql[{s}],qi[{s}]}};')
   req_ready[s].append(f'(req{o}.accept&&req{o}.grant[{i}])')
  emit('assign selected_narrow='+'|'.join(f'narrow[{i}]' for i in range(n))+';')
  locals_=[(i,s)for i,s in enumerate(sources)if s>=48]
  data='|'.join(f'({{256{{grant[{i}]}}}}&qd[{s-48}])' for i,s in locals_) or "256'b0"
  wr='|'.join(f'(grant[{i}]&&qw[{s-48}])' for i,s in locals_) or "1'b0"
  emit(f'''lf_select #(.N({n})) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={{{wr},selected_narrow,{data}}};end
 assign gv[{o}]=valid;assign gd[{o}]=hold;end''')
for s in range(S):emit(f'assign qr[{s}]='+'|'.join(req_ready[s])+';')
for port in range(32):
 emit(f'''begin:port{port}
 wire [3:0] tw;wire [127:0] tl;wire [4*74-1:0] ti,ri_;wire [1023:0] td,trd;wire[7:0] rs;
 for(genvar c=0;c<4;c=c+1)begin:client
 assign {{tw[c],tl[c*32+:32],ti[c*74+:74],td[c*256+:256]}}=gd[{port*4}+c];
 assign dest[{port*4}+c]=ri_[c*74+68+:6];
 assign bd[{port*4}+c]={{rs[c*2+:2],ri_[c*74+:74],trd[c*256+:256]}};
 end
 wire pv,pr,pw,sv2,sr2;wire[31:0] pl;wire[4:0] pt,st;wire[255:0] pd,sd2;wire[1:0] ss2;
 lf_tagged_port #(.OWNER_ID({port}),.ID_W(74)) fabric(.clk,.reset,.cv(gv[{port*4}+:4]),.cr(gr[{port*4}+:4]),.cw(tw),.cl(tl),.cid(ti),.cd(td),.rv(bv[{port*4}+:4]),.rr(br[{port*4}+:4]),.rid(ri_),.rd(trd),.rstatus(rs),.mv(pv),.mr(pr),.mw(pw),.ml(pl),.mtag(pt),.md(pd),.sv(sv2),.sr(sr2),.stag(st),.sd(sd2),.sstatus(ss2),.error(port_error[{port}]),.idle(),.credits_used(),.peak_credits(),.client_accepted(),.physical_issued(),.physical_returned(),.client_returned());
 lf_fifo2 #(.WIDTH(294)) request_slice(.clk,.reset,.iv(pv),.ir(pr),.idata({{pw,pl,pt,pd}}),.ov(mv[{port}]),.ordy(mr[{port}]),.odata({{mw[{port}],ml[{port*32}+:32],mtag[{port*5}+:5],md[{port*256}+:256]}}));
 lf_fifo2 #(.WIDTH(263)) response_slice(.clk,.reset,.iv(sv[{port}]),.ir(sr[{port}]),.idata({{sstatus[{port*2}+:2],stag[{port*5}+:5],sd[{port*256}+:256]}}),.ov(sv2),.ordy(sr2),.odata({{ss2,st,sd2}}));
 end''')
back_ready=[[] for _ in range(128)];response_connections=[]
for s in range(S):
 cls=0 if s<16 else 1 if s<48 or s>=176 else 2 if s<112 else 3
 port=None if s<48 else (s-48)//2 if s<112 else (s-112)//2 if s<176 else s-176
 inputs=[p*4+cls for p in range(32)]if port is None else [port*4+cls]
 code=s if s<48 else 48+(s-48)%2 if s<112 else 50+(s-112)%2 if s<176 else 52
 n=len(inputs);response_connections.append({'source':s,'inputs':inputs})
 emit(f'begin:ret{s}\nwire [{n-1}:0] eligible,grant;wire any;wire accept=!rv[{s}]||rr[{s}];reg valid;reg [331:0] hold;wire [331:0] word_[{n}];')
 for i,q in enumerate(inputs):
  emit(f'assign eligible[{i}]=bv[{q}]&&dest[{q}]=={code};assign word_[{i}]=bd[{q}]&{{332{{grant[{i}]}}}};')
  back_ready[q].append(f'(ret{s}.accept&&ret{s}.grant[{i}])')
 if n==1:emit('assign any=eligible[0];assign grant=eligible;')
 else:emit(f'lf_select #(.N({n})) sel(.clk,.reset,.valid(eligible),.accept,.grant,.any);')
 emit('wire [331:0] selected='+'|'.join(f'word_[{i}]'for i in range(n))+';')
 emit(f'''always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<=selected;end
 assign rv[{s}]=valid;assign {{rstatus[{s*2}+:2],ri[{s}],raw_rd[{s}]}}=hold;end''')
for q in range(128):emit(f'assign br[{q}]='+'|'.join(back_ready[q])+';')
emit('endmodule')
(p/'lf_network.sv').write_text('\n'.join(lines)+'\n')
(p/'source_legality.json').write_text(json.dumps({'base':'7dd79b2eb97f9bed1b36629e06b2fab3723fc4ec','physical_ports':32,'credits_per_port':32,'request_connections':request_connections,'response_connections':response_connections,'wire_identity':{'source_code':[68,73],'kind':[64,67],'generation':[32,63],'local_id':[0,31]},'generation_note':'32 bits preserve scratch line identity; no gen8 truncation','frontend_write_payload_bits':0,'local_write_payload_bits':256,'external_status_bits':2,'owner_runtime_checked':True},indent=2)+'\n')
