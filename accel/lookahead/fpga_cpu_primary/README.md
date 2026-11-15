# CPU-primary complete L1 core

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
