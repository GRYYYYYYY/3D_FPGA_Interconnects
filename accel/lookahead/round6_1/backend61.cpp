#include "bucket61.hpp"
#include "identity61.hpp"
#include "backend.hpp"
#include <omp.h>
#include <cstdlib>
#include <cstdio>
#include <cfenv>
extern "C" int la_backend_v1(const la::BackendInput* in,la::Cost* out,la::Stats* stats,la::BackendMetrics* metrics,char* error,uint32_t error_size){try{
 const char* mode=getenv("VPR_LA_MODE");if(!mode||std::string(mode)!="ALT_BUCKET_FP32_V1")throw std::runtime_error("explicit VPR_LA_MODE=ALT_BUCKET_FP32_V1 required");
 if(!in||in->version!=1||!in->contexts||in->contexts>16||!in->n)throw std::runtime_error("invalid ABI");
 unsigned shift=0;if(const char* s=getenv("VPR_LA_BUCKET_SHIFT"))shift=std::stoul(s);if(shift!=0&&shift!=20)throw std::runtime_error("invalid shift");
 auto start=std::chrono::steady_clock::now();auto seconds=[](std::chrono::steady_clock::time_point t){return std::chrono::duration<double>(std::chrono::steady_clock::now()-t).count();};
 const auto& a=*in;auto w=la61::view(a);
 if(w.row[0]!=0||w.row[a.n]!=a.ne)throw std::runtime_error("bad CSR");
 for(size_t u=0;u<a.n;++u)if(w.row[u]>w.row[u+1]||w.node[u].cost>=a.nk)throw std::runtime_error("bad node");
 for(auto e:w.edge)if(e.dst>=a.n)throw std::runtime_error("bad dst");for(auto j:w.job)if(j.source>=a.n)throw std::runtime_error("bad source");for(auto c:w.cell)if(c< -1||c>=int64_t(a.nc))throw std::runtime_error("bad cell");
 std::fesetround(FE_TONEAREST);la61::Prepared prep(w);std::vector<la61::ScratchT<std::map<uint32_t,std::vector<uint32_t>>>> scratch;for(unsigned i=0;i<a.contexts;++i)scratch.emplace_back(a.n);*metrics={1,1,seconds(start),0,0,0,0};auto search_start=std::chrono::steady_clock::now();int failed=0;
 #pragma omp parallel for schedule(dynamic) num_threads(a.contexts) reduction(max:failed)
 for(size_t q=0;q<a.nj;++q){try{auto p=la61::search<false>(w,q,prep.targets[q],shift,scratch[omp_get_thread_num()],out+q*a.nc);stats[q]={p.updates,p.processed,p.raw,p.processed,p.pending_peak,p.status};failed=std::max(failed,int(p.status));}catch(...){stats[q].status=la::INVALID_INPUT;failed=la::INVALID_INPUT;}}
 metrics->resident_s=seconds(search_start);double e1_wall=metrics->resident_s;auto release=std::chrono::steady_clock::now();scratch.clear();metrics->release_s=seconds(release);metrics->service_s=seconds(start);if(failed)throw std::runtime_error("incomplete ALT sample");fprintf(stdout,"R61_BACKEND backend=CPU shift=%u representation=original E1_wall_s=%.9f complete=1 fallback=0\n",shift,e1_wall);la61::capture(a,out,prep.targets,shift,"CPU");return 0;
}catch(const std::exception& e){if(error_size)snprintf(error,error_size,"%s",e.what());return 1;}}
