#define main mechanism_unit_main
#include "tb51.cpp"
#undef main
#include "reference4.hpp"
int main(int argc,char**argv){unsigned tested=0,skipped=0;for(int f=1;f<argc;++f){la::Workload w(argv[f]);if(w.h.nodes>32||w.h.edges>128||w.h.jobs>8||w.h.cells>8||w.h.costs>64){++skipped;continue;}la4::Prepared p(w);n=w.h.nodes;ne=w.h.edges;nj=w.h.jobs;nk=w.h.costs;nc=w.h.cells;cap=ne+1;++gv;++cv;
 for(unsigned i=0;i<=n;++i)row[i]=w.row[i];for(unsigned i=0;i<n;++i)nodes[i]=pack_node(w.node[i]);for(unsigned i=0;i<ne;++i)edges[i]=w.edge[i].dst;for(unsigned i=0;i<nk;++i)costs[i]=pack_cost(w.cost[i]);for(unsigned q=0;q<nj;++q){sources[q]=w.job[q].source;targets[q]=p.targets[q];for(unsigned u=0;u<n;++u)cells[q*32+u]=w.cell[q*n+u];}
 for(unsigned mode=0;mode<2;++mode){call(mode?1:2,mode);expect(status==0,"fixture status");golden(mode);for(unsigned q=0;q<nj;++q)for(unsigned c=0;c<nc;++c)expect(output[q*8+c]==pack_cost(w.golden[q*nc+c]),"archived golden");}++tested;
 }std::cout<<"PASS fixtures="<<tested<<" capacity_skipped="<<skipped<<" (no replicated jobs)\n";return 0;}
