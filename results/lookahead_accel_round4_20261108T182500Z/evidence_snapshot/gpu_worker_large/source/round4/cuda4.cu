#include "reference4.hpp"
#include "cuda_kernel4.cuh"
#include <chrono>
#include <cstring>
#include <iomanip>
#include <iostream>
#define CUDA(c) do{cudaError_t e=(c);if(e!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(e));}while(0)
using Clock=std::chrono::steady_clock;
double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
template<class T>T* allocate(size_t n){T* p=nullptr;CUDA(cudaMalloc(&p,std::max<size_t>(n,1)*sizeof(T)));return p;}
template<class T>T* upload(const std::vector<T>& v){T* p=allocate<T>(v.size());if(v.size())CUDA(cudaMemcpy(p,v.data(),v.size()*sizeof(T),cudaMemcpyHostToDevice));return p;}
int main(int argc,char** argv){try{
    if(argc!=5)throw std::runtime_error("cuda4 workload CTAs warm_repeats full|early");
    la::Workload w(argv[1]);unsigned B=std::stoul(argv[2]),repeats=std::stoul(argv[3]);std::string mode=argv[4];
    if(!B||B>w.h.jobs||(mode!="full"&&mode!="early"))throw std::runtime_error("invalid config");
    auto service=Clock::now();la4::Prepared prepared(w);double target_prepare=seconds(service);CUDA(cudaFree(nullptr));
    auto row=upload(w.row);auto nodes=upload(w.node);auto edges=upload(w.edge);auto costs=upload(w.cost);auto jobs=upload(w.job);auto cells=upload(w.cell);auto targets=upload(prepared.targets);
    auto visited=allocate<float>(B*w.h.nodes);auto expanded=allocate<uint32_t>(B*w.h.nodes);auto heaps=allocate<la::Entry>(size_t(B)*(w.h.edges+1));
    auto out=allocate<la::Cost>(w.golden.size());auto stats=allocate<la::Stats>(w.h.jobs);auto next=allocate<unsigned>(1);
    std::vector<la::Cost> result(w.golden.size());std::vector<la::Stats> host_stats(w.h.jobs);
    cudaEvent_t a,b;CUDA(cudaEventCreate(&a));CUDA(cudaEventCreate(&b));double prepare=seconds(service);std::cout<<std::setprecision(17);
    for(unsigned repeat=0;repeat<=repeats;++repeat){
        auto start=Clock::now();CUDA(cudaEventRecord(a));CUDA(cudaMemsetAsync(next,0,sizeof(unsigned)));
        if(mode=="early")batch4<true><<<B,128>>>(row,nodes,edges,costs,jobs,cells,visited,expanded,heaps,out,stats,next,targets,w.h.nodes,w.h.jobs,w.h.cells,w.h.edges+1);
        else batch4<false><<<B,128>>>(row,nodes,edges,costs,jobs,cells,visited,expanded,heaps,out,stats,next,targets,w.h.nodes,w.h.jobs,w.h.cells,w.h.edges+1);
        CUDA(cudaGetLastError());CUDA(cudaEventRecord(b));CUDA(cudaEventSynchronize(b));float ms;CUDA(cudaEventElapsedTime(&ms,a,b));double complete=seconds(start);
        auto readback=Clock::now();CUDA(cudaMemcpy(result.data(),out,result.size()*sizeof(la::Cost),cudaMemcpyDeviceToHost));CUDA(cudaMemcpy(host_stats.data(),stats,host_stats.size()*sizeof(la::Stats),cudaMemcpyDeviceToHost));double readback_time=seconds(readback);
        if(std::memcmp(result.data(),w.golden.data(),result.size()*sizeof(la::Cost)))throw std::runtime_error("native golden mismatch");
        uint64_t pops=0,edge_visits=0,pushes=0;for(auto s:host_stats){if(s.status)throw std::runtime_error("search status failure");pops+=s.pops;edge_visits+=s.edges;pushes+=s.pushes;}
        std::cout<<"{\"kind\":\"batch\",\"backend\":\"cuda4_basic_CTA128\",\"mode\":\""<<la4::mode_name(mode=="early")<<"\",\"scope\":\"E1_resident_flood_batch\",\"evidence_type\":\"gpu_measured\",\"phase\":\""<<(repeat?"warm":"cold_first_call")<<"\",\"repeat\":"<<repeat<<",\"contexts\":"<<B<<",\"resident_s\":"<<double(ms)/1000<<",\"host_complete_s\":"<<complete<<",\"readback_s\":"<<readback_time<<",\"prepare_s\":"<<prepare<<",\"target_prepare_s\":"<<target_prepare<<",\"pops\":"<<pops<<",\"edges\":"<<edge_visits<<",\"pushes\":"<<pushes<<",\"all_golden_bits_match\":true}\n";
    }
    CUDA(cudaEventDestroy(a));CUDA(cudaEventDestroy(b));
    for(void* p:std::vector<void*>{row,nodes,edges,costs,jobs,cells,targets,visited,expanded,heaps,out,stats,next})CUDA(cudaFree(p));
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
