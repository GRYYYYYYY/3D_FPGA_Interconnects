from pathlib import Path
import json
p=Path(__file__).resolve().parent;s=(p/'lf_network.sv').read_text().replace('module lf_network(', 'module lf_radix_network(')
# Keep the typed adapters, all local source FIFOs, local request arbiters,
# actual shared tagged ports and local return holds. Replace dynamic paths only.
import re
for n in range(48):
 pattern=rf'df_fifo #\(\.WIDTH\(106\),\.DEPTH\(4\)\) q{n}\(.*?\);'
 repl=f'assign fqv[{n}]=cv[{n}]&&legal[{n}];assign source_accept[{n}]=fqr[{n}];assign fqd[{n}*106+:106]={{cl[{n}*32+:32],ai[{n}]}};assign fqdest[{n}*6+:6]={{cl[{n}*32+:5],1\'b{int(n>=16)}}};'
 s,num=re.subn(pattern,repl,s);assert num==1,(n,num)
# Global narrow request network and separate read return network.
extra='''wire[63:0]fqv,fqr,fxv,fxr,bxv,bxr,frv,frr;
 wire[64*106-1:0]fqd,fxd;wire[383:0]fqdest,brdest;
 wire[64*332-1:0]brdata,frdata;
 lf_radix #(.WIDTH(106)) front_requests(.clk,.reset,.iv(fqv),.ir(fqr),.dest(fqdest),.idata(fqd),.ov(fxv),.ordy(fxr),.odata(fxd));
 lf_radix #(.WIDTH(332)) front_returns(.clk,.reset,.iv(bxv),.ir(bxr),.dest(brdest),.idata(brdata),.ov(frv),.ordy(frr),.odata(frdata));
 assign fqv[63:48]=0;assign fqd[64*106-1:48*106]=0;assign fqdest[383:288]=0;assign frr[63:48]=0;
'''
s=s.replace(' wire [207:0] qv',extra+' wire [207:0] qv')
for port in range(32):
 # EDGE directly consumes stage2 registered output. Control/admin merge has one hold.
 for cls in [0,1]:
  o=port*4+cls;start=s.index(f'begin:req{o}\n');end=s.index(';end',s.index(f'assign gv[{o}]=valid;',start))+len(';end')
  if cls==0:repl=f"assign gv[{o}]=fxv[{2*port}];assign fxr[{2*port}]=gr[{o}];assign gd[{o}]={{1'b0,fxd[{2*port}*106+:106],256'b0}};"
  else:
   src=176+port
   repl=f'''begin:req{o}
 wire[1:0]eligible={{qv[{src}],fxv[{2*port+1}]}};wire[1:0]grant;wire any;wire accept=!gv[{o}]||gr[{o}];reg valid;reg[362:0]hold;
 lf_select #(.N(2)) select_(.clk,.reset,.valid(eligible),.accept,.grant,.any);
 wire[105:0]selected_narrow=(fxd[{2*port+1}*106+:106]&{{106{{grant[0]}}}})|({{ql[{src}],qi[{src}]}}&{{106{{grant[1]}}}});
 always @(posedge clk)if(reset)valid<=0;else if(accept)begin valid<=any;if(any)hold<={{grant[1]&&qw[{src-48}],selected_narrow,qd[{src-48}]&{{256{{grant[1]}}}}}};end
 assign gv[{o}]=valid;assign gd[{o}]=hold;assign fxr[{2*port+1}]=accept&&grant[0];end'''
  s=s[:start]+repl+s[end:]
for n in range(48):
 s=re.sub(rf'assign qr\[{n}\]=.*?;', '',s)
 # Replace each global return output arbiter with one radix output.
 start=s.index(f'begin:ret{n}\n');end=s.index(';end',s.index(f'assign rv[{n}]=valid;',start))+len(';end')
 repl=f'assign rv[{n}]=frv[{n}];assign frr[{n}]=rr[{n}];assign {{rstatus[{n*2}+:2],ri[{n}],raw_rd[{n}]}}=frdata[{n}*332+:332];'
 s=s[:start]+repl+s[end:]
for port in range(32):
 # Only frontclass0/1 enter the global return network. Admin stays local.
 for cls in [0,1]:
  o=port*4+cls;e=port*2+cls
  repl=f'assign bxv[{e}]=bv[{o}]&&dest[{o}]<48;assign brdest[{e}*6+:6]=dest[{o}];assign brdata[{e}*332+:332]=bd[{o}];assign br[{o}]=(dest[{o}]<48&&bxr[{e}])'
  if cls==1:repl+=f'|(ret{176+port}.accept&&ret{176+port}.grant[0])'
  repl+=';'
  s,num=re.subn(rf'assign br\[{o}\]=.*?;',lambda _:repl,s);assert num==1
 # Local admin arbiter is input1 rather than input32 of old static merge.
 s=s.replace(f'assign qr[{176+port}]=(req{port*4+1}.accept&&req{port*4+1}.grant[32]);',f'assign qr[{176+port}]=(req{port*4+1}.accept&&req{port*4+1}.grant[1]);')
(p/'lf_radix_network.sv').write_text(s)
# Exhaustive source/destination permutation proof, independent of generator wiring.
paths=[]
for source in range(64):
 for dest in range(64):
  loc=source;path=[]
  for stage in range(3):
   loc=(loc//4)*4+((dest>>(4-2*stage))&3);path.append(loc)
   if stage<2:loc=((loc<<2)&63)|(loc>>4)
  assert loc==dest;(paths.append([source,dest,*path]))
(p/'radix_reachability.json').write_text(json.dumps({'pairs':4096,'all_destinations_match':True,'path_rows':paths},separators=(',',':'))+'\n')
