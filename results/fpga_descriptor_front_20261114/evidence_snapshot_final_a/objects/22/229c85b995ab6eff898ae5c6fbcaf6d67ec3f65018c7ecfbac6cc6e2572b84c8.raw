#include "ack_model.hpp"
#include <fstream>
#include <sstream>
#include <iostream>
uint64_t num(const std::string&s){if(s.find_first_of("xXzZ")!=std::string::npos)return 0;return std::stoull(s,nullptr,16);}
uint64_t field(std::string s,unsigned slot,unsigned width){if(s.size()<width)s=std::string(width-s.size(),'0')+s;return num(s.substr(width-16*(slot+1),16));}
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("usage replay_ack trace");dfoutput::AckCollector<uint64_t>a;std::ifstream f(argv[1]);std::string line;unsigned rows=0,accepted=0,retired=0,peak=0;
 while(std::getline(f,line)){std::istringstream ss(line);unsigned cycle,reset;std::string vis,irs,ovs,ors,ids,ods;ss>>cycle>>reset>>vis>>irs>>ovs>>ors>>ids>>ods;++rows;
  if(reset){a=dfoutput::AckCollector<uint64_t>();continue;}
  uint32_t iv=num(vis),ir=num(irs);unsigned ov=num(ovs),ordy=num(ors),count=0;std::vector<std::optional<uint64_t>>in(32);std::array<bool,2>ready{bool(ordy&1),bool(ordy&2)};
  for(unsigned s=0;s<32;++s)if(iv>>s&1){in[s]=field(ids,s,512);++count;}peak=std::max(peak,count);auto takes=a.input_ready(in,ready);
  for(unsigned s=0;s<32;++s){if(takes[s]!=bool(ir>>s&1))throw std::runtime_error("ACK_IR cycle="+std::to_string(cycle));accepted+=takes[s];}
  for(unsigned k=0;k<2;++k){if(bool(ov>>k&1)!=a.out[k].has_value())throw std::runtime_error("ACK_OV");if(a.out[k]&&field(ods,k,32)!=*a.out[k])throw std::runtime_error("ACK_DATA");if(a.out[k]&&ready[k])++retired;}
  a.tick(in,ready);
 }
 if(accepted!=62||retired!=62||peak<3)throw std::runtime_error("ACK_TRACE_TERMINAL");
 std::cout<<"{\"status\":\"PASS\",\"cycles_checked\":"<<rows<<",\"source_ACKs\":"<<accepted<<",\"export_ACKs\":"<<retired<<",\"simultaneous_source_peak\":"<<peak<<",\"registered_slots\":2}\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
