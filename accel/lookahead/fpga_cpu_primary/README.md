# CPU-primary complete L1 core

[Latest completed results, conclusions and in-flight experiment (2026-11-16)](../../../docs/lookahead_fpga_cpu_primary_progress_20261116.md).

[Earlier frozen snapshot (2026-11-15)](../../../docs/lookahead_fpga_cpu_primary_progress_20261115.md).

This independent candidate starts at `3c7f96e6037030949b729240977c2ced373843c6`.
The research goal is `CPU_PRIMARY_GPU_COMPARATOR`; a GPU win is **not** an entry
condition. GPU evidence is retained. No board measurements are claimed.

`rtl/cp_full_top.sv` connects the production64 lanes/16 frontends/64 banks to
one32-port radix memory network. Runtime job configuration contains source and
unique eligible-target count for each sample (up to256), not expected results.
All samples use real state initialization, cost reads, SEED, MIN, TAKE/RELEASE,
canonical POP, T/D/ready/target processing, enum2/scratch, K8 commit, serialized
L1 publication, and output writes followed by ACK drain. The capacities are
unchanged from the production L1 contract. The external service remains an
explicit simulation assumption.

The caller must keep configuration stable from accepted start through done.
Immutable graph admission validates descriptor/edge encoding and cost nibble
`<cfg_costs`; the latter is not independently checked by the leaf datapath.
Bases address32-byte lines, are32-line aligned, and refer to disjoint admitted
regions. The top rejects upper address bits and per-sample/end-range overflow;
it does not silently truncate64-bit leaf addresses into the32-bit network.
The shared network preserves source/kind/generation/local-ID, and owns the
physical live-tag exact-once return contract. `cp_admin` additionally checks
response kind/status/generation and cost beat/port; it does not claim a second
independent duplicate-response scoreboard after the trusted network.

Core scope excludes platform shell, PCIe and HBM controllers. OOC resources
must not be presented as deployable card user-region resources. Initial timing
is5ns with0.1ns clock uncertainty and0.1/0.8ns min/max boundary delays; actual
setup/hold/DRC qualification is required before a frequency is selected.

## Layout

- `backend/`: complete finite L1 bank and targeted production-capacity tests.
- `dispatch/`: finite directory/POP scheduler, token ownership and tests.
- `fixtures/`: two complete native graphs, independent production-C++ validation,
  bounded external-memory test model and full-core testbench.
- `software/`: completed affinity/NUMA CPU8/32/64 thread audit and measurements.
- `model/`: new finite structural model and later RTL calibration.
- `delivery/`: exact source closure, source freeze, EDA and evidence tooling.

Raw results go only under `results/fpga_cpu_primary_20261115/`. Earlier worktrees,
results, STRICT and golden data remain unchanged. `experiment_config.json`
retains the initial declaration (also bound by model compilations). Updated
qualification is separate in raw `qualification_progress.json`; source existence
and a launched run do not establish fit or timing. Main report: `docs/lookahead_fpga_cpu_primary_closure.md`.


## Selected source and replay

Current h followup: the isolated `dispatch/return_wordmux/sources.json` closure
changes only dispatcher return-payload selection. Local and new52-native/11-
rejection full-core calibration passed; unchanged g160 evidence is reused via
`model_calibration_h_return_wordmux_a`. Full synthesis h started once at
2026-11-16 19:12:06UTC. Its resource/timing result is unknown. The default source
closure below remains f for reproducibility. See the
[continuation and recovery report](../../../docs/lookahead_fpga_cpu_primary_resume_db1d7e454.md).

The preceding f candidate is the31-source wordmux closure in
`delivery/sources.json`. Its full RTL52-sample/11-rejection results and explicit
reuse of160 complete model_g samples are bound by
`model_calibration_g_wordmux_a/calibration_reuse_contract.json` under the raw
result root. The previous e core failed actual post-opt capacity at1,351,028
LUTs; current f synthesis completed at1,244,096 LUTs (95.43%). Its terminal
synthesis reports/source binding are audited; actual standard-opt resources are
1,241,143 LUTs (95.20%) with terminal reports/checkpoint verified. Full-core
place/phys-opt/route resumed from that checkpoint at23:54:12UTC. Actual placement
completed at1,233,715 LUTs (94.63%) and749,174 FF, with high-congestion warnings.
Post-place timing fails setup/hold; standard phys_opt completed with zero WNS
gain. Original f routing failed with level7 global congestion and5,809,714 node
overlaps. Its error DCP confirms the same global resources; a `Routed` report
header does not waive those conflicts. One independent `SSI_SpreadSLLs`
implementation from the same opt DCP is now running, with unchanged RTL,5ns,
8 threads and ultrathreads. Its placement completed at1,232,534LUT/749,226FF,
with unchanged BRAM/URAM/DSP and2BUFGCE. Post-place reports completed with
WNS−15.487ns/WHS−3.530ns. Default phys_opt completed with zero cell changes
and zero timing gain; default route began at14:14:28UTC and returned1 at
18:42:24UTC with Route35-3 congestion7 and5,795,346 trial overlaps. Error DCP
saving completed; full terminal report collection remains active.
Placed SLL usage shifts to85.45%/89.09% on the two boundaries, but CLB sites
remain99.92% occupied and high-congestion warnings persist.
Initial router SLL demand is97.98%/106.02%, with localized columns
above capacity on both boundaries; these differ from placed utilization and
are not a terminal result. External OOC ports still lack physical boundary
locations. Route35-447 now prioritizes connectivity over timing due to
congestion; the subsequent command has now failed. Missing boundary context continues
to limit interface timing accuracy. No qualified full-core frequency
is available yet. `delivery/ssi_replay.tcl` records the single followup flow;
see the closure report and raw `full_impl_f_ssi_spreadslls_a` for bindings/status.

From the repository root, with the retained raw fixtures available, these
commands use **new, nonexistent output directories**:

```sh
python3 accel/lookahead/fpga_cpu_primary/rtl/run_candidate_wordmux.py \
  results/fpga_cpu_primary_20261115/replay_local_NEW
python3 accel/lookahead/fpga_cpu_primary/fixtures/run_full_core.py \
  results/fpga_cpu_primary_20261115/fixtures_a \
  results/fpga_cpu_primary_20261115/replay_full_NEW \
  --frozen results/fpga_cpu_primary_20261115/full_synth_f_wordmux/source \
  --sources-list accel/lookahead/fpga_cpu_primary/delivery/sources.json
python3 accel/lookahead/fpga_cpu_primary/fixtures/run_full_core.py \
  results/fpga_cpu_primary_20261115/fixtures_a \
  results/fpga_cpu_primary_20261115/replay_conservative_NEW \
  --frozen results/fpga_cpu_primary_20261115/full_synth_f_wordmux/source \
  --sources-list accel/lookahead/fpga_cpu_primary/delivery/sources.json \
  --latency-ns 160 --issue-ns 10 --skip-negatives --skip-stress
```

The second command runs32 positive samples plus11 rejects; the third runs20
positive samples and reuses rejection coverage from the second. Each run
freezes source hashes, exact tool commands, service parameters, outputs and
traces. `fixtures_wordmux_a/commands.json` and
`fixtures_wordmux_conservative_a/commands.json` retain the commands actually
executed for the reported results. The local miter is separate from the full
core and does not grant area or timing qualification.

`delivery/archive.py --verify` checks the compressed evidence and source
bindings. To inspect raw evidence elsewhere, use `--restore` with an entirely
new destination; restored source/fixture paths in the replay commands must
then point to that destination. Vendor projects and DCPs are retained in the
original workspace and represented by digests, not included as Git binaries.
Large original inputs and software executables follow their explicit retained
path/hash receipts; a restored evidence archive does not manufacture them.

For a new complete-core OOC project, `delivery/prepare_eda.py NEW_OUTPUT_DIR`
freezes the current closure and emits `setup.tcl`, `clock.xdc` and a synthesis
report script. In Vivado2022.2 Tcl, source that new setup, run
`launch_runs synth_1 -jobs 8`, then `wait_on_run synth_1`, and collect the actual
reports. The selected run additionally records census/constraints/path reports
in its source-bound collector. Resource review precedes implementation;
`full_synth_e_restructured/post_opt` retains the actual standard opt-only
script, reports and failure, including the reset-BUFG timing limitation.
Do not reset or relaunch a retained active project as a replay shortcut.

The model runner and service conversion are documented in `model/README.md`.
Its selected full-batch receipts already exist and are explicitly reused; a
new physical frequency requires new nanosecond-to-cycle calibration and full
executions, not dividing the existing cycles by another frequency.

For a progress snapshot while a vendor run is active, pass
`--in-flight-dir results/fpga_cpu_primary_20261115/full_synth_f_wordmux`
to `delivery/archive.py`. It explicitly omits terminal checkpoint digests in
that subtree; completed test/log snapshots remain archived. An in-flight DCP
must not be interpreted as a verified final checkpoint.
