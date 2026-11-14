#pragma once
#include <cstdint>
#include <stdexcept>
namespace pending17 {
constexpr uint64_t INF=0x7f8000007f800000ull;
struct Old {uint64_t label=INF;uint32_t pending=0;};
struct Packed {uint64_t label=INF;uint32_t pv=0;}; // low16 version, bit16 present
inline uint32_t expand(Packed x){return x.pv&65536 ? 0x10000000u|((x.pv&65535)<<12)|uint32_t(x.label>>52):0;}
inline Packed encode(Old x){
 if(x.pending && (!(x.pending&0x10000000u)||(x.pending&4095)!=(x.label>>52)||(x.pending>>29)))throw std::runtime_error("pending invariant");
 return {x.label,x.pending?65536u|((x.pending>>12)&65535):0};
}
// Reference is a transcription of node_state.sv apply_record ops 2,3,5.
inline unsigned old_op(Old& x,unsigned op,uint64_t value,uint32_t arg){
 if(op==5){x={0,0x10001000};return 1;}
 if(op==2){if((x.pending&0x10000000)&&((x.pending&0xfffffff)==arg)){x.pending=0;return 1;}return 0;}
 if(op!=3)throw std::runtime_error("op");
 if(value>=x.label)return 8;
 unsigned append=!(x.pending&0x10000000)||(x.pending&4095)!=(value>>52);
 if(append)x.pending=0x10000000|((((x.pending>>12)+1)&65535)<<12)|(value>>52);
 x.label=value;return append;
}
inline unsigned packed_op(Packed& x,unsigned op,uint64_t value,uint32_t arg){
 if(op==5){x={0,65537};return 1;}
 if(op==2){if((x.pv&65536)&&(((x.pv&65535)<<12)|(x.label>>52))==arg){x.pv=0;return 1;}return 0;}
 if(op!=3)throw std::runtime_error("op");
 if(value>=x.label)return 8;
 unsigned append=!(x.pv&65536)||(x.label>>52)!=(value>>52);
 if(append)x.pv=65536|((x.pv+1)&65535);
 x.label=value;return append;
}
inline void check(Old a,Packed b){if(a.label!=b.label||a.pending!=expand(b)||(!(b.pv&65536)&&b.pv))throw std::runtime_error("pending17 differential");}
inline unsigned both(Old& a,Packed& b,unsigned op,uint64_t value,uint32_t arg){check(a,b);auto x=old_op(a,op,value,arg),y=packed_op(b,op,value,arg);if(x!=y)throw std::runtime_error("pending17 event");check(a,b);return x;}
}
