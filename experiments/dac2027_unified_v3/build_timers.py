"""Rebuild in private output directories. All historical files are read-only."""
import concurrent.futures, hashlib, json, os, shlex, shutil, subprocess
from pathlib import Path
here=Path(__file__).resolve().parent
base=here.parents[2]
stock=base/'3D_FPGA_routing/vendor/vtr'
old=next((base/'3D_FPGA_Interconnects_R6_1/results').glob('*/native_build/commands.json')).parent
runtime=base/'3D_FPGA_Interconnects/data/vpr_runtime_20261025'
tbb=base/'3D_FPGA_Interconnects/results/lookahead_accel_20261108T125500Z/deps/tbb/usr/include'
out=here/'build'
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,cwd=None): subprocess.run(args,cwd=cwd,check=True)
def replace(args,opt,new):
    args[args.index(opt)+1]=str(new)
def instrument(source,d):
    key='void MapLookahead::compute(const std::vector<t_segment_inf>& segment_inf) {'
    s=source.read_text()
    assert s.count(key)==1
    p=d/'router_lookahead_map.cpp'
    p.write_text('#include "e2_timer.hpp"\n'+s.replace(key,key+'\n    V3ComputeTimer v3_timer;'))
    return p
def build_candidate():
    d=out/'candidate';d.mkdir(exist_ok=True)
    cmds=json.loads((old/'commands.json').read_text())
    cwd,args=cmds[0];src=Path(args[-1]);args[-1]=str(instrument(src,d))
    args[1:1]=['-I'+str(src.parent),'-I'+str(here)];obj=d/'router_lookahead_map.cpp.o';replace(args,'-o',obj)
    run(args,cwd)
    archive=d/'libvpr.a';shutil.copyfile(old/'libvpr.a',archive);run(['ar','r',archive,obj])
    cwd,args=cmds[-1];args[args.index(str(old/'libvpr.a'))]=str(archive);replace(args,'-o',d/'vpr')
    run(args,cwd)
def build_stock():
    d=out/'stock';d.mkdir(exist_ok=True)
    baseline='0b912334fdd83bb754b302146ac0d1ec9edc9a0e'
    tar=d/'pristine.tar'
    run(['git','-C',stock,'archive','-o',tar,baseline,'vpr/src'])
    run(['tar','xf',tar,'-C',d])
    shared=Path('vpr/src/draw/breakpoint_state_globals.h')
    assert sha(d/shared)==sha(stock/shared)
    (d/shared).unlink();(d/shared).symlink_to(stock/shared)
    build=stock/'build/vpr';cfg=build/'CMakeFiles/libvpr.dir'
    cfgs={k:shlex.split(v) for k,v in (line.split(' = ',1) for line in (cfg/'flags.make').read_text().splitlines() if ' = ' in line)}
    flags=[str(x).replace(str(stock/'vpr/src'),str(d/'vpr/src')) for k in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS') for x in cfgs[k]]
    flags+=['-I'+str(tbb),'-I'+str(here)]
    objects=shlex.split((cfg/'link.txt').read_text().splitlines()[0])[3:]
    def compile_one(item):
        relative=Path(item).relative_to('CMakeFiles/libvpr.dir').with_suffix('')
        src=d/'vpr'/relative
        if not src.exists(): return None # extension absent from pristine source tree
        obj=d/'objects'/relative.with_suffix(relative.suffix+'.o')
        obj.parent.mkdir(parents=True,exist_ok=True)
        if src.name=='router_lookahead_map.cpp':
            args=['-I'+str(src.parent)];src=instrument(src,d)
        else: args=[]
        if not obj.exists() or src.name=='router_lookahead_map.cpp':
            run(['/usr/bin/g++-11',*flags,*args,'-c',src,'-o',obj],build)
        return obj
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        objs=[x for x in pool.map(compile_one,objects) if x]
    assert len(objs)>250,len(objs)
    archive=d/'libvpr.a'
    run(['ar','rcs',archive,*objs])
    cmd=shlex.split((build/'CMakeFiles/vpr.dir/link.txt').read_text())
    cmd[cmd.index('libvpr.a')]=str(archive);replace(cmd,'-o',d/'vpr_stock')
    for i,a in enumerate(cmd):
        if a.startswith('/usr/lib/') and 'libtbb' in a: cmd[i]=str(runtime/Path(a).name.replace('.12.5','.12').replace('.2.5','.2'))
    cmd.insert(1,'-Wl,-rpath-link,'+str(runtime))
    run(cmd,build)
if __name__=='__main__':
    build_candidate();build_stock()
    paths=[here/'e2_timer.hpp',here/'build_timers.py',out/'candidate/vpr',out/'stock/vpr_stock']
    (here/'audit/timer_build.json').write_text(json.dumps({str(p):sha(p) for p in paths},indent=2)+'\n')
