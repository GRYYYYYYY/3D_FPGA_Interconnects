#include "radix_model.hpp"
#include <fstream>
#include <iostream>
#include <sstream>
#include <iomanip>
#include <memory>
#include <set>
static std::string bits(const std::array<uint32_t,64>&v,unsigned width){std::string s;for(int nib=int((64*width)/4)-1;nib>=0;--nib){unsigned x=0;for(unsigned b=0;b<4;++b){unsigned k=nib*4+b;x|=((v[k/width]>>(k%width))&1)<<b;}s+="0123456789abcdef"[x];}return s;}
int main(int argc,char**argv){try{auto p=std::make_unique<lf::Radix<uint32_t>>();auto&r=*p;std::ofstream f(argv[1]);std::array<unsigned,64>sent{};std::set<unsigned>seen;unsigned cycles=0;bool reach[64][64]={};
 for(;seen.size()<8192||!r.idle();++cycles){if(cycles>20000)throw std::runtime_error("TIMEOUT");lf::Radix<uint32_t>::Inputs in{};lf::Radix<uint32_t>::Ready ready{};std::array<uint32_t,64> iv{},ir{},dest{},data{},ov{},orr{},out{};auto can=r.ready();
  for(unsigned i=0;i<64;++i){ready[i]=(cycles>1000||i!=0)&&((cycles+i*7)%23>4);orr[i]=ready[i];ir[i]=can[i];ov[i]=bool(r.out[i]);if(r.out[i])out[i]=*r.out[i];
   if(sent[i]<128){iv[i]=1;data[i]=i*256+sent[i];dest[i]=(i+sent[i]*17)%64;in[i]=dfservice::Routed<uint32_t>{dest[i],data[i]};}
   if(r.out[i]&&ready[i]){unsigned id=*r.out[i],s=id/256,n=id%256;if(n>=128||s>=64||i!=(s+n*17)%64||!seen.insert(id).second)throw std::runtime_error("ROUTE_OR_DUPLICATE");reach[s][i]=true;}
  }
  f<<bits(iv,1)<<' '<<bits(ir,1)<<' '<<bits(dest,6)<<' '<<bits(data,32)<<' '<<bits(ov,1)<<' '<<bits(orr,1)<<' '<<bits(out,32)<<'\n';
  r.tick(in,ready);for(unsigned i=0;i<64;++i)if(iv[i]&&can[i])++sent[i];
 }
 uint64_t hol=0,blocked=0;for(auto&a:r.hol)for(auto n:a)hol+=n;for(auto&a:r.blocked)for(auto n:a)blocked+=n;for(auto&a:reach)for(auto x:a)if(!x)throw std::runtime_error("COVERAGE");
 std::cout<<"PASS radix_model all4096pairs packets8192 cycles="<<cycles<<" head_block_cycles="<<hol<<" output_block_cycles="<<blocked<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
