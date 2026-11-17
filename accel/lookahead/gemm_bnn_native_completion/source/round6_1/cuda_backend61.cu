#include "cuda_solver61.cuh"
#include <omp.h>
extern "C" int la_backend_v1(const la::BackendInput* in,la::Cost* output,la::Stats* stats,la::BackendMetrics* metrics,char* error,uint32_t error_size){try{
 if(!in||in->version!=1||!in->n||!getenv("VPR_LA_MODE")||std::string(getenv("VPR_LA_MODE"))!="ALT_BUCKET_FP32_V1")throw std::runtime_error("explicit ALT mode required");unsigned shift=getenv("VPR_LA_BUCKET_SHIFT")?std::stoul(getenv("VPR_LA_BUCKET_SHIFT")):20;if(shift!=20)throw std::runtime_error("native CUDA gate only shift20");auto service=Clock::now();auto& a=*in;
 // No reference file, no old export, no CPU fallback. Initial CUDA context is inside service.
 CudaSession61<la::Node,la::Edge> s(a,shift,a.nodes,a.edges);auto out=s.solve();*metrics={1,2,s.prepare_s,s.resident_s,s.readback_s,0,0};double e1=s.E1_wall_s;auto release=Clock::now();s.release();metrics->release_s=seconds(release);metrics->service_s=seconds(service);
 int device;CK(cudaGetDevice(&device));cudaDeviceProp prop;CK(cudaGetDeviceProperties(&prop,device));char bus[32];CK(cudaDeviceGetPCIBusId(bus,sizeof(bus),device));
 if(getenv("R61_VERIFY_CPU")){auto w=la61::view(a);la61::Prepared prep(w);std::vector<la::Cost> reference(out.size());int failure=0;
  #pragma omp parallel for num_threads(8) reduction(max:failure)
  for(size_t q=0;q<a.nj;++q){la61::ScratchT<std::map<uint32_t,std::vector<uint32_t>>> scratch(a.n);auto p=la61::search<false>(w,q,prep.targets[q],20,scratch,reference.data()+q*a.nc);failure=std::max(failure,int(p.status));}
  if(failure||memcmp(out.data(),reference.data(),out.size()*8))throw std::runtime_error("native input CPU/CUDA pair mismatch");fprintf(stdout,"R61_NATIVE_PAIR_VERIFY all_pairs_equal=1 coverage_equal=1 qids=%u\n",a.nj);
 }
 std::memcpy(output,out.data(),out.size()*8);for(unsigned q=0;q<a.nj;++q)stats[q]={UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX,la::OK};
 fprintf(stdout,"R61_BACKEND backend=CUDA shift=20 representation=original E1_wall_s=%.9f complete=1 fallback=0 device=%d pci_bus=%s stats=not_collected device_name=%s\n",e1,device,bus,prop.name);la61::capture(a,output,s.target_host,20,"CUDA");return 0;
}catch(const std::exception& e){if(error_size)snprintf(error,error_size,"%s",e.what());return 1;}}
