#include "io.hpp"
#include "kernel.hpp"
#include "strict_heap.hpp"
#include <queue>
#include <random>
#include <cstring>
#include <iostream>
#include <cassert>
struct Cmp {bool operator()(la::Entry a,la::Entry b)const{return a.delay>b.delay;}};
static void heap_test() {
 std::mt19937 rng(20261108);std::priority_queue<la::Entry,std::vector<la::Entry>,Cmp> ref;
 la::Entry h[4096];uint32_t count=0;
 for(unsigned i=0;i<20000;++i) {
  if(ref.empty() || (count<4000 && rng()%2)) {la::Entry v={i,float(rng()%5),float(i)};ref.push(v);la::push(h,count,v);}
  else {auto a=ref.top();ref.pop();auto b=la::pop(h,count);assert(!std::memcmp(&a,&b,sizeof(a)));}
 }
 while(count){auto a=ref.top();ref.pop();auto b=la::pop(h,count);assert(!std::memcmp(&a,&b,sizeof(a)));}
}
static std::vector<la::Cost> oracle(const std::vector<uint64_t>& row,const std::vector<la::Node>& node,const std::vector<la::Edge>& edge,const std::vector<la::Cost>& cost,const std::vector<la::Job>& job,const std::vector<int32_t>& cell,unsigned nc) {
 std::vector<la::Cost> out(job.size()*nc,{la::missing(),la::missing()});
 for(size_t q=0;q<job.size();++q) {
  std::vector<float> visited(node.size(),-1);std::vector<bool> expanded(node.size(),false);std::priority_queue<la::Entry,std::vector<la::Entry>,Cmp> heap;heap.push({job[q].source,0,0});
  while(!heap.empty()) {
   auto a=heap.top();heap.pop();if(expanded[a.node])continue;
   int c=cell[q*node.size()+a.node];if(node[a.node].type==1 && c>=0) {auto& old=out[q*nc+c];if(std::isnan(old.delay)||a.delay<old.delay)old={a.delay,a.congestion};}
   for(uint64_t i=row[a.node];i<row[a.node+1];++i) {
    auto v=edge[i].dst;auto p=node[a.node],n=node[v];
    if(!n.inter)continue;if(p.segment_kind>=0 && n.segment_kind>=0 && p.segment_kind!=n.segment_kind)continue;if(n.type==2)break;if(expanded[v])continue;
    la::Entry b={v,a.delay+cost[n.cost].delay,a.congestion+cost[n.cost].congestion};if(visited[v]>=0 && visited[v]<b.delay)continue;visited[v]=b.delay;heap.push(b);
   }
   expanded[a.node]=true;
  }
 }
 return out;
}
int main(int argc,char** argv) {
 heap_test();
 std::vector<la::Node> node(12,{0,0,1,0});node[3].type=1;node[4].type=2;node[5].type=1;node[6].segment_kind=1;node[7].inter=0;node[8].type=1;node[9].type=1;
 node[1].cost=1;node[2].cost=2;node[3].cost=3;node[8].cost=3;node[9].cost=3;node[3].segment_kind=-1;node[4].segment_kind=-1;
 std::vector<la::Cost> costs={{0,0},{1,11},{1,23},{0,2}};
 // parallel edges, zero cycle, >6 degree; eligible SINK in the middle must stop node 1.
 std::vector<std::vector<unsigned>> adj={{1,2,1,6,7,0,10,11},{3,4,5},{8,9},{4},{},{},{5},{5},{},{},{},{}};
 std::vector<uint64_t> row(1,0);std::vector<la::Edge> edge;for(auto a:adj){for(auto v:a)edge.push_back({v,0});row.push_back(edge.size());}
 std::vector<la::Job> jobs={{0,0,0,0,0,0},{2,0,1,1,0,0},{5,1,0,1,0,0}};
 std::vector<int32_t> cell(jobs.size()*node.size(),-1);for(unsigned q=0;q<jobs.size();++q){cell[q*12+3]=0;cell[q*12+8]=0;cell[q*12+9]=1;cell[q*12+5]=2;}
 unsigned nc=4;auto golden=oracle(row,node,edge,costs,jobs,cell,nc);
 assert(golden[0].delay==1 && std::isnan(golden[2].delay));assert(golden[4].delay==0);assert(golden[10].delay==0); // source cost excluded
 if(argc==3 && std::string(argv[1])=="--emit") {
  if(std::ifstream(argv[2]).good())return 10;
  la::Header h={la::MAGIC,node.size(),edge.size(),jobs.size(),costs.size(),nc,2};std::ofstream f(argv[2],std::ios::binary);la::write(f,&h,1);la::write(f,row.data(),row.size());la::write(f,node.data(),node.size());la::write(f,edge.data(),edge.size());la::write(f,costs.data(),costs.size());la::write(f,jobs.data(),jobs.size());la::write(f,cell.data(),cell.size());la::write(f,golden.data(),golden.size());
 }
 std::vector<float> visited(64);std::vector<uint32_t> expanded(64);std::vector<la::Entry> heap(257);std::vector<la::Cost> out(512);std::vector<la::Stats> stats(8);
 // Pad all testbench buffers to AXI adapter depths; these are simulation bounds, not hardware capacities.
 row.resize(65);node.resize(64);edge.resize(256);costs.resize(64);jobs.resize(8);cell.resize(512);
 lookahead_top(row.data(),node.data(),edge.data(),costs.data(),jobs.data(),cell.data(),visited.data(),expanded.data(),heap.data(),out.data(),stats.data(),12,3,nc,257,10000);
 for(unsigned i=0;i<3;++i)assert(stats[i].status==la::OK);
 assert(!std::memcmp(out.data(),golden.data(),golden.size()*sizeof(la::Cost)));
 std::cout<<"normal pushes="<<stats[0].pushes<<" pops="<<stats[0].pops<<" edges="<<stats[0].edges<<" peak="<<stats[0].peak<<"\n";
 lookahead_top(row.data(),node.data(),edge.data(),costs.data(),jobs.data(),cell.data(),visited.data(),expanded.data(),heap.data(),out.data(),stats.data(),12,1,nc,1,10000);assert(stats[0].status==la::QUEUE_OVERFLOW);
 lookahead_top(row.data(),node.data(),edge.data(),costs.data(),jobs.data(),cell.data(),visited.data(),expanded.data(),heap.data(),out.data(),stats.data(),12,1,nc,257,0);assert(stats[0].status==la::BUDGET_EXCEEDED);
 costs[1].delay=1e-40f;
 lookahead_top(row.data(),node.data(),edge.data(),costs.data(),jobs.data(),cell.data(),visited.data(),expanded.data(),heap.data(),out.data(),stats.data(),12,1,nc,257,10000);assert(stats[0].status==la::UNSUPPORTED_NUMERIC);
 lookahead_top(row.data(),node.data(),edge.data(),costs.data(),jobs.data(),cell.data(),visited.data(),expanded.data(),heap.data(),out.data(),stats.data(),12,0,nc,257,10000);
 std::cout<<"PASS strict heap 20000 mixed operations; native-order flood; tie/parallel/SINK/network/empty/overflow/budget/subnormal\n";
}
