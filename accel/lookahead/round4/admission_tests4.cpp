#include "onchip_api4.hpp"
#include <cassert>
#include <iostream>
#include <vector>
int main(){
    std::vector<uint64_t> row={0,1,1};
    std::vector<la::Node> nodes={{0,0,1,0},{1,1,1,-1}};
    std::vector<la::Edge> edges={{1,0}};
    std::vector<la::Cost> costs={{0,0},{1,2}},out(2);
    std::vector<la::Job> jobs(2);jobs[0].source=0;jobs[1].source=1;
    std::vector<int32_t> cells={-1,0,-1,0};std::vector<la::Stats> stats(2);
    unsigned n=2,ne=1,nj=2,nk=2,nc=1,status=99;
    auto run=[&](unsigned cmd){lookahead_onchip4(row.data(),nodes.data(),edges.data(),costs.data(),jobs.data(),cells.data(),out.data(),stats.data(),n,ne,nj,nk,nc,cmd,status);return status;};
    assert(run(1)==la::INVALID_INPUT); // No implicit external fallback.
    assert(run(0)==la::OK&&run(1)==la::OK);
    assert(out[0].delay==1&&out[1].delay==0);
    costs[1]={la::missing(),la::missing()};assert(run(1)==la::OK&&out[0].delay==1);
    assert(run(0)==la::INVALID_INPUT&&run(1)==la::INVALID_INPUT); // Bad load invalidates image.
    costs[1]={1,2};assert(run(2)==la::OK);
    n=on4::MAX_N+1;assert(run(0)==la::INVALID_INPUT);n=2;assert(run(1)==la::INVALID_INPUT);
    assert(run(0)==la::OK);ne=0;assert(run(1)==la::INVALID_INPUT);ne=1;
    row[0]=1;assert(run(0)==la::INVALID_INPUT);row[0]=0;
    edges[0].dst=2;assert(run(0)==la::INVALID_INPUT);edges[0].dst=1;
    cells[1]=1;assert(run(0)==la::INVALID_INPUT);cells[1]=0;
    jobs[0].source=2;assert(run(0)==la::INVALID_INPUT);jobs[0].source=0;
    nodes[1].cost=2;assert(run(0)==la::INVALID_INPUT);nodes[1].cost=1;
    for(float bad:{-0.f,-1.f,1.e38f,la::missing()}){costs[1].delay=bad;assert(run(0)==la::INVALID_INPUT);}costs[1].delay=1;
    assert(run(0)==la::OK);nj=0;assert(run(0)==la::OK&&run(1)==la::OK);nj=2;
    // Shrink all dimensions and reuse the same statically allocated hardware state.
    n=1;ne=0;nj=1;nk=1;nc=0;row[1]=0;cells[0]=-1;
    assert(run(2)==la::OK&&run(1)==la::OK&&stats[0].status==la::OK);
    assert(stats[0].pops==(LA4_EARLY?0:1));
    assert(run(3)==la::INVALID_INPUT&&run(1)==la::INVALID_INPUT);
    std::cout<<"PASS admission, invalidation, poisoned external input, capacity, shape, runtime shrink and empty jobs/targets\n";
}
