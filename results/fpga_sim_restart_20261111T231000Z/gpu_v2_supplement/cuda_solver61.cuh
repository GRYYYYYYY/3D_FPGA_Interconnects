#pragma once
#include "bucket61.hpp"
#include "identity61.hpp"
#include <cuda_runtime.h>
#include <iostream>
#include <iomanip>
#include <fstream>
using U=unsigned long long;
const U INF=0x7f8000007f800000ULL;
#define CK(x) do{auto e=(x);if(e!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(e));}while(0)
struct Meta {unsigned current,next,done,target;};
__device__ U pairkey(float d,float c){return (U(__float_as_uint(d))<<32)|__float_as_uint(c);}
__global__ void initialize(U* label,U* prop,unsigned* pending,unsigned char* settled,U* out,Meta* m,const la::Job* jobs,const unsigned* targets,unsigned n,unsigned nc,unsigned nj){
 unsigned q=blockIdx.y;size_t u=size_t(blockIdx.x)*blockDim.x+threadIdx.x;size_t i=size_t(q)*n+u;
 if(u<n){label[i]=prop[i]=u==jobs[q].source?0:INF;pending[i]=u==jobs[q].source?0:~0u;settled[i]=0;}
 for(size_t c=u;c<nc;c+=size_t(gridDim.x)*blockDim.x)out[size_t(q)*nc+c]=INF;
 if(u==0)m[q]={0,~0u,unsigned(!targets[q]),targets[q]};
}
// Basic GPU control: dense pending directory, parallel frontier expansion.
// Directory scans and launch barriers are measured, not treated as free.
template<class N,class E> __global__ void expand(const uint64_t* row,const N* nodes,const E* edges,const la::Cost* costs,const U* label,U* prop,unsigned* pending,unsigned char* settled,const Meta* m,unsigned n,unsigned shift,unsigned* error){
 unsigned q=blockIdx.y,u=blockIdx.x*blockDim.x+threadIdx.x;size_t i=size_t(q)*n+u;if(u>=n||m[q].done||pending[i]!=m[q].current)return;
 pending[i]=~0u;settled[i]=1;U val=label[i];float d=__uint_as_float(unsigned(val>>32)),c=__uint_as_float(unsigned(val));
 for(uint64_t k=row[u];k<row[u+1];++k){unsigned v=la61::destination(edges[k]);int a=la::eligible(la61::decode(nodes[u]),la61::decode(nodes[v]));if(!a)continue;if(a<0)break;auto cost=costs[la61::decode(nodes[v]).cost];float nd=__fadd_rn(d,cost.delay),nc=__fadd_rn(c,cost.congestion);if(!la::numeric(nd)||!la::numeric(nc)){atomicExch(error,3u);continue;}atomicMin(prop+size_t(q)*n+v,pairkey(nd,nc));}
}
__global__ void commit(U* label,const U* prop,unsigned* pending,Meta* m,unsigned n,unsigned shift){
 unsigned q=blockIdx.y,u=blockIdx.x*blockDim.x+threadIdx.x;size_t i=size_t(q)*n+u;if(m[q].done)return;
 if(u<n&&prop[i]<label[i]){label[i]=prop[i];pending[i]=unsigned(prop[i]>>32)>>shift;}
 // One atomic per CTA after reduction; avoid N contending atomics.
 __shared__ unsigned keys[256];keys[threadIdx.x]=u<n?pending[i]:~0u;__syncthreads();
 for(unsigned s=128;s;s>>=1){if(threadIdx.x<s)keys[threadIdx.x]=min(keys[threadIdx.x],keys[threadIdx.x+s]);__syncthreads();}
 if(threadIdx.x==0)atomicMin(&m[q].next,keys[0]);
}
template<class N> __global__ void confirm(const N* nodes,const int* cells,const U* label,unsigned char* settled,U* out,const Meta* m,unsigned n,unsigned nc){
 unsigned q=blockIdx.y,u=blockIdx.x*blockDim.x+threadIdx.x;if(u>=n||m[q].done||m[q].current==m[q].next)return;size_t i=size_t(q)*n+u;
 if(settled[i]){settled[i]=0;int c=cells[i];if(c>=0&&la61::decode(nodes[u]).type==1)atomicMin(out+size_t(q)*nc+c,label[i]);}
}
__global__ void advance(Meta* m,const U* out,unsigned nc,unsigned nj,unsigned* done){unsigned q=blockIdx.x*blockDim.x+threadIdx.x;if(q>=nj)return;if(!m[q].done&&m[q].next!=m[q].current){unsigned count=0;for(unsigned c=0;c<nc;++c)count+=out[size_t(q)*nc+c]!=INF;if(count==m[q].target||m[q].next==~0u)m[q].done=1;}m[q].current=m[q].next;m[q].next=~0u;if(m[q].done)atomicAdd(done,1u);}
template<class T>T* alloc(size_t n){T* p=nullptr;if(n)CK(cudaMalloc(&p,n*sizeof(T)));return p;}
template<class T>T* upload(const std::vector<T>& v){T* p=alloc<T>(v.size());if(v.size())CK(cudaMemcpy(p,v.data(),v.size()*sizeof(T),cudaMemcpyHostToDevice));return p;}
using Clock=std::chrono::steady_clock;double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
#include <functional>
#include <map>
struct Phase {
 bool enabled;std::map<std::string,double> times;
 explicit Phase(bool e):enabled(e){}
 template<class F>void kernel(const char* name,F fn){if(!enabled){fn();return;}cudaEvent_t a,b;CK(cudaEventCreate(&a));CK(cudaEventCreate(&b));CK(cudaEventRecord(a));fn();CK(cudaEventRecord(b));CK(cudaEventSynchronize(b));float ms;CK(cudaEventElapsedTime(&ms,a,b));times[name]+=ms/1000.;CK(cudaEventDestroy(a));CK(cudaEventDestroy(b));}
};
template<class N,class E>struct CudaSession61 {
 const la::BackendInput& in;unsigned shift;size_t n,j,nc,total,bytes;double prepare_s,conversion_s=0,E1_wall_s,resident_s,readback_s;unsigned waves;
 uint64_t* row=nullptr;N* nodes=nullptr;E* edges=nullptr;la::Cost* costs=nullptr;la::Job* jobs=nullptr;int* cells=nullptr;unsigned* targets=nullptr;U *label=nullptr,*prop=nullptr,*output=nullptr;unsigned *pending=nullptr,*done=nullptr,*error=nullptr;unsigned char* settled=nullptr;Meta* meta=nullptr;
 std::vector<uint32_t> target_host;std::vector<U> packed;Phase phase;
 template<class T>T* copy(const T* p,size_t count){T* d=alloc<T>(count);if(count)CK(cudaMemcpy(d,p,count*sizeof(T),cudaMemcpyHostToDevice));return d;}
 CudaSession61(const la::BackendInput& a,unsigned s,const N* ns,const E* es,bool profile=false):in(a),shift(s),n(a.n),j(a.nj),nc(a.nc),total(n*j),packed(j*nc),phase(profile){
  auto begin=Clock::now();if(shift!=0&&shift!=20)throw std::runtime_error("bad shift");la61::Prepared p(la61::view(a));target_host=p.targets;
  bytes=21*total+8*j*nc+(n+1)*8+n*sizeof(N)+a.ne*sizeof(E)+total*4+a.nk*8+j*(24+4+sizeof(Meta))+8;size_t free,tm;CK(cudaMemGetInfo(&free,&tm));if(bytes>free*8/10)throw std::runtime_error("device capacity admission");
  try{row=copy(a.row,n+1);nodes=copy(ns,n);edges=copy(es,a.ne);costs=copy(a.costs,a.nk);jobs=copy(a.jobs,j);cells=copy(a.cells,total);targets=copy(target_host.data(),j);label=alloc<U>(total);prop=alloc<U>(total);output=alloc<U>(j*nc);pending=alloc<unsigned>(total);settled=alloc<unsigned char>(total);meta=alloc<Meta>(j);done=alloc<unsigned>(1);error=alloc<unsigned>(1);CK(cudaDeviceSynchronize());prepare_s=seconds(begin);}catch(...){release();throw;}
 }
 void release(){for(void* p:{(void*)row,(void*)nodes,(void*)edges,(void*)costs,(void*)jobs,(void*)cells,(void*)targets,(void*)label,(void*)prop,(void*)output,(void*)pending,(void*)settled,(void*)meta,(void*)done,(void*)error})if(p)cudaFree(p);row=nullptr;nodes=nullptr;edges=nullptr;costs=nullptr;jobs=nullptr;cells=nullptr;targets=nullptr;label=prop=output=nullptr;pending=done=error=nullptr;settled=nullptr;meta=nullptr;}
 ~CudaSession61(){release();}
 std::vector<la::Cost> solve(){std::vector<la::Cost> out(j*nc);auto start=Clock::now();dim3 grid((n+255)/256,j);unsigned completed=0,err=0;waves=0;phase.times.clear();
  phase.kernel("initialize",[&]{CK(cudaMemset(error,0,4));if(j)initialize<<<grid,256>>>(label,prop,pending,settled,output,meta,jobs,targets,n,nc,j);});
  while(completed<j){if(++waves>100000||seconds(start)>180)throw std::runtime_error("CUDA incomplete budget");
   phase.kernel("expand",[&]{expand<<<grid,256>>>(row,nodes,edges,costs,label,prop,pending,settled,meta,n,shift,error);});
   phase.kernel("commit_min_scan",[&]{commit<<<grid,256>>>(label,prop,pending,meta,n,shift);});
   phase.kernel("confirm",[&]{confirm<<<grid,256>>>(nodes,cells,label,settled,output,meta,n,nc);});
   phase.kernel("advance",[&]{CK(cudaMemset(done,0,4));advance<<<(j+127)/128,128>>>(meta,output,nc,j,done);});
   auto wait=Clock::now();CK(cudaMemcpy(&completed,done,4,cudaMemcpyDeviceToHost));if(phase.enabled)phase.times["host_completion_copy_wait"]+=seconds(wait);
  }
  CK(cudaDeviceSynchronize());resident_s=seconds(start);auto read=Clock::now();CK(cudaMemcpy(&err,error,4,cudaMemcpyDeviceToHost));if(err)throw std::runtime_error("CUDA unsupported numeric");if(!packed.empty())CK(cudaMemcpy(packed.data(),output,packed.size()*8,cudaMemcpyDeviceToHost));
  for(size_t i=0;i<out.size();++i){if(packed[i]==INF)out[i]={la::missing(),la::missing()};else{unsigned d=packed[i]>>32,c=packed[i];std::memcpy(&out[i].delay,&d,4);std::memcpy(&out[i].congestion,&c,4);}}
  CK(cudaDeviceSynchronize());readback_s=seconds(read);E1_wall_s=seconds(start);if(phase.enabled)phase.times["final_D2H_unpack"]=readback_s;return out;
 }
};
