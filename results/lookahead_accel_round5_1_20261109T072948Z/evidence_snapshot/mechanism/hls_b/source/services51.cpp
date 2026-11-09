#include "api51.hpp"
#include "services51.hpp"
extern "C" void lookahead_services51(const uint32_t row[33],const on4::NodeWord nodes[32],const uint32_t edges[128],const on4::CostWord costs[64],const uint32_t sources[8],const int32_t cells[256],const uint32_t targets[8],on4::CostWord output[64],la::Stats stats[8],unsigned n,unsigned ne,unsigned nj,unsigned nk,unsigned nc,unsigned capacity,unsigned command,unsigned graph_version,unsigned cost_version,bool early,unsigned heap_hold,unsigned map_hold,unsigned& status,unsigned hm0[8],unsigned hm1[8],unsigned em[8],unsigned mm[8],unsigned cm[8]){
#pragma HLS INTERFACE ap_memory port=row
#pragma HLS INTERFACE ap_memory port=nodes
#pragma HLS INTERFACE ap_memory port=edges
#pragma HLS INTERFACE ap_memory port=costs
#pragma HLS INTERFACE ap_memory port=sources
#pragma HLS INTERFACE ap_memory port=cells
#pragma HLS INTERFACE ap_memory port=targets
#pragma HLS INTERFACE ap_memory port=output
#pragma HLS INTERFACE ap_memory port=stats
#pragma HLS INTERFACE ap_memory port=hm0
#pragma HLS INTERFACE ap_memory port=hm1
#pragma HLS INTERFACE ap_memory port=em
#pragma HLS INTERFACE ap_memory port=mm
#pragma HLS INTERFACE ap_memory port=cm
 using namespace svc51;
 static uint32_t sr[N+1],se[E],ss[J],st[J];static NodeWord sn[N],mn[N];static CostWord sk[64];static int32_t sc[J*N];
#pragma HLS BIND_STORAGE variable=sr type=ram_2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=se type=ram_2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=sn type=ram_2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=mn type=ram_2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=sk type=ram_2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=sc type=ram_2p impl=bram latency=1
 static bool loaded=false;static unsigned gv=0,cv=0,gen=0,sn_saved=0,se_saved=0,sj_saved=0,sk_saved=0,sc_saved=0;
 status=la::INVALID_INPUT;
 if(command!=1)loaded=false;
 if(command>2||!n||n>N||ne>E||nj>J||!nk||nk>64||nc>C||!capacity||capacity>H)return;
 if(command!=1){
  bool bad=false;unsigned prev=0;
  for(unsigned i=0;i<=n;++i){unsigned v=row[i];sr[i]=v;if(v>ne||v<prev||(!i&&v)||(i==n&&v!=ne))bad=true;prev=v;}
  for(unsigned i=0;i<nk;++i)sk[i]=costs[i];
  for(unsigned i=0;i<n;++i){sn[i]=nodes[i];mn[i]=nodes[i];auto a=node(nodes[i]);if(a.cost>=nk||a.type>2||a.segment_kind< -1||a.segment_kind>1)bad=true;else if(a.inter&&a.type!=2){auto c=cost(sk[a.cost]);if(!la::numeric(c.delay)||!la::numeric(c.congestion)||((bits(c.delay)>>23)&255)>240||((bits(c.congestion)>>23)&255)>240)bad=true;}}
  for(unsigned i=0;i<ne;++i){se[i]=edges[i];if(se[i]>=n)bad=true;}
  for(unsigned q=0;q<nj;++q){ss[q]=sources[q];if(ss[q]>=n)bad=true;bool mask[C]={};unsigned count=0;for(unsigned u=0;u<n;++u){int c=cells[q*N+u];sc[q*N+u]=c;if(c< -1||c>=int(nc))bad=true;else if(c>=0&&node(sn[u]).type==1&&!mask[c]){mask[c]=true;++count;}}st[q]=count;if(targets[q]!=count)bad=true;}
  if(bad)return;
  gv=graph_version;cv=cost_version;sn_saved=n;se_saved=ne;sj_saved=nj;sk_saved=nk;sc_saved=nc;loaded=true;
 }
 if(!loaded||gv!=graph_version||cv!=cost_version||n!=sn_saved||ne!=se_saved||nj!=sj_saved||nk!=sk_saved||nc!=sc_saved)return;
 if(command!=0){++gen;network(sr,sn,mn,se,sk,ss,sc,st,output,stats,n,nj,nc,capacity,gen,early,heap_hold,map_hold,hm0,hm1,em,mm,cm);}
 status=la::OK;
}
