#include "bucket61.hpp"
#include <omp.h>
#include <iostream>
#include <fstream>
#include <iomanip>
int main(int argc,char**argv){try{
 if(argc!=4)return 2;la::Workload w(argv[1]);la61::Prepared p(w);unsigned threads=8;
 std::vector<la61::ScratchT<std::map<uint32_t,std::vector<uint32_t>>>> s;for(unsigned i=0;i<threads;++i)s.emplace_back(w.h.nodes);
 std::vector<la::Cost> out(w.h.jobs*w.h.cells);std::vector<uint32_t> status(w.h.jobs);std::vector<char>expected;
 std::ifstream gold(argv[2],std::ios::binary);expected.assign(std::istreambuf_iterator<char>(gold),{});if(expected.size()!=out.size()*8)throw std::runtime_error("reference size");
 std::cout<<std::setprecision(12);
 for(unsigned r=0;r<4;++r){auto start=std::chrono::steady_clock::now();
 #pragma omp parallel for schedule(dynamic) num_threads(8)
 for(unsigned q=0;q<w.h.jobs;++q)status[q]=la61::search<false>(w,q,p.targets[q],20,s[omp_get_thread_num()],out.data()+q*w.h.cells,false,500000000,524288).status;
 double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
 for(auto st:status)if(st)throw std::runtime_error("incomplete CPU job");if(memcmp(out.data(),expected.data(),expected.size()))throw std::runtime_error("full output difference");
 std::cout<<"{\"scope\":\"RESIDENT_COMPLETE_BATCH_V2\",\"backend\":\"original_ALT_CPU\",\"process\":\""<<argv[3]<<"\",\"rep\":"<<r<<",\"warmup\":"<<(r==0?"true":"false")<<",\"threads\":8,\"jobs\":"<<w.h.jobs<<",\"resident_s\":"<<elapsed<<",\"output_equal\":true,\"output_destination\":\"host_DRAM\"}\n"<<std::flush;
 }
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
