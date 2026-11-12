from pathlib import Path
import json,struct,sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_20261112';case=sys.argv[1] if len(sys.argv)>1 else 'native_d3_w8'
w=next(x for x in json.load(open(root/'accel/lookahead/fpga_sim_restart/config/inputs.json')) if x['case']==case)
b=(r/case/'prepared.bin').read_bytes();h=struct.unpack_from('<6Q',b);_,n,e,j,c,ncells=h;offset=48
row=b[offset:offset+8*(n+1)];offset+=8*(n+1);edge=b[offset:offset+4*e];offset+=4*e
nodes=[struct.unpack_from('<IIIi',b,offset+16*k) for k in range(n)];offset+=16*n
cost=b[offset:offset+8*c];offset+=8*c;cells=struct.unpack_from('<'+str(n*j)+'i',b,offset);offset+=4*n*j
jobs=[struct.unpack_from('<6I',b,offset+24*k) for k in range(j)];offset+=24*j;targets=struct.unpack_from('<'+str(j)+'I',b,offset)
a=lambda x:(x+255)&~255;rb=1024;eb=a(rb+(len(row)+31)//32);cb=a(eb+(len(edge)+31)//32);mb=a(cb+(len(cost)+31)//32);stride=a((8*n+31)//32)
mem=bytearray((mb+stride*j+64)*32);mem[rb*32:rb*32+len(row)]=row;mem[eb*32:eb*32+len(edge)]=edge
for k in range(c):lo,hi=struct.unpack_from('<II',cost,k*8);struct.pack_into('<Q',mem,cb*32+k*8,(lo<<32)|hi)
for q in range(j):
 for k in range(n):struct.pack_into('<Q',mem,(mb+q*stride)*32+k*8,((nodes[k][0]==1)<<32)|(cells[q*n+k]&0xffffffff))
out=r/(case+'_xsim');out.mkdir(exist_ok=True)
(out/'memory.hex').write_text(''.join(mem[k:k+32][::-1].hex()+'\n' for k in range(0,len(mem),32)))
(out/'config.txt').write_text(f'{j} {n} {ncells} {c} {rb} {eb} {cb} {mb} {stride} {len(mem)//32}\n'+''.join(f'{jobs[q][0]} {targets[q]}\n' for q in range(j)))
expected=(r/case/'output.bin').read_bytes();(out/'expected.hex').write_text(''.join(f'{a:08x}{b:08x}\n' for a,b in struct.iter_unpack('<II',expected)))
