#pragma once
#include "onchip_types4.hpp"
namespace on4 {
// No external-memory pointer or conditional cache-miss path enters this function.
template<int ID>
void search(const uint32_t row[MAX_N+1],const NodeWord nodes[MAX_N],const uint32_t edges[MAX_E],
            const CostWord costs[MAX_K],const uint32_t sources[LOCAL_J],const int32_t cells[LOCAL_J*MAX_N],
            const uint32_t targets[LOCAL_J],CostWord output[LOCAL_J*MAX_C],la::Stats stats[LOCAL_J],
            unsigned n,unsigned jobs,unsigned nc,unsigned capacity){
#pragma HLS INLINE off
    uint32_t visited[MAX_N];ap_uint<1> expanded[MAX_N];
    Word even[BANK_DEPTH],odd[BANK_DEPTH];
#pragma HLS BIND_STORAGE variable=visited type=ram_t2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=expanded type=ram_t2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=even type=ram_t2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=odd type=ram_t2p impl=bram latency=1
    SAMPLE: for(unsigned q=0;q<jobs;++q){
        RESET_LABELS: for(unsigned u=0;u<n;++u){
#pragma HLS PIPELINE II=1
            visited[u]=0xbf800000u;expanded[u]=0;
        }
        unsigned base=q*MAX_C,cell_base=q*MAX_N;
        RESET_OUTPUT: for(unsigned c=0;c<nc;++c){
#pragma HLS PIPELINE II=1
            output[base+c]=pack_cost({la::missing(),la::missing()});
        }
        la::Stats st={0,0,0,0,0,la::OK};unsigned count=0,remaining=0;
        if(LA4_EARLY)remaining=targets[q];
        if(LA4_EARLY && !remaining){stats[q]=st;continue;}
        push(even,odd,count,pack({sources[q],0,0}));st.pushes=st.peak=1;
        FLOOD: while(count){
            la::Entry cur=unpack(pop(even,odd,count));++st.pops;unsigned u=cur.node;
            if(expanded[u])continue;
            la::Node parent=node(nodes[u]);int cell=cells[cell_base+u];
            if(parent.type==1 && cell>=0){
                la::Cost old=cost(output[base+cell]);bool first=old.delay!=old.delay;
                la::record(old,cur);output[base+cell]=pack_cost(old);
                if(LA4_EARLY && first && --remaining==0)break;
            }
            unsigned end=row[u+1];
            CSR: for(unsigned i=row[u];i<end;++i){
                ++st.edges;unsigned v=edges[i];la::Node child=node(nodes[v]);
                int allowed=la::eligible(parent,child);if(!allowed)continue;if(allowed<0)break;
                if(expanded[v])continue;
                la::Cost c=cost(costs[child.cost]);
                la::Entry next={v,cur.delay+c.delay,cur.congestion+c.congestion};
                if(!la::numeric(next.delay)||!la::numeric(next.congestion)){st.status=la::UNSUPPORTED_NUMERIC;break;}
                uint32_t old=visited[v],value=bits(next.delay);
                if(!(old>>31) && old<value)continue;
                if(count==capacity){st.status=la::QUEUE_OVERFLOW;break;}
                visited[v]=value;push(even,odd,count,pack(next));++st.pushes;
                if(count>st.peak)st.peak=count;
            }
            if(st.status)break;expanded[u]=1;++st.expanded;
        }
        stats[q]=st;
    }
}

// Each template instance owns its complete static image; only LOAD touches graph AXI.
template<int ID>
void engine(const uint64_t* ext_row,const la::Node* ext_nodes,const la::Edge* ext_edges,
            const la::Cost* ext_costs,const la::Job* ext_jobs,const int32_t* ext_cells,
            la::Cost* ext_output,la::Stats* ext_stats,unsigned n,unsigned ne,unsigned nj,unsigned nk,unsigned nc,
            unsigned command,unsigned& status){
#pragma HLS INLINE off
    static uint32_t row[MAX_N+1],edges[MAX_E],sources[LOCAL_J],targets[LOCAL_J];
    static NodeWord nodes[MAX_N];static CostWord costs[MAX_K];
    static int32_t cells[LOCAL_J*MAX_N];
    CostWord output[LOCAL_J*MAX_C];la::Stats stats[LOCAL_J];
#pragma HLS BIND_STORAGE variable=row type=ram_2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=nodes type=ram_2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=edges type=ram_2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=costs type=ram_2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=cells type=ram_2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=output type=ram_t2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=stats type=ram_2p impl=bram latency=1
    static bool loaded=false;static unsigned saved_n=0,saved_e=0,saved_j=0,saved_k=0,saved_c=0;
    status=la::INVALID_INPUT;
    if(command!=1)loaded=false;
    if(!n||n>MAX_N||ne>MAX_E||nj>MAX_J||!nk||nk>MAX_K||nc>MAX_C||command>2)return;
    unsigned jobs=nj>unsigned(ID)?(nj-1-ID)/LA4_ENGINES+1:0;
    if(command!=1){
        bool bad=false;uint64_t previous=0;
        LOAD_ROW: for(unsigned i=0;i<=n;++i){
#pragma HLS PIPELINE II=1
            uint64_t x=ext_row[i];row[i]=x;
            if(x>ne||x<previous||(i==0&&x)||(i==n&&x!=ne))bad=true;previous=x;
        }
        LOAD_COST: for(unsigned i=0;i<nk;++i){
#pragma HLS PIPELINE II=1
            costs[i]=pack_cost(ext_costs[i]);
        }
        LOAD_NODE: for(unsigned i=0;i<n;++i){
#pragma HLS PIPELINE II=1
            la::Node a=ext_nodes[i];nodes[i]=pack_node(a);
            if(a.cost>=nk||a.type>2||a.segment_kind< -1||a.segment_kind>1)bad=true;
            else if(a.inter && a.type!=2){
                la::Cost c=cost(costs[a.cost]);
                // MAX_N=4096: exponent <=240 leaves >2*MAX_N accumulation headroom.
                if(!la::numeric(c.delay)||!la::numeric(c.congestion)||((bits(c.delay)>>23)&255)>240||((bits(c.congestion)>>23)&255)>240)bad=true;
            }
        }
        LOAD_EDGE: for(unsigned i=0;i<ne;++i){
#pragma HLS PIPELINE II=1
            unsigned v=ext_edges[i].dst;edges[i]=v;if(v>=n)bad=true;
        }
        LOAD_TASK: for(unsigned local=0;local<jobs;++local){
            unsigned q=ID+local*LA4_ENGINES;unsigned source=ext_jobs[q].source;
            sources[local]=source;if(source>=n)bad=true;
            bool mask[MAX_C];
#pragma HLS ARRAY_PARTITION variable=mask complete
            if(LA4_EARLY)for(unsigned c=0;c<nc;++c)mask[c]=false;
            unsigned target=0;
            LOAD_CELL: for(unsigned u=0;u<n;++u){
#pragma HLS PIPELINE II=1
                int cell=ext_cells[q*n+u];cells[local*MAX_N+u]=cell;
                if(cell< -1||cell>=int(nc))bad=true;
                else if(LA4_EARLY && node(nodes[u]).type==1 && cell>=0 && !mask[cell]){mask[cell]=true;++target;}
            }
            targets[local]=target;
        }
        if(bad)return;
        loaded=true;saved_n=n;saved_e=ne;saved_j=nj;saved_k=nk;saved_c=nc;
    }
    if(!loaded||n!=saved_n||ne!=saved_e||nj!=saved_j||nk!=saved_k||nc!=saved_c)return;
    if(command!=0){
        search<ID>(row,nodes,edges,costs,sources,cells,targets,output,stats,n,jobs,nc,ne+1);
        FLUSH_TASK: for(unsigned local=0;local<jobs;++local){
            unsigned q=ID+local*LA4_ENGINES;
            FLUSH_MAP: for(unsigned c=0;c<nc;++c){
#pragma HLS PIPELINE II=1
                ext_output[q*nc+c]=cost(output[local*MAX_C+c]);
            }
            ext_stats[q]=stats[local];
        }
    }
    status=la::OK;
}
}
