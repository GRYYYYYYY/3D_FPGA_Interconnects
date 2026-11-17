#pragma once
#include <array>
#include <vector>
#include <stdexcept>
#include <cstdint>
namespace la61 {
// One bitmap/directory per qid. pop freezes a vector, then clears visibility;
// the synchronous commit phase may publish a NEW vector of the same key.
class DirectDirectory {
 std::array<std::pair<uint32_t,std::vector<uint32_t>>,4096> slots;
 std::array<uint64_t,64> bits{};uint64_t upper=0;size_t count=0;
public:
 using iterator=decltype(slots)::iterator;
 DirectDirectory(){for(unsigned i=0;i<4096;++i)slots[i].first=i;}
 bool empty()const{return !upper;}size_t size()const{return count;}
 iterator begin(){if(!upper)throw std::runtime_error("empty directory");unsigned group=__builtin_ctzll(upper);return slots.begin()+64*group+__builtin_ctzll(bits[group]);}
 std::vector<uint32_t>& operator[](unsigned k){if(k>=4096)throw std::runtime_error("bucket key overflow");unsigned g=k/64;uint64_t mask=1ULL<<(k%64);if(!(bits[g]&mask)){bits[g]|=mask;upper|=1ULL<<g;++count;}return slots[k].second;}
 void erase(iterator i){unsigned k=i->first,g=k/64;bits[g]&=~(1ULL<<(k%64));if(!bits[g])upper&=~(1ULL<<g);--count;i->second.clear();}
 void clear(){while(!empty())erase(begin());}
};
}
