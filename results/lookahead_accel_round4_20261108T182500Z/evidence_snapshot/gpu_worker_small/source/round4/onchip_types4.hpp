#pragma once
#include "workload.hpp"
#include <ap_int.h>
#ifndef LA4_ENGINES
#define LA4_ENGINES 1
#endif
#ifndef LA4_EARLY
#define LA4_EARLY 0
#endif
namespace on4 {
static const unsigned MAX_N=4096,MAX_E=16384,MAX_J=32,MAX_C=128,MAX_K=64;
static const unsigned LOCAL_J=(MAX_J+LA4_ENGINES-1)/LA4_ENGINES;
static const unsigned BANK_DEPTH=(MAX_E+2)/2;
typedef ap_uint<96> Word;
typedef ap_uint<128> NodeWord;
typedef ap_uint<64> CostWord;
inline uint32_t bits(float f){union{float f;uint32_t u;}x;x.f=f;return x.u;}
inline float fp(uint32_t u){union{float f;uint32_t u;}x;x.u=u;return x.f;}
inline Word pack(la::Entry e){Word w;w.range(31,0)=e.node;w.range(63,32)=bits(e.delay);w.range(95,64)=bits(e.congestion);return w;}
inline la::Entry unpack(Word w){la::Entry e={(uint32_t)w.range(31,0),fp(w.range(63,32)),fp(w.range(95,64))};return e;}
inline uint32_t delay(Word w){return w.range(63,32);}
inline NodeWord pack_node(la::Node n){NodeWord w;w.range(31,0)=n.type;w.range(63,32)=n.cost;w.range(95,64)=n.inter;w.range(127,96)=uint32_t(n.segment_kind);return w;}
inline la::Node node(NodeWord w){la::Node n={(uint32_t)w.range(31,0),(uint32_t)w.range(63,32),(uint32_t)w.range(95,64),(int32_t)(uint32_t)w.range(127,96)};return n;}
inline CostWord pack_cost(la::Cost c){CostWord w;w.range(31,0)=bits(c.delay);w.range(63,32)=bits(c.congestion);return w;}
inline la::Cost cost(CostWord w){la::Cost c={fp(w.range(31,0)),fp(w.range(63,32))};return c;}
inline Word get(Word even[BANK_DEPTH],Word odd[BANK_DEPTH],unsigned i){
#pragma HLS INLINE
    return (i&1)?odd[i>>1]:even[i>>1];
}
inline void put(Word even[BANK_DEPTH],Word odd[BANK_DEPTH],unsigned i,Word value){
#pragma HLS INLINE
    if(i&1)odd[i>>1]=value;else even[i>>1]=value;
}
inline void push(Word even[BANK_DEPTH],Word odd[BANK_DEPTH],unsigned& count,Word value){
#pragma HLS INLINE
    unsigned hole=count++;
    HEAP_PUSH: while(hole){
#pragma HLS PIPELINE II=2
        unsigned p=(hole-1)/2;Word parent=get(even,odd,p);
        if(!(delay(parent)>delay(value)))break;
        put(even,odd,hole,parent);hole=p;
    }
    put(even,odd,hole,value);
}
inline Word pop(Word even[BANK_DEPTH],Word odd[BANK_DEPTH],unsigned& count){
#pragma HLS INLINE off
    Word result=even[0],value=get(even,odd,--count);if(!count)return result;
    unsigned hole=0,right=2;
    HEAP_DOWN: while(right<count){
#pragma HLS PIPELINE II=2
        // 0-based siblings: right is even, left is odd, independent RAM banks.
        Word r=even[right>>1],l=odd[(right-1)>>1];
        bool left=delay(r)>delay(l);unsigned child=left?right-1:right;
        put(even,odd,hole,left?l:r);hole=child;right=2*(hole+1);
    }
    if(right==count){put(even,odd,hole,odd[(right-1)>>1]);hole=right-1;}
    HEAP_UP: while(hole){
#pragma HLS PIPELINE II=2
        unsigned p=(hole-1)/2;Word parent=get(even,odd,p);
        if(!(delay(parent)>delay(value)))break;
        put(even,odd,hole,parent);hole=p;
    }
    put(even,odd,hole,value);return result;
}
}
