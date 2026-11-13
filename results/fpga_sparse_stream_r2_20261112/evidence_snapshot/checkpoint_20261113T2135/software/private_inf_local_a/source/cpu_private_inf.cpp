#include "bucket61.hpp"
#include <omp.h>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <array>
#include <limits>
#include <cstring>
using Pair=uint64_t;
constexpr Pair INF=0x7f8000007f800000ull, MISSING=0x7fc000007fc00000ull;
static Pair pack(la::Cost p){return uint64_t(la61::bits(p.delay))<<32|la61::bits(p.congestion);}
static Pair add(Pair a,Pair b){uint32_t ad=a>>32,ac=a,bd=b>>32,bc=b;float x,y,z,t;memcpy(&x,&ad,4);memcpy(&y,&bd,4);memcpy(&z,&ac,4);memcpy(&t,&bc,4);x=x+y;z=z+t;memcpy(&ad,&x,4);memcpy(&ac,&z,4);if((ad&0x7f800000)==0x7f800000||(ac&0x7f800000)==0x7f800000)throw std::runtime_error("numeric overflow");return Pair(ad)<<32|ac;}
struct Prepared {
 std::vector<uint64_t> row;std::vector<uint32_t> edge;std::vector<uint32_t> targets;
 explicit Prepared(const la::Workload&w){la61::Prepared c(w);targets=c.targets;row.reserve(w.h.nodes+1);edge.reserve(w.h.edges);
  if(w.h.nodes>=(1u<<28)||w.h.costs>16)throw std::runtime_error("representation admission");
  for(unsigned n=0;n<w.h.nodes;++n){row.push_back(edge.size());for(auto i=w.row[n];i<w.row[n+1];++i){auto v=w.edge[i].dst;int e=la::eligible(w.node[n],w.node[v]);if(e<0)break;if(!e)continue;edge.push_back(v|(w.node[v].cost<<28));}}row.push_back(edge.size());
 }
};
struct Scratch {
 static constexpr unsigned CAP=524288,NIL=~0u;
 struct Member{uint32_t node,version,next;};
 std::vector<Pair> label,prop;std::vector<uint32_t> pending,version;std::vector<uint8_t> marked,seen;
 std::vector<Member> member;std::vector<uint32_t> free_ids,active,changed;
 std::array<uint32_t,32768> head,tail;std::array<uint64_t,64> bitmap;uint64_t groups;unsigned used;
 Scratch(unsigned n,unsigned cells):label(n),prop(n),pending(n),version(n),marked(n),seen(cells),member(CAP),free_ids(CAP){active.reserve(CAP);changed.reserve(n);}
 unsigned minimum()const{unsigned g=__builtin_ctzll(groups);return g*64+__builtin_ctzll(bitmap[g]);}
 void append(unsigned key,unsigned n){if(used==CAP)throw std::runtime_error("member overflow");unsigned p=free_ids[used++],h=key*8+((n>>2)&7);member[p]={n,++version[n],NIL};pending[n]=key;if(head[h]==NIL)head[h]=p;else member[tail[h]].next=p;tail[h]=p;bitmap[key/64]|=1ull<<(key%64);groups|=1ull<<(key/64);}
 void solve(const la::Workload&w,const Prepared&p,const std::array<Pair,16>&cost,unsigned q,Pair*out){
  std::fill(label.begin(),label.end(),INF);std::fill(prop.begin(),prop.end(),INF);std::fill(pending.begin(),pending.end(),NIL);std::fill(version.begin(),version.end(),0);std::fill(marked.begin(),marked.end(),0);std::fill(seen.begin(),seen.end(),0);std::fill(out,out+w.h.cells,MISSING);
  head.fill(NIL);tail.fill(NIL);bitmap.fill(0);groups=0;used=0;for(unsigned i=0;i<CAP;++i)free_ids[i]=i;
  // Mirrors hardware initialization even when there are no targets.
  unsigned src=w.job[q].source;label[src]=0;append(0,src);if(!p.targets[q])return;
  unsigned recorded=0,waves=0;
  while(groups){if(++waves>1000000)throw std::runtime_error("wave watchdog");unsigned key=minimum();active.clear();changed.clear();bitmap[key/64]&=~(1ull<<(key%64));if(!bitmap[key/64])groups&=~(1ull<<(key/64));
   for(unsigned b=0;b<8;++b){unsigned h=key*8+b,id=head[h];head[h]=tail[h]=NIL;while(id!=NIL){auto m=member[id];free_ids[--used]=id;id=m.next;if(pending[m.node]!=key||version[m.node]!=m.version)continue;unsigned n=m.node;pending[n]=NIL;if(active.size()==CAP)throw std::runtime_error("active overflow");active.push_back(n);
    int cell=w.cell[q*w.h.nodes+n];if(w.node[n].type==1&&cell>=0){if(!seen[cell]||label[n]<out[cell])out[cell]=label[n];if(!seen[cell]){seen[cell]=1;++recorded;}}
   }}
   for(auto n:active){Pair parent=label[n];for(auto e=p.row[n];e<p.row[n+1];++e){auto desc=p.edge[e];unsigned v=desc&0xfffffff;Pair candidate=add(parent,cost[desc>>28]);if(candidate<prop[v]){prop[v]=candidate;if(!marked[v]){if(changed.size()==label.size())throw std::runtime_error("touched overflow");marked[v]=1;changed.push_back(v);}}}}
   for(auto v:changed){if(prop[v]<label[v]){label[v]=prop[v];unsigned k=label[v]>>52;if(pending[v]!=k)append(k,v);}prop[v]=INF;marked[v]=0;}
   if((!groups||minimum()!=key)&&recorded==p.targets[q])break;
  }
 }
};
int main(int argc,char**argv){try{
 if(argc<4)throw std::runtime_error("usage workload reference process [threads] [repetitions]");la::Workload w(argv[1]);Prepared p(w);unsigned threads=argc>4?std::stoul(argv[4]):8,reps=argc>5?std::stoul(argv[5]):4;
 std::vector<Scratch>s;for(unsigned t=0;t<threads;++t)s.emplace_back(w.h.nodes,w.h.cells);
 std::vector<Pair>out(w.h.jobs*w.h.cells),ref(out.size());std::ifstream f(argv[2],std::ios::binary);la::read(f,ref.data(),ref.size());for(auto &v:ref)v=v<<32|v>>32;
 std::cout<<std::setprecision(12);
 for(unsigned rep=0;rep<reps;++rep){std::array<Pair,16>cost{};int failure=0;auto start=std::chrono::steady_clock::now();for(unsigned c=0;c<w.h.costs;++c)cost[c]=pack(w.cost[c]);
  #pragma omp parallel for schedule(dynamic) num_threads(threads) reduction(max:failure)
  for(unsigned q=0;q<w.h.jobs;++q){try{s[omp_get_thread_num()].solve(w,p,cost,q,out.data()+q*w.h.cells);}catch(...){failure=1;}}
  double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();if(failure||out!=ref)throw std::runtime_error("full batch output/error mismatch");
  std::cout<<"{\"scope\":\"RESIDENT_COMPLETE_BATCH_V2\",\"backend\":\"prepared_CSR_valid_POP_private_INF_CPU\",\"process\":\""<<argv[3]<<"\",\"threads\":"<<threads<<",\"jobs\":"<<w.h.jobs<<",\"rep\":"<<rep<<",\"warmup\":"<<(rep==0?"true":"false")<<",\"resident_s\":"<<sec<<",\"output_equal\":true,\"measured_CPU\":true,\"FPGA_measurement\":false}\n"<<std::flush;
 }
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
