// Post-V1 metadata observer; no search, no route, exit86. Original ABI unchanged.
#include "backend.hpp"
#include <cstdio>
#include <cstdlib>
#include <vector>
extern "C" int la_backend_v1(const la::BackendInput* a,la::Cost*,la::Stats*,la::BackendMetrics*,char*,uint32_t){
 if(!a||a->version!=1)std::exit(87);
 FILE* f=std::fopen(std::getenv("GEMM_BNN_METADATA"),"wx");if(!f)std::exit(89);
 unsigned invalid=0;for(unsigned u=0;u<a->n;++u)if(a->nodes[u].inter&&a->nodes[u].type!=2){auto c=a->costs[a->nodes[u].cost];invalid+=!la::numeric(c.delay)||!la::numeric(c.congestion);}
 unsigned long long bytes=25ULL*a->n*a->nj+8ULL*a->nj*a->nc+8ULL*(a->n+1ULL)+16ULL*a->n+8ULL*a->ne+8ULL*a->nk+44ULL*a->nj+8;
 std::fprintf(f,"{\"N\":%u,\"E\":%llu,\"J\":%u,\"cells\":%u,\"costs\":%u,\"cuda_estimated_bytes\":%llu,\"invalid_admitted_cost_nodes\":%u,\"search_executed\":false,\"expected_exit\":86,\"jobs\":[",a->n,(unsigned long long)a->ne,a->nj,a->nc,a->nk,bytes,invalid);
 std::vector<unsigned char> seen(a->nc);
 for(unsigned q=0;q<a->nj;++q){std::fill(seen.begin(),seen.end(),0);unsigned targets=0;for(unsigned u=0;u<a->n;++u){int c=a->cells[size_t(q)*a->n+u];if(c>=0&&a->nodes[u].type==1&&!seen[c]){seen[c]=1;++targets;}}auto j=a->jobs[q];std::fprintf(f,"%s{\"source\":%u,\"group\":%u,\"ordinal\":%u,\"layer\":%u,\"segment\":%u,\"channel\":%u,\"targets\":%u}",q?",":"",j.source,j.group,j.ordinal,j.layer,j.segment,j.channel,targets);}
 std::fprintf(f,"]}\n");std::fclose(f);std::fflush(nullptr);std::exit(86);
}
