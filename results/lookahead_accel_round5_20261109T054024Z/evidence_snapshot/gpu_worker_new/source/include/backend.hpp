#pragma once
#include "workload.hpp"
// In-process, versioned ABI. Input is the current native graph and global jobs;
// no golden map or output filename is accepted by a live backend.
namespace la {
struct BackendInput {
 uint32_t version, contexts, n, nj, nc, nk;
 uint64_t ne;
 const uint64_t* row;const Node* nodes;const Edge* edges;const Cost* costs;
 const Job* jobs;const int32_t* cells;
};
struct BackendMetrics {
 uint32_t version, kind; // 1=host measured, 2=CUDA measured
 double prepare_s, resident_s, readback_s, release_s, service_s;
};
using Backend = int(*)(const BackendInput*,Cost*,Stats*,BackendMetrics*,char*,uint32_t);
}
extern "C" int la_backend_v1(const la::BackendInput*,la::Cost*,la::Stats*,la::BackendMetrics*,char*,uint32_t);
