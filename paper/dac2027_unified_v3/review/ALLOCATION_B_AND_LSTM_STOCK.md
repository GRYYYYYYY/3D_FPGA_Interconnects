# Allocation B and LSTM Stock investigation

## Allocation B

The job started at 13:41:48 UTC on 18 November 2026. At 16:43:45 UTC, Inspire logged a job-level `StopJob` from `inspire-studio-backend` because usage failed the administrator's auto-recycle rules. The job reached `job_stopped` at 16:43:50 UTC after 10,922 seconds, and the platform deleted the worker pod. The configured 24-hour maximum was an upper runtime limit. The experiment script's separate deadline was 13:00 UTC the next day.

The workspace configuration retrieved during this investigation has `auto_recycle_train=1` and a GPU utilization rule with `hrs=3` and `thresh=40`. Scheduled recycling has `timed_recycle_train=0`. This rule is consistent with the event just after three hours. The historical metric query returned a service error, so the measured utilization and aggregation formula remain unavailable. The worker was performing CPU-only independent GEMM route readback at termination. [Job-level events and workspace policy](ALLOCATION_B_EVENTS.json) · [Frozen experiment receipt](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/671a31e1c9fd18d2242a5c32c4d53ac5f50ec992/experiments/dac2027_unified_v3/allocation_b/audit/allocation_stop.json)

## LSTM Stock

Stock loaded the architecture, packed netlist, placement and RR graph, then wrote its wire map after 60.953 s of native construction. Its digest matches STRICT Pipeline and the historical Stock map. The last complete routing row was iteration 4. The process exited with signal 11 and emitted no route. The job continued with the remaining workloads for more than two hours.

The existing core dump and SHA-matched V3 Stock executable locate the failure in the native parallel routing path. The stack includes `ParallelNetlistRouter::route_partition_tree_node`, `route_net`, `route_sink`, `RouteTree::update_from_heap` and `RouteTree::add_subtree_from_heap`. During the route-tree predecessor walk, the code loaded `rr_node_route_inf[new_inode].prev_edge`, which held `RREdgeId::INVALID()` (the unsigned 32-bit all-ones sentinel), and passed it to the RR edge source lookup. The instruction and core registers identify the resulting out-of-bounds read as the fault reported in the signal record. The origin of the invalid predecessor remains open.

| Question | Evidence |
|---|---|
| Input | All five input SHA256 bindings match the successful archived Stock runs. Stock and STRICT emitted the same wire map. LSTM Pipeline and both ALT backends produced routes that passed independent FULL/STA on the same inputs. The input can still exercise a routing corner case. |
| Binary | The original Stock binary succeeded four times in the prior LSTM campaign with matching routing settings, including eight workers, the parallel router, seed 2 and width 120. The V3 Stock executable is a separate timed rebuild. The faulting function has matching normalized machine instructions in both binaries. The campaigns do not isolate differences elsewhere in the build, runtime or scheduling. |
| Routing | The immediate failure is an invalid predecessor edge during construction of a route-tree branch in the native parallel router. It occurs downstream of lookahead construction and serialization. |
| Resources | The core records an unmapped-address SIGSEGV. Reported peak RSS before failure was 7,314.2 MiB under a 200 GiB allocation, roughly the same as the successful candidates. CPU quota throttling counters remained zero across the invocation. |

The original Stock binary is bound by SHA256 `37cc22c8b1b5d9d378e25379e85afcb7e56b5f1f6f72e3e9186e5e107ed5ce62`. The V3 Stock executable used to interpret the core is bound by SHA256 `b02632d3ddfaa3251aa2ccf102b4b0ad4787a51320b35ceb3878442ed7e38868`. The local `allocation_b/run/qualification/lstm/0/stock/core.11008` is bound by SHA256 `c437357bec08a41ac5332b399f7e2a4d2d8d285d6a1b9d7236b107a73cb3d27c`. GDB 12.1 resolved the VPR frames from the executable's symbols. [Historical LSTM records](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/blob/d999a250f8e9358b264c713095a050b8f8467819/paper/dac2027_mechanism_ablation/evidence/holdout_results.json) · [Frozen qualification and process archive](https://github.com/GRYYYYYYY/3D_FPGA_Interconnects/tree/671a31e1c9fd18d2242a5c32c4d53ac5f50ec992/experiments/dac2027_unified_v3/allocation_b/audit)

## V3 scope

The original execution plan covered 54 formal runs. The completed 36 runs form a full primary matrix for GEMM and BNN, each with all six configurations and three matched repeats on the same worker. LSTM contributes auxiliary map identity, backend equivalence and three independently checked routes. Its formal runtime and matched Stock-relative QoR remain open.
