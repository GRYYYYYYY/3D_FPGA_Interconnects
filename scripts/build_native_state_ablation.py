"""Isolated one-object rebuild using retained build commands, through make."""
from pathlib import Path
import subprocess,shlex,json,shutil,sys,hashlib,difflib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_state_ablation_20261102';BUILD=ROOT/'build_cpu_paper'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=False);(OUT/'bin').mkdir();(OUT/'source').mkdir();(OUT/'HANDOFF.before_study.md').write_text((ROOT/'HANDOFF.md').read_text())
 original=ROOT/'vendor/vtr_cpu_paper/vpr/src/route/route.cpp';s=original.read_text();old=s
 s='#include <cstdlib>\n#include <cstring>\n'+s
 marker='    for (itry = 1; itry <= router_opts.max_router_iterations; ++itry) {'
 code='''    // Experimental attribution only; the normal default retains both fixes.
    const char* repair_mode = std::getenv("VPR_CPU_REPAIR_MODE");
    if (!repair_mode) repair_mode = "both";
    VTR_ASSERT(std::strcmp(repair_mode, "none") == 0 || std::strcmp(repair_mode, "dynamic") == 0
               || std::strcmp(repair_mode, "reload") == 0 || std::strcmp(repair_mode, "both") == 0);
    const bool repair_dynamic = std::strcmp(repair_mode, "both") == 0 || std::strcmp(repair_mode, "dynamic") == 0;
    const bool repair_reload = std::strcmp(repair_mode, "both") == 0 || std::strcmp(repair_mode, "reload") == 0;
    VTR_LOG("CPU_REPAIR mode=%s dynamic=%d reload=%d\\n", repair_mode, repair_dynamic, repair_reload);
'''
 assert s.count(marker)==1;s=s.replace(marker,code+marker)
 target='            dynamic_update_bounding_boxes(iter_results.rerouted_nets, iter_results.bb_updated_nets);'
 s=s.replace(target,'''            if (repair_dynamic) {
                dynamic_update_bounding_boxes(iter_results.rerouted_nets, iter_results.bb_updated_nets);
            } else {
                // Reproduce the original by-value output: boxes change, notifications are discarded.
                auto discarded_notifications = iter_results.bb_updated_nets;
                dynamic_update_bounding_boxes(iter_results.rerouted_nets, discarded_notifications);
            }''')
 marker='        if (itry >= high_effort_congestion_mode_iteration_threshold) {'
 s=s.replace(marker,'''        if (!repair_reload) {
            num_net_bounding_boxes_updated = iter_results.bb_updated_nets.size();
            netlist_router->handle_bb_updated_nets(iter_results.bb_updated_nets);
        }

'''+marker)
 s=s.replace('                auto all_nets = net_list.nets();\n                iter_results.bb_updated_nets.assign(all_nets.begin(), all_nets.end());','''                if (repair_reload) {
                    auto all_nets = net_list.nets();
                    iter_results.bb_updated_nets.assign(all_nets.begin(), all_nets.end());
                }''')
 s=s.replace('        // Notify only after both dynamic box growth and conflicted-mode reloads.\n        num_net_bounding_boxes_updated = iter_results.bb_updated_nets.size();\n        netlist_router->handle_bb_updated_nets(iter_results.bb_updated_nets);','''        // Notify after full reload only when the second fix is enabled.
        if (repair_reload) {
            num_net_bounding_boxes_updated = iter_results.bb_updated_nets.size();
            netlist_router->handle_bb_updated_nets(iter_results.bb_updated_nets);
        }''')
 source=OUT/'source/route.cpp';source.write_text(s);(OUT/'state_ablation.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=str(original),tofile=str(source))))
 cmds=subprocess.check_output(['ninja','-C',str(BUILD),'-t','commands','vpr'],text=True).splitlines()
 compile=shlex.split(next(c for c in cmds if ' -c ' in c and c.endswith('/route/route.cpp')))
 for option,value in [('-o',OUT/'route.cpp.o'),('-MF',OUT/'route.cpp.o.d'),('-MT',OUT/'route.cpp.o'),('-c',source)]:compile[compile.index(option)+1]=str(value)
 link=shlex.split(cmds[-1].removeprefix(': && ').removesuffix(' && :'))
 link[link.index('-o')+1]=str(OUT/'bin/vpr_state');link[link.index('vpr/libvpr.a')]=str(OUT/'libvpr.a')
 steps=[compile,['cp','--reflink=auto',str(BUILD/'vpr/libvpr.a'),str(OUT/'libvpr.a')],['ar','r',str(OUT/'libvpr.a'),str(OUT/'route.cpp.o')],link]
 makefile=OUT/'Makefile';makefile.write_text('.PHONY: all\nall:\n'+''.join('\tcd '+shlex.quote(str(BUILD))+' && '+shlex.join(c)+'\n' for c in steps))
 bindings={str(original):sha(original),str(source):sha(source),str(BUILD/'vpr/libvpr.a'):sha(BUILD/'vpr/libvpr.a')}
 with (OUT/'build.log').open('w') as log:subprocess.run(['make','-f',str(makefile)],cwd=ROOT/'vendor/vtr_cpu_paper',stdout=log,stderr=subprocess.STDOUT,check=True)
 for path,h in bindings.items():assert sha(Path(path))==h
 (OUT/'build_provenance.json').write_text(json.dumps(dict(commands=steps,source_bindings=bindings,binary=dict(path=str(OUT/'bin/vpr_state'),sha256=sha(OUT/'bin/vpr_state')),scope='Existing libraries read-only; isolated copy of libvpr archive with only route.cpp.o replaced. Same compiler flags, no default binary changed.'),indent=2)+'\n')
 print('built',OUT)
if __name__=='__main__':main()
