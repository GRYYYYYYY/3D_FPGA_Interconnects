// Differential tests use the independent std::priority_queue oracle from the adversarial TB.
#define main unused_adversarial_main
#include "testbench.cpp"
#undef main
int main(){
 std::mt19937 rng(83017);
 for(unsigned trial=0;trial<200;++trial){
  // Include more than 64 nodes so the 64-line direct-mapped label cache must alias.
  unsigned n=8+rng()%160;std::vector<la::Node> nodes(n);std::vector<la::Cost> costs(n);std::vector<uint64_t> row(1,0);std::vector<la::Edge> edges;
  for(unsigned u=0;u<n;++u){nodes[u]={unsigned(rng()%4==0?1:rng()%13==0?2:0),u,unsigned(rng()%8!=0),int(rng()%3)-1};costs[u]={std::ldexp(float(rng()%7),int(rng()%15)-25),std::ldexp(float(rng()%7),int(rng()%10)-4)};unsigned degree=rng()%10;for(unsigned i=0;i<degree;++i)edges.push_back({uint32_t(rng()%n),0});row.push_back(edges.size());}
  std::vector<la::Job> jobs={{uint32_t(rng()%n),0,0,0,0,0},{uint32_t(rng()%n),0,1,1,0,0}};std::vector<int32_t> cells(2*n);for(auto& c:cells)c=int(rng()%6)-1;
  auto golden=oracle(row,nodes,edges,costs,jobs,cells,5);std::vector<float> v(n);std::vector<uint32_t> ex(n);std::vector<la::Entry> heap(edges.size()+1);std::vector<la::Cost> out(10);std::vector<la::Stats> st(2);
  lookahead_top(row.data(),nodes.data(),edges.data(),costs.data(),jobs.data(),cells.data(),v.data(),ex.data(),heap.data(),out.data(),st.data(),n,2,5,heap.size(),edges.size()+1);
  for(auto s:st)assert(s.status==la::OK);assert(!std::memcmp(out.data(),golden.data(),80));
 }
 std::cout<<"PASS 200 randomized differential floods, cache aliases/output collisions/FP32 rounding/zero cycles/filters\n";
}
