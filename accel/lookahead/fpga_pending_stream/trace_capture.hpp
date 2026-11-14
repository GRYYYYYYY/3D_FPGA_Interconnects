#pragma once
#include <set>
// Offline trace storage is a verification artifact, never on-chip capacity.
struct TraceCapture {
 struct Pop{uint32_t node,arg,pv,valid,target,parent;uint64_t label;};
 struct Edge{uint32_t node;uint64_t pair;};
 struct Parent{uint32_t node;uint64_t label;std::vector<Edge> edges;};
 std::set<std::pair<unsigned,unsigned>> selection;
 std::vector<Pop> pops;std::vector<Parent> parents;std::set<unsigned> lines;
 std::string dir;unsigned sample=0,wave=0,bucket=0;bool enabled=false;
 explicit TraceCapture(const std::string& d):dir(d){
  if(const char* p=getenv("PENDING_STREAM_SELECTION")){std::ifstream f(p);unsigned q,w;while(f>>q>>w)selection.insert({q,w});}
 }
 void begin(unsigned q,unsigned w,unsigned b){sample=q;wave=w;bucket=b;enabled=selection.count({q,w});pops.clear();parents.clear();lines.clear();}
 void pop(unsigned n,unsigned arg,unsigned pv,bool valid,bool target,uint64_t label){if(!enabled)return;pops.push_back({n,arg,pv,unsigned(valid),unsigned(target),~0u,label});}
 void parent(unsigned n,uint64_t label){if(!enabled)return;parents.push_back({n,label,{}});}
 void candidate(unsigned n,uint64_t p){if(!enabled)return;parents.back().edges.push_back({n,p});lines.insert(n/4);}
 template<class Labels,class States>void finish(const Labels& label,const Labels& prop,const States& state){
  if(!enabled)return;size_t pi=0;for(auto& p:pops)if(p.valid){if(pi>=parents.size()||parents[pi].node!=p.node)throw Failure("TRACE_PARENT_ORDER");p.parent=pi++;}if(pi!=parents.size())throw Failure("TRACE_PARENT_COUNT");
  uint64_t ne=0;for(auto& p:parents)ne+=p.edges.size();
  std::ofstream f(dir+"/wave_"+std::to_string(sample)+"_"+std::to_string(wave)+".bin",std::ios::binary);
  uint64_t h[]={0x5053545241434531ull,sample,wave,bucket,pops.size(),parents.size(),ne,lines.size()};la::write(f,h,8);
  for(auto p:pops){uint32_t a[]={p.node,p.arg,p.pv,p.valid,p.target,p.parent};la::write(f,a,6);la::write(f,&p.label,1);}
  for(auto& p:parents){uint32_t a[]={p.node,uint32_t(p.edges.size())};la::write(f,a,2);la::write(f,&p.label,1);for(auto e:p.edges){la::write(f,&e.node,1);la::write(f,&e.pair,1);}}
  for(auto l:lines){la::write(f,&l,1);uint64_t before[4],after[4];uint32_t pv[4];for(unsigned k=0;k<4;++k){unsigned n=l*4+k;before[k]=n<label.size()?pack(label[n]):pending17::INF;after[k]=n<prop.size()?pack(prop[n]):pending17::INF;pv[k]=n<state.size()?state[n].pv:0;}la::write(f,before,4);la::write(f,pv,4);la::write(f,after,4);}
  std::cout<<"TRACE_SAVED sample="<<sample<<" wave="<<wave<<" pops="<<pops.size()<<" candidates="<<ne<<std::endl;
 }
};
