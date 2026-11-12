# SPARSE_STREAM_R2 — in progress

Independent implementation from `5651a34abb97939bee6402c5af585753ab07f64b`.
Main contract: `RESIDENT_COMPLETE_BATCH_V2`; never substitute assumed clock or
memory parameters for measured hardware or qualified full-kernel OOC results.

`reference_pop_reduce.cpp` implements valid-POP whole-pair output reduction and
retains a separately stored closed-fold oracle strictly for functional checking.
It is not a CPU performance benchmark. `config/experiment_spec.r2.yaml` records
capacities and explicit memory assumptions; the supplied guide/package is copied
under `config/guidance_package` with its original hash manifest.

The actual 8-lane hardware has one batch start, runtime cost preload with leaf
acknowledgements, tagged POP metadata, eight cell RAM banks, registered minimum
selection/control, bounded initialization and output-write contexts, and a
finite shared physical-memory fabric. Mutable initialization, all device traffic,
commands, conflicts, commit and write acknowledgements are timed. No host loop
performs free sample initialization or intermediate output extraction.

Build and run (Python 3, g++, local Verilator 4.038 as recorded in provenance):

```sh
python3 accel/lookahead/fpga_sparse_stream_r2/sim/build.py pipe_full_NEW
python3 accel/lookahead/fpga_sparse_stream_r2/sim/run_small.py pipe_full_NEW 60
python3 accel/lookahead/fpga_sparse_stream_r2/sim/run_fixtures.py pipe_full_NEW 60
python3 accel/lookahead/fpga_sparse_stream_r2/sim/run_stress.py pipe_full_NEW
python3 accel/lookahead/fpga_sparse_stream_r2/sim/test_owner_pipeline.py owner_NEW
python3 accel/lookahead/fpga_sparse_stream_r2/sim/test_bank_pipeline.py bank_NEW
python3 accel/lookahead/fpga_sparse_stream_r2/sim/test_node_state.py state_NEW
```

Run names must be new; failed source snapshots/results are not overwritten.
`pipe_full*` builds substitute the actual pipelined owner, changed service and
bank commit modules into the complete top. Plain names keep the serial R1 owner
for controlled ablations. `POP_REDUCE=0` is only an explicit old-closure ablation;
the new path has no closed scan.

Generator scripts reproduce the reviewed module variants. Source snapshots in
each build are authoritative for that experiment; later generator changes do not
retroactively qualify earlier experiments. Vivado 2022.2 flows use `tile_ooc.xdc`,
`synth_pre.tcl`, `synth_post.tcl`, and `route_post.tcl`. The failed `pipe_full_c`
RAM inference and its report are retained; explicit RAM-port repair is in
`pipe_full_d` and later. No register-dissolve threshold override or false-path
waiver was used to hide that failure.

The independent `owner_pipeline_model.hpp` is newly calibrated for the two
recorded owner schedules. This does not calibrate the new whole tile or 32/64
scale. `r2_node_state` is an actual finite 4 KiB cache for external 128-bit node
records; its 64 MiB backing / 4M-address unit test is standalone. Integration with
the full large-graph scheduler and scaled shared topology remains work in progress.

The granular checkpoint and raw logs are in
`results/fpga_sparse_stream_r2_20261112`; compact immutable checkpoints are under
its `evidence_snapshot`. See `docs/lookahead_fpga_sparse_stream_r2.md` for current
scope and unresolved work. No FPGA speedup claim or board measurement is made.
