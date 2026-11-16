# CPU-primary complete L1 core

[Current completed results, conclusions and in-flight experiment (2026-11-15)](../../../docs/lookahead_fpga_cpu_primary_progress_20261115.md).

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

The selected candidate is now the31-source wordmux closure in
`delivery/sources.json`. Its full RTL52-sample/11-rejection results and explicit
reuse of160 complete model_g samples are bound by
`model_calibration_g_wordmux_a/calibration_reuse_contract.json` under the raw
result root. The previous e core failed actual post-opt capacity at1,351,028
LUTs; current f synthesis completed at1,244,096 LUTs (95.43%). Its terminal
synthesis reports/source binding are audited; actual standard-opt resources are
1,241,143 LUTs (95.20%) with terminal reports/checkpoint verified. Full-core
place/phys-opt/route resumed from that checkpoint at23:54:12UTC. Neither result supplies a qualified
full-core frequency yet. See the closure report for current qualification.

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
