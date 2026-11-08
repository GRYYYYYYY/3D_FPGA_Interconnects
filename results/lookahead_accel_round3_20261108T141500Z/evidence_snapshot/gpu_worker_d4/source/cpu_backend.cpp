#include "backend.hpp"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cfenv>
#include <queue>
#include <vector>
#include <stdexcept>
#include <omp.h>
namespace {
using Clock=std::chrono::steady_clock;
double elapsed(Clock::time_point a){return std::chrono::duration<double>(Clock::now()-a).count();}
struct Compare {bool operator()(la::Entry a,la::Entry b)const{return a.delay>b.delay;}};
struct Scratch {
 std::vector<float> visited;std::vector<unsigned char> expanded;
 std::priority_queue<la::Entry,std::vector<la::Entry>,Compare> queue;
};
}
extern "C" int la_backend_v1(const la::BackendInput* in,la::Cost* out,la::Stats* stats,
 la::BackendMetrics* metrics,char* error,uint32_t error_size) {
 try {
  if(!in || in->version!=1 || !in->contexts || in->contexts>128 || in->ne>=UINT32_MAX)
   throw std::runtime_error("invalid backend input");
  const auto& w=*in;auto service=Clock::now();*metrics={1,1,0,0,0,0,0};
  std::fesetround(FE_TONEAREST);
  std::vector<Scratch> scratch(w.contexts);
  for(auto& s:scratch){s.visited.resize(w.n);s.expanded.resize(w.n);
   std::vector<la::Entry> data;data.reserve(w.ne+1);s.queue=decltype(s.queue)(Compare{},std::move(data));}
  metrics->prepare_s=elapsed(service);auto start=Clock::now();int failed=0;
  #pragma omp parallel for schedule(dynamic) num_threads(w.contexts) reduction(max:failed)
  for(uint32_t q=0;q<w.nj;++q) {
   auto& s=scratch[omp_get_thread_num()];auto& pq=s.queue;
   std::fill(s.visited.begin(),s.visited.end(),-1.f);std::fill(s.expanded.begin(),s.expanded.end(),0);
   for(uint32_t c=0;c<w.nc;++c)out[uint64_t(q)*w.nc+c]={la::missing(),la::missing()};
   la::Stats st={1,0,0,0,1,la::OK};pq.push({w.jobs[q].source,0,0});
   while(!pq.empty()) {
    auto cur=pq.top();pq.pop();++st.pops;auto u=cur.node;if(s.expanded[u])continue;
    int32_t cell=w.cells[uint64_t(q)*w.n+u];if(w.nodes[u].type==1 && cell>=0)la::record(out[uint64_t(q)*w.nc+cell],cur);
    for(uint64_t i=w.row[u];i<w.row[u+1];++i){++st.edges;auto v=w.edges[i].dst;
     int e=la::eligible(w.nodes[u],w.nodes[v]);if(!e)continue;if(e<0)break;if(s.expanded[v])continue;
     la::Cost c=w.costs[w.nodes[v].cost];la::Entry next={v,cur.delay+c.delay,cur.congestion+c.congestion};
     if(!la::numeric(c.delay)||!la::numeric(c.congestion)||!la::numeric(next.delay)||!la::numeric(next.congestion)){
      st.status=la::UNSUPPORTED_NUMERIC;failed=1;continue;}
     if(s.visited[v]>=0 && s.visited[v]<next.delay)continue;
     s.visited[v]=next.delay;pq.push(next);++st.pushes;st.peak=std::max<uint64_t>(st.peak,pq.size());
    }
    s.expanded[u]=1;++st.expanded;
   }
   stats[q]=st;
  }
  metrics->resident_s=elapsed(start);start=Clock::now();scratch.clear();
  metrics->release_s=elapsed(start);metrics->service_s=elapsed(service);
  if(failed)throw std::runtime_error("unsupported numeric case");
  return 0;
 }catch(const std::exception& e){if(error_size)std::snprintf(error,error_size,"%s",e.what());return 1;}
}
