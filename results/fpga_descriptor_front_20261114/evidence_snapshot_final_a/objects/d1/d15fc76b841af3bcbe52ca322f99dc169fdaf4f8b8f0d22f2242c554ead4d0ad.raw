#include "directory_model.hpp"
#include <fstream>
#include <random>
#include <deque>
#include <cassert>
#include <iostream>
using namespace dfservice;
int main(int argc,char**argv){if(argc!=2)return 2;std::ofstream f(argv[1]);MinimumTree t;std::mt19937 rng(777);std::deque<unsigned> oracle;unsigned accepted=0,got=0;for(unsigned c=0;c<1200;++c){std::optional<std::array<unsigned,64>>in;if(c<1000&&rng()%4){in.emplace();for(auto&x:*in)x=(rng()%5==0)?4096:rng()%4096;if(c%7==0)in->fill(4096);}bool rr=rng()%3;f<<std::hex<<bool(in)<<' '<<rr<<' '<<t.ready(rr)<<' '<<bool(t.output())<<' '<<t.output().value_or(4096)<<' ';for(unsigned i=0;i<64;++i)f<<(in?(*in)[i]:4096)<<' ';f<<'\n';if(t.output()&&rr){assert(!oracle.empty()&&oracle.front()==*t.output());oracle.pop_front();++got;}if(in&&t.ready(rr)){oracle.push_back(*std::min_element(in->begin(),in->end()));++accepted;}t.tick(in,rr);}assert(oracle.empty()&&accepted==got);std::cout<<"MIN_TREE_MODEL_PASS cycles=1200 transactions="<<got<<"\n";}
