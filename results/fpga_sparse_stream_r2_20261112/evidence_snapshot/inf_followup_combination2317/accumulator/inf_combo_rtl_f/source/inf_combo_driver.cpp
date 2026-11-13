#include "Vinf_combo_owner.h"
#include "verilated.h"
#include "pending17.hpp"
#include <array>
#include <vector>
#include <deque>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <random>
using Row=std::array<uint64_t,4>;constexpr uint64_t INF=pending17::INF;
void req(bool b,const char*s){if(!b)throw std::runtime_error(s);}
template<class A>uint64_t get(const A&a,unsigned bit,unsigned n){uint64_t x=0;for(unsigned i=0;i<n;++i)x|=uint64_t((a[(bit+i)/32]>>((bit+i)%32))&1)<<i;return x;}
template<class A>void put(A&a,unsigned bit,unsigned n,uint64_t x){for(unsigned i=0;i<n;++i){unsigned j=(bit+i)/32,k=(bit+i)%32;a[j]=(a[j]&~(1u<<k))|(((x>>i)&1)<<k);}}
struct E{uint32_t n;uint64_t p;};struct O{unsigned n,op,arg;uint64_t p;};struct R{unsigned client,line;bool write;Row data;uint64_t due;};struct Expected{uint64_t old;unsigned status,mask,arg;};
int main(int argc,char**argv){try{
 req(argc==4,"args");std::string name=argv[1];constexpr unsigned CAP=1<<20;
 std::vector<Row> label(CAP,Row{INF,INF,INF,INF}),scratch(CAP),expected=label;std::vector<unsigned char> sv(CAP),touch(CAP);std::vector<unsigned> lines;
 std::array<std::vector<E>,2> events;std::array<std::vector<O>,2> ops;std::vector<pending17::Old> old(256);std::vector<pending17::Packed> packed(256);
 auto add=[&](E e){auto l=e.n/4;req(l<CAP&&!(l&31),"owner0/MAX_N contract");auto b=(l>>5)&1;events[b].push_back(e);if(!touch[l]){touch[l]=1;lines.push_back(l);}expected[l][e.n&3]=std::min(expected[l][e.n&3],e.p);};
 bool overflow_expected=name=="spill2049";unsigned wave_count=name=="two_waves"?2:1;
 if(name=="maxn_overflow"){}else if(name=="operations"){
  for(unsigned b=0;b<2;++b){unsigned base=b*128;for(unsigned k=0;k<200;++k){unsigned n=base+k%4;ops[b].push_back({n,5,0,0});ops[b].push_back({n,2,0x1001,0});ops[b].push_back({n,2,0x1000,0});ops[b].push_back({n,3,0,0});}}
 }else if(name=="empty"){}
 else if(name=="capacity4096"||name=="capacity4097"||name=="spill2048"||overflow_expected){unsigned n=name=="capacity4096"?4096:name=="capacity4097"?4097:name=="spill2048"?6144:6145;for(unsigned i=0;i<n;++i)for(unsigned b=0;b<2;++b)add({(i*64+b*32)*4,0x3f80000040000000ull});}
 else if(name=="directed"||name=="two_waves"){
  std::mt19937 gen(1729);for(unsigned i=0;i<10000;++i)for(unsigned b=0;b<2;++b){unsigned slot=i<512?0:gen()%12;add({(slot*64*1024+b*32)*4+i%4,(uint64_t(0x3f800000+gen()%16)<<32)|(0x40000000+gen()%256)});}
 }else{
  std::ifstream f(name,std::ios::binary);uint64_t h[6];f.read((char*)h,sizeof(h));req(h[0]==0x5741564541434331ull,"magic");
  for(uint64_t i=0;i<h[4];++i){E e;f.read((char*)&e.n,4);f.read((char*)&e.p,8);if(!((e.n/4)&31))add(e);}
  for(uint64_t i=0;i<h[5];++i){unsigned l,mask;Row before,final;f.read((char*)&l,4);f.read((char*)&mask,4);f.read((char*)before.data(),32);f.read((char*)final.data(),32);if(!(l&31)){label[l]=before;for(unsigned k=0;k<4;++k){expected[l][k]=std::min(before[k],expected[l][k]);req(expected[l][k]==final[k],"recorded complete row");}}}req(bool(f),"input truncated");
 }
 if(name=="concurrent_word")for(unsigned b=0;b<2;++b){unsigned base=b*128;for(unsigned k=0;k<10000;++k){unsigned n=base+k%4;ops[b].push_back({n,5,0,0});ops[b].push_back({n,2,0x1001,0});ops[b].push_back({n,2,0x1000,0});ops[b].push_back({n,3,0,0});}}
 Vinf_combo_owner d;d.node_count=name=="maxn_overflow"?(1u<<22)+1:1u<<22;d.clk=0;d.reset=1;d.in_valid=0;d.op_valid=0;d.flush=0;d.rsp_valid=0;d.mem_ready=0;d.event_ready=0;
 for(unsigned i=0;i<3;++i){d.clk=0;d.eval();d.clk=1;d.eval();}d.reset=0;
 std::array<size_t,2> pos{},oppos{};std::array<std::deque<Expected>,2> replies;std::vector<R> pending;std::array<bool,4> outstanding{};uint64_t tx[4][2]={},accept=0,dual=0,commit_events=0,first=0,last=0,reverse=0;unsigned rr=0,wave=0;bool passed=false;
 std::ofstream cycles(argv[2]);cycles<<"cycle,accept,retired0,retired1,requests,responses,events,credits,overflow\n";
 for(uint64_t t=0;t<5000000;++t){
  d.clk=0;d.in_valid=d.op_valid=0;d.in_node=d.op_node=0;for(auto &x:d.in_pair)x=0;for(auto &x:d.op_pair)x=0;d.op_code=0;d.op_arg=0;
  for(unsigned b=0;b<2;++b){if(pos[b]<events[b].size()){auto e=events[b][pos[b]];d.in_valid|=1<<b;d.in_node|=uint64_t(e.n)<<(b*32);put(d.in_pair,b*64,64,e.p);}if(oppos[b]<ops[b].size()){auto o=ops[b][oppos[b]];d.op_valid|=1<<b;d.op_node|=uint64_t(o.n)<<(b*22);d.op_code|=o.op<<(b*3);d.op_arg|=uint64_t(o.arg)<<(b*28);put(d.op_pair,b*64,64,o.p);}}
  bool ops_done=oppos[0]==ops[0].size()&&oppos[1]==ops[1].size()&&replies[0].empty()&&replies[1].empty();
  d.flush=pos[0]==events[0].size()&&pos[1]==events[1].size()&&(name=="concurrent_word"||ops_done);
  d.event_ready=t%29<21?3:0;d.mem_ready=0;d.rsp_valid=0;for(auto&x:d.rsp_data)x=0;d.eval();
  // Shared physical channel accepts at most ONE32B request/cycle, 32 total credits.
  if(pending.size()<32&&t%19<16)for(unsigned j=0;j<4;++j){unsigned c=(rr+j)%4;if((d.mem_valid>>c&1)&&!outstanding[c]){d.mem_ready=1<<c;rr=(c+1)%4;break;}}
  // Ready ACK with largest due stamp first: deliberate reverse completion order.
  int resp=-1;for(unsigned i=0;i<pending.size();++i)if(pending[i].due<=t&&(resp<0||pending[i].due>pending[resp].due))resp=i;
  if(resp>=0){auto&q=pending[resp];d.rsp_valid=1<<q.client;for(unsigned k=0;k<4;++k)put(d.rsp_data,q.client*256+k*64,64,q.data[k]);}
  d.eval();unsigned a=d.in_valid&d.in_ready,oa=d.op_valid&d.op_ready,m=d.mem_valid&d.mem_ready,rv=d.rsp_valid&d.rsp_ready,ev=d.event_valid&d.event_ready;
  for(unsigned b=0;b<2;++b){if(a>>b&1){++pos[b];++accept;if(!first)first=t;last=t;}if(oa>>b&1){auto o=ops[b][oppos[b]++];Expected e{old[o.n].label,0,0,0};e.status=pending17::both(old[o.n],packed[o.n],o.op,o.p,o.arg);e.mask=(o.op!=2&&(e.status&1))?1u<<(o.n&3):0;e.arg=((packed[o.n].pv&65535)<<12)|(packed[o.n].label>>52);replies[b].push_back(e);expected[o.n/4][o.n&3]=old[o.n].label;}
   if(ev>>b&1){if(!replies[b].empty()){auto e=replies[b].front();replies[b].pop_front();if(e.mask){unsigned sector=__builtin_ctz(e.mask);req(get(d.event_arguments,b*112+sector*28,28)==e.arg,"directory event argument");}req(get(d.old_label,b*64,64)==e.old,"old atomic label");req(((d.event_status>>(b*4))&15)==e.status,"pending op status");req(((d.append_mask>>(b*4))&15)==e.mask,"pending append mask");}else ++commit_events;}}
  dual+=a==3;
  if(rv){req(resp>=0,"response id");auto q=pending[resp];if(q.write){if(q.client%2)label[q.line]=q.data;else{scratch[q.line]=q.data;sv[q.line]=1;}}outstanding[q.client]=false;if(resp)++reverse;pending.erase(pending.begin()+resp);}
  if(m){unsigned c=__builtin_ctz(m);unsigned l=get(d.mem_line,c*20,20);bool wr=d.mem_write>>c&1;req(l<CAP,"memory capacity");req(!outstanding[c],"client credit");Row data;
   if(wr)for(unsigned k=0;k<4;++k)data[k]=get(d.mem_data,c*256+k*64,64);else if(c%2)data=label[l];else{req(sv[l],"uninitialized first-spill read");data=scratch[l];}
   pending.push_back({c,l,wr,data,t+8+((c*17+t)%29)});outstanding[c]=true;++tx[c][wr];}
  cycles<<t<<','<<a<<','<<uint32_t(d.retired)<<','<<uint32_t(d.retired>>32)<<','<<m<<','<<rv<<','<<ev<<','<<pending.size()<<','<<unsigned(d.overflow)<<'\n';d.clk=1;d.eval();
  if(d.address_error){req(name=="maxn_overflow","unexpected node capacity/owner error");passed=true;break;}
  if(d.overflow){req(overflow_expected,"unexpected spill overflow");passed=true;break;}
  if(d.done==3&&pending.empty()&&replies[0].empty()&&replies[1].empty()&&ops_done){
   req(!overflow_expected,"missing overflow");for(auto l:lines)req(label[l]==expected[l],"full row output differential");
   if(name=="operations")for(unsigned n=0;n<256;++n)req(label[n/4][n&3]==expected[n/4][n&3],"operation label differential");
   if(++wave<wave_count){for(auto &bank:events)for(auto&e:bank){e.p+=0x100000000ull;expected[e.n/4][e.n&3]=std::min(expected[e.n/4][e.n&3],e.p);}pos={};std::fill(sv.begin(),sv.end(),0);}else{passed=true;break;}
  }
 }
 req(passed,"timeout");if(!overflow_expected&&name!="maxn_overflow"){req(d.retired==d.accepted,"candidate conservation");req(d.op_retired==d.op_accepted,"atomic retirement conservation");req(commit_events==wave_count*lines.size(),"unique line commit conservation");}
 std::ofstream out(argv[3]);out<<"line,sector,actual,expected\n";for(auto l:lines)for(unsigned k=0;k<4;++k)out<<l<<','<<k<<','<<label[l][k]<<','<<expected[l][k]<<'\n';
 uint64_t total=0;for(auto&row:tx)for(auto x:row)total+=x;
 std::cout<<"{\"passed\":true,\"expected_capacity_rejection\":"<<(overflow_expected?"true":"false")<<",\"accepted\":"<<accept<<",\"dual_accept_cycles\":"<<dual<<",\"accept_span_cycles\":"<<last-first+1<<",\"unique_commit_events\":"<<commit_events<<",\"reverse_ack_completions\":"<<reverse<<",\"physical_requests32B\":"<<total<<",\"spill_peak0\":"<<(d.spill_peak&4095)<<",\"spill_peak1\":"<<(d.spill_peak>>12)<<",\"board_measured\":false}\n";
}catch(std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
