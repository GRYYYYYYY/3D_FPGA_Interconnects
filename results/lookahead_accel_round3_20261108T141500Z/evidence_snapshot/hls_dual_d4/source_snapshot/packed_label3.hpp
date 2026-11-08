#pragma once
#include "cache.hpp"
#ifndef LA_LABEL_WRITEBACK
#define LA_LABEL_WRITEBACK 0
#endif
namespace la {
// Packing preserves the exact FP32 bits; expanded occupies the high 32 bits.
inline uint64_t pack_label(LabelLine l) {
 union {float f;uint32_t u;} bits;bits.f=l.visited;
 return (uint64_t(l.expanded)<<32)|bits.u;
}
inline LabelLine unpack_label(uint32_t key,uint64_t data) {
 union {float f;uint32_t u;} bits;bits.u=uint32_t(data);
 LabelLine l={key,uint32_t(data>>32),bits.f,true};return l;
}
struct PackedLabelMemory {
 uint64_t* external;
 LabelLine lines[LA_LABEL_LINES];
 bool dirty[LA_LABEL_LINES];
 void reset(){for(unsigned i=0;i<LA_LABEL_LINES;++i){lines[i].valid=false;dirty[i]=false;}}
 void evict(unsigned i){
#if LA_LABEL_WRITEBACK
  if(lines[i].valid && dirty[i])external[lines[i].tag]=pack_label(lines[i]);
#endif
  dirty[i]=false;
 }
 LabelLine get(uint32_t key){
  unsigned i=key%LA_LABEL_LINES;LabelLine l=lines[i];
  if(l.valid && l.tag==key)return l;
  evict(i);l=unpack_label(key,external[key]);lines[i]=l;return l;
 }
 void put(LabelLine l){
  unsigned i=l.tag%LA_LABEL_LINES;lines[i]=l;
#if LA_LABEL_WRITEBACK
  dirty[i]=true;
#else
  external[l.tag]=pack_label(l);
#endif
 }
 void set_visited(uint32_t key,float value){LabelLine l=get(key);l.visited=value;put(l);}
 void set_expanded(uint32_t key){LabelLine l=get(key);l.expanded=1;put(l);}
 // Included in E1, also on error: no dirty state is discarded at sample boundaries.
 void flush(){for(unsigned i=0;i<LA_LABEL_LINES;++i)evict(i);}
};
}
