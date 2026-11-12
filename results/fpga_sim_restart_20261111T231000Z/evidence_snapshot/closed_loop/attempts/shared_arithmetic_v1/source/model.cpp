// Closed-loop algorithm model: inputs are graph/jobs, never golden frontiers.
// Scan controller matches graph_control.sv. All IO shares 32 finite channels.
#include "bucket61.hpp"
#include <iostream>
#include <fstream>
#include <iomanip>
#include <array>
#include <algorithm>
#include <cmath>
#include <deque>
using U=uint64_t;
enum A{ROW,EDGE,NODE,COST,CELL,JOB,LABEL,PROP,PENDING,CLOSED,OUTPUT,ARRAYS};
const char*names[]={"row","edge","node","cost","cell","job","label","proposal","pending","closed","output"};
struct Memory{
 struct Channel{U link=0,last=0;bool dir=false;std::array<U,16>bank{};std::vector<U>out;};
 std::array<Channel,32>ch;std::array<U,ARRAYS>base{},reads{},writes{};U latency,gap,bankgap=8,turn=4;unsigned hwm=0;U stalls=0;
 Memory(const la::Workload&w,U lat,U bandwidth):latency(lat){gap=(204800000000ULL+bandwidth-1)/bandwidth;U off=0;U size[]={8*(w.h.nodes+1),8*w.h.edges,16*w.h.nodes,8*w.h.costs,4*w.h.nodes*w.h.jobs,32*w.h.jobs,8*w.h.nodes,8*w.h.nodes,4*w.h.nodes,4*w.h.nodes,8*w.h.jobs*w.h.cells};for(unsigned a=0;a<ARRAYS;++a){off=(off+1023)/1024*1024;base[a]=off/32;off+=(size[a]+31)/32*32;}if(off>8589934592ULL)throw std::runtime_error("8GiB capacity");}
 U issue(A a,U byte,bool write,U earliest){U line=base[a]+byte/32;auto&c=ch[line%32];unsigned b=line/32%16;U at=std::max({earliest,c.link,c.bank[b],c.last});if(write!=c.dir)at=std::max(at,c.last+turn);
 c.out.erase(std::remove_if(c.out.begin(),c.out.end(),[&](U done){return done<=at;}),c.out.end());
 if(c.out.size()>=64){at=std::max(at,*std::min_element(c.out.begin(),c.out.end()));c.out.erase(std::remove_if(c.out.begin(),c.out.end(),[&](U done){return done<=at;}),c.out.end());}
 U ack=at+latency+1;c.out.push_back(ack);hwm=std::max<unsigned>(hwm,c.out.size());c.link=at+gap;c.bank[b]=at+bankgap;c.last=at;c.dir=write;stalls+=at-earliest;(write?writes:reads)[a]++;return ack;
 }
 // Exact aggregation of uncontended blocking scans. Each access is still 32B.
 // Preconditions ensure no hidden throughput beyond the explicit serial RTL.
 void bulk(A a,U first,U stride,U count,bool wr,U start,U step,bool validate=true){if(!count)return;if(step<latency+4||step<bankgap||step<gap)throw std::runtime_error("invalid bulk interval");
 (wr?writes:reads)[a]+=count;
 // At most the last 512 physical lines can define any channel/bank's final use.
 U keep=std::min<U>(count,512*32/std::min<U>(stride,32)+1);
 U first_t=start+2;for(auto&c:ch)for(U due:c.out)if(validate&&due>first_t)throw std::runtime_error("bulk with live memory");
 for(U i=count-keep;i<count;++i){U at=first_t+i*step,line=base[a]+(first+i*stride)/32;auto&c=ch[line%32];c.link=std::max(c.link,at+gap);if(at>=c.last){c.last=at;c.dir=wr;}c.bank[line/32%16]=std::max(c.bank[line/32%16],at+bankgap);c.out.clear();c.out.push_back(c.last+latency+1);}hwm=std::max(hwm,1u);
 }
 U io(A a,U byte,bool wr,U t){return issue(a,byte,wr,t+2)+1;}
};
struct Line{bool valid=false,dirty=false;uint32_t tag=0;std::array<la::Cost,4> data;};
struct Owners{
 unsigned n;bool f0;Memory&m;std::vector<la::Cost>home;std::vector<std::array<Line,128>>cache;std::vector<std::array<unsigned,32>>rr;std::vector<U>busy;
 U events=0,hits=0,evictions=0,front_backpressure=0;unsigned req_hwm=0,mshr_hwm=0,dirty_hwm=0;
 Owners(unsigned count,bool bypass,Memory&mm,size_t nodes):n(count),f0(bypass),m(mm),home((nodes+3)/4*4,{INFINITY,INFINITY}),cache(n),rr(n),busy(n){}
 void reset(unsigned source,bool has){std::fill(home.begin(),home.end(),la::Cost{INFINITY,INFINITY});if(has)home[source]={0,0};for(auto&c:cache)for(auto&e:c)e={};std::fill(busy.begin(),busy.end(),0);}
 U write(Line&e,U at){if(!e.valid||!e.dirty)return at;for(unsigned s=0;s<4;++s)home[e.tag*4+s]=e.data[s];e.dirty=false;dirty_hwm=std::max(dirty_hwm,1u);return m.issue(PROP,U(e.tag)*32,true,at);}
 U candidate(unsigned dst,la::Cost pair,U at){++events;req_hwm=std::max(req_hwm,1u);unsigned line=dst/4,owner=line%n,set=(line/n)%32;auto&c=cache[owner];
 U begin=std::max(at,busy[owner]);front_backpressure+=begin-at;Line*e=nullptr;if(!f0)for(unsigned w=0;w<4;++w)if(c[w*32+set].valid&&c[w*32+set].tag==line)e=&c[w*32+set];
 if(e){++hits;}else{unsigned way=rr[owner][set];for(int w=3;w>=0;--w)if(!c[w*32+set].valid)way=w;e=&c[way*32+set];bool dirty=e->valid&&e->dirty;evictions+=e->valid;
 write(*e,begin+3);*e={};e->valid=true;e->tag=line;rr[owner][set]=(way+1)%4;for(unsigned s=0;s<4;++s)e->data[s]=home[line*4+s];
 busy[owner]=m.issue(PROP,U(line)*32,false,begin+(dirty?5:3))+1;mshr_hwm=std::max(mshr_hwm,1u);}
 if(la61::less(pair,e->data[dst%4])){e->data[dst%4]=pair;e->dirty=true;}
 if(f0){busy[owner]=write(*e,std::max(begin,busy[owner])+3);e->valid=false;}
 return begin-at;
 }
 U fence(U t){U end=t+6;for(unsigned o=0;o<n;++o){U scan=std::max(t+6,busy[o]+2);std::vector<U>dirty;
 for(unsigned k=0;k<128;++k){auto&e=cache[o][k];dirty.erase(std::remove_if(dirty.begin(),dirty.end(),[&](U d){return d<=scan;}),dirty.end());
 if(e.valid&&e.dirty){if(dirty.size()==16){scan=std::max(scan,*std::min_element(dirty.begin(),dirty.end()));dirty.erase(std::remove_if(dirty.begin(),dirty.end(),[&](U d){return d<=scan;}),dirty.end());}dirty.push_back(write(e,scan+3)+2);dirty_hwm=std::max<unsigned>(dirty_hwm,dirty.size());}e.valid=false;++scan;}
 for(U done:dirty)scan=std::max(scan,done);busy[o]=scan;end=std::max(end,scan+4);}return end+2;}
};
int main(int argc,char**argv){try{
 if(argc!=8)throw std::runtime_error("model INPUT EXPECTED_BINARY OUT_PREFIX owners F0|F1 latency bandwidth");
 la::Workload w(argv[1]);la61::Prepared prep(w);unsigned owners=std::stoul(argv[4]);bool f0=std::string(argv[5])=="F0";U latency=std::stoull(argv[6]),bw=std::stoull(argv[7]);Memory m(w,latency,bw);Owners o(owners,f0,m,w.h.nodes);
 std::vector<la::Cost> label(w.h.nodes),out(w.h.jobs*w.h.cells);std::vector<uint32_t>pending(w.h.nodes),closed(w.h.nodes);
 std::ifstream ref(argv[2],std::ios::binary);std::vector<la::Cost>expected(out.size());la::read(ref,expected.data(),expected.size());
 U t=4,waves=0,closures=0,raw=0,accepted=0;std::array<U,8>phase{};std::ofstream qlog(std::string(argv[3])+".jsonl");
 auto io=[&](A a,U byte,bool wr=false){t=m.io(a,byte,wr,t);};
 auto bulk=[&](A a,U first,U stride,U count,bool wr,U step){U latest=0;for(auto&c:m.ch)for(U due:c.out)latest=std::max(latest,due);while(count&&latest>t+2){t=m.io(a,first,wr,t)+(step-latency-4);first+=stride;--count;latest=0;for(auto&c:m.ch)for(U due:c.out)latest=std::max(latest,due);}m.bulk(a,first,stride,count,wr,t,step);t+=count*step;};
 for(unsigned q=0;q<w.h.jobs;++q){U qstart=t,mark=t;io(JOB,U(q)*32);unsigned source=w.job[q].source,nt=prep.targets[q],recorded=0,entries=1;bool have=false;unsigned bucket=0;U waveq=0;auto*output=out.data()+q*w.h.cells;
 ++t;bulk(LABEL,0,32,(w.h.nodes+3)/4,true,latency+4);++t;bulk(PROP,0,32,(w.h.nodes+3)/4,true,latency+4);++t;bulk(PENDING,0,32,(w.h.nodes+7)/8,true,latency+4);++t;bulk(CLOSED,0,32,(w.h.nodes+7)/8,true,latency+4);++t;bulk(OUTPUT,U(q)*w.h.cells*8,8,w.h.cells,true,latency+4);
 std::fill(label.begin(),label.end(),la::Cost{INFINITY,INFINITY});std::fill(pending.begin(),pending.end(),UINT32_MAX);std::fill(closed.begin(),closed.end(),0);std::fill(output,output+w.h.cells,la::Cost{la::missing(),la::missing()});o.reset(source,nt);
 ++t;if(nt){io(LABEL,U(source)*8,true);io(PROP,U(source)*8,true);io(PENDING,U(source)*4,true);label[source]={0,0};pending[source]=0;}phase[0]+=t-mark;
 while(nt){if(++waveq>1000000)throw std::runtime_error("wave budget");mark=t;bulk(PENDING,0,4,w.h.nodes,false,latency+5);unsigned next=*std::min_element(pending.begin(),pending.end());++t;phase[1]+=t-mark;
 if(have&&next!=bucket){mark=t;++t;U skip=0,first=0;auto flush=[&](){if(skip){bulk(CLOSED,first*4,4,skip,false,latency+5);skip=0;}};
 for(unsigned u=0;u<w.h.nodes;++u){if(!closed[u]){if(!skip)first=u;++skip;continue;}flush();io(CLOSED,U(u)*4);io(NODE,U(u)*16);if(w.node[u].type==1){io(CELL,(U(q)*w.h.nodes+u)*4);int c=w.cell[U(q)*w.h.nodes+u];if(c>=0){io(LABEL,U(u)*8);io(OUTPUT,(U(q)*w.h.cells+c)*8);bool first=std::isnan(output[c].delay);if(first||la61::less(label[u],output[c])){++t;io(OUTPUT,(U(q)*w.h.cells+c)*8,true);output[c]=label[u];recorded+=first;}else ++t;}else ++t;}else ++t;io(CLOSED,U(u)*4,true);closed[u]=0;}
 flush();t+=2;phase[5]+=t-mark;have=false;++closures;if(recorded==nt)break;
 }
 if(next==UINT32_MAX)break;if(next>=4096)throw std::runtime_error("bucket capacity");bucket=next;have=true;++waves;mark=t;++t;
 U skip=0,first=0;auto flush=[&](){if(skip){bulk(PENDING,first*4,4,skip,false,latency+5);skip=0;}};
 for(unsigned u=0;u<w.h.nodes;++u){if(pending[u]!=bucket){if(!skip)first=u;++skip;continue;}flush();io(PENDING,U(u)*4);++t;io(PENDING,U(u)*4,true);pending[u]=UINT32_MAX;--entries;io(CLOSED,U(u)*4,true);closed[u]=1;io(NODE,U(u)*16);io(LABEL,U(u)*8);io(ROW,U(u)*8);io(ROW,U(u+1)*8);++t;
 const auto parent=label[u];for(U k=w.row[u];k<w.row[u+1];++k){++raw;io(EDGE,k*8);auto v=w.edge[k].dst;io(NODE,U(v)*16);int eligible=la::eligible(w.node[u],w.node[v]);if(eligible<=0){++t;if(eligible<0)break;continue;}io(COST,U(w.node[v].cost)*8);la::Cost pair{parent.delay+w.cost[w.node[v].cost].delay,parent.congestion+w.cost[w.node[v].cost].congestion};if(!la::numeric(pair.delay)||!la::numeric(pair.congestion))throw std::runtime_error("numeric");t+=o.candidate(v,pair,t+4);++accepted;t+=2;}
 t+=2;
 }
 flush();++t;phase[2]+=t-mark;mark=t;t=o.fence(t);phase[3]+=t-mark;mark=t;++t;
 // Each non-improving node still consumes two external 32B reads plus compare.
 U unchanged=0,begin=0;auto commit_bulk=[&](){if(!unchanged)return;U st=t,step=2*(latency+4)+1;
 // Interleaved two-array blocking scans; disjoint address ranges, no live owner traffic.
 m.bulk(PROP,begin*8,8,unchanged,false,st,step);m.bulk(LABEL,begin*8,8,unchanged,false,st+latency+4,step,false);t+=unchanged*step;unchanged=0;};
 for(unsigned v=0;v<w.h.nodes;++v){if(!la61::less(o.home[v],label[v])){if(!unchanged)begin=v;++unchanged;continue;}commit_bulk();io(PROP,U(v)*8);io(LABEL,U(v)*8);++t;io(LABEL,U(v)*8,true);label[v]=o.home[v];io(PENDING,U(v)*4);unsigned dest=la61::bits(label[v].delay)>>20;if(dest<bucket||dest>=4096)throw std::runtime_error("nonmonotone/capacity");if(pending[v]==UINT32_MAX&&++entries>524288)throw std::runtime_error("member capacity");pending[v]=dest;io(PENDING,U(v)*4,true);}
 commit_bulk();++t;phase[4]+=t-mark;
 }
 t+=2;if(memcmp(output,expected.data()+q*w.h.cells,w.h.cells*8))throw std::runtime_error("whole sample output mismatch q="+std::to_string(q));
 qlog<<"{\"qid\":"<<q<<",\"cycles\":"<<t-qstart<<",\"total_cycles\":"<<t<<",\"output_equal\":true}\n"<<std::flush;std::cout<<"q="<<q<<" cycles="<<t<<" exact\n"<<std::flush;
 }
 std::ofstream f(std::string(argv[3])+".bin",std::ios::binary);la::write(f,out.data(),out.size());std::ofstream j(std::string(argv[3])+".json");j<<"{\"owners\":"<<owners<<",\"ablation\":\""<<(f0?"F0":"F1")<<"\",\"latency_cycles\":"<<latency<<",\"bandwidth_requested\":"<<bw<<",\"bandwidth_effective\":"<<204800000000ULL/m.gap<<",\"cycles\":"<<t<<",\"jobs\":"<<w.h.jobs<<",\"waves\":"<<waves<<",\"closures\":"<<closures<<",\"raw_edges\":"<<raw<<",\"candidates\":"<<accepted<<",\"hits\":"<<o.hits<<",\"front_backpressure\":"<<o.front_backpressure<<",\"channel_outstanding_hwm\":"<<m.hwm<<",\"dirty_hwm\":"<<o.dirty_hwm<<",\"mshr_hwm\":"<<o.mshr_hwm<<",\"output_equal\":true,\"phase_cycles\":[";
 for(unsigned x=0;x<8;++x){if(x)j<<',';j<<phase[x];}j<<"],\"traffic\":{";for(unsigned a=0;a<ARRAYS;++a){if(a)j<<',';j<<'\"'<<names[a]<<"\":{\"reads32B\":"<<m.reads[a]<<",\"writes32B\":"<<m.writes[a]<<'}';}j<<"}}\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
