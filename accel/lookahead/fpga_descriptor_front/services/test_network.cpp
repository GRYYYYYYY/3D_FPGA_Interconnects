#include "network_model.hpp"
#include <random>
#include <fstream>
#include <iostream>
#include <set>
#include <cassert>
using namespace dfservice;
struct Packet{unsigned source=0,cls=0,line=0,id=0;bool write=false;uint64_t data=0;};
struct Flight{unsigned tag=0;uint64_t data=0,due=0;};
int main(int argc,char**argv){if(argc!=2)return 2;std::ofstream f(argv[1]);std::mt19937 rng(0x5e7a11);
 // Independently compare optimized rank selection with definition, including
 // non-power-of-two208-input/128-output geometry and sampled8input masks/cursors.
 for(unsigned ni:{8u,208u}){RegisteredRouter<unsigned> r(ni,ni==8?4:128);std::vector<std::optional<Routed<unsigned>>> in(ni);std::vector<bool> ready(r.no);
  for(unsigned trial=0;trial<10000;++trial){for(unsigned i=0;i<ni;++i)in[i]=(rng()%4)?std::optional<Routed<unsigned>>{{unsigned(rng()%r.no),i}}:std::nullopt;for(unsigned o=0;o<r.no;++o){ready[o]=rng()&1;r.cursor[o]=rng()%ni;r.out[o]=(rng()&1)?std::optional<unsigned>{1}:std::nullopt;}
   auto g=r.grants(in,ready);for(unsigned o=0;o<r.no;++o){int expected=-1;if(!r.out[o]||ready[o])for(unsigned k=0;k<ni;++k){unsigned i=(r.cursor[o]+k)%ni;if(in[i]&&in[i]->dest==o){expected=i;break;}}assert(g[o]==expected);}
  }
 }
 constexpr unsigned NS=8,NP=2,N=256;MemoryNetwork<Packet> net(NS,NP);
 std::array<unsigned,NS> sent{},received{};std::vector<std::optional<Packet>> input(NS);std::vector<bool> rr(NS),mr(NP);std::vector<std::optional<unsigned>> response(NP);
 std::array<std::vector<Flight>,NP> flight;std::array<std::optional<Flight>,NP> held;std::set<unsigned> delivered,issued;
 unsigned cyc=0,ooo=0,peakq=0,peakback=0,peakcredit=0,stalls=0;bool done=false;
 for(;cyc<100000;++cyc){
  for(unsigned s=0;s<NS;++s){if(!input[s]&&sent[s]<N){unsigned id=(s<<20)|(sent[s]<<4)|(sent[s]&15);input[s]=Packet{s,s/2,(sent[s]*32)|((s+sent[s]/7)&1),id,bool(sent[s]&1),(uint64_t(id)<<32)|(~id&0xffffffffu)};}rr[s]=cyc>=220&&(cyc%29<22)&&((rng()%11)!=0);}
  for(unsigned p=0;p<NP;++p){mr[p]=cyc>=25&&(rng()%9!=0);if(!held[p]){for(int i=int(flight[p].size())-1;i>=0;--i)if(flight[p][i].due<=cyc){held[p]=flight[p][i];if(i)++ooo;flight[p].erase(flight[p].begin()+i);break;}}response[p]=held[p]?std::optional<unsigned>(held[p]->tag):std::nullopt;}
  f<<std::hex;
  for(unsigned s=0;s<NS;++s){auto x=input[s].value_or(Packet{});auto r=net.response_router.out[s].value_or(Packet{});f<<bool(input[s])<<' '<<x.write<<' '<<x.line<<' '<<x.id<<' '<<x.data<<' '<<rr[s]<<' '<<!net.source[s].full()<<' '<<bool(net.response_router.out[s])<<' '<<r.id<<' '<<r.data<<' ';}
  for(unsigned p=0;p<NP;++p){bool v=!net.request_slice[p].empty();typename MemoryNetwork<Packet>::Tagged x{};if(v)x=net.request_slice[p].front();f<<mr[p]<<' '<<bool(held[p])<<' '<<(held[p]?held[p]->tag:0)<<' '<<(held[p]?held[p]->data:0)<<' '<<v<<' '<<x.packet.write<<' '<<x.packet.line<<' '<<x.tag<<' '<<x.packet.data<<' '<<!net.response_slice[p].full()<<' ';}
  f<<'\n';
  for(unsigned s=0;s<NS;++s)if(net.response_router.out[s]&&rr[s]){auto x=*net.response_router.out[s];assert(x.source==s&&delivered.insert(x.id).second);assert(x.data==((uint64_t(x.id)<<32)|(~x.id&0xffffffffu)));++received[s];}
  for(unsigned p=0;p<NP;++p){if(held[p]&&!net.response_slice[p].full())held[p].reset();if(!net.request_slice[p].empty()&&mr[p]){auto x=net.request_slice[p].front();assert(issued.insert(x.packet.id).second);flight[p].push_back({x.tag,x.packet.data,cyc+16+rng()%80});}for(auto&q:net.port[p].q)peakq=std::max(peakq,q.n);peakback=std::max(peakback,net.port[p].back.n);peakcredit=std::max(peakcredit,net.port[p].credits());}
  auto accepted=input;for(unsigned s=0;s<NS;++s){if(input[s]&&!net.source[s].full()){++sent[s];input[s].reset();}else if(input[s])++stalls;}
  net.tick(accepted,rr,mr,response);
  done=net.idle();for(unsigned s=0;s<NS;++s)done=done&&received[s]==N;for(unsigned p=0;p<NP;++p)done=done&&flight[p].empty()&&!held[p];if(done)break;
 }
 assert(done&&peakq==4&&peakback==4&&peakcredit==32&&ooo>0&&stalls>0);assert(delivered==issued);
 std::cout<<"NETWORK_MODEL_PASS cycles="<<cyc+1<<" requests="<<issued.size()<<" out_of_order="<<ooo<<" peak_clientQ="<<peakq<<" peak_backQ="<<peakback<<" peak_credit="<<peakcredit<<" source_stalls="<<stalls<<"\n";
}
