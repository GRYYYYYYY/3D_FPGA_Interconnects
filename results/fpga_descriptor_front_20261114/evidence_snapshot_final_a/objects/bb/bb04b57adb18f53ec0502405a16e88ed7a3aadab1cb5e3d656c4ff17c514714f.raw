#include "ack_model.hpp"
#include <fstream>
#include <iostream>
#include <iomanip>
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("usage test_ack vectors");std::ofstream o(argv[1]);dfoutput::AckCollector<uint64_t>a;std::array<unsigned,32>sent{},seen{};unsigned accepted=0,retired=0,cycles=0,full=0,peak=0;
 for(unsigned t=0;t<5000;++t){std::vector<std::optional<uint64_t>>in(32);uint32_t iv=0;for(unsigned s=0;s<32;++s)if(sent[s]<12){in[s]=0xa5a5000000000000ull|(uint64_t(s)<<16)|sent[s];iv|=1u<<s;}
  std::array<bool,2>ready{t>12&&t%7>1,t>24&&t%11>3};auto take=a.input_ready(in,ready);unsigned ir=0,ov=0,ordy=ready[0]|unsigned(ready[1])<<1;
  for(unsigned s=0;s<32;++s)if(take[s])ir|=1u<<s;for(unsigned k=0;k<2;++k)if(a.out[k])ov|=1u<<k;
  o<<std::hex<<std::setfill('0')<<std::setw(8)<<iv<<' ';for(int s=31;s>=0;--s)o<<std::setw(16)<<in[s].value_or(0);o<<' '<<ordy<<' '<<std::setw(8)<<ir<<' '<<ov<<' ';for(int k=1;k>=0;--k)o<<std::setw(16)<<a.out[k].value_or(0);o<<'\n';
  for(unsigned k=0;k<2;++k)if(a.out[k]&&ready[k]){uint64_t p=*a.out[k];unsigned s=(p>>16)&31,n=p&65535;if(n!=seen[s]++||p>>32!=0xa5a50000ull)throw std::runtime_error("ACK_ORDER_METADATA");++retired;}
  unsigned grants=0;for(unsigned s=0;s<32;++s)if(take[s]){++sent[s];++accepted;++grants;}if(grants>2)throw std::runtime_error("ACK_CAPACITY");peak=std::max(peak,grants);full+=ov==3&&!ordy;
  a.tick(in,ready);cycles=t+1;if(retired==384&&a.idle())break;
 }if(accepted!=384||retired!=384||!full||peak!=2)throw std::runtime_error("ACK_TERMINAL");
 std::cout<<"{\"status\":\"PASS\",\"cycles\":"<<cycles<<",\"accepted\":"<<accepted<<",\"retired\":"<<retired<<",\"max_grants\":"<<peak<<",\"two_holders_blocked_cycles\":"<<full<<",\"sources\":32,\"registered_holder_capacity\":2}\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
