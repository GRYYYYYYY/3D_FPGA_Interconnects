#pragma once
#include <cstdint>
#include <stdexcept>
namespace lf {
inline unsigned cls(unsigned s){return s<16?0:s<48?1:s<112?2:s<176?3:1;}
inline bool legal(unsigned s,unsigned kind,uint64_t line){
 if(s>=208||line>0xffffffffull)return false;
 bool k=s<16?kind==2:s<32?(kind==1||kind==11):s<48?kind==3:s<112?(kind>=4&&kind<=6):s<176?(kind==7||kind==8):(kind==0||kind==9||kind==10);
 unsigned p=s<112?(s-48)/2:s<176?(s-112)/2:s-176;
 return k&&(s<48||(line&31)==p);
}
// Bit-exact 74-bit adapter word. Fixed local route is reconstructed using owner.
struct WireIdentity {uint64_t lo;uint16_t hi;};
inline unsigned code(unsigned s){return s<48?s:s<112?48+(s-48)%2:s<176?50+(s-112)%2:52;}
inline WireIdentity pack(unsigned s,unsigned kind,uint32_t id,uint32_t generation){return {uint64_t(generation)<<32|id,uint16_t(code(s)<<4|kind)};}
inline unsigned unpack_source(WireIdentity x,unsigned port){unsigned c=x.hi>>4;if(c<48)return c;if(c<50)return 48+2*port+c-48;if(c<52)return 112+2*port+c-50;if(c==52)return 176+port;throw std::runtime_error("WIRE_ROUTE_CODE");}
}
