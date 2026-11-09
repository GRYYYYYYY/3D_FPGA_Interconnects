#include "api51.hpp"
#include "strict_heap.hpp"
#include <iostream>
#include <cstring>
#include <vector>
#include <cstdlib>
using namespace on4;
uint32_t row[33]={},edges[128]={},sources[8]={},targets[8]={};NodeWord nodes[32];CostWord costs[64],output[64];int32_t cells[256];la::Stats stats[8];unsigned hm0[8],hm1[8],em[8],mm[8],cm[8],status;
uint64_t stats_words[48]={};
unsigned n=12,ne=0,nj=3,nk=2,nc=2,cap=129,gv=1,cv=1;
void call(unsigned command,bool early,unsigned hh=0,unsigned mh=0){lookahead_services51(row,nodes,edges,costs,sources,cells,targets,output,stats_words,n,ne,nj,nk,nc,cap,command,gv,cv,early,hh,mh,status,hm0,hm1,em,mm,cm);for(unsigned q=0;q<nj&&q<8;++q)stats[q]={stats_words[q*6],stats_words[q*6+1],stats_words[q*6+2],stats_words[q*6+3],stats_words[q*6+4],unsigned(stats_words[q*6+5])};}
void expect(bool x,const char* why){if(!x){std::cerr<<"FAIL "<<why<<'\n';std::exit(1);}}
void golden(bool early){for(unsigned q=0;q<nj;++q){float vis[32];bool exp[32]={};std::fill(vis,vis+32,-1);la::Cost out[8];for(auto& v:out)v={la::missing(),la::missing()};la::Entry hp[129];unsigned sz=0,remaining=targets[q];la::Stats st={};if(!early||remaining){la::push(hp,sz,{sources[q],0,0});st.pushes=st.peak=1;}while(sz){auto cur=la::pop(hp,sz);++st.pops;if(exp[cur.node])continue;int c=cells[q*32+cur.node];if(node(nodes[cur.node]).type==1&&c>=0){bool first=out[c].delay!=out[c].delay;la::record(out[c],cur);if(early&&first&&!--remaining)break;}for(unsigned i=row[cur.node];i<row[cur.node+1];++i){++st.edges;unsigned dst=edges[i];int a=la::eligible(node(nodes[cur.node]),node(nodes[dst]));if(!a)continue;if(a<0)break;if(exp[dst])continue;auto co=cost(costs[node(nodes[dst]).cost]);la::Entry v={dst,cur.delay+co.delay,cur.congestion+co.congestion};if(!la::numeric(v.delay)||!la::numeric(v.congestion)){st.status=la::UNSUPPORTED_NUMERIC;break;}if(vis[dst]>=0&&vis[dst]<v.delay)continue;if(sz==cap){st.status=la::QUEUE_OVERFLOW;break;}vis[dst]=v.delay;la::push(hp,sz,v);++st.pushes;if(sz>st.peak)st.peak=sz;}if(st.status)break;exp[cur.node]=true;++st.expanded;}for(unsigned c=0;c<nc;++c)expect(pack_cost(out[c])==output[q*8+c],"map bits");expect(st.pushes==stats[q].pushes&&st.pops==stats[q].pops&&st.edges==stats[q].edges&&st.expanded==stats[q].expanded&&st.peak==stats[q].peak&&st.status==stats[q].status,"strict stats");}}
void setup(){std::fill(cells,cells+256,-1);for(unsigned i=0;i<n;++i)nodes[i]=pack_node({0,i%2,1,-1});nodes[10]=pack_node({1,0,1,-1});nodes[11]=pack_node({2,0,1,-1});costs[0]=pack_cost({1,2});costs[1]=pack_cost({2,1});ne=0;for(unsigned u=0;u<n;++u){row[u]=ne;if(u==0){for(unsigned v=1;v<=9;++v)edges[ne++]=v;edges[ne++]=1;edges[ne++]=2;}else if(u<10){edges[ne++]=10;if(u==2){edges[ne++]=11;edges[ne++]=3;}}}row[n]=ne;for(unsigned q=0;q<nj;++q){sources[q]=q==1?1:0;cells[q*32+10]=0;targets[q]=1;}}
int main(){setup();call(2,false,24,9);expect(status==0,"load-run");golden(false);std::cout<<"PASS full backpressure\n";call(1,true,24,9);expect(status==0,"warm early");golden(true);std::cout<<"PASS warm early\n";
#ifndef LA51_RTL_SHORT
 call(1,false);golden(false);auto saved_cost=costs[0];costs[0]=pack_cost({la::missing(),la::missing()});call(1,false);expect(status==0,"warm ignores external poison");costs[0]=saved_cost;golden(false);cap=2;call(1,false,24,9);golden(false);expect(stats[0].status==la::QUEUE_OVERFLOW,"overflow");cap=129;
 ++gv;call(1,false);expect(status==la::INVALID_INPUT,"version mismatch");call(0,false);expect(status==0,"load only");call(1,false);golden(false);
 unsigned saved=n;n=33;call(0,false);expect(status==la::INVALID_INPUT,"capacity invalidates");n=saved;call(1,false);expect(status==la::INVALID_INPUT,"failed reload invalidates");call(2,false);golden(false);
 --row[n];call(2,false);expect(status==la::INVALID_INPUT,"incomplete CSR");++row[n];call(1,false);expect(status==la::INVALID_INPUT,"incomplete load invalidates");call(2,false);golden(false);
 costs[0]=pack_cost({-1,2});++cv;call(2,true);expect(status==la::INVALID_INPUT,"numeric admission");setup();++cv;call(2,true);golden(true);
 for(unsigned q=0;q<nj;++q){targets[q]=0;cells[q*32+10]=-1;}++gv;call(2,true);golden(true);expect(stats[0].pushes==0,"empty targets");nj=0;call(2,true);expect(status==0,"empty batch");
 std::cout<<"PASS overflow versions failed-reload numeric empty-target empty-batch\n";
#endif
 return 0;}
