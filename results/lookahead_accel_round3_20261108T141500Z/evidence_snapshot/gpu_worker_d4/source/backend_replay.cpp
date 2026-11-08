#include "backend.hpp"
#include "io.hpp"
#include <dlfcn.h>
#include <iostream>
#include <cstring>
int main(int argc,char** argv) {
 try {
  if(argc!=4)throw std::runtime_error("usage: backend_replay workload library contexts");
  la::Workload w(argv[1]);void* lib=dlopen(argv[2],RTLD_NOW|RTLD_LOCAL|RTLD_NODELETE);
  if(!lib)throw std::runtime_error(dlerror());
  auto backend=reinterpret_cast<la::Backend>(dlsym(lib,"la_backend_v1"));
  if(!backend)throw std::runtime_error("missing backend symbol");
  la::BackendInput input={1,uint32_t(std::stoul(argv[3])),uint32_t(w.h.nodes),uint32_t(w.h.jobs),uint32_t(w.h.cells),uint32_t(w.h.costs),w.h.edges,w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),w.job.data(),w.cell.data()};
  std::vector<la::Cost> out(w.golden.size());std::vector<la::Stats> stats(w.h.jobs);
  la::BackendMetrics m={};char error[1024]={};
  if(backend(&input,out.data(),stats.data(),&m,error,sizeof(error)))throw std::runtime_error(error);
  if(m.version!=1 || (m.kind!=1 && m.kind!=2))throw std::runtime_error("invalid metrics");
  for(auto s:stats)if(s.status)throw std::runtime_error("sample failed");
  if(std::memcmp(out.data(),w.golden.data(),out.size()*sizeof(la::Cost)))throw std::runtime_error("golden mismatch");
  std::cout<<"{\"status\":\"passed\",\"kind\":"<<m.kind<<",\"prepare_s\":"<<m.prepare_s
   <<",\"resident_s\":"<<m.resident_s<<",\"readback_s\":"<<m.readback_s<<",\"release_s\":"<<m.release_s
   <<",\"service_s\":"<<m.service_s<<",\"matches_native_samples\":true,\"cold_service\":true}\n";
  dlclose(lib);return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
