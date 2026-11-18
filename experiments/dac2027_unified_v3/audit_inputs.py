import csv, hashlib, json, subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
base = here.parents[2]
prior = here.parents[1] / 'accel/lookahead/gemm_bnn_native_completion'
paper = base / '3D_FPGA_Interconnects_PAPER_V3/paper/dac2027_mechanism_ablation/evidence'
def read(p): return json.loads(p.read_text())
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(4<<20), b''): h.update(chunk)
    return h.hexdigest()

cases = {k:v['case'] for k,v in read(prior/'input_manifest.json').items()}
cases['lstm'] = read(base/'3D_FPGA_Interconnects/results/native_cpu_width120_20261104/lstm_s2/vpr_case.json')
assert cases['lstm']['inputs']['rr_graph']['sha256']==read(paper/'holdout_selection.json')['input_bindings']['rr_graph']['sha256']
(here/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
bindings = read(prior/'source_binding.json')
with (here/'audit/bindings.csv').open('w') as f:
    out=csv.writer(f);out.writerow(['role','file','bytes','sha256','expected','match'])
    def check(role,p,h):
        p=Path(p); actual=sha(p);out.writerow([role,str(p),p.stat().st_size,actual,h,actual==h]);f.flush()
        if actual!=h: raise ValueError(str(p))
    for case,data in cases.items():
        for k,v in data['inputs'].items(): check(case+'.'+k,v['path'],v['sha256'])
    for k,v in bindings['binary'].items(): check(k,v['path'],v['sha256'])
    for k,h in bindings['source_sha256'].items(): check('source',prior/k,h)
    for v in read(prior/'runtime.json')['libraries']: check('runtime',v['path'],v['sha256'])
subprocess.run(['g++','-O2','-std=c++17','topology.cpp','-o','build/topology'],cwd=here,check=True)
with (here/'audit/topology.csv').open('w') as f:
    f.write('case,layers,nodes,edges,intra_local,inter_layer_span,disjoint_endpoint_spans,CHANZ,samples,seed,width\n')
    for case,data in cases.items():
        stats=subprocess.check_output([here/'build/topology',data['inputs']['rr_graph']['path']],text=True).strip()
        if case=='lstm':
            sel=read(paper/'holdout_selection.json')['actual_RR']
            ref=(sel['N'],sel['E'])
        else:
            meta=read(prior/'metadata'/f'{case}.json'); assert len(meta['jobs'])==meta['J']==40
            ref=(meta['N'],meta['E'])
        assert tuple(map(int,stats.split(',')[1:3]))==ref
        f.write(f"{case},{stats},40,{data['seed']},{data['route_chan_width']}\n");f.flush()
