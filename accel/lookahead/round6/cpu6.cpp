#include "bucket6.hpp"
#include <omp.h>
#include <cfenv>
#include <iostream>
#include <iomanip>
using Clock=std::chrono::steady_clock;
double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
int main(int argc,char** argv){try{
 if(argc<7)throw std::runtime_error("cpu6 workload shift workers repeats output profile[0|1|2=witness] [edge_budget] [member_budget]");
 auto begin=Clock::now();std::fesetround(FE_TONEAREST);la::Workload w(argv[1]);double load=seconds(begin);unsigned shift=std::stoul(argv[2]),workers=std::stoul(argv[3]),repeats=std::stoul(argv[4]),profile=std::stoul(argv[6]);
 if((shift!=0&&shift!=20)||!workers||workers>16)throw std::runtime_error("invalid configuration");
 if(w.h.nodes*uint64_t(workers)*64>16ULL*1024*1024*1024)throw std::runtime_error("16GiB scratch admission exceeded");
 begin=Clock::now();la6::Prepared prep(w);std::vector<la6::Scratch> scratch;for(unsigned i=0;i<workers;++i)scratch.emplace_back(w.h.nodes);std::vector<la::Cost> out(w.golden.size()),previous;std::vector<la6::Profile> ps(w.h.jobs);double prepare=seconds(begin);
 std::cout<<std::setprecision(12);
 for(unsigned r=0;r<=repeats;++r){begin=Clock::now();int failed=0;
  #pragma omp parallel for schedule(dynamic) num_threads(workers) reduction(max:failed)
  for(size_t q=0;q<w.h.jobs;++q){try{auto& s=scratch[omp_get_thread_num()];ps[q]=profile?la6::search<true>(w,q,prep.targets[q],shift,s,out.data()+q*w.h.cells,profile==2,argc>7?std::stoull(argv[7]):500000000,argc>8?std::stoull(argv[8]):0):la6::search<false>(w,q,prep.targets[q],shift,s,out.data()+q*w.h.cells);failed=std::max(failed,int(ps[q].status));}catch(...){ps[q].status=la::INVALID_INPUT;failed=la::INVALID_INPUT;}}
  double elapsed=seconds(begin);uint64_t d=0,c=0,missing=0,coverage=0;for(size_t i=0;i<out.size();++i){d+=la6::bits(out[i].delay)!=la6::bits(w.golden[i].delay);c+=la6::bits(out[i].congestion)!=la6::bits(w.golden[i].congestion);missing+=std::isnan(out[i].delay)!=std::isnan(w.golden[i].delay);coverage+=!std::isnan(out[i].delay);}
  bool deterministic=previous.empty()||memcmp(previous.data(),out.data(),out.size()*8)==0;previous=out;
  std::cout<<"{\"kind\":\"batch\",\"mode\":\"ALT_BUCKET_FP32_V1\",\"shift\":"<<shift<<",\"workers\":"<<workers<<",\"repeat\":"<<r<<",\"E1_s\":"<<elapsed<<",\"load_s\":"<<load<<",\"prepare_s\":"<<prepare<<",\"status\":"<<failed<<",\"delay_diff\":"<<d<<",\"congestion_diff\":"<<c<<",\"missing_diff\":"<<missing<<",\"coverage\":"<<coverage<<",\"deterministic\":"<<(deterministic?"true":"false")<<"}\n";
  if(failed||!deterministic)return failed?failed:5;
 }
 std::ofstream f(argv[5],std::ios::binary);la::write(f,out.data(),out.size());
 if(profile)for(size_t q=0;q<ps.size();++q){auto& p=ps[q];
 std::cout<<"{\"kind\":\"profile\",\"qid\":"<<q<<",\"raw\":"<<p.raw<<",\"eligible\":"<<p.eligible<<",\"fp32_adds\":"<<2*p.eligible<<",\"updates\":"<<p.updates<<",\"processed\":"<<p.processed<<",\"repeat_nodes\":"<<p.repeat_nodes<<",\"stale\":"<<p.stale<<",\"migrations\":"<<p.migrations<<",\"dedup\":"<<p.dedup<<",\"directory_lookups\":"<<p.dir_lookup<<",\"min_select\":"<<p.min_select<<",\"closures\":"<<p.closures<<",\"pending_peak\":"<<p.pending_peak<<",\"bucket_peak\":"<<p.bucket_peak<<",\"targets\":"<<p.targets<<",\"recorded\":"<<p.recorded<<",\"waves\":[";
 for(size_t i=0;i<p.waves.size();++i){auto z=p.waves[i];if(i)std::cout<<',';std::cout<<'['<<z.bucket<<','<<z.width<<','<<z.raw<<','<<z.edges<<','<<z.distinct_dst<<','<<z.max_dst<<','<<z.bank_max<<']';}std::cout<<"],\"witness\":[";
 for(size_t i=0;i<p.witness.size();++i){auto z=p.witness[i];if(i)std::cout<<',';std::cout<<'['<<z.parent<<','<<z.dst<<','<<la6::bits(z.pair.delay)<<','<<la6::bits(z.pair.congestion)<<']';}std::cout<<"]}\n";
 }
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 10;}}
