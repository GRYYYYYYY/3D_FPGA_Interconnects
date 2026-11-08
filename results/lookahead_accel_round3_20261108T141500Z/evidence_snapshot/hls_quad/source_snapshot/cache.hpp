#pragma once
#include "workload.hpp"
#ifndef LA_HEAP_TOP
#define LA_HEAP_TOP 31
#endif
#ifndef LA_LABEL_LINES
#define LA_LABEL_LINES 0
#endif
namespace la {
struct HeapMemory {
 Entry* external;
 Entry top[LA_HEAP_TOP>0?LA_HEAP_TOP:1];
 Entry get(uint32_t i) {return i<LA_HEAP_TOP?top[i]:external[i];}
 void set(uint32_t i,Entry v){if(i<LA_HEAP_TOP)top[i]=v;else external[i]=v;}
};
inline void cached_push(HeapMemory& a,uint32_t& n,Entry v) {
 uint32_t hole=n++;while(hole){uint32_t p=(hole-1)/2;Entry old=a.get(p);if(!(old.delay>v.delay))break;a.set(hole,old);hole=p;}a.set(hole,v);
}
inline Entry cached_pop(HeapMemory& a,uint32_t& n) {
 Entry result=a.get(0),v=a.get(--n);if(!n)return result;uint32_t hole=0,child=2;
 while(child<n){Entry right=a.get(child),left=a.get(child-1);if(right.delay>left.delay){--child;right=left;}a.set(hole,right);hole=child;child=2*(hole+1);}
 if(child==n){a.set(hole,a.get(child-1));hole=child-1;}
 while(hole){uint32_t p=(hole-1)/2;Entry old=a.get(p);if(!(old.delay>v.delay))break;a.set(hole,old);hole=p;}a.set(hole,v);return result;
}
struct LabelLine {uint32_t tag,expanded;float visited;bool valid;};
struct LabelMemory {
 float* v;uint32_t* e;LabelLine lines[LA_LABEL_LINES>0?LA_LABEL_LINES:1];
 void reset(){for(unsigned i=0;i<LA_LABEL_LINES;++i)lines[i].valid=false;}
 LabelLine get(uint32_t key){
#if LA_LABEL_LINES > 0
  unsigned index=key%LA_LABEL_LINES;LabelLine l=lines[index];if(l.valid && l.tag==key)return l;
  l={key,e[key],v[key],true};lines[index]=l;return l;
#else
  LabelLine l={key,e[key],v[key],true};return l;
#endif
 }
 void set_visited(uint32_t key,float value){v[key]=value;
#if LA_LABEL_LINES > 0
  LabelLine l=get(key);l.visited=value;lines[key%LA_LABEL_LINES]=l;
#endif
 }
 void set_expanded(uint32_t key){e[key]=1;
#if LA_LABEL_LINES > 0
  LabelLine l=get(key);l.expanded=1;lines[key%LA_LABEL_LINES]=l;
#endif
 }
};
}
