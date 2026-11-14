#pragma once
#include "compact61.hpp"
#include <cstdlib>
#include <cstdio>
namespace la61 {
inline void capture(const la::BackendInput& a,const la::Cost* output,const std::vector<uint32_t>& targets,unsigned shift,const char* backend){
 const char* path=getenv("R61_CAPTURE");if(!path)return;
 // Audit only, after measured service. This is NEVER enabled in formal E2 runs.
 std::ofstream f(std::string(path)+".bin",std::ios::binary);uint64_t groups=1;for(unsigned q=0;q<a.nj;++q)groups=std::max(groups,uint64_t(a.jobs[q].group)+1);
 la::Header h={la::MAGIC,a.n,a.ne,a.nj,a.nk,a.nc,groups};la::write(f,&h,1);la::write(f,a.row,a.n+1);la::write(f,a.nodes,a.n);la::write(f,a.edges,a.ne);la::write(f,a.costs,a.nk);la::write(f,a.jobs,a.nj);la::write(f,a.cells,size_t(a.n)*a.nj);la::write(f,output,size_t(a.nj)*a.nc);
 fprintf(stdout,"R61_IDENTITY backend=%s shift=%u hash=FNV1a64 row=%016llx node=%016llx edge=%016llx cost=%016llx job=%016llx cell=%016llx target=%016llx output=%016llx n=%u e=%llu j=%u c=%u complete=1\n",backend,shift,(unsigned long long)hash_bytes(a.row,(a.n+1)*8),(unsigned long long)hash_bytes(a.nodes,a.n*16ULL),(unsigned long long)hash_bytes(a.edges,a.ne*8),(unsigned long long)hash_bytes(a.costs,a.nk*8),(unsigned long long)hash_bytes(a.jobs,a.nj*24),(unsigned long long)hash_bytes(a.cells,size_t(a.n)*a.nj*4),(unsigned long long)hash_bytes(targets.data(),targets.size()*4),(unsigned long long)hash_bytes(output,size_t(a.nj)*a.nc*8),a.n,(unsigned long long)a.ne,a.nj,a.nc);
}
}
