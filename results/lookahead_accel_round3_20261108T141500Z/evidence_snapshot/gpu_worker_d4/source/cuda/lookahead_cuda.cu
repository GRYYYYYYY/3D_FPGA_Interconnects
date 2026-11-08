#include "io.hpp"
#include "strict_heap.hpp"
#include <cuda_runtime.h>
#include <iostream>
#include <chrono>
#include <cstring>
#define CUDA(c) do {cudaError_t e=(c);if(e!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(e));}while(0)
// One persistent CTA owns one private workspace; lanes calculate ordered edge tiles.
__global__ void batch(const uint64_t* row,const la::Node* nodes,const la::Edge* edges,const la::Cost* costs,const la::Job* jobs,const int32_t* cells,float* v,uint32_t* ex,la::Entry* heaps,la::Cost* output,la::Stats* statistics,unsigned* next,unsigned n,unsigned nj,unsigned nc,unsigned cap) {
 __shared__ unsigned q,count,active,stop,u;
 __shared__ la::Entry cur,candidate[128];__shared__ la::Node parent,children[128];__shared__ la::Stats st;__shared__ uint64_t begin,end;
 unsigned lane=threadIdx.x;v+=size_t(blockIdx.x)*n;ex+=size_t(blockIdx.x)*n;heaps+=size_t(blockIdx.x)*cap;
 while(true) {
  if(!lane) q=atomicAdd(next,1u);__syncthreads();if(q>=nj)return;
  for(unsigned i=lane;i<n;i+=blockDim.x){v[i]=-1;ex[i]=0;}
  for(unsigned i=lane;i<nc;i+=blockDim.x)output[size_t(q)*nc+i]={la::missing(),la::missing()};
  if(!lane){count=0;st={1,0,0,0,1,la::OK};la::push(heaps,count,{jobs[q].source,0,0});}__syncthreads();
  while(true) {
   if(!lane){active=count!=0 && st.status==la::OK;if(active){cur=la::pop(heaps,count);++st.pops;u=cur.node;active=ex[u]?2:1;if(active==1){parent=nodes[u];begin=row[u];end=row[u+1];stop=0;int c=cells[size_t(q)*n+u];if(parent.type==1 && c>=0)la::record(output[size_t(q)*nc+c],cur);}}}
   __syncthreads();if(!active)break;if(active==2)continue;
   for(uint64_t base=begin;base<end;base+=blockDim.x) {
    uint64_t i=base+lane;
    if(i<end){unsigned dst=edges[i].dst;children[lane]=nodes[dst];la::Cost c=costs[children[lane].cost];candidate[lane]={dst,__fadd_rn(cur.delay,c.delay),__fadd_rn(cur.congestion,c.congestion)};}
    __syncthreads();
    if(!lane)for(unsigned k=0;k<blockDim.x && base+k<end;++k) {
     ++st.edges;auto child=children[k];auto b=candidate[k];int e=la::eligible(parent,child);if(!e)continue;if(e<0){stop=1;break;}if(ex[b.node])continue;
     auto c=costs[child.cost];if(!la::numeric(c.delay)||!la::numeric(c.congestion)||!la::numeric(b.delay)||!la::numeric(b.congestion)){st.status=la::UNSUPPORTED_NUMERIC;stop=1;break;}
     if(v[b.node]>=0 && v[b.node]<b.delay)continue;if(count==cap){st.status=la::QUEUE_OVERFLOW;stop=1;break;}v[b.node]=b.delay;la::push(heaps,count,b);++st.pushes;if(count>st.peak)st.peak=count;
    }
    __syncthreads();if(stop)break;
   }
   if(!lane && st.status==la::OK){ex[u]=1;++st.expanded;}__syncthreads();
  }
  if(!lane)statistics[q]=st;__syncthreads();
 }
}
template<class T>T* upload(const std::vector<T>& v){T* p=nullptr;CUDA(cudaMalloc(&p,std::max<size_t>(1,v.size())*sizeof(T)));if(!v.empty())CUDA(cudaMemcpy(p,v.data(),v.size()*sizeof(T),cudaMemcpyHostToDevice));return p;}
template<class T>T* allocate(size_t n){T* p=nullptr;CUDA(cudaMalloc(&p,std::max<size_t>(n,1)*sizeof(T)));return p;}
int main(int argc,char** argv) {
 try {
  if(argc!=4)throw std::runtime_error("usage: lookahead_cuda workload.bin output.bin contexts");if(std::ifstream(argv[2]).good())throw std::runtime_error("output exists");
  la::Workload w(argv[1]);unsigned B=std::stoul(argv[3]);if(!B||(w.h.jobs?B>w.h.jobs:B!=1)||w.h.edges>=UINT32_MAX)throw std::runtime_error("invalid contexts or queue capacity");unsigned cap=w.h.edges+1;
  cudaDeviceProp prop;CUDA(cudaGetDeviceProperties(&prop,0));CUDA(cudaFree(nullptr));
  auto row=upload(w.row);auto nodes=upload(w.node);auto edges=upload(w.edge);auto costs=upload(w.cost);auto jobs=upload(w.job);auto cells=upload(w.cell);
  auto visited=allocate<float>(B*w.h.nodes);auto expanded=allocate<uint32_t>(B*w.h.nodes);auto heaps=allocate<la::Entry>(size_t(B)*cap);auto out=allocate<la::Cost>(w.golden.size());auto stats=allocate<la::Stats>(w.h.jobs);auto next=allocate<unsigned>(1);
  cudaEvent_t a,b;CUDA(cudaEventCreate(&a));CUDA(cudaEventCreate(&b));std::vector<la::Cost> result(w.golden.size());std::vector<la::Stats> host_stats(w.h.jobs);
  for(int repeat=-1;repeat<3;++repeat) {
   auto host=std::chrono::steady_clock::now();CUDA(cudaEventRecord(a));CUDA(cudaMemsetAsync(next,0,sizeof(unsigned)));
   batch<<<B,128>>>(row,nodes,edges,costs,jobs,cells,visited,expanded,heaps,out,stats,next,w.h.nodes,w.h.jobs,w.h.cells,cap);CUDA(cudaGetLastError());CUDA(cudaEventRecord(b));CUDA(cudaEventSynchronize(b));float ms;CUDA(cudaEventElapsedTime(&ms,a,b));
   CUDA(cudaMemcpy(result.data(),out,result.size()*sizeof(la::Cost),cudaMemcpyDeviceToHost));CUDA(cudaMemcpy(host_stats.data(),stats,host_stats.size()*sizeof(la::Stats),cudaMemcpyDeviceToHost));
   double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-host).count();for(auto s:host_stats)if(s.status)throw std::runtime_error("device sample failed");if(std::memcmp(result.data(),w.golden.data(),result.size()*sizeof(la::Cost)))throw std::runtime_error("golden mismatch");
   if(repeat>=0)std::cout<<"{\"evidence_type\":\"gpu_measured\",\"semantic_mode\":\"STRICT_FP32\",\"timing_scope\":\"resident_flood_batch\",\"repeat\":"<<repeat<<",\"gpu_model\":\""<<prop.name<<"\",\"contexts\":"<<B<<",\"resident_elapsed_s\":"<<ms/1000<<",\"host_service_elapsed_s\":"<<wall<<",\"d2h_bytes\":"<<result.size()*sizeof(la::Cost)+host_stats.size()*sizeof(la::Stats)<<",\"matches_reference\":true}\n";
  }
  std::ofstream f(argv[2],std::ios::binary);la::write(f,result.data(),result.size());
  CUDA(cudaEventDestroy(a));CUDA(cudaEventDestroy(b));CUDA(cudaFree(row));CUDA(cudaFree(nodes));CUDA(cudaFree(edges));CUDA(cudaFree(costs));CUDA(cudaFree(jobs));CUDA(cudaFree(cells));CUDA(cudaFree(visited));CUDA(cudaFree(expanded));CUDA(cudaFree(heaps));CUDA(cudaFree(out));CUDA(cudaFree(stats));CUDA(cudaFree(next));
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
