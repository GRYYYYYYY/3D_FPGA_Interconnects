#include "heap51.hpp"
#include "reference4.hpp"
#include "strict_heap.hpp"
#include <cassert>
#include <cstring>
#include <iostream>

// Bounded native-workload replay. The strict heap is the independent oracle;
// inspect its unmodified path to count accesses, then verify the candidate heap.
int main(int argc,char** argv) { try {
    if(argc!=3)throw std::runtime_error("heap_profile51 workload trace.csv");
    la::Workload w(argv[1]);la4::Prepared prep(w);
    constexpr unsigned CAP=on4::MAX_E+1;
    if(w.h.edges+1>CAP)throw std::runtime_error("bounded small-graph profile only");
    std::ofstream trace(argv[2]),pop_trace(std::string(argv[2])+".pop_path.csv");
    pop_trace<<"early,qid,pop,initial_size,down,up_compares,up_moves,single_child\n";
    for(unsigned early=0;early<2;++early)for(unsigned q=0;q<w.h.jobs;++q) {
        std::vector<la::Entry> heap(CAP);
        on4::Word even[(CAP+1)/2],odd[(CAP+1)/2];
        std::vector<float> visited(w.h.nodes,-1);
        std::vector<bool> expanded(w.h.nodes,false);
        std::vector<la::Cost> out(w.h.cells,{la::missing(),la::missing()});
        unsigned count=0,actual_count=0,recorded=0;
        uint64_t pushes=0,pops=0,push_levels=0,down=0,up=0,up_moves=0,pairs=0,single=0,checks=0;
        unsigned max_down=0,max_up=0;
        auto check=[&]() {
            assert(count==actual_count);
            for(unsigned i=0;i<count;++i){assert(on4::get(even,odd,i)==on4::pack(heap[i]));++checks;}
        };
        auto event=[&](char op,uint64_t work,uint64_t seq){trace<<early<<','<<q<<','<<op<<','<<work<<','<<seq<<'\n';};
        auto push=[&](la::Entry e) {
            assert(count<CAP);unsigned hole=count,levels=0;
            while(hole){++levels;unsigned p=(hole-1)/2;if(!(heap[p].delay>e.delay))break;hole=p;}
            la::push(heap.data(),count,e);on4::push(even,odd,actual_count,on4::pack(e));
            push_levels+=levels;event('U',levels,++pushes);check();
        };
        if(!early||prep.targets[q])push({w.job[q].source,0,0});
        while(count) {
            unsigned size=count-1,right=2,d=0,u=0,moves=0,one=0;
            la::Entry path[on51::path_slots(CAP)],value=heap[size];
            if(size) {
                while(right<size){++pairs;unsigned c=heap[right].delay>heap[right-1].delay?right-1:right;path[d++]=heap[c];right=2*(c+1);}
                if(right==size){++single;one=1;path[d++]=heap[right-1];}
                for(unsigned i=d;i;--i){++u;if(!(path[i-1].delay>value.delay))break;++moves;}
            }
            down+=d;up+=u;up_moves+=moves;max_down=std::max(max_down,d);max_up=std::max(max_up,u);
            auto cur=la::pop(heap.data(),count);
            assert(on51::pop_path<CAP>(even,odd,actual_count)==on4::pack(cur));check();
            event('P',d+u,++pops);
            pop_trace<<early<<','<<q<<','<<pops<<','<<size+1<<','<<d<<','<<u<<','<<moves<<','<<one<<'\n';
            unsigned node=cur.node;if(expanded[node])continue;
            int cell=w.cell[q*w.h.nodes+node];
            if(w.node[node].type==1&&cell>=0) {
                bool first=out[cell].delay!=out[cell].delay;la::record(out[cell],cur);
                if(first)++recorded;if(early&&recorded==prep.targets[q])break;
            }
            for(uint64_t i=w.row[node];i<w.row[node+1];++i) {
                unsigned dst=w.edge[i].dst;int a=la::eligible(w.node[node],w.node[dst]);event('E',a==1,i);
                if(!a)continue;if(a<0)break;if(expanded[dst])continue;
                auto c=w.cost[w.node[dst].cost];la::Entry e={dst,cur.delay+c.delay,cur.congestion+c.congestion};
                if(visited[dst]>=0&&visited[dst]<e.delay)continue;
                visited[dst]=e.delay;push(e);
            }
            expanded[node]=true;
        }
        assert(!std::memcmp(out.data(),w.golden.data()+q*w.h.cells,w.h.cells*sizeof(la::Cost)));
        // Verify the speculative early-stop suffix too, but exclude it from work counters.
        unsigned suffix=0;while(count){auto e=la::pop(heap.data(),count);assert(on51::pop_path<CAP>(even,odd,actual_count)==on4::pack(e));check();++suffix;}
        std::cout<<"{\"early\":"<<early<<",\"qid\":"<<q<<",\"pushes\":"<<pushes<<",\"pops\":"<<pops
                 <<",\"push_levels\":"<<push_levels<<",\"pop_down_levels\":"<<down<<",\"pop_up_compares\":"<<up
                 <<",\"pop_up_moves\":"<<up_moves<<",\"down_pair_reads\":"<<2*pairs<<",\"down_single_reads\":"<<single
                 <<",\"old_pop_heap_reads\":"<<2*pops+2*pairs+single+up<<",\"new_pop_heap_reads\":"<<2*pops+2*pairs+single
                 <<",\"saved_up_heap_reads\":"<<up<<",\"down_writes_restored_by_up\":"<<up_moves
                 <<",\"max_down\":"<<max_down<<",\"max_up\":"<<max_up<<",\"suffix_pop_checks\":"<<suffix
                 <<",\"full_active_heap_word_checks\":"<<checks<<",\"golden_match\":true}\n";
    }
}catch(std::exception& e){std::cerr<<e.what()<<'\n';return 1;} }
