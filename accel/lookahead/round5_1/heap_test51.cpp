#include "heap51.hpp"
#include "strict_heap.hpp"
#include <algorithm>
#include <cassert>
#include <iostream>
#include <random>
#include <vector>

static uint64_t operations = 0, word_checks = 0;
template<int CAP> struct Check {
    on4::Word even[(CAP+1)/2], odd[(CAP+1)/2];
    la::Entry oracle[CAP];
    unsigned count = 0, reference_count = 0;
    Check() { for (unsigned i=0;i<CAP;++i) {
        oracle[i] = {0, 0, 0}; on4::put(even, odd, i, on4::pack(oracle[i]));
    } }
    void check() {
        assert(count == reference_count);
        // Include inactive tail slots: even the writes are identical to strict_heap.
        for (unsigned i=0;i<CAP;++i) {
            assert(on4::get(even,odd,i)==on4::pack(oracle[i])); ++word_checks;
        }
        ++operations;
    }
    void push(la::Entry e) {
        assert(count < CAP);
        la::push(oracle,reference_count,e);on4::push(even,odd,count,on4::pack(e));check();
    }
    void pop() {
        assert(count);
        auto expected=la::pop(oracle,reference_count);
        assert(on51::pop_path<CAP>(even,odd,count)==on4::pack(expected));check();
    }
    void drain() { while (count) pop(); }
};

template<int CAP> void random_case(unsigned seed,unsigned rounds,unsigned ties) {
    Check<CAP> c;std::mt19937 rng(seed);
    for(unsigned i=0;i<rounds;++i) {
        if(!c.count||(c.count<CAP && rng()%2))
            c.push({i,float(rng()%ties),float(rng()%100000)});
        else c.pop();
    }
    c.drain();
    // Every boundary size through CAP, complete drain, all delays tied.
    for(unsigned i=0;i<CAP;++i)c.push({i,1.f,float(CAP-i)});
    c.drain();
    // Descending delays produce long successful UP paths during push/pop.
    for(unsigned i=0;i<CAP;++i)c.push({i,float(CAP-i),float(i)});
    c.drain();
}

int main() {
    // Exhaust all 3-valued insertion orders up to length 8, then check each pop.
    for(unsigned length=1;length<=8;++length) {
        unsigned combinations=1;for(unsigned j=0;j<length;++j)combinations*=3;
        for(unsigned code=0;code<combinations;++code) {
            Check<8> c;unsigned digits=code;
            for(unsigned j=0;j<length;++j){c.push({j,float(digits%3),float(j+1)});digits/=3;}
            c.drain();
        }
    }
    random_case<1>(1,1000,1);random_case<2>(2,1000,2);
    random_case<3>(3,1000,2);random_case<4>(4,1000,3);
    random_case<7>(7,10000,3);random_case<8>(8,10000,5);
    random_case<9>(9,10000,31);random_case<127>(127,50000,4);
    random_case<128>(128,50000,31);random_case<129>(129,50000,65536);
    random_case<16385>(4001,1000,7);
    std::cout<<"{\"status\":\"passed\",\"operations\":"<<operations
             <<",\"full_array_word_checks\":"<<word_checks
             <<",\"max_capacity\":16385,\"oracle\":\"strict_heap.hpp\","
               "\"includes_inactive_tail\":true,\"exhaustive_three_delay_sequences_max_length\":8}\n";
}
