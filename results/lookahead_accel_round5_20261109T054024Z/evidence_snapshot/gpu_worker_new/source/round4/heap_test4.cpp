#include "onchip_types4.hpp"
#include <algorithm>
#include <cassert>
#include <iostream>
#include <random>
#include <vector>
struct Compare {bool operator()(la::Entry a,la::Entry b)const{return a.delay>b.delay;}};
int main(){
    static on4::Word even[on4::BANK_DEPTH],odd[on4::BANK_DEPTH];
    std::vector<la::Entry> reference;unsigned count=0;std::mt19937 rng(4001);
    for(unsigned round=0;round<25000;++round){
        bool insert=reference.empty()||(reference.size()<on4::MAX_E+1&&(rng()%3));
        if(insert){la::Entry e={round,float(rng()%31),float(rng()%101)};
            reference.push_back(e);std::push_heap(reference.begin(),reference.end(),Compare{});
            on4::push(even,odd,count,on4::pack(e));
        }else{
            auto expected=reference.front();std::pop_heap(reference.begin(),reference.end(),Compare{});reference.pop_back();
            auto actual=on4::pop(even,odd,count);assert(actual==on4::pack(expected));
        }
        assert(count==reference.size());
        // Full physical heap arrangement, not only root or popped delay.
        for(unsigned i=0;i<count;++i)assert(on4::get(even,odd,i)==on4::pack(reference[i]));
    }
    while(count){auto expected=reference.front();std::pop_heap(reference.begin(),reference.end(),Compare{});reference.pop_back();assert(on4::pop(even,odd,count)==on4::pack(expected));}
    for(unsigned i=0;i<=on4::MAX_E;++i)on4::push(even,odd,count,on4::pack({i,1.f,float(i)}));
    assert(count==on4::MAX_E+1);while(count)on4::pop(even,odd,count);
    std::cout<<"PASS banked 96-bit heap: full arrangement after 25000 mixed operations, equal delays, maximum capacity\n";
}
