#include "pending17.hpp"
#include <random>
#include <iostream>
#include "Vpending17_transform.h"
#include "verilated.h"
Vpending17_transform dut;
unsigned rtl(pending17::Old&a,pending17::Packed&b,unsigned op,uint64_t value,uint32_t arg){
 dut.old_label=b.label;dut.old_pv=b.pv;dut.opcode=op;dut.value=value;dut.argument=arg;dut.eval();
 unsigned result=pending17::both(a,b,op,value,arg);
 if(dut.new_label!=b.label||dut.new_pv!=b.pv||dut.status!=result)throw std::runtime_error("RTL pending17 bit-level differential");
 return result;
}
int main(){using namespace pending17;std::mt19937_64 rng(1729);uint64_t n=0;unsigned wraps=0;
 for(unsigned key=0;key<4096;++key)for(unsigned v:{0u,1u,65534u,65535u}){
  Old a{(uint64_t(key)<<52)|0xfffffffffffull,0x10000000u|(v<<12)|key};Packed b=encode(a);check(a,b);
  auto aa=a;auto bb=b;rtl(aa,bb,2,0,(v<<12)|key);if(bb.pv)throw std::runtime_error("POP must clear all PV");++n;
  rtl(a,b,3,uint64_t(key)<<52,0);++n; // same bucket, keep V including zero
  if(key){rtl(a,b,3,uint64_t(key-1)<<52,0);++n;if(v==65535){++wraps;if(b.pv!=65536)throw std::runtime_error("wrap lost present");}}
 }
 for(unsigned trial=0;trial<1000;++trial){Old a;Packed b;
  for(unsigned i=0;i<1000;++i){unsigned op=rng()%3;uint64_t value=rng()&0x7fffffffffffffffull;uint32_t arg=rng()&0xfffffff;
   if(op==0){op=2;if(rng()&1)arg=expand(b)&0xfffffff;}else if(op==1)op=3;else op=5;
   rtl(a,b,op,value,arg);++n;
  }
 }
 std::cout<<"{\"all_pass\":true,\"operations\":"<<n<<",\"constructed_wraps\":"<<wraps<<",\"natural_wrap_claim\":false}\n";
}
