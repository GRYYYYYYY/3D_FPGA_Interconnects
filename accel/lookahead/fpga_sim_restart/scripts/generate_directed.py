#!/usr/bin/env python3
"""Independent whole-memory FP32 oracle; no RTL internals/golden frontier."""
import pathlib, struct, random, json, sys
out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
r=random.Random(62012); N=2048; inf=(float('inf'),float('inf')); mem=[inf]* (N*4); ops=[]; snapshots=[]
def bits(v):return struct.unpack('>I',struct.pack('>f',v))[0]
def emit(line,sec,d,c):
    p=(float(d),float(c));ops.append(f'0 {line:x} {sec:x} {bits(d):08x}{bits(c):08x}\n');i=line*4+sec;mem[i]=min(mem[i],p)
def fence():
    ops.append('1 0 0 0\n');snapshots.extend(f'{bits(b):08x}{bits(a):08x}' for a,b in [])
    # Each line stores sector 0 in the low bits, each pair delay in high word.
    snapshots.extend(''.join(f'{bits(mem[l*4+s][0]):08x}{bits(mem[l*4+s][1]):08x}' for s in range(3,-1,-1))+'\n' for l in range(N))
for i in range(96):emit(0,i%4,100-i,200+i)
for i in range(400):emit(i,0,1000-i,50+i)
for i in range(250):emit((i%17)*32,i%4,500-i,10+i)
for i in range(1500):emit(r.randrange(512),r.randrange(4),r.randrange(1,1000),r.randrange(1,1000))
fence()
# Full invalidate/reset between samples. Home persists here to expose stale tags.
ops.append('2 0 0 0\n')
for i in range(200):emit((i%9)*32,i%4,200-i,600+i)
for i in range(200):emit(i,i%4,10000,10000) # mostly non-improving
fence()
(out/'stimulus.txt').write_text(''.join(ops));(out/'expected.hex').write_text(''.join(snapshots))
(out/'stimulus.json').write_text(json.dumps({'seed':62012,'lines':N,'updates':len(ops)-3,'fences':2,'oracle':'Python numeric tuple minimum; complete memory snapshots'},indent=2)+'\n')
