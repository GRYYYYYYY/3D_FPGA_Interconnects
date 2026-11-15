# L1 production bank integration

`cp_backend_bank.sv` implements the [interface](interface.md). Instantiate64
banks with BANK_ID0..63. No local `ec_tagged_port` is included: CAN/SCR requests
are connected to the shared network's logical sources. `sources.json` is the
complete synthesis/simulation RTL closure (testbench added by `run_test.py`).

The derived files retain L1 whole-word K8 semantics and serialized directory:

- `cp_pending_k8`: old canonical K8 with full32-bit per-slot generation,
  opaque20-bit cookie captured at actual `free_slot` and read at `out_slot`,
  runtime64-bit label base checked before narrowing, read kind4/5 and write6,
  full response generation/kind/status checks. IDs are proven slot0..7;
  wrapper rejects nonzero upper localID bits before forming internal slot3.
- `cp_enum2_bank`: old enum2 plus actual initialization/expand-drain status.
- `cp_scratch_finalize`: old finite2048-ID scratch, mergeFIFO16/commitFIFO16,
  plus actual initialization/expand-drain status. Scratch identity is full
  relative line (within proven20-bit graph capacity), zero-extended32 with
  all32 return bits checked; local ID is BANK_ID, also checked in full.
- `cp_backend_bank`: candidate/op FIFO2, internal commit priority, immutable
  result ACK context, real directory control FIFO2s and event wrapper. Event
  capture→submit→real RAM response→deferred ACK allows measured II8. There is
  no L2 journal or early whole-word release.

`reset` reinitializes actual RAM state. `sample_clear` is a one-edge pulse at
idle; global controller may instead assert reset at a drained sample boundary.
`wave_restart` only drops the latched flush; enum reopens and scratch clears its
bitmap while PV/directory/generation persist. Wait `expansion_idle` before
starting the next expand phase. `initialized` includes real PV/directory/enum/
scratch initialization. `done` includes real canonical retirement, all memory
ACKs, publication and control drain, not just candidate enqueue or FIFO empty.

## Tests executed with XSim2022.2

The final targeted run is `results/fpga_cpu_primary_20261115/backend_bank_b/`.
It uses actual SET_BITS10, WORD_BITS14, K8,8192 directory members and2048 scratch
IDs. Frozen source hashes, xvlog/xelab/xsim commands, all logs and explicit PASS
are in that directory. Run without overwriting completed evidence:

```sh
python3 accel/lookahead/fpga_cpu_primary/backend/run_test.py results/fpga_cpu_primary_20261115/backend_bank_new
```

Positive section:27065 cycles,385 candidate handshakes,97 real canonical
commits,385 directory events,220 CAN and64 SCR requests,33 out-of-order CAN
responses, and280 observed consecutive APPEND command intervals of8 clocks.
Checks include eight simultaneously live K8 operations with blocked results,
opaque cookies under OOO returns, same-word stale POP contention with a checker
that releases the word only on the actual core retirement ACK, non-echo memory,
request/result/control stability under backpressure, six ways across16 sets
forcing32 unique scratch spills, and every committed whole line against an
independent minimum oracle. Directory MIN/TAKE/RELEASE traverses the exact8
SEED members and376 candidate members from actual RAM. The second wave verifies
that PV version1 survives restart and advances to2 on a new bucket. Sample
clear verifies actual initialization and reset state.

External negative tests flip bit31 of returned generation, returned localID,
and scratch generation; all are rejected without aliasing. A runtime label
base of2^32 is rejected before any memory request. No forced internal state or
backdoor expected-PV injection is used. Original run_a remains preserved;
run_b extends coverage without changing bank RTL.

This is local bank behavioral verification, not full-top calibration or timing
qualification. Parent integration owns full graph, global network, output and
phase/controller checks. Formal coverage and postroute simulation are not
claimed. The reused2022.2 non-project simulator driver follows the Ross RTL
simulation workflow; no historical Vivado session or old source was modified.
