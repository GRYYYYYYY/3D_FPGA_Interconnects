// Exhaustive boundary/width checks against an independent per-bit oracle.
#include "many_tile_model.hpp"
#include <random>
#include <iostream>
int main(){
 using M=r2_model::ManyTileModel<32,32,8192,8192>;
 std::mt19937_64 rng(94731);uint64_t cases=0;
 for(unsigned at=0;at<128;++at)for(unsigned width=0;width<=64;++width)for(unsigned rep=0;rep<32;++rep){
  std::array<uint32_t,6>a,b;for(auto&x:a)x=rng();b=a;uint64_t value=rng();
  for(unsigned i=0;i<width;++i){uint32_t mask=1u<<((at+i)%32);b[(at+i)/32]=(b[(at+i)/32]&~mask)|((value>>i&1)?mask:0);}
  M::set(a,at,width,value);if(a!=b)return 1;uint64_t reference=0;
  for(unsigned i=0;i<width;++i)reference|=uint64_t(b[(at+i)/32]>>((at+i)%32)&1)<<i;
  if(M::get(a,at,width)!=reference)return 2;++cases;
 }
 std::cout<<"PASS "<<cases<<" packed bus boundaries\n";
}
