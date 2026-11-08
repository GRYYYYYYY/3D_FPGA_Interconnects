#include "io.hpp"
#include <queue>
#include <chrono>
#include <iostream>
#include <cstring>
#include <cfenv>
#include <omp.h>
struct Compare {bool operator()(la::Entry a,la::Entry b) const {return a.delay>b.delay;}};
int main(int argc,char** argv) {
 try {
  if(argc!=3 && argc!=4) throw std::runtime_error("usage: cpu_reference workload.bin output.bin [workers]");
  if(std::ifstream(argv[2]).good()) throw std::runtime_error("output exists");
  std::fesetround(FE_TONEAREST);la::Workload w(argv[1]);
  int workers=argc==4?std::stoi(argv[3]):1;if(workers<1 || workers>128)throw std::runtime_error("invalid workers");
  struct Scratch {std::vector<float> visited;std::vector<unsigned char> expanded;std::priority_queue<la::Entry,std::vector<la::Entry>,Compare> pq;};
  std::vector<Scratch> scratch(workers);std::vector<la::Cost> out(w.h.jobs*w.h.cells);
  for(auto& s:scratch){s.visited.resize(w.h.nodes);s.expanded.resize(w.h.nodes);std::vector<la::Entry> storage;storage.reserve(w.h.edges+1);s.pq=decltype(s.pq)(Compare{},std::move(storage));}
  // Numeric validation is part of E1 below. Failure is reduced, not thrown across an OpenMP region.
  int failed=0;
  uint64_t pushes=0,pops=0,edges=0,peak=0;
  auto start=std::chrono::steady_clock::now();
  #pragma omp parallel for schedule(dynamic) num_threads(workers) reduction(+:pushes,pops,edges) reduction(max:peak,failed)
  for(size_t q=0;q<w.h.jobs;++q) {
   auto& local=scratch[omp_get_thread_num()];auto& visited=local.visited;auto& expanded=local.expanded;auto& pq=local.pq;
   std::fill(visited.begin(),visited.end(),-1.f);std::fill(expanded.begin(),expanded.end(),0);
   for(size_t c=0;c<w.h.cells;++c) out[q*w.h.cells+c]={la::missing(),la::missing()};
   pq.push({w.job[q].source,0,0});++pushes;peak=std::max<uint64_t>(peak,1);
   while(!pq.empty()) {
    auto cur=pq.top();pq.pop();++pops;auto u=cur.node;if(expanded[u])continue;
    int32_t cell=w.cell[q*w.h.nodes+u];if(w.node[u].type==1 && cell>=0)la::record(out[q*w.h.cells+cell],cur);
    for(uint64_t i=w.row[u];i<w.row[u+1];++i) {
     ++edges;uint32_t v=w.edge[i].dst;int e=la::eligible(w.node[u],w.node[v]);if(!e)continue;if(e<0)break;if(expanded[v])continue;
     auto c=w.cost[w.node[v].cost];if(!la::numeric(c.delay)||!la::numeric(c.congestion)){failed=1;continue;}
     la::Entry next{v,cur.delay+c.delay,cur.congestion+c.congestion};
     if(!la::numeric(next.delay)||!la::numeric(next.congestion)){failed=1;continue;}
     if(visited[v]>=0 && visited[v]<next.delay)continue;visited[v]=next.delay;pq.push(next);++pushes;peak=std::max<uint64_t>(peak,pq.size());
    }
    expanded[u]=1;
   }
  }
  double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
  if(failed)throw std::runtime_error("unsupported_numeric_case");
  for(size_t i=0;i<out.size();++i) if(std::memcmp(&out[i],&w.golden[i],sizeof(la::Cost))) {std::cerr<<"first mismatch cell "<<i<<"\n";return 2;}
  std::ofstream f(argv[2],std::ios::binary);la::write(f,out.data(),out.size());
  std::cout<<"{\"evidence_type\":\"cpu_measured\",\"variant\":\"C1_std_priority_queue\",\"semantic_mode\":\"STRICT_FP32\",\"timing_scope\":\"resident_flood_batch\",\"resident_elapsed_s\":"<<elapsed<<",\"matches_reference\":true,\"cpu_workers\":"<<workers<<",\"pushes\":"<<pushes<<",\"pops\":"<<pops<<",\"edge_visits\":"<<edges<<",\"peak_queue_entries\":"<<peak<<"}\n";
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
