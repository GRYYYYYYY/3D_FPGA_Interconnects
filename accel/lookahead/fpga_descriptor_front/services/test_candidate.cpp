#include "transport_model.hpp"
#include <random>
#include <fstream>
#include <iostream>
#include <set>
#include <cassert>
using namespace dfservice;
struct P{unsigned node=0;uint64_t pair=0;};
int main(int argc,char**argv){if(argc!=2)return 2;std::ofstream f(argv[1]);std::mt19937 rng(0x641644);RegisteredRouter<P> r(64,64);std::array<Queue<P,4>,64> q;std::array<Queue<P,16>,64> bank;std::vector<std::optional<P>> in(64);std::vector<bool> ready(64);std::array<unsigned,64> count{};std::set<uint64_t> sent,got;unsigned peak=0,cy=0;bool done=false;
 for(;cy<10000;++cy){for(unsigned i=0;i<64;++i){if(!in[i]&&count[i]<64){unsigned dst=count[i]<32?0:rng()%64;unsigned node=((dst/2)<<2)|((dst%2)<<7)|(count[i]%4);in[i]=P{node,(uint64_t(i)<<32)|count[i]};}ready[i]=cy>100&&(rng()%4!=0);}
  f<<std::hex;for(unsigned i=0;i<64;++i){P x=in[i].value_or(P{}),y=bank[i].empty()?P{}:bank[i].front();f<<bool(in[i])<<' '<<x.node<<' '<<x.pair<<' '<<ready[i]<<' '<<!q[i].full()<<' '<<!bank[i].empty()<<' '<<y.node<<' '<<y.pair<<' ';}f<<'\n';
  std::vector<std::optional<Routed<P>>> heads(64);std::vector<bool> br(64);for(unsigned i=0;i<64;++i){if(!q[i].empty()){P x=q[i].front();heads[i]=Routed<P>{2*((x.node/4)&31)+((x.node>>7)&1),x};}br[i]=!bank[i].full();}
  auto take=r.input_ready(heads,br);for(unsigned i=0;i<64;++i){if(!bank[i].empty()&&ready[i])assert(got.insert(bank[i].front().pair).second);bank[i].tick(r.out[i],ready[i]);if(in[i]&&!q[i].full()){assert(sent.insert(in[i]->pair).second);q[i].tick(in[i],take[i]);in[i].reset();++count[i];}else q[i].tick({},take[i]);peak=std::max(peak,bank[i].n);}
  r.tick(heads,br);done=sent.size()==4096&&got==sent;for(unsigned i=0;i<64;++i)done=done&&q[i].empty()&&bank[i].empty()&&!r.out[i];if(done)break;
 }
 assert(done&&peak==16);std::cout<<"CANDIDATE_MODEL_PASS cycles="<<cy+1<<" accepted="<<sent.size()<<" peak_bank_fifo="<<peak<<"\n";
}
