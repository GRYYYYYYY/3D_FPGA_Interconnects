#include "reference4.hpp"
#include "strict_heap.hpp"
#include <iostream>
#include <cstring>
#include <array>
#include <sstream>
struct Profile {uint64_t eligible=0,fp=0,cross=0,crosspush=0,last=0,down=0,up=0;std::array<uint64_t,32> depth{};};
int main(int argc,char**argv){try{
 if(argc!=5)throw std::runtime_error("profile5 workload layers|- output trace|-");
 la::Workload w(argv[1]);la4::Prepared prep(w);std::vector<uint32_t> layers(w.h.nodes);bool has=std::string(argv[2])!="-";if(has){std::ifstream f(argv[2],std::ios::binary);la::read(f,layers.data(),layers.size());}
 std::ofstream report(argv[3]),trace;if(std::string(argv[4])!="-")trace.open(argv[4]);
 std::vector<la::Entry> heap(w.h.edges+1);std::vector<float> visit(w.h.nodes);std::vector<bool> expanded(w.h.nodes);std::vector<la::Cost> out(w.h.cells);
 for(int early=0;early<2;++early)for(unsigned q=0;q<w.h.jobs;++q){
 Profile p;la::Stats st{};uint32_t count=0,recorded=0;std::fill(visit.begin(),visit.end(),-1);std::fill(expanded.begin(),expanded.end(),false);for(auto&c:out)c={la::missing(),la::missing()};
 auto event=[&](char op,uint64_t work,uint64_t seq){if(trace)trace<<early<<','<<q<<','<<op<<','<<work<<','<<seq<<'\n';};
 auto push=[&](la::Entry v){uint32_t hole=count++;unsigned levels=0;while(hole){++levels;unsigned par=(hole-1)/2;if(!(heap[par].delay>v.delay))break;heap[hole]=heap[par];hole=par;}heap[hole]=v;p.up+=levels;++st.pushes;st.peak=std::max<uint64_t>(st.peak,count);event('U',levels,st.pushes);};
 if(!early||prep.targets[q])push({w.job[q].source,0,0});
 while(count){unsigned dep=0;for(unsigned n=count;n>1;n>>=1)++dep;++p.depth[dep];
 auto cur=heap[0],v=heap[--count];unsigned hole=0,child=2,levels=0,up=0;
 if(count){while(child<count){++levels;if(heap[child].delay>heap[child-1].delay)--child;heap[hole]=heap[child];hole=child;child=2*(hole+1);}if(child==count){++levels;heap[hole]=heap[child-1];hole=child-1;}while(hole){++up;unsigned par=(hole-1)/2;if(!(heap[par].delay>v.delay))break;heap[hole]=heap[par];hole=par;}heap[hole]=v;}p.down+=levels;p.up+=up;++st.pops;event('P',levels+up,st.pops);
 unsigned u=cur.node;if(expanded[u])continue;int cell=w.cell[q*w.h.nodes+u];if(w.node[u].type==1&&cell>=0){bool first=out[cell].delay!=out[cell].delay;la::record(out[cell],cur);if(first){++recorded;p.last=st.pops;}if(early&&recorded==prep.targets[q])break;}
 for(uint64_t i=w.row[u];i<w.row[u+1];++i){++st.edges;unsigned dst=w.edge[i].dst;if(has&&layers[u]!=layers[dst])++p.cross;int a=la::eligible(w.node[u],w.node[dst]);event('E',a==1,i);if(!a)continue;if(a<0)break;++p.eligible;if(expanded[dst])continue;
 auto c=w.cost[w.node[dst].cost];la::Entry e={dst,cur.delay+c.delay,cur.congestion+c.congestion};p.fp+=2;if(visit[dst]>=0&&visit[dst]<e.delay)continue;visit[dst]=e.delay;push(e);if(has&&layers[u]!=layers[dst])++p.crosspush;
 }expanded[u]=true;++st.expanded;
 }
 if(std::memcmp(out.data(),w.golden.data()+q*w.h.cells,w.h.cells*sizeof(la::Cost)))throw std::runtime_error("profile map mismatch");
 auto j=w.job[q];report<<"{\"evidence\":\"measured\",\"kind\":\"logical_CXX_counts\",\"early\":"<<early<<",\"qid\":"<<q<<",\"source\":"<<j.source<<",\"group\":"<<j.group<<",\"ordinal\":"<<j.ordinal<<",\"layer\":"<<j.layer<<",\"segment\":"<<j.segment<<",\"channel\":"<<j.channel<<",\"targets\":"<<prep.targets[q]<<",\"recorded\":"<<recorded<<",\"last_target_pop\":"<<p.last<<",\"pops\":"<<st.pops<<",\"pushes\":"<<st.pushes<<",\"original_edges\":"<<st.edges<<",\"actual_candidates\":"<<p.eligible<<",\"heap_peak\":"<<st.peak<<",\"expanded\":"<<st.expanded<<",\"heap_down_levels\":"<<p.down<<",\"heap_up_levels\":"<<p.up<<",\"fp_adds\":"<<p.fp<<",\"reset_labels\":"<<w.h.nodes<<",\"output_cells\":"<<w.h.cells<<",\"cross_edges\":"<<(has?std::to_string(p.cross):"null")<<",\"cross_pushes\":"<<(has?std::to_string(p.crosspush):"null")<<",\"scheduler_wait\":null,\"heap_depth_histogram\":[";for(unsigned i=0;i<32;++i)report<<(i?",":"")<<p.depth[i];report<<"],\"map_match\":true}\n";report.flush();
 }std::cout<<"PASS all native maps "<<argv[1]<<'\n';
}catch(std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
