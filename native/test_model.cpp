#include "model_io.hpp"
#include <iostream>
#include <iomanip>
int main(int argc,char**argv){
    try{
        if(argc<3)throw std::runtime_error("usage: test_model model.bin query.bin ...");
        auto m=h3d_native::Model::load(argv[1]);uint64_t checked=0,exact=0;double max_relative=0;
        for(int i=2;i<argc;++i){h3d_native::Query q(argv[i]);for(auto e:q.entries){
            float h=h3d_native::expected(m.view(),e.node,q.header.sink,q.header.criticality,m.header.sink_base);
            h=q.header.astar*std::max(0.f,h-q.header.astar_offset);
            double relative=std::abs(double(h)-e.heuristic)/std::max(1e-30,double(e.heuristic));
            if(!std::isfinite(h)||relative>2e-6)throw std::runtime_error("native lookahead mismatch query="+std::to_string(q.header.sequence)+" node="+std::to_string(e.node)+" kind="+std::to_string(m.nodes[e.node].kind)+" relative="+std::to_string(relative));
            ++checked;exact+=h==e.heuristic;max_relative=std::max(max_relative,relative);
        }}
        std::cout<<"{\"checked\":"<<checked<<",\"bit_exact\":"<<exact<<",\"max_relative_error\":"<<std::setprecision(12)<<max_relative<<"}\n";
    }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
