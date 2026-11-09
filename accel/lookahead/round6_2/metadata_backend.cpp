// Metadata-only ABI observer. Intentionally exits before any search or route.
#include "backend.hpp"
#include <cstdio>
#include <cstdlib>
extern "C" int la_backend_v1(const la::BackendInput* a,la::Cost*,la::Stats*,la::BackendMetrics*,char*,uint32_t){
 if(!a||a->version!=1)std::exit(87);
 const char* p=std::getenv("R62_METADATA");if(!p)std::exit(88);
 FILE* f=std::fopen(p,"wx");if(!f)std::exit(89);
 std::fprintf(f,"{\"N\":%u,\"E\":%llu,\"J\":%u,\"cells\":%u,\"costs\":%u,\"search_executed\":false,\"expected_exit\":86}\n",a->n,(unsigned long long)a->ne,a->nj,a->nc,a->nk);
 std::fclose(f);std::fflush(nullptr);std::exit(86);
}

