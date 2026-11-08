#pragma once
#include "strict_heap.hpp"
#include <cuda_runtime.h>
template<bool EARLY> __global__ void batch4(const uint64_t* row,const la::Node* nodes,const la::Edge* edges,const la::Cost* costs,const la::Job* jobs,const int32_t* cells,float* v,uint32_t* ex,la::Entry* heaps,la::Cost* output,la::Stats* statistics,unsigned* next,const unsigned* targets,unsigned n,unsigned nj,unsigned nc,unsigned cap) {
 __shared__ unsigned q,count,active,stop,u,remaining;
 __shared__ la::Entry cur,candidate[128];__shared__ la::Node parent,children[128];__shared__ la::Stats st;__shared__ uint64_t begin,end;
 unsigned lane=threadIdx.x;v+=size_t(blockIdx.x)*n;ex+=size_t(blockIdx.x)*n;heaps+=size_t(blockIdx.x)*cap;
 while(true) {
  if(!lane) q=atomicAdd(next,1u);__syncthreads();if(q>=nj)return;
  for(unsigned i=lane;i<n;i+=blockDim.x){v[i]=-1;ex[i]=0;}
  for(unsigned i=lane;i<nc;i+=blockDim.x)output[size_t(q)*nc+i]={la::missing(),la::missing()};
  if(!lane){count=0;remaining=EARLY?targets[q]:0;st={0,0,0,0,0,la::OK};if(!EARLY||remaining){st.pushes=st.peak=1;la::push(heaps,count,{jobs[q].source,0,0});}}__syncthreads();
  while(true) {
   if(!lane){active=count!=0 && st.status==la::OK;if(active){cur=la::pop(heaps,count);++st.pops;u=cur.node;active=ex[u]?2:1;if(active==1){parent=nodes[u];begin=row[u];end=row[u+1];stop=0;int c=cells[size_t(q)*n+u];if(parent.type==1 && c>=0){auto& value=output[size_t(q)*nc+c];bool first=value.delay!=value.delay;la::record(value,cur);if(EARLY&&first&&--remaining==0)active=0;}}}}
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
