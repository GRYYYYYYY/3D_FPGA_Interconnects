#include "Vgraph_top.h"
#include "verilated.h"
#include <array>
#include <fstream>
#include <sstream>
#include <vector>
#include <iostream>
#include <iomanip>
#include <cstring>
#include <stdexcept>
#include <filesystem>
using Line=std::array<uint32_t,8>;
struct Request{bool valid=false,write=false;uint32_t line=0,mask=0,id=0;uint64_t due=0;Line data{};};
struct Response{bool valid=false;int slot=-1;};
uint32_t bits(const uint32_t* a,unsigned off,unsigned n){uint64_t v=a[off/32];if(off%32+n>32)v|=uint64_t(a[off/32+1])<<32;return(v>>(off%32))&((uint64_t(1)<<n)-1);}
void put(uint32_t*a,unsigned off,unsigned n,uint32_t val){for(unsigned b=0;b<n;++b){auto&x=a[(off+b)/32];uint32_t m=1u<<((off+b)%32);x=(x&~m)|((val>>b&1)?m:0);}}
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("graph_driver DIR owners latency");std::string dir=argv[1];unsigned owners=std::stoul(argv[2]),lat=std::stoul(argv[3]);
 Verilated::commandArgs(argc,argv);Vgraph_top d;
 std::ifstream cfg(dir+"/config.txt");unsigned lines;cfg>>d.nodes>>d.jobs>>d.cells>>lines;
 cfg>>d.base_row>>d.base_edge>>d.base_node>>d.base_cost>>d.base_cell>>d.base_job>>d.base_label>>d.base_prop>>d.base_pending>>d.base_closed>>d.base_output;if(!cfg)throw std::runtime_error("config");
 std::vector<Line> mem(lines);std::ifstream image(dir+"/memory.hex");std::string s;for(auto&l:mem){image>>s;if(s.size()!=64)throw std::runtime_error("image");for(unsigned j=0;j<8;++j)l[j]=std::stoul(s.substr((7-j)*8,8),nullptr,16);}
 std::vector<uint64_t> expected(d.jobs*d.cells);std::ifstream gold(dir+"/expected.hex");for(auto&v:expected){gold>>s;v=std::stoull(s,nullptr,16);}if(!gold)throw std::runtime_error("gold");
 std::array<std::array<Request,64>,32> pending{};std::array<Response,32> response{};
 std::array<std::array<uint64_t,16>,32> bank{};std::array<uint64_t,32> link{},last{};std::array<bool,32> direction{};
 std::ofstream states(dir+"/states.csv"),transactions(dir+"/transactions.csv");states<<"cycle,qid,waves,state\n";transactions<<"cycle,event,channel,id,write,line\n";
 unsigned previous=255,oldq=~0u;uint64_t reads=0,writes=0,tick=0;unsigned high=0;bool passed=false;
 for(;tick<300000000;++tick){
 d.clk=0;d.rst=tick<4;d.start=tick==4;d.eval();d.mem_ready=0;d.rsp_valid=0;
 std::array<int,32> free{};for(unsigned c=0;c<32;++c){free[c]=-1;unsigned occ=0;for(int k=63;k>=0;--k){if(!pending[c][k].valid)free[c]=k;else ++occ;}high=std::max(high,occ);
 uint32_t line=d.mem_line[c];if(free[c]>=0&&tick>=link[c]&&tick>=bank[c][line/32%16]&&((bool(d.mem_write>>c&1)==direction[c])||tick>=last[c]+4))d.mem_ready|=1u<<c;
 if(response[c].valid){d.rsp_valid|=1u<<c;auto&r=pending[c][response[c].slot];put(d.rsp_id,c*13,13,r.id);std::copy(r.data.begin(),r.data.end(),d.rsp_data+c*8);}
 }
 d.eval();
 auto qmask=d.mem_valid&d.mem_ready,rmask=d.rsp_valid&d.rsp_ready;std::array<Request,32> incoming{};std::array<int,32> chosen{};
 for(unsigned c=0;c<32;++c){chosen[c]=-1;if(!response[c].valid)for(unsigned k=0;k<64;++k)if(pending[c][k].valid&&pending[c][k].due<=tick)chosen[c]=k;
 if(qmask>>c&1){auto&r=incoming[c];r.valid=true;r.write=d.mem_write>>c&1;r.line=d.mem_line[c];r.mask=d.mem_mask[c];r.id=bits(d.mem_id,c*13,13);r.due=tick+lat;
 if(r.line>=lines||r.line%32!=c)throw std::runtime_error("address/channel");
 for(auto&p:pending[c])if(p.valid&&p.line==r.line&&(p.write||r.write))throw std::runtime_error("RAW ordering");
 if(r.write)std::copy(d.mem_data+c*8,d.mem_data+c*8+8,r.data.begin());else r.data=mem[r.line];
 }
 }
 if(d.state!=previous||d.qid!=oldq){states<<tick<<','<<d.qid<<','<<d.waves<<','<<unsigned(d.state)<<'\n';previous=d.state;oldq=d.qid;}
 d.clk=1;d.eval();
 for(unsigned c=0;c<32;++c){
 if(qmask>>c&1){auto&r=incoming[c];pending[c][free[c]]=r;link[c]=tick+2;bank[c][r.line/32%16]=tick+8;last[c]=tick;direction[c]=r.write;if(r.write)++writes;else ++reads;transactions<<tick<<",Q,"<<c<<','<<r.id<<','<<r.write<<','<<r.line<<'\n';}
 if(rmask>>c&1){auto&r=pending[c][response[c].slot];if(r.write)for(unsigned b=0;b<32;++b)if(r.mask>>b&1){uint32_t mask=255u<<(b%4*8);mem[r.line][b/4]=(mem[r.line][b/4]&~mask)|(r.data[b/4]&mask);}r.valid=false;response[c].valid=false;transactions<<tick<<",R,"<<c<<','<<r.id<<','<<r.write<<','<<r.line<<'\n';}
 if(chosen[c]>=0)response[c]={true,chosen[c]};
 }
 if(d.error)throw std::runtime_error("DUT error state="+std::to_string(d.state));
 if(tick%1000000==0)std::cout<<"PROGRESS "<<tick<<" q="<<d.qid<<" waves="<<d.waves<<std::endl;
 if(d.done){passed=true;++tick;break;}
 }
 if(!passed)throw std::runtime_error("watchdog");for(auto&ch:pending)for(auto&r:ch)if(r.valid)throw std::runtime_error("early done");
 for(unsigned o=0;o<owners;++o)if(d.accepted[o]!=d.retired[o])throw std::runtime_error("lost candidate");
 std::ofstream actual(dir+"/actual.hex");actual<<std::hex<<std::setfill('0');unsigned diffs=0;for(unsigned x=0;x<expected.size();++x){auto&l=mem[d.base_output+x/4];uint64_t v=(uint64_t(l[x%4*2+1])<<32)|l[x%4*2];actual<<std::setw(16)<<v<<'\n';diffs+=v!=expected[x];}actual.close();
 std::ofstream summary(dir+"/summary.json");summary<<"{\"owners\":"<<owners<<",\"jobs\":"<<d.jobs<<",\"cycles\":"<<tick<<",\"waves\":"<<d.waves<<",\"latency_cycles\":"<<lat<<",\"reads32B\":"<<reads<<",\"writes32B\":"<<writes<<",\"compared_pairs\":"<<expected.size()<<",\"differences\":"<<diffs<<",\"channel_outstanding_hwm\":"<<high<<"}\n";
 if(diffs)throw std::runtime_error("output differences="+std::to_string(diffs));std::cout<<"TEST_PASS complete batch cycles="<<tick<<std::endl;d.final();
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
