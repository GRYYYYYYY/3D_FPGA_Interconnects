# Thesis and measured-source correspondence

The method removes sample scheduling barriers while retaining source/context and ordered consumption (C1), and separately defines whole-pair FP32 wave selection inside a sample (C2). STRICT CPU, ALT CPU and ALT CUDA are configurations, not serial stages. V1 uses no results from new experiments.

`evidence/algorithm_source_binding.json` records exact SHA256 values and paths. The original native build binding identifies executable 5d32c536b729d87ffd33a9c354ec157662b703f96dcc8ed02fcb522355de2355. `evidence/holdout_plan.json` binds the LSTM tests to that binary and the CPU/CUDA libraries. Original compiled-source receipt hashes match bucket61.hpp, backend61.cpp, cuda_solver61.cuh and cuda_backend61.cu. The archived native scheduler/outer files also match original build hashes. No later prepared-POP/INF source is used to describe these timings.

| Manuscript component | Locked source / behavior |
|---|---|
| Graph, group and sample enumeration | native_router_lookahead_map.cpp `compute_router_wire_lookahead`; native_router_lookahead_map_utils.cpp `get_routing_cost_maps_pipeline`, group/source loop |
| C1 enumeration and bounded exposure | native utils lines 1209 onward: native order jobs; token min(J,max(1,2P)); thread-specific scratch; serial producer, parallel flood, serial-in-order consumer |
| Private native flood | same utils `flood_wire_sample`, thread-local dijkstra workspace, unchanged selection/filtering |
| Native tie merge | `merge_smallest` / native `add_cost_entry(SMALLEST,...)`; finite-delay conditional proof applies only with unchanged sample engine, occupancy and outer order |
| Native outer writes/interpolation | native map `compute_router_wire_lookahead`; sampled vector returned, then original group write/fill loop; not arbitrary reordering of fills |
| Alternative dispatch | native utils line 1241 calls `la_live` immediately after job enumeration and returns before the TBB pipeline on success. Logical enumeration is shared; STRICT pipeline execution is bypassed, not reused or run first. |
| Live graph/context export | vpr_live.cpp: current RRGraph to CSR; native source geometry and IPIN map; job ordinal/group/layer/type; ABI shape checks; exactly one library call |
| ALT CPU | backend61.cpp: FE_TONEAREST; `std::map` sparse directory, contexts private scratch; OpenMP dynamic parallel-for over all jobs; not DirectDirectory in native CPU |
| C2 snapshot and commit | bucket61.hpp `search`: pending/stale extraction; stable label array, separate touched proposals; strict whole-pair improvement after expansion; re-publication/dedup; closed-set IPIN output after same-bucket closure |
| Whole pair and numeric predicate | workload.hpp `numeric`, `eligible`; bucket61.hpp `less`; CUDA `pairkey` and 64-bit atomicMin. Positive normal/+0 only; internal INF and missing NaN are sentinels, not admitted costs. Eligibility skips forbidden destinations and stops adjacency traversal on eligible SINK. |
| GPU mapping | cuda_solver61.cuh: grid.x nodes in blocks of256, grid.y samples; each active node thread loops adjacency; persistent proposals equal committed labels at wave boundary; commit/minimum scan, confirm, advance, host completion copy |
| Completion and bounds | target count uses all distinct mapped IPIN cells. CPU stops at target completion after closure or empty directory; guards include 180s, 1M waves, 500M scanned edges and queue entries. GPU uses 100K waves/180s; API failures and invalid numerics abort. Missing unreachable cells are retained; no successful partial map after an error. |
| GPU memory | original Node16/Edge8; label8+proposal8+pending4+settled1+mapping4 =25JN bytes, output8JC, CSR8(N+1), nodes16N, edges8M, costs8nk, jobs24J, targets4J, Meta16J, done/error8. Capacity <=80% free memory. |
| Size wording correction | original live ABI checks unsigned shape, edges <UINT32_MAX and mapped signed cell index; original ALT does not itself check N<2^23. This tighter limit is a retained historical qualification/STRICT envelope, not a newly asserted ALT code check. |
| E2 and Process | native map entry/exit includes live conversion/service/merge, interpolation, SOURCE/OPIN/minima/interposer. Wrapper process wall additionally includes loading/route/serialization; readback and pre-generated inputs are excluded. |

C1 memory counts the result map entry type symbolically, not as an assumed 8-byte pair: native Expansion_Cost_Entry can contain more state. C2 work sums actual wave edge visits and directory/scan costs; no edge-once bound or global lexicographic optimality theorem is asserted. The native GPU source maintains persistent proposals; no reset kernel is invented.

The figure locates two levels of parallelism but the comparisons do not form a complete two-dimensional causal ablation. Group/Flat/Pipeline controls test scheduling; shift0/20 profiles test wave organization; matched ALT CPU/CUDA and native cohort timings test concrete realizations. Results across workloads, workers, representations or timing scopes are never multiplied.
