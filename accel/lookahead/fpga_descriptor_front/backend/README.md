# Backend parent context

This candidate preserves ccec3da's enum2, finite scratch, K8 whole-word canonical,
PV RAM and shared tagged-port RTL. `df_backend_context.sv` adds synthesizable
launch/capture boundaries so original external-input-to-PV-RAM paths become real
parent-register-to-RAM paths. No original source or result is edited.

`df_fifo2` is a registered depth2 queue, with no empty fallthrough or full-edge
capacity borrowing. Independent instances cover each bank's candidate and opcode
input, plus the shared physical request and physical return. `df_ack_slice`
holds directory events and completion results. It captures without acknowledging,
waits for actual downstream acceptance, then returns a registered acknowledgement.
Thus canonical ownership survives external output backpressure; even zero-event
transactions pass the real capture/consume/ACK chain. Directory-ready means the
actual directory operation has completed, including its RAM writes.

The exact edge contract is `../coordination/backend_interface.md`. Its added
capacities/delays are explicitly communicated to the new finite-model worker.
The local four clients are canonical0/canonical1/scratch0/scratch1. They are not
the full global fabric's EDGE/control/canonical/scratch classes. Full integration
must replace the local owner fabric at those logical client pins and retain the
common finite network's concentration and return arbitration. This local replay
and OOC do not qualify that different composition or a complete kernel.

## Functional and cycle evidence

`results/fpga_descriptor_front_20261114/backend/` holds the raw runs.

* `sim_reg_fixed`: all16 native/stress fixtures,19waves, fixed16-edge external memory.
* `sim_reg_jitter`: same19waves with bounded request, directory and completion stalls,
  and out-of-order returns. Complete labels/PV/events and final drain pass.
* `sim_reg_ops`:2048 explicit updates/unchanged updates/valid POPs,1024 directory
  events,1024 zero-event completions,3072 physical requests and responses.
  Both banks fill all8 canonical records and both opcode FIFO2s saturate.
* `sim_reg_port`:2048 requests, all32tags, allfour clientFIFO4s, physical returnFIFO4
  and both new physical FIFO2s saturate. Return payload is held while blocked;
  all request/response payloads and final drain pass with true out-of-order returns.

`calibrate_slices.py` independently predicts registered ready/valid/payload from
boundary input pins, including backpressure and deferred acknowledgements.
`calibrate_canonical.py` independently predicts K8 slot selection, generation,
PV capture, request/apply/PV/publication RR and retirement from canonical boundary
inputs. `sim_reg_ops/canonical_calibration.json` checks11749cycles/bank. The frozen
`integration/calibrate_port.py` also replays all2907nonresetcycles of the new
saturated context's inner physical-port boundary. These are exact local cycle
checks, not whole-batch performance or full-network calibration.

Native fixtures use their frozen owner0 projection/prestate and actual full14bit
PV clear; graph POP/front FP32/native map export are not within this local test.
No historical baseline experiment is rerun. Added context overhead is measured
against read-only historical receipts, rather than silently counted as free.

## Reproduction and failures

Use Vivado2022.2 on `xcu280-fsvh2892-2L-e`. Tcl entry points are `run_reg_fixed.tcl`,
`run_reg_jitter.tcl`, `run_reg_ops.tcl`, `run_reg_port.tcl`, and `run_ooc_b.tcl`.
They use distinct result directories; choose a new run name before rerunning.
`setup.tcl` lists all frozen dependencies and new context sources. `prepare.py`
copies bound input fixtures and constructs the native TB from the historical
scoreboard without changing old files. Source bindings, explicit terminal
markers and raw logs determine whether any named run is valid.

Initial `sim_a` failed because the wiring generator parsed ANSI comma declarations
incorrectly. The failed generated source/log is retained; explicit token parsing
fixed it before any passing run. `sim_port_a` is superseded by `sim_port_b` because
the saturated memory stimulus needed to retain response payload under backpressure.
Neither is labeled an architecture no-go. Early replay parser failures came from
irrelevant ready values on invalid payloads and four-state read-request write-data;
final replay ignores only invalid-ready and preserves all payload symbols exactly.

OOC uses unchanged5ns, uncertainty0.1ns, I/O min0.1/max0.8ns budgets, no false paths,
no multicycle exceptions and no timing waivers. All new registers carry functional
payload/control and incur latency/capacity in simulation. Actual final route reports,
methodology dispositions and status are recorded in `ooc_b/` and `summary.json`.
No complete-kernel frequency or board measurement is claimed.

The initial context FIFO2 inferred LUTRAM; final `df_context_slices.sv` uses
`ram_style="registers"` to obtain real launch FFs. Four recompiled final suites
have byte-identical boundary/transaction/metric traces against their passing
pre-inference-repair runs (`physical_inference_fix_pin_cycles_identical=true`).
`ooc_a` retains the preliminary routed result; `ooc_b` is the final FF version.
No capacity, delay, interface budget or canonical algorithm changed in this repair.

Raw native `transactions_1.csv` inherits the field name `retire` from the old
scoreboard; in this wrapper it denotes external result consumption. Actual
canonical word/slot release occurs one ACK edge later. The final explicit-op
stage replay matches all2048 observed internal releases to that exact +1edge;
`canonical_calibration.json/deferred_ack_proof` records it. Final `done` waits
for internal release and all context queues, so wall-cycle totals include it.
The raw field is retained without silently relabeling historical or current CSVs.

Independent physical trace checking confirms all75868 final native fixed-run
responses arrive16edges after actual external issue; the request/return context
residence is charged in addition. This is the declared80ns service condition,
not a measured board memory latency. `context_cost_vs_readonly_history.json`
separates context overhead from the frozen no-context K8 local result.

## Final routed result

Final B actual5ns: setup+0.005ns,hold-0.080ns/2450failing outer input paths,
pulse+1.800ns. Every negative hold terminates in new parent launch/configFFs;
none reaches frozen `core/`. Real internal register paths meet setup+0.005ns
andhold+0.011ns. Overall OOC remains **ROUTED_LOCAL_TIMING_FAIL** under unchanged
min0.1/max0.8ns external budgets; this is not a whole-context200MHz or full-kernel
qualification. All12check_timing categories0,32existing SYNTH-5 mappings and
1572external-output-only RTSTATnets are explicitly dispositioned without waiver.

Actual resources:16834LUT/19184FF/12RAMB36+4RAMB18/16URAM/0DSP. Newcontext
storage is3653FDRE+4FDSE and0RAM/SRL. The full report, allnegative-path object
classification and the common-network subtraction ledger are under `ooc_b/`.
Removing only the replaced localfabric and physicalFIFO2 terms leaves the
bookkeeping value12745LUT/12029FF per2banks; this still includes potentially
duplicated142FF of fabrictelemetry and is not a synthesized global design.

`summary.json`, final source/compiled-project bindings, rawreports and terminal
receipts are collected by `archive.py`; `archive.py --verify` checks every archived
path hash and live new source binding. FullDCPs stay server-side with recorded
hashes. No commit/push is performed by this backend subtask.
