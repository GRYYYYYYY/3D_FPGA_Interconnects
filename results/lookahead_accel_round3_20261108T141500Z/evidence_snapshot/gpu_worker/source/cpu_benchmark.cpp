#include "io.hpp"
#include <queue>
#include <chrono>
#include <iostream>
#include <iomanip>
#include <cstring>
#include <cfenv>
#include <omp.h>
using Clock=std::chrono::steady_clock;
double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
struct Compare{bool operator()(la::Entry a,la::Entry b)const{return a.delay>b.delay;}};
struct Scratch{std::vector<float> visited;std::vector<unsigned char> expanded;std::priority_queue<la::Entry,std::vector<la::Entry>,Compare> pq;};
int main(int argc,char** argv){try{
 if(argc!=4)throw std::runtime_error("usage: cpu_benchmark workload workers warm_repeats");
 std::fesetround(FE_TONEAREST);la::Workload w(argv[1]);int workers=std::stoi(argv[2]),repeats=std::stoi(argv[3]);
 if(workers<1||workers>128||repeats<1)throw std::runtime_error("invalid configuration");
 auto service=Clock::now();std::vector<Scratch> scratch(workers);std::vector<la::Cost> out(w.golden.size());std::vector<la::Stats> stats(w.h.jobs);
 for(auto& s:scratch){s.visited.resize(w.h.nodes);s.expanded.resize(w.h.nodes);std::vector<la::Entry> a;a.reserve(w.h.edges+1);s.pq=decltype(s.pq)(Compare{},std::move(a));}
 double prepare=seconds(service);std::cout<<std::setprecision(17);
 for(int repeat=0;repeat<=repeats;++repeat){
  auto begin=Clock::now();int failed=0;
  #pragma omp parallel for schedule(dynamic) num_threads(workers) reduction(max:failed)
  for(size_t q=0;q<w.h.jobs;++q){auto& s=scratch[omp_get_thread_num()];auto& pq=s.pq;
   std::fill(s.visited.begin(),s.visited.end(),-1.f);std::fill(s.expanded.begin(),s.expanded.end(),0);
   for(size_t c=0;c<w.h.cells;++c)out[q*w.h.cells+c]={la::missing(),la::missing()};
   la::Stats st={1,0,0,0,1,la::OK};pq.push({w.job[q].source,0,0});
   while(!pq.empty()){auto cur=pq.top();pq.pop();++st.pops;unsigned u=cur.node;if(s.expanded[u])continue;
    int cell=w.cell[q*w.h.nodes+u];if(w.node[u].type==1 && cell>=0)la::record(out[q*w.h.cells+cell],cur);
    for(auto i=w.row[u];i<w.row[u+1];++i){++st.edges;auto v=w.edge[i].dst;int e=la::eligible(w.node[u],w.node[v]);if(!e)continue;if(e<0)break;if(s.expanded[v])continue;
     auto c=w.cost[w.node[v].cost];la::Entry next={v,cur.delay+c.delay,cur.congestion+c.congestion};
     if(!la::numeric(c.delay)||!la::numeric(c.congestion)||!la::numeric(next.delay)||!la::numeric(next.congestion)){failed=1;continue;}
     if(s.visited[v]>=0 && s.visited[v]<next.delay)continue;s.visited[v]=next.delay;pq.push(next);++st.pushes;st.peak=std::max<uint64_t>(st.peak,pq.size());
    }s.expanded[u]=1;++st.expanded;
   }stats[q]=st;
  }
  double elapsed=seconds(begin),service_time=repeat?elapsed:seconds(service);
  if(failed||std::memcmp(out.data(),w.golden.data(),out.size()*sizeof(la::Cost)))throw std::runtime_error("numeric or golden mismatch");
  std::cout<<"{\"backend\":\"cpu_std_priority_queue\",\"evidence_type\":\"measured\",\"scope\":\"resident_flood_batch\",\"phase\":\""<<(repeat?"warm":"cold_first_call")<<"\",\"repeat\":"<<repeat<<",\"workers\":"<<workers<<",\"prepare_s\":"<<(repeat?0:prepare)<<",\"resident_s\":"<<elapsed<<",\"service_to_result_s\":"<<service_time<<",\"all_golden_bits_match\":true}\n";
 }
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
