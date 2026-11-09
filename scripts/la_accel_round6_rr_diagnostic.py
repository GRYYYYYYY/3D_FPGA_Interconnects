"""Build an isolated RR-load attribution binary; never modify vendor/build inputs."""
import json,shlex,subprocess,shutil,sys
from pathlib import Path
from prepare import sha256
R=Path(__file__).resolve().parents[1];o=Path(sys.argv[1]).resolve();o.mkdir(exist_ok=False);src=o/'io';shutil.copytree(R/'vendor/vtr_cpu_slices/libs/librrgraph/src/io',src)
(src/'r6_timer.hpp').write_text('''#pragma once
#include <chrono>
#include <cstdio>
struct R6Timer {const char* name;std::chrono::steady_clock::time_point start;R6Timer(const char* n):name(n),start(std::chrono::steady_clock::now()){}~R6Timer(){fprintf(stderr,"R6_RR_STAGE %s %.9f\\n",name,std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count());}};
''')
p=src/'gen/rr_graph_uxsdcxx.h';s=p.read_text();s='#include "../r6_timer.hpp"\n'+s
s=s.replace('pugi::xml_parse_result result = doc.load(is);','pugi::xml_parse_result result; {R6Timer t("read_parse_dom_allocate"); result = doc.load(is);}')
for name in ['load_rr_nodes','load_rr_edges']:
 needle='inline void '+name+'(';pos=s.index(needle,s.index('/* Load function for the root element. */'));pos=s.index('{',pos);s=s[:pos+1]+f' R6Timer r6t("{name}");'+s[pos+1:]
s=s.replace('out.finish_load();','{R6Timer t("finish_load_total");out.finish_load();}');p.write_text(s)
p=src/'rr_graph_uxsdcxx_serializer.h';s='#include "r6_timer.hpp"\n'+p.read_text()
for needle,name in [('rr_graph_builder_->partition_edges();','partition_edges'),('process_rr_node_indices();','node_indices'),('rr_graph_builder_->init_fan_in();','fan_in')]:
 assert needle in s;s=s.replace(needle,'{R6Timer t("'+name+'");'+needle+'}')
for needle,name in [('        alloc_and_load_rr_indexed_data(','indexed_data'),('            check_rr_graph(*rr_graph_,','check_rr_graph')]:
 pos=s.index(needle);end=s.index(');',pos)+2;s=s[:pos]+'{R6Timer t("'+name+'");'+s[pos:end]+'}'+s[end:]
p.write_text(s)
c=next(x for x in json.load(open(R/'build_cpu_slices/compile_commands.json')) if x['file'].endswith('/rr_graph_reader.cpp'));cmd=shlex.split(c['command']);cmd[cmd.index('-c')+1]=str(src/'rr_graph_reader.cpp');cmd[cmd.index('-o')+1]=str(o/'reader.o');cmd.insert(1,'-I'+str(src/'gen'))
commands=[(c['directory'],cmd)];cwd,link=json.load(open(R/'results/lookahead_accel_20261108T125500Z/native_build_v4/commands.json'))[-1];link[link.index('-o')+1]=str(o/'vpr_rr_diagnostic');link.insert(1,str(o/'reader.o'));runtime=R/'data/vpr_runtime_20261025';link=[str(runtime/Path(x).name.replace('.so.12.5','.so.12').replace('.so.2.5','.so.2')) if Path(x).name.startswith(('libtbb.so','libtbbmalloc')) else x for x in link];link.insert(1,'-Wl,-rpath-link,'+str(runtime));commands.append((cwd,link));(o/'commands.json').write_text(json.dumps(commands,indent=2))
with (o/'build.log').open('w') as f:
 for cwd,cmd in commands:subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=180,check=True)
(o/'binding.json').write_text(json.dumps(dict(binary_sha256=sha256(o/'vpr_rr_diagnostic'),sources={str(p.relative_to(o)):sha256(p) for p in src.rglob('*') if p.is_file()},scope='Diagnostic only; parse includes file IO and DOM allocations; serializer timers nest, do not add inclusive totals'),indent=2))
