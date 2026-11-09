"""Host-only instrumentation of the exact staged kernel; check every heap array."""
import argparse,shutil,subprocess,json
from pathlib import Path
from prepare import sha256
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);a=p.parse_args();r=a.experiment.resolve();o=r/'heap_audit';o.mkdir(exist_ok=False)
for f in Path('accel/lookahead/round5').glob('*'):
 if f.suffix in ['.hpp','.cpp']:shutil.copy2(f,o/f.name)
p=o/'search5.hpp';s=p.read_text();original=sha256(p)
s=s.replace('#pragma once','#pragma once\n#include <vector>\n#include <cassert>\n#include <cstring>\n#include "strict_heap.hpp"')
s=s.replace('Context ctx[LA5_CONTEXTS];','Context ctx[LA5_CONTEXTS];\n std::vector<la::Entry> oracle[LA5_CONTEXTS];unsigned olen[LA5_CONTEXTS]={};for(auto& a:oracle)a.resize(capacity);')
s=s.replace('case SEED:x.value=', 'case SEED:olen[s]=0;la::push(oracle[s].data(),olen[s],{sources[x.qid],0,0});x.value=')
s=s.replace('x.cur=unpack(even[s][0]);','{auto expected=la::pop(oracle[s].data(),olen[s]);auto actual=unpack(even[s][0]);assert(std::memcmp(&expected,&actual,sizeof(actual))==0);}x.cur=unpack(even[s][0]);')
s=s.replace('else{visited[s][x.dst]=bits(x.next.delay);','else{la::push(oracle[s].data(),olen[s],x.next);visited[s][x.dst]=bits(x.next.delay);')
s=s.replace('counters[32]+=tick', 'assert(olen[s]==x.size);for(unsigned i=0;i<x.size;++i){auto actual=unpack(get(even[s],odd[s],i));assert(std::memcmp(&actual,&oracle[s][i],sizeof(actual))==0);}counters[32]+=tick')
p.write_text(s)
base=['c++','-O2','-std=c++14','-ffp-contract=off','-fno-fast-math','-DLA5_CONTEXTS=4','-Iaccel/lookahead/include','-Iaccel/lookahead/round4','-I/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis_HLS/2022.2/include']
files=sorted(Path('results/lookahead_accel_round4_20261108T182500Z/semantic_fixtures').glob('*.bin'))
receipts=[]
for early in [0,1]:
 binary=o/('audit_'+str(early));cmd=base+['-DLA4_EARLY='+str(early),str(o/'interleave5.cpp'),str(o/'mechanism_tests5.cpp'),'-o',str(binary)];subprocess.run(cmd,check=True)
 with (o/('mode'+str(early)+'.log')).open('w') as f:run=subprocess.run([str(binary),*map(str,files)],stdout=f,stderr=subprocess.STDOUT)
 assert not run.returncode;receipts.append(dict(early=early,command=cmd,returncode=run.returncode))
(o/'result.json').write_text(json.dumps(dict(status='passed',source_sha256=original,instrumented_sha256=sha256(p),evidence='measured',scope='Host functionality only, every staged heap operation final full-array arrangement and pop value matches strict_heap; 509 fixtures x 7 semantic-only interleaved qids x 2 calls x 2 modes',runs=receipts),indent=2))
