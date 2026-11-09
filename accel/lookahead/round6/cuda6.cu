#include "bucket6.hpp"
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
__global__ void expand(const uint64_t* row,const la::Node* nodes,const la::Edge* edges,const la::Cost* costs,const U* label,U* prop,unsigned* pending,unsigned char* settled,const Meta* m,unsigned n,unsigned shift,unsigned* error){
 unsigned q=blockIdx.y,u=blockIdx.x*blockDim.x+threadIdx.x;size_t i=size_t(q)*n+u;if(u>=n||m[q].done||pending[i]!=m[q].current)return;
 pending[i]=~0u;settled[i]=1;U val=label[i];float d=__uint_as_float(unsigned(val>>32)),c=__uint_as_float(unsigned(val));
 for(uint64_t k=row[u];k<row[u+1];++k){unsigned v=edges[k].dst;int a=la::eligible(nodes[u],nodes[v]);if(!a)continue;if(a<0)break;auto cost=costs[nodes[v].cost];float nd=__fadd_rn(d,cost.delay),nc=__fadd_rn(c,cost.congestion);if(!la::numeric(nd)||!la::numeric(nc)){atomicExch(error,3u);continue;}atomicMin(prop+size_t(q)*n+v,pairkey(nd,nc));}
}
__global__ void commit(U* label,const U* prop,unsigned* pending,Meta* m,unsigned n,unsigned shift){
 unsigned q=blockIdx.y,u=blockIdx.x*blockDim.x+threadIdx.x;size_t i=size_t(q)*n+u;if(m[q].done)return;
 if(u<n&&prop[i]<label[i]){label[i]=prop[i];pending[i]=unsigned(prop[i]>>32)>>shift;}
 // One atomic per CTA after reduction; avoid N contending atomics.
 __shared__ unsigned keys[256];keys[threadIdx.x]=u<n?pending[i]:~0u;__syncthreads();
 for(unsigned s=128;s;s>>=1){if(threadIdx.x<s)keys[threadIdx.x]=min(keys[threadIdx.x],keys[threadIdx.x+s]);__syncthreads();}
 if(threadIdx.x==0)atomicMin(&m[q].next,keys[0]);
}
__global__ void confirm(const la::Node* nodes,const int* cells,const U* label,unsigned char* settled,U* out,const Meta* m,unsigned n,unsigned nc){
 unsigned q=blockIdx.y,u=blockIdx.x*blockDim.x+threadIdx.x;if(u>=n||m[q].done||m[q].current==m[q].next)return;size_t i=size_t(q)*n+u;
 if(settled[i]){settled[i]=0;int c=cells[i];if(c>=0&&nodes[u].type==1)atomicMin(out+size_t(q)*nc+c,label[i]);}
}
__global__ void advance(Meta* m,const U* out,unsigned nc,unsigned nj,unsigned* done){unsigned q=blockIdx.x*blockDim.x+threadIdx.x;if(q>=nj)return;if(!m[q].done&&m[q].next!=m[q].current){unsigned count=0;for(unsigned c=0;c<nc;++c)count+=out[size_t(q)*nc+c]!=INF;if(count==m[q].target||m[q].next==~0u)m[q].done=1;}m[q].current=m[q].next;m[q].next=~0u;if(m[q].done)atomicAdd(done,1u);}
template<class T>T* alloc(size_t n){T* p=nullptr;if(n)CK(cudaMalloc(&p,n*sizeof(T)));return p;}
template<class T>T* upload(const std::vector<T>& v){T* p=alloc<T>(v.size());if(v.size())CK(cudaMemcpy(p,v.data(),v.size()*sizeof(T),cudaMemcpyHostToDevice));return p;}
using Clock=std::chrono::steady_clock;double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
int main(int argc,char** argv){try{
 if(argc!=6)throw std::runtime_error("cuda6 workload shift warm_repeats cpp_reference output");auto start=Clock::now();la::Workload w(argv[1]);unsigned shift=std::stoul(argv[2]),repeats=std::stoul(argv[3]);if(shift!=0&&shift!=20)throw std::runtime_error("invalid shift");double load=seconds(start);start=Clock::now();la6::Prepared prep(w);
 size_t n=w.h.nodes,j=w.h.jobs,nc=w.h.cells,total=n*j;size_t bytes=21*total+8*j*nc+w.row.size()*8+w.node.size()*16+w.edge.size()*8+w.cell.size()*4;size_t free,totalmem;CK(cudaMemGetInfo(&free,&totalmem));if(bytes>free*8/10)throw std::runtime_error("device capacity admission");
 auto row=upload(w.row);auto nodes=upload(w.node);auto edges=upload(w.edge);auto costs=upload(w.cost);auto jobs=upload(w.job);auto cells=upload(w.cell);auto targets=upload(prep.targets);
 auto label=alloc<U>(total),prop=alloc<U>(total),output=alloc<U>(j*nc);auto pending=alloc<unsigned>(total);auto settled=alloc<unsigned char>(total);auto meta=alloc<Meta>(j);auto done=alloc<unsigned>(1),error=alloc<unsigned>(1);CK(cudaDeviceSynchronize());double prepare=seconds(start);
 std::vector<la::Cost> reference(j*nc),out(j*nc);std::ifstream rf(argv[4],std::ios::binary);la::read(rf,reference.data(),reference.size());std::vector<U> packed(j*nc);dim3 grid((n+255)/256,j);std::cout<<std::setprecision(12);
 cudaEvent_t a,b;CK(cudaEventCreate(&a));CK(cudaEventCreate(&b));
 for(unsigned r=0;r<=repeats;++r){start=Clock::now();CK(cudaEventRecord(a));unsigned completed=0,err=0,waves=0;CK(cudaMemset(error,0,4));
 if(j)initialize<<<grid,256>>>(label,prop,pending,settled,output,meta,jobs,targets,n,nc,j);
 while(completed<j){if(++waves>100000||seconds(start)>180)throw std::runtime_error("incomplete CUDA budget exceeded");
  expand<<<grid,256>>>(row,nodes,edges,costs,label,prop,pending,settled,meta,n,shift,error);
  commit<<<grid,256>>>(label,prop,pending,meta,n,shift);
  confirm<<<grid,256>>>(nodes,cells,label,settled,output,meta,n,nc);
  CK(cudaMemset(done,0,4));advance<<<(j+127)/128,128>>>(meta,output,nc,j,done);CK(cudaMemcpy(&completed,done,4,cudaMemcpyDeviceToHost));
 }
 CK(cudaMemcpy(&err,error,4,cudaMemcpyDeviceToHost));CK(cudaMemcpy(packed.data(),output,packed.size()*8,cudaMemcpyDeviceToHost));CK(cudaEventRecord(b));CK(cudaEventSynchronize(b));float event_ms;CK(cudaEventElapsedTime(&event_ms,a,b));
 for(size_t i=0;i<out.size();++i){if(packed[i]==INF)out[i]={la::missing(),la::missing()};else{unsigned d=packed[i]>>32,c=packed[i];std::memcpy(&out[i].delay,&d,4);std::memcpy(&out[i].congestion,&c,4);}}
 double elapsed=seconds(start);bool equal=!memcmp(out.data(),reference.data(),out.size()*8);
 std::cout<<"{\"kind\":\"batch\",\"backend\":\"cuda6\",\"shift\":"<<shift<<",\"repeat\":"<<r<<",\"E1_s\":"<<elapsed<<",\"device_timeline_including_host_gaps_s\":"<<event_ms/1000<<",\"load_s\":"<<load<<",\"prepare_s\":"<<prepare<<",\"waves_batch\":"<<waves<<",\"scratch_and_input_bytes\":"<<bytes<<",\"cpp_match\":"<<(equal?"true":"false")<<",\"status\":"<<err<<"}\n"<<std::flush;
 if(err||!equal)return 3;
 }
 std::ofstream f(argv[5],std::ios::binary);la::write(f,out.data(),out.size());
 // Fresh-process allocation ownership; all CUDA allocations released before exit.
 for(void* p:{(void*)row,(void*)nodes,(void*)edges,(void*)costs,(void*)jobs,(void*)cells,(void*)targets,(void*)label,(void*)prop,(void*)output,(void*)pending,(void*)settled,(void*)meta,(void*)done,(void*)error})if(p)CK(cudaFree(p));CK(cudaEventDestroy(a));CK(cudaEventDestroy(b));
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 10;}}
