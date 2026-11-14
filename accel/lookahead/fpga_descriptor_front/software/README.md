# Same-semantics packed CPU and software evidence

`cpu.cpp` uses real persisted packed descriptor backing and a prepared packed
edge array. The complete backing is decoded and compared to native row/type/cell
semantics before execution; no metadata/row-derived descriptor is recomputed in
the resident hot path. Each valid POP decodes once, updates the valid target
branch, and retains begin/end for expansion. Stale POPs do not fetch descriptors.
Immutable wave-start parents, FP32 RNE whole-pair min, eligible order and target
completion semantics are preserved. Every sample resets labels, proposals,
pending/version, output, seen, directory heads/tails/bitmap and free pool.
This is a software implementation, not a hardware service/cycle model.

`descriptor_a`/`software_functional_a` contain all100native complete samples plus
20forced16B small samples, exact to frozen ALT/native golden. BNN full output SHA:
`a8ca4003a3b015145635a3f776bb62a3aec1ec2121a1fbfc8712d2a2dc1c8c3f`;
LSTM: `6b2acd7718d880075d653b3b83f1fa3abb5161f6f346ed39c3aa1285160a95cf`.
The source-bound functional runs use4threads, profile counters and one initial
batch; their6.016595860/4.737579348s are contention-unqualified warm-up diagnostics,
not a formal performance baseline and not comparable speedup claims.

Measured construction wall times were0.633990821/0.969947226s, plus backing writes
0.220795086/0.249685633s. Native load/preparation, admission, independent decode and
cache validation are separately recorded. These measurements were also under
potential contention. E2 must add whichever construction/cache validation and
transfer steps the deployment actually uses; no free amortization is assumed.
No transfer, board or new native Process runtime was measured here.

`formal.py --isolated-window` is ready for the parent-selected quiet window after
model/EDA work is complete. It uses8distinct permitted physical cores, explicit
OpenMP placement, three independent processes per case and one warm-up plus three
retained complete batches per process. It checks outputs every repetition,
records environment, detects active model/EDA/software competitors before and
during the run, and reports process means separately. Profile counters are
compiled out in this run. Filesystem output export is outside resident; output
memory stores and sample state resets remain inside. Formal execution is pending
the shared-node window; do not treat functional timing as formal.

`software_reuse_a/software_baselines.json` independently extracts completed,
fixed-commit CPU receipts, actual raw repetitions, environment and source hashes.
The strongest existing8thread prepared-POP controls on the H100 worker have
mean-of-process-means3.654426308/3.669705272s for BNN/LSTM. A separate prepared-POP
cohort has4.534045816/4.623006792s; private-INF has4.794919236/4.766490565s. All
cohorts are retained; the fastest valid one is not hidden. There are3independent
processes with3retained repeats each, not9independent processes. Host is Xeon
Platinum8462Y+ on the H100 worker, distinct from this FPGA tooling host.

The same report separates existing native stock/flat/pipeline/ALT E2 and Process
receipts. Stock/flat/pipeline lack a resident complete-batch wall timer; summed
router worker-seconds and MapLookahead E2 cannot fill that field. No claim of
resident superiority over original VPR follows from beating CUDA or ALT CPU.

`software_reuse_a/native_identity.json` rehashes every original/native input
section, the new full output, the old actually imported full output and final
wire-map. The unchanged import adapter plus identical inputs/sample order/output
bytes justify reuse of the actual previous native/QoR chain. This is an explicit
transitive identity proof, not a new VPR run. BNN map:
`f9805a5660060b1b68e995120fa3009f449cbd46a6d39e39433c16b95595b82c`;
LSTM map: `2f5746ca56a0581ee3ea45b6e67f9b1b4ec41f1f6aa501f174022b880394a57d`.
BNN's original exported embedded golden is STRICT and differs from ALT; only
the six input arrays are matched to the qualified native ALT capture, and the
new output is matched to its ALT tail. STRICT equivalence is not claimed.

No previous GPU/INF/prepared-POP experiments were rerun, and no CUDA supplement
was rewritten. A new descriptor CUDA comparison requires the parent to select it
after the main candidate provides the guide's required performance evidence.


Final formal results are now available in `software_formal_a/terminal.json`:
BNN/LSTM means of process means 2.842626751333/2.933218058 seconds, all exact and
all competition checks passed. `isolated_window.json` proves sixteen owned EDA
processes were temporarily suspended with zero CPU-tick progress, then resumed
with the same identities. No experiment was restarted. This supersedes the
pending formal-run status above. `construction_isolated_a` adds one isolated
conversion observation per case with exact backing identity. The self-contained
report gives stage costs and host/boundary limitations.
