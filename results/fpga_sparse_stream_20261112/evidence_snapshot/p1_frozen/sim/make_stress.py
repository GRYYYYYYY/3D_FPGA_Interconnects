from pathlib import Path
import struct,json
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_20261112/stress';r.mkdir(exist_ok=True)
n=3200;nodes=[(0,0,1,-1) for _ in range(n)]
nodes[3072]=(1,1,1,-1);nodes[3073]=(1,0,1,-1);nodes[3074]=(2,0,1,-1);nodes[3075]=(0,0,0,-1)
adj=[[] for _ in range(n)];adj[0]=list(range(32,64));adj[1]=list(range(32,64))
for u in range(32,64):adj[u]=[3075]+list(range(256,3000))+[256]*64+[3074,3073]
for u in range(256,3000):adj[u]=[3072]
row=[0];edges=[]
for a in adj:edges.extend((v,0) for v in a);row.append(len(edges))
cells=[-1]*n;cells[3072]=0;cells[3073]=1
with (r/'workload.bin').open('wb') as f:
 f.write(struct.pack('<7Q',0x31414c5443495254,n,len(edges),2,2,2,1));f.write(struct.pack('<'+str(n+1)+'Q',*row))
 for node in nodes:f.write(struct.pack('<IIIi',*node))
 for edge in edges:f.write(struct.pack('<II',*edge))
 f.write(struct.pack('<4f',0,0,1,0))
 for src in [0,1]:f.write(struct.pack('<6I',src,0,0,0,0,0))
 f.write(struct.pack('<'+str(n*2)+'i',*(cells*2)));f.write(struct.pack('<8I',*([0x7fc00000]*8)))
(r/'contract.json').write_text(json.dumps({'nodes':n,'jobs':2,'parents':32,'same_bucket_reentry':True,'ineligible_skip_node':3075,'eligible_break_node':3074,'must_remain_unreached_after_break':3073,'repeated_destination':256,'latency_and_responses':'finite memory driver; out-of-order; random backpressure','expected':'only target cell0=(1,0); cell1 missing'},indent=2))
