#include "heap51.hpp"
#include "strict_heap.hpp"
#include <cassert>
#include <iostream>
#include <random>
extern "C" on4::Word heap_pop51(on4::Word*,on4::Word*,unsigned&);
int main() {
    constexpr unsigned CAP=on4::MAX_E+1;
    on4::Word even[on4::BANK_DEPTH],odd[on4::BANK_DEPTH];
    la::Entry oracle[CAP];std::mt19937 rng(5109);
    const unsigned sizes[]={1,2,3,4,7,8,9,31,32,33,127,128,129,1023,16385};
    unsigned transaction=0;
    for(unsigned mode=0;mode<3;++mode)for(unsigned size:sizes) {
        for(unsigned i=0;i<CAP;++i){oracle[i]={0,0,0};on4::put(even,odd,i,on4::pack(oracle[i]));}
        unsigned count=0;
        for(unsigned i=0;i<size;++i) {
            float delay=mode==0 ? 1.f : mode==1 ? float(rng()%31) : float(size-i);
            la::push(oracle,count,{i,delay,float(i+1)});
        }
        for(unsigned i=0;i<size;++i)on4::put(even,odd,i,on4::pack(oracle[i]));
        unsigned expected_count=count;auto expected=la::pop(oracle,expected_count);
        auto result=heap_pop51(even,odd,count);
        assert(result==on4::pack(expected));assert(count==expected_count);
        for(unsigned i=0;i<CAP;++i)assert(on4::get(even,odd,i)==on4::pack(oracle[i]));
        std::cout<<"transaction="<<transaction++<<" mode="<<mode<<" initial_size="<<size<<" PASS\n";
    }
    std::cout<<"PASS 45 exact POP transactions, complete physical heaps, CAP=16385\n";
}
