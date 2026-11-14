#include "packed.hpp"
#include <iostream>
#include <functional>
int main(){try{unsigned passed=0;uint8_t p[16]{};
 auto rejects=[&](const char*name,auto f){bool caught=false;try{f();}catch(const std::runtime_error&){caught=true;}dfdesc::require(caught,name);++passed;};
 for(unsigned fmt:{8u,16u})for(auto begin:{uint64_t(0),uint64_t(32),uint64_t(UINT32_MAX)-65535})for(auto degree:{0u,1u,65535u})for(bool valid:{false,true}){
  dfdesc::encode_record(p,fmt,begin,begin+degree,32767,valid,UINT32_MAX,32768);auto d=dfdesc::decode_record(p,fmt,UINT32_MAX,32768);dfdesc::require(d.begin==begin&&d.end==begin+degree&&d.cell==(valid?32767u:0u)&&d.valid==valid,"BOUNDARY_DECODE");++passed;
 }
 rejects("degree65536 reject8",[&]{dfdesc::encode_record(p,8,0,65536,0,true,65536,1);});
 dfdesc::encode_record(p,16,0,65536,0,true,65536,1);dfdesc::require(dfdesc::decode_record(p,16,65536,1).end==65536,"FALLBACK_65536");++passed;
 rejects("offset end overflow",[&]{dfdesc::encode_record(p,16,UINT32_MAX,uint64_t(UINT32_MAX)+1,0,false,uint64_t(UINT32_MAX)+1,1);});
 rejects("offset begin overflow",[&]{dfdesc::encode_record(p,16,uint64_t(UINT32_MAX)+1,uint64_t(UINT32_MAX)+1,0,false,uint64_t(UINT32_MAX)+1,1);});
 rejects("decreasing row",[&]{dfdesc::encode_record(p,8,8,7,0,false,20,1);});
 rejects("edge array overrun",[&]{dfdesc::encode_record(p,8,8,9,0,false,8,1);});
 rejects("cell capacity",[&]{dfdesc::encode_record(p,16,0,0,0,false,0,32769);});
 rejects("valid out of range",[&]{dfdesc::encode_record(p,8,0,0,1,true,0,1);});
 rejects("valid negative",[&]{dfdesc::encode_record(p,8,0,0,-1,true,0,1);});
 dfdesc::encode_record(p,8,UINT32_MAX,UINT32_MAX,0,false,UINT32_MAX,1);p[4]=1;
 rejects("decode addition wraps32",[&]{dfdesc::decode_record(p,8,UINT32_MAX,1);});
 dfdesc::encode_record(p,16,0,0,0,false,0,1);p[12]=2;
 rejects("reserved flags",[&]{dfdesc::decode_record(p,16,0,1);});
 dfdesc::encode_record(p,8,0,0,0,false,0,1);p[6]=1;
 rejects("invalid cell noncanonical",[&]{dfdesc::decode_record(p,8,0,1);});
 dfdesc::Layout l(1ull<<32,4102608,40,16);dfdesc::require(l.total_bytes>INT32_MAX&&l.address(39,4102607)>UINT32_MAX&&l.address(39,4102607)+16<=l.end_bytes,"WIDE_LAYOUT");++passed;
 rejects("address overflow",[&]{dfdesc::Layout(UINT64_MAX-1023,4102608,40,16);});
 rejects("multiply overflow",[&]{dfdesc::Layout(0,UINT64_MAX,40,16);});
 rejects("sample out of range",[&]{l.address(40,0);});
 std::cout<<"{\"status\":\"PASS\",\"boundary_checks\":"<<passed<<",\"fallback_degree\":65536,\"layout_above_2GiB\":true,\"decode_u64_carry_checked\":true}\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
