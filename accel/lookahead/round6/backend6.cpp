#include "bucket6.hpp"
#include "backend.hpp"
#include <omp.h>
#include <cstdlib>
#include <cstdio>
#include <cfenv>
template<class T> struct Span {const T* p;size_t n;const T* begin()const{return p;}const T* end()const{return p+n;}const T& operator[](size_t i)const{return p[i];}};
struct View {la::Header h;Span<uint64_t> row;Span<la::Node> node;Span<la::Edge> edge;Span<la::Cost> cost;Span<la::Job> job;Span<int32_t> cell;};
extern "C" int la_backend_v1(const la::BackendInput* in,la::Cost* out,la::Stats* stats,la::BackendMetrics* metrics,char* error,uint32_t error_size){try{
 const char* mode=getenv("VPR_LA_MODE");if(!mode||std::string(mode)!="ALT_BUCKET_FP32_V1")throw std::runtime_error("explicit VPR_LA_MODE=ALT_BUCKET_FP32_V1 required");
 if(!in||in->version!=1||!in->contexts||in->contexts>16||!in->n)throw std::runtime_error("invalid ABI");
 unsigned shift=0;if(const char* s=getenv("VPR_LA_BUCKET_SHIFT"))shift=std::stoul(s);if(shift!=0&&shift!=20)throw std::runtime_error("invalid shift");
 auto start=std::chrono::steady_clock::now();auto seconds=[](std::chrono::steady_clock::time_point t){return std::chrono::duration<double>(std::chrono::steady_clock::now()-t).count();};
 const auto& a=*in;View w={{la::MAGIC,a.n,a.ne,a.nj,a.nk,a.nc,0},{a.row,a.n+1},{a.nodes,a.n},{a.edges,a.ne},{a.costs,a.nk},{a.jobs,a.nj},{a.cells,uint64_t(a.n)*a.nj}};
 if(w.row[0]!=0||w.row[a.n]!=a.ne)throw std::runtime_error("bad CSR");
 for(size_t u=0;u<a.n;++u)if(w.row[u]>w.row[u+1]||w.node[u].cost>=a.nk)throw std::runtime_error("bad node");
 for(auto e:w.edge)if(e.dst>=a.n)throw std::runtime_error("bad dst");for(auto j:w.job)if(j.source>=a.n)throw std::runtime_error("bad source");for(auto c:w.cell)if(c< -1||c>=int64_t(a.nc))throw std::runtime_error("bad cell");
 std::fesetround(FE_TONEAREST);la6::Prepared prep(w);std::vector<la6::Scratch> scratch;for(unsigned i=0;i<a.contexts;++i)scratch.emplace_back(a.n);*metrics={1,1,seconds(start),0,0,0,0};auto search_start=std::chrono::steady_clock::now();int failed=0;
 #pragma omp parallel for schedule(dynamic) num_threads(a.contexts) reduction(max:failed)
 for(size_t q=0;q<a.nj;++q){try{auto p=la6::search<false>(w,q,prep.targets[q],shift,scratch[omp_get_thread_num()],out+q*a.nc);stats[q]={p.updates,p.processed,p.raw,p.processed,p.pending_peak,p.status};failed=std::max(failed,int(p.status));}catch(...){stats[q].status=la::INVALID_INPUT;failed=la::INVALID_INPUT;}}
 metrics->resident_s=seconds(search_start);auto release=std::chrono::steady_clock::now();scratch.clear();metrics->release_s=seconds(release);metrics->service_s=seconds(start);if(failed)throw std::runtime_error("incomplete ALT sample");return 0;
}catch(const std::exception& e){if(error_size)snprintf(error,error_size,"%s",e.what());return 1;}}
