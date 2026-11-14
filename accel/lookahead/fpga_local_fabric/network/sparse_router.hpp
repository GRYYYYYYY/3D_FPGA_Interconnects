#pragma once
#include "../../fpga_descriptor_front/services/transport_model.hpp"
namespace lf {
// Static admissible edges; each output owns one real registered holding packet.
// This preserves legal-traffic old RR ordering while removing unreachable muxes.
template<class P>struct SparseRouter{
 unsigned ni,no;bool request;std::vector<unsigned>cursor;std::vector<std::optional<P>>out;
 std::vector<std::vector<unsigned>>inputs;
 SparseRouter(bool req):ni(req?208:128),no(req?128:208),request(req),cursor(no,0),out(no),inputs(no){
  for(unsigned o=0;o<no;++o)for(unsigned i=0;i<ni;++i)if(connected(i,o))inputs[o].push_back(i);
 }
 bool connected(unsigned i,unsigned o)const{
  unsigned s=request?i:o,p=request?o/4:i/4,c=request?o%4:i%4;
  unsigned sc=s<16?0:s<48||s>=176?1:s<112?2:3;
  if(sc!=c)return false;if(s<48)return true;
  return p==(s<112?(s-48)/2:s<176?(s-112)/2:s-176);
 }
 std::vector<int>grants(const std::vector<std::optional<dfservice::Routed<P>>>&in,const std::vector<bool>&ready)const{
  if(in.size()!=ni||ready.size()!=no)throw std::runtime_error("SPARSE_GEOMETRY");
  std::vector<int>g(no,-1);std::vector<unsigned>rank(no,ni);
  for(unsigned i=0;i<ni;++i)if(in[i]){unsigned o=in[i]->dest;if(o>=no||!connected(i,o))throw std::runtime_error("ILLEGAL_STATIC_CONNECTION");
   if(!out[o]||ready[o]){unsigned r=i>=cursor[o]?i-cursor[o]:i+ni-cursor[o];if(r<rank[o]){rank[o]=r;g[o]=int(i);}}}
  return g;
 }
 std::vector<bool>input_ready(const std::vector<std::optional<dfservice::Routed<P>>>&in,const std::vector<bool>&ready)const{auto g=grants(in,ready);std::vector<bool>r(ni,false);for(int i:g)if(i>=0)r[i]=true;return r;}
 void tick(const std::vector<std::optional<dfservice::Routed<P>>>&in,const std::vector<bool>&ready){auto g=grants(in,ready);for(unsigned o=0;o<no;++o)if(!out[o]||ready[o]){out[o].reset();if(g[o]>=0){out[o]=in[g[o]]->payload;cursor[o]=(g[o]+1)%ni;}}}
};
}
