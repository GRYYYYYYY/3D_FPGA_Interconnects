#include "takeover_validate.hpp"
#include <iostream>
using namespace h3d_native;
int main(int argc,char**argv){
 if(argc!=2)return 2;std::string d=argv[1];Graph g(d+"/graph.bin");auto m=Model::load(d+"/model.bin");auto t=Takeover::load(d+"/takeover_0.bin");TakeoverValidator good(g,m,t);auto prepared=good.prepare();
 require(prepared.active==t.active&&prepared.base==t.base&&prepared.seeds.size()==t.seeds.size(),"reconstructed payload differs");
 for(size_t i=0;i<t.seeds.size();++i)require(prepared.seeds[i].node==t.seeds[i].node&&prepared.seeds[i].backward==t.seeds[i].backward&&prepared.seeds[i].total==t.seeds[i].total,"reconstructed seed changed");
 int rejected=0;
 auto bad=[&](auto mutate){auto copy=t;mutate(copy);try{TakeoverValidator check(g,m,copy);}catch(const std::exception&){++rejected;}};
 bad([](auto&t){t.tree.erase(std::remove_if(t.tree.begin(),t.tree.end(),[](auto n){return n.parent==invalid;}),t.tree.end());});bad([](auto&t){t.active.pop_back();});bad([](auto&t){t.labels[0].prev=0xfffffffe;});bad([](auto&t){t.state[0].occupancy=-1;});bad([](auto&t){t.heap[0].node=0xfffffffe;});bad([](auto&t){t.seeds[0].backward+=1.f;});
 std::cout<<"invalid takeover variants rejected="<<rejected<<"/6\n";return rejected==6?0:1;
}
