#include "target_router.hpp"
#include <chrono>
#include <iomanip>
#include <sstream>
#include <iostream>
#include <stdexcept>
#include <string>
int main(int argc,char** argv) {
    try {
        if(argc<4) {
            std::cerr<<"Usage: h3d_route GRAPH NETS RESULT [--threads N] [--batch N] [--iterations N] [--backend cpu|cuda|cuda_dense|cpu_target|cuda_target] [--tree-objective source|incremental] [--delay-file FILE] [--criticality-file FILE] [--bbox-margin N] [--bucket-width N] [--bootstrap-criticality 0..990] [--present N] [--present-cap N]\n";
            return 1;
        }
        h3d::Options o;bool session=false;
        for(int i=4;i<argc;i+=2) {
            if(i+1>=argc) throw std::runtime_error("missing option value");
            const std::string k=argv[i],v=argv[i+1];
            if(k=="--backend") o.backend=v;
            else if(k=="--delay-file") o.delay_file=v;
            else if(k=="--criticality-file") o.criticality_file=v;
            else if(k=="--trace-file") o.trace_file=v;
            else if(k=="--window-mode") {if(v!="host" && v!="device")throw std::runtime_error("invalid window mode");o.window_mode=v;}
            else if(k=="--heuristic") {if(v!="hop" && v!="span")throw std::runtime_error("invalid heuristic");o.heuristic=v;}
            else if(k=="--schedule") { if(v!="naive" && v!="portal") throw std::runtime_error("invalid schedule"); o.portal_schedule=v=="portal"; }
            else if(k=="--tree-objective") { if(v!="source" && v!="incremental") throw std::runtime_error("invalid tree objective"); o.source_tree=v=="source"; }
            else {
                size_t p=0; int n=std::stoi(v,&p); if(p!=v.size() || n<0) throw std::runtime_error("invalid integer");
                if(k=="--threads") o.threads=n;
                else if(k=="--batch") o.batch=n;
                else if(k=="--iterations") o.iterations=n;
                else if(k=="--portal-k") o.portal_k=n;
                else if(k=="--vertical-penalty") o.vertical_penalty=n;
                else if(k=="--bbox-margin") o.bbox_margin=n;
                else if(k=="--bucket-width") o.bucket_width=n;
                else if(k=="--bootstrap-criticality") o.bootstrap_criticality=n;
                else if(k=="--present") o.present=n;
                else if(k=="--present-cap") o.present_cap=n;
                else if(k=="--repair" && n<=1) o.repair=n;
                else if(k=="--session" && n<=1) session=n;
                else if(k=="--incremental-congestion" && n<=1) o.incremental_congestion=n;
                else throw std::runtime_error("unknown option/value: "+k);
            }
        }
        if((o.backend=="cpu_target" || o.backend=="cuda_target") && o.delay_file.empty())
            throw std::runtime_error("target backend requires explicit --delay-file (ps, validated timing scope)");
        const auto start=std::chrono::steady_clock::now();
        auto seconds=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();};
        std::cerr<<"route_phase=graph_read_begin elapsed="<<seconds()<<std::endl;
        const auto g=h3d::Graph::read(argv[1]);
        std::cerr<<"route_phase=graph_read_end elapsed="<<seconds()<<" nodes="<<g.nodes.size()<<" edges="<<g.edges.size()<<std::endl;
        const auto nets=h3d::read_nets(argv[2],g);
        std::cerr<<"route_phase=nets_read_end elapsed="<<seconds()<<" nets="<<nets.size()<<std::endl;
        if(session) {
            if(o.backend!="cpu_target" && o.backend!="cuda_target")throw std::runtime_error("persistent refinement requires target backend");
            std::string output=argv[3];uint32_t epoch=0;
            h3d::route_target_session(g,nets,o,[&](const h3d::Result& r){
                h3d::write_result(output,g,nets,o,r);
                std::cout<<"TARGET_READY "<<epoch<<' '<<int(r.success)<<std::endl;
                std::string line,command,extra;if(!std::getline(std::cin,line))return h3d::TargetFeedback{};
                std::istringstream in(line);in>>command;
                if(command=="STOP"){if(in>>extra)throw std::runtime_error("trailing stop fields");return h3d::TargetFeedback{};}
                h3d::TargetFeedback feedback;std::string next_output;
                if(command!="REFINE" || !(in>>std::quoted(feedback.criticality_file)>>std::quoted(next_output)>>feedback.threshold>>feedback.max_connections))throw std::runtime_error("invalid refinement command");
                std::string mode;
                if(in>>mode){if(mode!="legal" && mode!="negotiate")throw std::runtime_error("invalid refinement mode");feedback.negotiate=mode=="negotiate";}
                if(in>>extra)throw std::runtime_error("trailing refinement fields");
                if(feedback.criticality_file.empty() || next_output.empty())throw std::runtime_error("empty refinement path");
                output=next_output;++epoch;return feedback;
            });
            return 0;
        }
        const auto r=h3d::route(g,nets,o); h3d::write_result(argv[3],g,nets,o,r);
        std::cout<<"success="<<r.success<<" nets="<<nets.size()<<" iterations="<<r.iterations.size()<<" seconds="<<r.routing_seconds<<'\n';
        return r.success?0:2;
    } catch(const std::exception& e) { std::cerr<<"error: "<<e.what()<<'\n'; return 1; }
}
