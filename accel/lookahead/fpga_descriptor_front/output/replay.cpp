#include "output_model.hpp"
#include <deque>
#include <fstream>
#include <iostream>
#include <sstream>
#include <memory>
using namespace dfoutput;
uint64_t number(const std::string&s,unsigned base=16){if(s.find_first_of("xXzZ")!=std::string::npos)return 0;return std::stoull(s,nullptr,base);}
void check(bool b,const char*m,unsigned cycle){if(!b)throw std::runtime_error(std::string(m)+" cycle="+std::to_string(cycle));}
struct Beat{unsigned index;uint64_t due;std::array<uint64_t,4>data;};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("usage replay trace");constexpr unsigned G=16,AW=4,CELLS=121,TOTAL=(CELLS+3)/4;
 std::ifstream f(argv[1]);std::string line;Service service(G,AW);std::deque<Beat>fifo;bool active=false,done=false;unsigned next=0,issued=0,acked=0,rows=0,updates=0,events=0,epochs=0,reads=0,writes=0,acks=0,first_count=0,improvements=0,peak=0;
 while(std::getline(f,line)){std::istringstream in(line);std::vector<std::string>v;std::string token;while(in>>token)v.push_back(token);if(v.empty())continue;unsigned cycle=number(v[0],10),reset=number(v[1],10);check(v.size()==73,"TRACE_COLUMN_COUNT",cycle);++rows;
  if(reset){service=Service(G,AW);fifo.clear();active=false;done=false;next=issued=acked=0;continue;}
  unsigned init=number(v[2],10),idle=number(v[3],10),iv=number(v[4]),ir=number(v[5]),ov=number(v[6]),ordy=number(v[7]),first=number(v[8]),improved=number(v[9]);
  check(init==service.init_done(),"INIT",cycle);check(idle==(service.idle()&&!active),"IDLE",cycle);
  std::vector<std::optional<Update>>input(G);std::array<bool,8>ready{};unsigned at=10;
  for(unsigned g=0;g<G;++g){unsigned cell=number(v[at++]);uint64_t pair=number(v[at++]);if(iv>>g&1)input[g]=Update{cell,pair};}
  for(unsigned b=0;b<8;++b){unsigned cell=number(v[at++]);uint64_t pair=number(v[at++]);auto event=service.bank[b].s2;ready[b]=ordy>>b&1;
   check(bool(ov>>b&1)==event.has_value(),"EVENT_VALID",cycle);
   if(event){check(cell==event->cell&&pair==event->pair,"EVENT_PAYLOAD",cycle);check(bool(first>>b&1)==event->first&&bool(improved>>b&1)==event->improved,"EVENT_FLAGS",cycle);}
  }
  unsigned start=number(v[at++],10),startready=number(v[at++],10),wv=number(v[at++]),wr=number(v[at++]);uint64_t lines[2]={number(v[at]),number(v[at+1])};at+=2;
  std::string data[2]={v[at],v[at+1]};at+=2;unsigned av=number(v[at++]),ar=number(v[at++]),observed_done=number(v[at++],10),error=number(v[at++],10),occupancy=number(v[at++],10),ni=number(v[at++],10),na=number(v[at++],10);
  check(at==v.size(),"TRACE_END",cycle);check(!error,"ERROR",cycle);check(startready==(service.idle()&&!active&&!done&&!iv),"EXPORT_READY",cycle);check(observed_done==done,"EXPORT_DONE",cycle);
  check(occupancy==fifo.size(),"PACKING_RESERVATIONS",cycle);peak=std::max(peak,occupancy);check(ni==issued&&na==acked,"WRITE_ACK_COUNTERS",cycle);check(ar==(active?3u:0u),"ACK_READY",cycle);
  unsigned expected_wv=0;
  if(active&&!fifo.empty()&&fifo[0].due<=cycle)expected_wv=1;
  if(active&&fifo.size()>1&&fifo[1].due<=cycle&&(wr&1))expected_wv|=2;
  check(wv==expected_wv,"WRITE_VALID",cycle);
  for(unsigned k=0;k<2;++k)if(wv>>k&1){check(lines[k]==1024+fifo[k].index,"WRITE_LINE",cycle);auto s=data[k];if(s.size()<64)s=std::string(64-s.size(),'0')+s;
   for(unsigned j=0;j<4;++j)check(number(s.substr(48-16*j,16))==fifo[k].data[j],"WRITE_DATA",cycle);
  }
  unsigned take=(wv&wr&1?1:0)+(wv&wr&2?1:0),incoming=(av&1?1:0)+(av&2?1:0);unsigned space=16-fifo.size();
  if(start&&startready){active=true;done=false;next=issued=acked=0;}
  else if(active){
   bool finish=next==TOTAL&&fifo.empty()&&acked==TOTAL;
   check(incoming<=issued-acked,"ACK_BEFORE_WRITE",cycle);
   unsigned launch=std::min({2u,space,TOTAL-next});for(unsigned k=0;k<take;++k)fifo.pop_front();issued+=take;acked+=incoming;writes+=take;acks+=incoming;
   for(unsigned k=0;k<launch;++k){Beat b{next++,cycle+2,{}};for(unsigned j=0;j<4;++j){unsigned c=b.index*4+j;b.data[j]=c<CELLS?service.get(c):MISSING;}fifo.push_back(b);++reads;}
   if(finish){active=false;done=true;++epochs;}
  }
  auto step=service.tick(input,ready);
  for(unsigned g=0;g<G;++g){check(step.accepted[g]==bool(ir>>g&1),"GROUP_HANDSHAKE",cycle);updates+=step.accepted[g];}
  for(auto&e:step.completion)if(e){++events;first_count+=e->first;improvements+=e->improved;}
 }
 check(epochs==2&&updates==1024&&events==1024&&peak==16&&reads==62&&writes==62&&acks==62,"TERMINAL_COUNTS",rows);
 std::cout<<"{\"status\":\"PASS\",\"cycles_checked\":"<<rows<<",\"updates\":"<<updates<<",\"retired\":"<<events<<",\"first\":"<<first_count<<",\"improved\":"<<improvements<<",\"export_beats\":"<<writes<<",\"actual_ACKs\":"<<acks<<",\"packing_peak\":"<<peak<<",\"epochs\":"<<epochs<<",\"scope\":\"exact groupRR, synchronousRAM forwarding/stall and finite export/ACK trace; not fullkernel timing\"}\n";
 }catch(const std::exception&e){std::cerr<<"REPLAY_FAIL "<<e.what()<<'\n';return 1;}
}
