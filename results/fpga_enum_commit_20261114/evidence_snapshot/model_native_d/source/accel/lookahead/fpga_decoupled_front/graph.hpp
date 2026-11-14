#pragma once
#include "bucket61.hpp"
struct Graph {
 la::Workload w;std::vector<uint64_t> row;std::vector<uint32_t> edge;
 uint64_t rowbase=0,edgebase,metabase,metastride;
 static uint64_t align(uint64_t n){return (n+31)&~uint64_t(31);}
 explicit Graph(const char* path):w(path){
  for(unsigned u=0;u<w.h.nodes;++u){row.push_back(edge.size());for(uint64_t e=w.row[u];e<w.row[u+1];++e){auto n=w.edge[e].dst;int ok=la::eligible(w.node[u],w.node[n]);if(ok<0)break;if(ok)edge.push_back(n|(w.node[n].cost<<28));}}
  row.push_back(edge.size());edgebase=align((row.size()+3)/4);metabase=align(edgebase+(edge.size()+7)/8);metastride=align((w.h.nodes+3)/4);
 }
 static uint64_t packed(la::Cost c){return uint64_t(la61::bits(c.delay))<<32|la61::bits(c.congestion);}
 static la::Cost unpack(uint64_t p){la::Cost c;uint32_t a=p>>32,b=p;memcpy(&c.delay,&a,4);memcpy(&c.congestion,&b,4);return c;}
 uint64_t pair(uint64_t parent,uint32_t desc)const{auto p=unpack(parent),c=w.cost[desc>>28];la::Cost r{p.delay+c.delay,p.congestion+c.congestion};if(!la::numeric(r.delay)||!la::numeric(r.congestion))throw std::runtime_error("FP32 domain");return packed(r);}
};
