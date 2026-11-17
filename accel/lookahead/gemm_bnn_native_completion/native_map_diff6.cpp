// Decode final native maps through the frozen generated schema, not raw offsets.
#include "map_lookahead.capnp.h"
#include <capnp/serialize.h>
#include <fcntl.h>
#include <unistd.h>
#include <cstring>
#include <cmath>
#include <iostream>
#include <stdexcept>
uint32_t bits(float x){uint32_t v;std::memcpy(&v,&x,4);return v;}
int main(int argc,char** argv){try{
 if(argc!=3)return 2;int fa=open(argv[1],O_RDONLY),fb=open(argv[2],O_RDONLY);if(fa<0||fb<0)return 2;capnp::ReaderOptions opt;opt.traversalLimitInWords=1ULL<<30;
 capnp::StreamFdMessageReader ar(fa,opt),br(fb,opt);auto a=ar.getRoot<VprMapLookahead>().getCostMap(),b=br.getRoot<VprMapLookahead>().getCostMap();auto ad=a.getDims(),bd=b.getDims();if(ad.size()!=bd.size())throw std::runtime_error("dimension count mismatch");for(unsigned i=0;i<ad.size();++i)if(ad[i]!=bd[i])throw std::runtime_error("shape mismatch");auto av=a.getData(),bv=b.getData();if(av.size()!=bv.size())throw std::runtime_error("size mismatch");uint64_t d=0,c=0,m=0;
 for(unsigned i=0;i<av.size();++i){auto x=av[i].getValue(),y=bv[i].getValue();d+=bits(x.getDelay())!=bits(y.getDelay());c+=bits(x.getCongestion())!=bits(y.getCongestion());m+=std::isnan(x.getDelay())!=std::isnan(y.getDelay());}
 std::cout<<"{\"entries\":"<<av.size()<<",\"delay_word_differences\":"<<d<<",\"congestion_word_differences\":"<<c<<",\"missing_state_differences\":"<<m<<"}\n";close(fa);close(fb);
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
