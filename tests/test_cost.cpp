#include "cost.hpp"
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <vector>

// Independent scalar oracle: tests the formula and saturation boundary rather
// than comparing two calls to the shared implementation.
static uint32_t oracle(h3d::Candidate c) {
    using namespace h3d;
    if(c.capacity==0 || c.base==0 || c.base>=COST_INF || c.history>=COST_INF ||
       c.present>=COST_INF || c.vertical_penalty>=COST_INF) return COST_INF;
    const uint64_t b=uint64_t(c.base)+(c.vertical?c.vertical_penalty:0);
    const uint64_t excess=uint64_t(c.occupancy)+1>c.capacity?uint64_t(c.occupancy)+1-c.capacity:0;
    const uint64_t value=b*(uint64_t(c.history)+1)+excess*c.present;
    return value>=COST_INF?COST_INF:uint32_t(value);
}
int main(int argc,char** argv) {
    std::vector<h3d::Candidate> input;
    if(argc==2) {
        std::ifstream in(argv[1]);h3d::Candidate c{};
        while(in>>c.base>>c.history>>c.occupancy>>c.capacity>>c.present>>c.vertical_penalty>>c.vertical) input.push_back(c);
        if(!in.eof() || input.empty()) return 2;
    } else {
        const uint32_t v[]={0,1,2,17,h3d::COST_INF-1,h3d::COST_INF,UINT32_MAX};
        for(auto b:v) for(auto h:v) for(auto o:v) for(auto cap:v)
            input.push_back({b,h,o,cap,31,53,1,0});
        uint32_t rng=71;
        for(int i=0;i<1000;++i) {
            rng=rng*1664525U+1013904223U;
            input.push_back({1+rng%1000,rng%100,rng%10,1+rng%9,rng%10000,rng%100,rng%2,0});
        }
    }
    const size_t count=input.size();
    // HLS 2022.2's AXI co-simulation wrapper serializes the declared depth,
    // including unused entries. Allocate the entire 4096-entry port region.
    input.resize(std::max(count,size_t(4096)),h3d::Candidate{});
    std::vector<uint32_t> output(input.size(),0xabcdefU);
    // Multiple invocations exercise FIFO draining; includes zero-length launch.
    evaluate_candidates(input.data(),output.data(),0);
    for(int repeat=0;repeat<2;++repeat) {
        evaluate_candidates(input.data(),output.data(),int(count));
        for(size_t i=0;i<count;++i) if(output[i]!=oracle(input[i])) {
            std::cerr<<"cost mismatch at "<<i<<'\n';return 1;
        }
        for(size_t i=count;i<output.size();++i) if(output[i]!=0xabcdefU) return 3;
    }
    std::cout<<"cost vectors="<<count<<" repeated=2 PASS\n";
    return 0;
}
