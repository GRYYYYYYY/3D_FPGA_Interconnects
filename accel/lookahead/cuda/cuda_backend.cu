// Reuse the exact first-round CUDA baseline kernel, without its file/CLI path.
#define main la_unused_cuda_cli_main
#include "lookahead_cuda.cu"
#undef main
#include "backend.hpp"
#include <cstdio>
namespace {
using Clock=std::chrono::steady_clock;
double elapsed(Clock::time_point a){return std::chrono::duration<double>(Clock::now()-a).count();}
struct Pool {
 std::vector<void*> memory;
 template<class T>T* get(size_t count,const T* input=nullptr){
  T* p=allocate<T>(count);memory.push_back(p);
  if(input && count)CUDA(cudaMemcpy(p,input,count*sizeof(T),cudaMemcpyHostToDevice));return p;
 }
 void release(){for(auto p:memory)cudaFree(p);memory.clear();}
 ~Pool(){release();}
};
}
extern "C" int la_backend_v1(const la::BackendInput* in,la::Cost* result,la::Stats* host_stats,
 la::BackendMetrics* metrics,char* error,uint32_t error_size) {
 cudaEvent_t start_event=nullptr,end_event=nullptr;
 try {
  if(!in || in->version!=1 || !in->contexts || in->contexts>in->nj || in->ne>=UINT32_MAX)
   throw std::runtime_error("invalid CUDA backend input");
  const auto& w=*in;auto service=Clock::now();*metrics={1,2,0,0,0,0,0};Pool p;
  CUDA(cudaFree(nullptr));unsigned cap=w.ne+1;
  auto row=p.get<uint64_t>(w.n+1,w.row);auto nodes=p.get<la::Node>(w.n,w.nodes);
  auto edges=p.get<la::Edge>(w.ne,w.edges);auto costs=p.get<la::Cost>(w.nk,w.costs);
  auto jobs=p.get<la::Job>(w.nj,w.jobs);auto cells=p.get<int32_t>(uint64_t(w.nj)*w.n,w.cells);
  auto visited=p.get<float>(uint64_t(w.contexts)*w.n);auto expanded=p.get<uint32_t>(uint64_t(w.contexts)*w.n);
  auto heap=p.get<la::Entry>(uint64_t(w.contexts)*cap);auto out=p.get<la::Cost>(uint64_t(w.nj)*w.nc);
  auto stats=p.get<la::Stats>(w.nj);auto next=p.get<unsigned>(1);
  CUDA(cudaEventCreate(&start_event));CUDA(cudaEventCreate(&end_event));metrics->prepare_s=elapsed(service);
  CUDA(cudaEventRecord(start_event));CUDA(cudaMemsetAsync(next,0,sizeof(unsigned)));
  batch<<<w.contexts,128>>>(row,nodes,edges,costs,jobs,cells,visited,expanded,heap,out,stats,next,w.n,w.nj,w.nc,cap);
  CUDA(cudaGetLastError());CUDA(cudaEventRecord(end_event));CUDA(cudaEventSynchronize(end_event));
  float ms;CUDA(cudaEventElapsedTime(&ms,start_event,end_event));metrics->resident_s=ms/1000.;
  auto start=Clock::now();
  CUDA(cudaMemcpy(result,out,uint64_t(w.nj)*w.nc*sizeof(la::Cost),cudaMemcpyDeviceToHost));
  CUDA(cudaMemcpy(host_stats,stats,w.nj*sizeof(la::Stats),cudaMemcpyDeviceToHost));metrics->readback_s=elapsed(start);
  for(uint32_t q=0;q<w.nj;++q)if(host_stats[q].status)throw std::runtime_error("CUDA sample failed");
  start=Clock::now();p.release();CUDA(cudaEventDestroy(start_event));start_event=nullptr;
  CUDA(cudaEventDestroy(end_event));end_event=nullptr;metrics->release_s=elapsed(start);
  metrics->service_s=elapsed(service);return 0;
 }catch(const std::exception& e){if(start_event)cudaEventDestroy(start_event);if(end_event)cudaEventDestroy(end_event);
  if(error_size)std::snprintf(error,error_size,"%s",e.what());return 1;}
}
