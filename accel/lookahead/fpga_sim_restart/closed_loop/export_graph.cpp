#include "bucket61.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
struct Image {
 std::vector<uint32_t> words; std::vector<std::pair<std::string,uint32_t>> bases;
 uint32_t reserve(std::string name,size_t bytes){while(words.size()%256)words.push_back(0);uint32_t base=words.size()/8;bases.push_back({name,base});words.resize(words.size()+((bytes+31)/32)*8);return base*8;}
 template<class T> uint32_t copy(std::string n,const std::vector<T>& x){auto k=reserve(n,x.size()*sizeof(T));memcpy(words.data()+k,x.data(),x.size()*sizeof(T));return k;}
};
int main(int argc,char**argv){if(argc!=3)return 2;la::Workload w(argv[1]);la61::Prepared p(w);Image m;
 m.copy("row",w.row);m.copy("edge",w.edge);m.copy("node",w.node);
 std::vector<uint64_t> co;for(auto c:w.cost)co.push_back((uint64_t(la61::bits(c.delay))<<32)|la61::bits(c.congestion));m.copy("cost",co);m.copy("cell",w.cell);
 std::vector<std::array<uint32_t,8>> jobs(w.h.jobs);for(unsigned q=0;q<w.h.jobs;++q){jobs[q][0]=w.job[q].source;jobs[q][1]=p.targets[q];}m.copy("job",jobs);
 m.reserve("label",w.h.nodes*8);m.reserve("prop",w.h.nodes*8);m.reserve("pending",w.h.nodes*4);m.reserve("closed",w.h.nodes*4);m.reserve("output",w.h.jobs*w.h.cells*8);
 std::string d=argv[2];std::ofstream hex(d+"/memory.hex"),cfg(d+"/config.txt"),info(d+"/layout.json"),gold(d+"/expected.hex");
 hex<<std::hex<<std::setfill('0');for(size_t i=0;i<m.words.size();i+=8){for(int s=7;s>=0;--s)hex<<std::setw(8)<<m.words[i+s];hex<<'\n';}
 cfg<<w.h.nodes<<' '<<w.h.jobs<<' '<<w.h.cells<<' '<<m.words.size()/8<<'\n';for(auto b:m.bases)cfg<<b.second<<' ';cfg<<'\n';
 info<<"{\"nodes\":"<<w.h.nodes<<",\"jobs\":"<<w.h.jobs<<",\"cells\":"<<w.h.cells<<",\"lines\":"<<m.words.size()/8<<",\"bases_line\":{";bool first=true;for(auto b:m.bases){if(!first)info<<',';first=false;info<<'\"'<<b.first<<"\":"<<b.second;}info<<"}}\n";
 la61::ScratchT<std::map<uint32_t,std::vector<uint32_t>>>s(w.h.nodes);std::vector<la::Cost>out(w.h.cells);gold<<std::hex<<std::setfill('0');
 for(unsigned q=0;q<w.h.jobs;++q){auto r=la61::search<false>(w,q,p.targets[q],20,s,out.data(),false,500000000,524288);if(r.status)return 3;for(auto v:out)gold<<std::setw(8)<<la61::bits(v.delay)<<std::setw(8)<<la61::bits(v.congestion)<<'\n';}
}
