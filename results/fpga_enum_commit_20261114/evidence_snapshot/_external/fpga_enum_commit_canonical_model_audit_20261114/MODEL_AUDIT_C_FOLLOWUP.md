
## Follow-up: distinguish audited A from corrected C

The original findings above apply to the audited **A** `model/finite.hpp`, SHA256 `5709772b8fc44252e1c38878c4a1a36c0c1077a293432282152702a3381257bc`. Its original audit copy and `results/fpga_enum_commit_canonical_model_audit_20261114/source_binding.json` remain preserved. They must not be read as a list of outstanding bugs in the corrected C implementation.

Read-only follow-up at 2026-11-14T09:40:55.665556+00:00 inspected the revised **C** current source, SHA256 `a305cffaccf8b57ed8521b0230bfe13f5a9ef39952e83579e78e9127a3b8a9b3`. This identifies the source file, not a Git commit or a completed experimental receipt. The parent's full C run is in progress; no new experiment was performed for this review.

Resolved in the reviewed C canonical path:

- One held `pub_slot` per bank serializes the complete publication bundle, including unchanged-line and stale-POP completions. Another transaction cannot bypass that held bundle. There is at most one completed transaction per bank per cycle.
- The last actual directory append and final completion occupy separate edges. The integration wrapper computes `remaining_events` from the pre-edge sent mask, so last-directory event at D allows completion no earlier than D+1.
- PV is synchronously captured at acceptance+1; the earliest local read admission is acceptance+3, rather than A's response-time PV snapshot and arbitrary four-cycle start.
- Request, apply, PV-write and publication have separate persistent grant cursors. This resolves A's shared cursor advanced on every clock. The local request-register versus global logical-enqueue distinction remains an explicit port-model abstraction below.
- A released slot has `reusable_at=t+1`, and the released whole word remains blocked through the release edge even if another slot is free. This resolves same-edge slot and same-word reuse.
- Same-edge replacement of an old completed PUB is **allowed** by the actual RTL `ec_pending_k8.sv`: `if(!ov||ordy)`. No completion bubble should be added. Final F evidence shows bank0 `RESULT_ENQUEUE cycle=57690 slot=7` concurrently with `RETIRE cycle=57690 index=365`, followed by `RETIRE cycle=57691 index=366`. The newly filled bundle cannot be consumed before the next edge.
- A PV write becoming EVENT at C is not eligible for PUB selection until C+1; C's `due=t+1` guard matches that pre-edge RTL eligibility.

The follow-up found no additional blocking capacity/semantic error in this rewritten canonical path. This is a source review of the stated fixes; it does not certify complete-model cycle equivalence or replace the full C run's eventual receipt. The separately corrected output-export bandwidth and ACK-backed output path belong to the model worker's implementation/validation.

Still unqualified after those fixes:

- Full-model global FIFO64, tag reservation at logical enqueue and one global ingress/port/cycle differ from the local RTL's four FIFO4 clients, tag allocation at physical request-register fill and independently admitted client requests. Actual queue geometry, registered request holding and arbitration therefore still require matched calibration.
- Return FIFO/per-client register head blocking and out-of-order completion behavior are not identical to the full model's flight FIFO/due abstraction. The nominal minimum registered delays alone do not establish exact full-port behavior.
- The full global directory's member/free/head/tail/bitmap RAMs, port counts and registered lookup/append/selection timings remain uncalibrated hardware services. A finite software member pool and one-event-per-bank limit do not establish that implementation.
- Local canonical cycle replay and local OOC, wherever separately qualified, do not grant full 64-lane/64-subbank/32-port kernel fit, frequency or end-to-end timing qualification.

These residual gaps retain the full-model timing result's conditional status. They are distinct from the A publication-capacity bugs which C has explicitly corrected. This follow-up does not relabel those fixed bugs as current limitations.
