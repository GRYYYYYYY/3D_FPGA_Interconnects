#include "io.hpp"
#include <iostream>
#include <cstring>
#include <algorithm>
#include <set>
// Logical operation counts only: this executable is never an FPGA timing model.
struct Heap {
 std::vector<la::Entry> a;uint64_t reads=0,writes=0,pair_hits=0,last_pair=UINT64_MAX;unsigned top;
 Heap(size_t n,unsigned t):a(n),top(t){}
 la::Entry get(unsigned i){if(i>=top){++reads;if(last_pair==i/2)++pair_hits;last_pair=i/2;}return a[i];}
 void set(unsigned i,la::Entry v){a[i]=v;if(i>=top)++writes;}
};
void push(Heap& a,unsigned& n,la::Entry v){unsigned h=n++;while(h){unsigned p=(h-1)/2;auto old=a.get(p);if(!(old.delay>v.delay))break;a.set(h,old);h=p;}a.set(h,v);}
la::Entry pop(Heap& a,unsigned& n){auto result=a.get(0),v=a.get(--n);if(!n)return result;unsigned h=0,c=2;
 while(c<n){auto right=a.get(c),left=a.get(c-1);if(right.delay>left.delay){--c;right=left;}a.set(h,right);h=c;c=2*(h+1);}
 if(c==n){a.set(h,a.get(c-1));h=c-1;}
 while(h){unsigned p=(h-1)/2;auto old=a.get(p);if(!(old.delay>v.delay))break;a.set(h,old);h=p;}a.set(h,v);return result;}
int main(int argc,char** argv){try{
 if(argc!=4)throw std::runtime_error("usage: spill_profile workload layers.bin heap_top");
 la::Workload w(argv[1]);std::vector<uint32_t> layers(w.h.nodes);std::ifstream f(argv[2],std::ios::binary);la::read(f,layers.data(),layers.size());
 unsigned top=std::stoul(argv[3]);uint64_t cross_static=0;for(unsigned u=0;u<w.h.nodes;++u)for(auto i=w.row[u];i<w.row[u+1];++i)cross_static+=layers[u]!=layers[w.edge[i].dst];
 std::cout<<"{\"evidence_type\":\"logical_counts_not_FPGA_cycles\",\"heap_top\":"<<top<<",\"static_cross_layer_edges\":"<<cross_static<<",\"samples\":[";
 for(unsigned q=0;q<w.h.jobs;++q){
  Heap heap(w.h.edges+1,top);unsigned count=0;std::vector<float> visited(w.h.nodes,-1.f);std::vector<unsigned> expanded(w.h.nodes,0);std::vector<la::Cost> out(w.h.cells,{la::missing(),la::missing()});
  la::Stats st={1,0,0,0,1,la::OK};uint64_t cross_scanned=0,cross_pushed=0;std::set<unsigned> reached;
  push(heap,count,{w.job[q].source,0,0});
  while(count){auto cur=pop(heap,count);++st.pops;unsigned u=cur.node;if(expanded[u])continue;reached.insert(layers[u]);
   int cell=w.cell[q*w.h.nodes+u];if(w.node[u].type==1 && cell>=0)la::record(out[cell],cur);
   for(auto i=w.row[u];i<w.row[u+1];++i){++st.edges;unsigned v=w.edge[i].dst;bool cross=layers[u]!=layers[v];cross_scanned+=cross;int eligible=la::eligible(w.node[u],w.node[v]);if(!eligible)continue;if(eligible<0)break;if(expanded[v])continue;
    auto c=w.cost[w.node[v].cost];la::Entry next={v,cur.delay+c.delay,cur.congestion+c.congestion};
    if(!la::numeric(c.delay)||!la::numeric(c.congestion)||!la::numeric(next.delay)||!la::numeric(next.congestion))throw std::runtime_error("unsupported numeric");
    if(visited[v]>=0 && visited[v]<next.delay)continue;visited[v]=next.delay;push(heap,count,next);cross_pushed+=cross;++st.pushes;st.peak=std::max<uint64_t>(st.peak,count);
   }expanded[u]=1;++st.expanded;
  }
  if(std::memcmp(out.data(),w.golden.data()+q*w.h.cells,out.size()*sizeof(la::Cost)))throw std::runtime_error("golden mismatch");
  if(q)std::cout<<",";std::cout<<"{\"qid\":"<<q<<",\"source\":"<<w.job[q].source<<",\"source_layer\":"<<layers[w.job[q].source]<<",\"expanded_layers\":"<<reached.size()<<",\"cross_scanned\":"<<cross_scanned<<",\"cross_pushed\":"<<cross_pushed<<",\"external_queue_reads\":"<<heap.reads<<",\"external_queue_writes\":"<<heap.writes<<",\"adjacent_pair_read_hits\":"<<heap.pair_hits<<",\"pushes\":"<<st.pushes<<",\"pops\":"<<st.pops<<",\"edges\":"<<st.edges<<",\"peak\":"<<st.peak<<"}";
 }std::cout<<"],\"all_native_golden_bits_match\":true}\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
