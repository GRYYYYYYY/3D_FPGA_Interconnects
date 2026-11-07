#pragma once
#include "model.hpp"
#include "replay.hpp"

namespace h3d_native {
struct Model {
    ModelHeader header;std::vector<ModelNode> nodes;std::vector<Cost>wires;std::vector<Reach>reachable;std::vector<uint32_t>groups;
    ModelView view()const{return {header,nodes.data(),wires.data(),reachable.data(),groups.data()};}
    void save(const std::string&file){
        header.nodes=nodes.size();header.wires=wires.size();header.reachable=reachable.size();header.groups=groups.size();
        std::ofstream f(file,std::ios::binary);f.exceptions(std::ios::badbit|std::ios::failbit);
        f.write(reinterpret_cast<const char*>(&header),sizeof(header));
        auto put=[&](const auto&v){f.write(reinterpret_cast<const char*>(v.data()),sizeof(v[0])*v.size());};
        put(nodes);put(wires);put(reachable);put(groups);
    }
    static Model load(const std::string&file){
        std::ifstream f(file,std::ios::binary);Model m;m.header=read<ModelHeader>(f);
        require(std::string(m.header.magic,7)=="H3DMAP1"&&m.header.version==1,"bad map ABI");
        m.nodes=read_vector<ModelNode>(f,m.header.nodes);m.wires=read_vector<Cost>(f,m.header.wires);
        m.reachable=read_vector<Reach>(f,m.header.reachable);m.groups=read_vector<uint32_t>(f,m.header.groups);
        require(f.peek()==EOF,"trailing model bytes");
        require(uint64_t(m.header.layers)*m.header.layers*m.header.channels*m.header.segments*m.header.width*m.header.height==m.wires.size(),"map dimensions mismatch");
        for(const auto&n:m.nodes){require(n.reach_begin+uint64_t(n.reach_count)<=m.reachable.size() && n.group_begin+uint64_t(n.group_count)<=m.groups.size(),"model range mismatch");}
        return m;
    }
};
}
