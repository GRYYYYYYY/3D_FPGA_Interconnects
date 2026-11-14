#include "bucket61.hpp"
#include <cuda_runtime.h>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <chrono>
using U=unsigned long long;
constexpr U INF=0x7f8000007f800000ULL,MISSING=0x7fc000007fc00000ULL;
#define CK(x) do{auto e=(x);if(e!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(e));}while(0)
struct Meta{unsigned current,next,done,target,recorded;};
struct BasicEdge{unsigned dst,cost;};
__device__ unsigned dst(BasicEdge e){return e.dst;}
__device__ unsigned ci(BasicEdge e){return e.cost;}
__device__ unsigned dst(unsigned e){return e&0xfffffff;}
__device__ unsigned ci(unsigned e){return e>>28;}
__global__ void initialize(U*label,U*prop,unsigned*pending,U*out,Meta*m,const la::Job*job,const unsigned*targets,unsigned n,unsigned nc){
 unsigned q=blockIdx.y,u=blockIdx.x*blockDim.x+threadIdx.x;size_t i=size_t(q)*n+u;
 if(u<n){label[i]=u==job[q].source?0:INF;prop[i]=INF;pending[i]=u==job[q].source?0:~0u;}
 for(unsigned c=u;c<nc;c+=gridDim.x*blockDim.x)out[size_t(q)*nc+c]=INF;
 if(!u)m[q]={0,~0u,unsigned(!targets[q]),targets[q],0};
}
// Exact valid-POP snapshot. Includes degree-zero targets; closure is decided
// only after proposal commit and minimum selection, never at first discovery.
template<class E> __global__ void expand(const uint64_t*row,const E*edge,const unsigned char*target_node,const int*cell,const la::Cost*cost,const U*label,U*prop,unsigned*pending,U*out,Meta*m,unsigned n,unsigned nc,unsigned*error){
 unsigned q=blockIdx.y,u=blockIdx.x*blockDim.x+threadIdx.x;size_t i=size_t(q)*n+u;
 if(u>=n||m[q].done||pending[i]!=m[q].current)return;
 pending[i]=~0u;U pair=label[i];int c=cell[i];
 if(target_node[u]&&c>=0){U old=atomicMin(out+size_t(q)*nc+c,pair);if(old==INF)atomicAdd(&m[q].recorded,1u);}
 float pd=__uint_as_float(unsigned(pair>>32)),pc=__uint_as_float(unsigned(pair));
 for(uint64_t k=row[u];k<row[u+1];++k){auto e=edge[k];auto w=cost[ci(e)];float d=__fadd_rn(pd,w.delay),c=__fadd_rn(pc,w.congestion);
  if(!la::numeric(d)||!la::numeric(c)){atomicExch(error,3u);continue;}
  U candidate=U(__float_as_uint(d))<<32|__float_as_uint(c);atomicMin(prop+size_t(q)*n+dst(e),candidate);
 }
}
__global__ void commit(U*label,U*prop,unsigned*pending,Meta*m,unsigned n,unsigned*error){
 unsigned q=blockIdx.y,u=blockIdx.x*blockDim.x+threadIdx.x;size_t i=size_t(q)*n+u;if(m[q].done)return;
 if(u<n&&prop[i]<label[i]){label[i]=prop[i];unsigned key=unsigned(prop[i]>>52);if(key<m[q].current)atomicExch(error,4u);pending[i]=key;}
 if(u<n)prop[i]=INF; // wave-private proposal; next expand sees only INF
 __shared__ unsigned key[256];key[threadIdx.x]=u<n?pending[i]:~0u;__syncthreads();
 for(unsigned step=128;step;step>>=1){if(threadIdx.x<step)key[threadIdx.x]=min(key[threadIdx.x],key[threadIdx.x+step]);__syncthreads();}
 if(!threadIdx.x)atomicMin(&m[q].next,key[0]);
}
__global__ void advance(Meta*m,unsigned jobs,unsigned*done,unsigned*error){
 unsigned q=blockIdx.x*blockDim.x+threadIdx.x;if(q>=jobs)return;
 if(m[q].recorded>m[q].target)atomicExch(error,5u);
 if(!m[q].done&&m[q].current!=m[q].next&&(m[q].recorded==m[q].target||m[q].next==~0u))m[q].done=1;
 m[q].current=m[q].next;m[q].next=~0u;if(m[q].done)atomicAdd(done,1u);
}
template<class T>T* alloc(size_t n){T*p=nullptr;if(n)CK(cudaMalloc(&p,n*sizeof(T)));return p;}
template<class T>T* copy(const T*p,size_t n){T*d=alloc<T>(n);if(n)CK(cudaMemcpy(d,p,n*sizeof(T),cudaMemcpyHostToDevice));return d;}
using Clock=std::chrono::steady_clock;
double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
template<class E>int run(const la::Workload&w,const std::vector<uint64_t>&row,const std::vector<E>&edge,const std::vector<unsigned>&targets,const char*refpath,const char*outpath,unsigned reps,const char*kind){
 unsigned n=w.h.nodes,j=w.h.jobs,nc=w.h.cells;size_t total=size_t(n)*j;size_t required=20*total+8*size_t(j)*nc+row.size()*8+edge.size()*sizeof(E)+n+4*total+j*(sizeof(la::Job)+sizeof(Meta)+4)+w.h.costs*8+8;
 size_t free,all;CK(cudaMemGetInfo(&free,&all));if(required>free*8/10)throw std::runtime_error("GPU capacity admission");
 std::vector<unsigned char>type(n);for(unsigned u=0;u<n;++u)type[u]=w.node[u].type==1;
 auto dr=copy(row.data(),row.size());auto de=copy(edge.data(),edge.size());auto dt=copy(type.data(),type.size());auto dc=copy(w.cell.data(),total);auto dk=copy(w.cost.data(),w.h.costs);auto dj=copy(w.job.data(),j);auto dtarget=copy(targets.data(),j);
 auto label=alloc<U>(total),prop=alloc<U>(total),out=alloc<U>(size_t(j)*nc);auto pending=alloc<unsigned>(total),done=alloc<unsigned>(1),error=alloc<unsigned>(1);auto meta=alloc<Meta>(j);
 std::vector<U>got(size_t(j)*nc),ref(got.size());std::ifstream rf(refpath,std::ios::binary);la::read(rf,ref.data(),ref.size());for(auto&x:ref)x=x<<32|x>>32;
 CK(cudaDeviceSynchronize());std::cout<<std::setprecision(12);cudaEvent_t a,b;CK(cudaEventCreate(&a));CK(cudaEventCreate(&b));
 for(unsigned rep=0;rep<reps;++rep){unsigned completed=0,err=0,waves=0;auto start=Clock::now();CK(cudaEventRecord(a));CK(cudaMemset(error,0,4));dim3 grid((n+255)/256,j);
  initialize<<<grid,256>>>(label,prop,pending,out,meta,dj,dtarget,n,nc);
  while(completed<j){if(++waves>100000||seconds(start)>300)throw std::runtime_error("incomplete GPU budget");
   expand<<<grid,256>>>(dr,de,dt,dc,dk,label,prop,pending,out,meta,n,nc,error);
   commit<<<grid,256>>>(label,prop,pending,meta,n,error);CK(cudaMemset(done,0,4));advance<<<(j+127)/128,128>>>(meta,j,done,error);CK(cudaGetLastError());CK(cudaMemcpy(&completed,done,4,cudaMemcpyDeviceToHost));
  }
  CK(cudaMemcpy(&err,error,4,cudaMemcpyDeviceToHost));CK(cudaEventRecord(b));CK(cudaEventSynchronize(b));double resident=seconds(start);float ms;CK(cudaEventElapsedTime(&ms,a,b));if(err)throw std::runtime_error("GPU numeric/semantic error "+std::to_string(err));
  CK(cudaMemcpy(got.data(),out,got.size()*8,cudaMemcpyDeviceToHost));for(auto&x:got)if(x==INF)x=MISSING;
  bool equal=got==ref;std::cout<<"{\"scope\":\"RESIDENT_COMPLETE_BATCH_V2\",\"backend\":\"CUDA_prepared_CSR_valid_POP_private_INF\",\"representation\":\""<<kind<<"\",\"rep\":"<<rep<<",\"warmup\":"<<(rep==0?"true":"false")<<",\"jobs\":"<<j<<",\"resident_s\":"<<resident<<",\"device_timeline_including_host_gaps_s\":"<<ms/1000<<",\"waves\":"<<waves<<",\"device_bytes\":"<<required<<",\"output_equal\":"<<(equal?"true":"false")<<",\"measured_GPU\":true}\n"<<std::flush;
  if(!equal)throw std::runtime_error("whole-output differential mismatch");
 }
 std::ofstream f(outpath,std::ios::binary);for(auto x:got){x=x<<32|x>>32;f.write((char*)&x,8);}CK(cudaEventDestroy(a));CK(cudaEventDestroy(b));
 for(void*p:{(void*)dr,(void*)de,(void*)dt,(void*)dc,(void*)dk,(void*)dj,(void*)dtarget,(void*)label,(void*)prop,(void*)out,(void*)pending,(void*)done,(void*)error,(void*)meta})if(p)CK(cudaFree(p));return 0;
}
int main(int argc,char**argv){try{
 if(argc!=7)throw std::runtime_error("workload prepared reference output repetitions basic|compact");la::Workload w(argv[1]);la61::Prepared targets(w);
 std::ifstream f(argv[2],std::ios::binary);if(!f)throw std::runtime_error("missing prepared CSR file");uint64_t h[6];la::read(f,h,6);if(h[0]!=0x5350415253455632ull||h[1]!=w.h.nodes||w.h.nodes>=(1u<<28)||w.h.costs>16)throw std::runtime_error("prepared admission");
 std::vector<uint64_t>row(h[1]+1);std::vector<unsigned>edge(h[2]);la::read(f,row.data(),row.size());la::read(f,edge.data(),edge.size());
 // Independently reconstruct eligible CSR, including skip and early-break.
 size_t pos=0;for(unsigned n=0;n<w.h.nodes;++n){if(row[n]!=pos)throw std::runtime_error("prepared row mismatch");for(auto k=w.row[n];k<w.row[n+1];++k){auto v=w.edge[k].dst;int a=la::eligible(w.node[n],w.node[v]);if(a<0)break;if(!a)continue;if(pos>=edge.size()||edge[pos++]!=(v|(w.node[v].cost<<28)))throw std::runtime_error("prepared edge mismatch");}}if(pos!=edge.size()||row.back()!=pos)throw std::runtime_error("prepared final row mismatch");
 // Preserve unreachable SOURCE/SINK costs; expand rejects every invalid reachable sum.
 if(std::string(argv[6])=="compact")return run(w,row,edge,targets.targets,argv[3],argv[4],std::stoul(argv[5]),argv[6]);
 if(std::string(argv[6])!="basic")throw std::runtime_error("representation");std::vector<BasicEdge>b;for(auto e:edge)b.push_back({e&0xfffffff,e>>28});return run(w,row,b,targets.targets,argv[3],argv[4],std::stoul(argv[5]),argv[6]);
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
