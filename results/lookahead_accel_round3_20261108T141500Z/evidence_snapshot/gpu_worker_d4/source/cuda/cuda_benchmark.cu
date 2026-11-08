// The round-one basic CUDA kernel is reused byte-for-byte.
#define main la_unused_cuda_cli_main
#include "lookahead_cuda.cu"
#undef main
#include <iomanip>
using Clock=std::chrono::steady_clock;
double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
int main(int argc,char** argv){try{
 if(argc!=4)throw std::runtime_error("usage: cuda_benchmark workload contexts warm_repeats");
 la::Workload w(argv[1]);unsigned B=std::stoul(argv[2]);int repeats=std::stoi(argv[3]);
 if(!B||B>w.h.jobs||w.h.edges>=UINT32_MAX||repeats<1)throw std::runtime_error("invalid configuration");
 auto service=Clock::now();CUDA(cudaFree(nullptr));unsigned cap=w.h.edges+1;
 auto row=upload(w.row);auto nodes=upload(w.node);auto edges=upload(w.edge);auto costs=upload(w.cost);auto jobs=upload(w.job);auto cells=upload(w.cell);
 auto visited=allocate<float>(B*w.h.nodes);auto expanded=allocate<uint32_t>(B*w.h.nodes);auto heap=allocate<la::Entry>(size_t(B)*cap);auto out=allocate<la::Cost>(w.golden.size());auto stats=allocate<la::Stats>(w.h.jobs);auto next=allocate<unsigned>(1);
 std::vector<la::Cost> result(w.golden.size());std::vector<la::Stats> host_stats(w.h.jobs);cudaEvent_t a,b;CUDA(cudaEventCreate(&a));CUDA(cudaEventCreate(&b));
 double prepare=seconds(service);std::cout<<std::setprecision(17);
 for(int repeat=0;repeat<=repeats;++repeat){
  auto begin=Clock::now();CUDA(cudaEventRecord(a));CUDA(cudaMemsetAsync(next,0,sizeof(unsigned)));
  batch<<<B,128>>>(row,nodes,edges,costs,jobs,cells,visited,expanded,heap,out,stats,next,w.h.nodes,w.h.jobs,w.h.cells,cap);
  CUDA(cudaGetLastError());CUDA(cudaEventRecord(b));CUDA(cudaEventSynchronize(b));float ms;CUDA(cudaEventElapsedTime(&ms,a,b));double complete=seconds(begin);
  auto readback=Clock::now();CUDA(cudaMemcpy(result.data(),out,result.size()*sizeof(la::Cost),cudaMemcpyDeviceToHost));CUDA(cudaMemcpy(host_stats.data(),stats,host_stats.size()*sizeof(la::Stats),cudaMemcpyDeviceToHost));
  double readback_time=seconds(readback),service_time=repeat?seconds(begin):seconds(service);
  for(auto s:host_stats)if(s.status)throw std::runtime_error("device sample failed");
  if(std::memcmp(result.data(),w.golden.data(),result.size()*sizeof(la::Cost)))throw std::runtime_error("golden mismatch");
  std::cout<<"{\"backend\":\"cuda_basic_CTA128\",\"evidence_type\":\"measured\",\"scope\":\"resident_flood_batch\",\"phase\":\""<<(repeat?"warm":"cold_first_call")<<"\",\"repeat\":"<<repeat<<",\"contexts\":"<<B<<",\"prepare_s\":"<<(repeat?0:prepare)<<",\"resident_s\":"<<double(ms)/1000<<",\"host_kernel_complete_s\":"<<complete<<",\"readback_s\":"<<readback_time<<",\"service_to_result_s\":"<<service_time<<",\"all_golden_bits_match\":true}\n";
 }
 CUDA(cudaEventDestroy(a));CUDA(cudaEventDestroy(b));
 for(void* p:std::vector<void*>{row,nodes,edges,costs,jobs,cells,visited,expanded,heap,out,stats,next})CUDA(cudaFree(p));
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
