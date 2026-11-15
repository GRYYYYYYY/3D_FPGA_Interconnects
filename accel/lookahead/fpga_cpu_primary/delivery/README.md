# Reproduction and evidence handling

The case is independent from previous candidate branches and rooted at the
fixed baseline SHA. Raw data belongs under `results/fpga_cpu_primary_20261115`.
Large immutable workload inputs remain at hash-bound existing paths in
`experiment_config.json`; they are not silently recreated or replaced.

- `sources.py` resolves the actual30-file production RTL closure.
- `prepare_eda.py OUT --period 5` creates a new source freeze, real project,
 5ns clock/boundary constraints and synthesis report script. Existing source
 freezes are rejected rather than overwritten. The actual started run is
 `full_synth_b`; the first setup attempt is retained as aborted.
- Use Vivado2022.2 Tcl-mode MCP. The project setup uses the supported explicit
 `set_property -name {...MORE OPTIONS} -value {-mode out_of_context}` syntax.
 Launch synth_1, wait for it, and collect full utilization/hierarchy/timing/DRC
 plus `census.tcl` with `cp_report_dir` set to the result directory. A live or
 successful syntax run is not a fit result.
- Implementation is conditional on actual fit. `prepare_impl.tcl` in the
 current raw run preserves OOC mode through init_design, applies the tested
 external clock-source context, and enables normal pre-route physical
 optimization. It is prepared, not proof that implementation has run.
 `route_reports.tcl` collects actual setup/hold/route/DRC/methodology and XDC.
- `process_identity.py` records original Linux process birth/boot identity;
 `supervision.json` records the single transition owner. A webserver status
 recursion error does not trigger a new job. Direct Tcl proxy/run log and the
 birth-matched process are authoritative for this installed tool version.
- `audit_synth.py` classifies actual source-bound warnings and waits for real
 reports before asserting any mapped-resource observation.
- `reuse_evidence.py` reconstructs/verifies only new copies of historical
 GPU/model/native evidence. It does not launch any historical benchmark.
- `check_protection.py` verifies20 protected refs, the guide hash and that
 changed paths remain restricted to this candidate.

The complete-core replay entry is `../fixtures/run_full_core.py`. The selected
finite model entry is `../model/run.py`. They freeze their compile closure,
commands, tool/compiler, binary/input/output identities and terminal receipts.
Model full40 runs require `--full-authorized` after the coordinator selects the
final candidate/frequency; this is an orchestration guard, not a request for
additional user permission. They are already authorized by the task.

At final delivery, `archive.py` builds a compressed content-addressed archive
under `../evidence_snapshot`; `archive.py --verify` verifies every object and
current source binding. `archive.py --restore NEW_EMPTY_DIRECTORY` reconstructs
the raw subtree without overwriting an existing or historical directory.
Vendor generated trees/checkpoints are excluded from Git and explicitly
identified; actual source, reports, traces and complete outputs are retained.
The selected run's DCP stays in the original raw workspace with a digest and
reproduction flow. Large original inputs remain external, exactly hash-bound.

Archive creation/verification is a delivery step; existence of this script does
not mean a final archive or final commit already exists. Consult the main
closure report and terminal receipts for completed stages.
