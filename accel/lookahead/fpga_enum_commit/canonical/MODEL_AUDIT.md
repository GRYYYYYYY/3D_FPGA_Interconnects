# Read-only audit of full model canonical/port timing

This audit reads `model/finite.hpp` after the parent's full functional/golden runs. It executes no model experiment and modifies no model/integration source. It does not invalidate the reported functional output comparison. It establishes that those timing totals remain conditional, with mixed optimistic and pessimistic abstractions; they are not an exactly calibrated full RTL model or a proven bound.

## Material gaps in the audited code

1. **No single held publication register / completion budget.** `canonical()` lines114–118 visits all eight records. An EVENT with no append does not consume `event_port`, and RELEASE has no shared completion budget. Multiple no-event records can therefore progress or retire within one bank/cycle after a backlog. Actual `ec_pending_k8` has one `ov/out_slot` register and at most one completion handshake per bank/cycle, including unchanged lines and stale POP. More generally the model round-robins individual event sectors across transactions, whereas the actual core holds one whole bundle until its consumer has published every event and acknowledged the bundle. The integrated wrapper's sent-events mask enforces this head-of-line behavior. Functional commutativity does not grant cycle equivalence. This can be optimistic for transactions bypassing a held completion; other interleavings can also be slower. No run is claimed to have measured the frequency or net timing impact of these cases.

2. **RR policies are different.** Model lines104–119 uses one `tx_rr`, advanced every clock regardless of which operation wins, for request/apply/PV/event/release. RTL has independent request/apply/PV/publication cursors, each advanced only on its own real grant. Scalar per-stage limits do not reproduce their order, tail, lock lifetimes or memory contention. The standalone exact replay verifier models the actual independent grant cursors; it is not the full model's `canonical()` implementation.

3. **Acceptance/read timing is an abstraction, not a calibrated PV pipeline.** `start_tx()` line89 sets due=t+4; the first read enqueue can occur at that cycle. In idle RTL, accept(c)→PV capture(c+1)→request register fill(c+2)→local request acceptance(c+3). The model's four-cycle start delay is one clock later at the canonical client boundary in this isolated case. It also snapshots PV at the canonical read response (line95), rather than at the synchronous PV read one cycle after acceptance. Under the held same-word lock the data value is unchanged, so functional equivalence can hold, but exact stage timing/port accounting has not been established by this shortcut.

4. **Same-edge reuse and phase ordering differ.** `step()` mutates state immediately; `dispatch_pop()` executes after `canonical()`. A transaction retired by canonical in cycle t can have its slot/word reused by dispatch_pop at that same modeled t. RTL `ir`/same-word hazard use the pre-edge reservation; the newly freed slot becomes admissible on the next edge. `final_backend()` can similarly benefit when its rotated service class runs after canonical. Conservative delay elsewhere cannot be used to silently cancel this difference.

5. **Physical queue/tag geometry differs.** Full model `Port` has one shared FIFO64 and reserves a tag at `request()` enqueue; only one global logical enqueue/physical port/cycle is allowed. Actual `ec_tagged_port` has four FIFO4 logical clients, can accept multiple clients into their own queues on one clock, and allocates a physical tag when moving one chosen FIFO head into the held physical request register. Its four-client RR and per-client head-of-line constraints are absent from the shared FIFO abstraction. Earlier tag reservation and serialized ingress can be pessimistic; larger shared capacity and changed head selection can be optimistic. There is no valid general ordering of complete execution times without matched replay.

6. **Return ordering/paths are abstracted.** `memory_end()` only examines `flight.front()` even when jitter changes younger due dates; the tagged RTL/environment supports out-of-order returns. The model back FIFO plus due=t+2 correctly charges a minimum two registered edges before a client sees a physical response, but it does not reproduce the RTL global return FIFO plus separate held client registers/head blockage. Canonical write ACK becoming PV-eligible at +1 and read response becoming apply-eligible at +1 are compatible minima, not full arbitration calibration.

7. **The finite directory remains an uncalibrated hardware service.** `directory.put()` updates member pool/free list/head/tail/bucket bitmap immediately at the modeled event handshake, and `dispatch_pop()` releases a member and admits its transaction in the same cycle. The finite524288/8192-per-bank capacity is explicit and there is a one-event/bank/cycle limit, but linked-list/PV/selection RAM latencies and physical port mappings for the complete directory have no corresponding RTL calibration in this audit. The local canonical fixture's finite TB directory is not that complete hardware structure.

## Properties which do match the intended logical contract

- Eight transaction records and whole canonical-line locking are explicit. Four sectors share a single lock. Per-record four-sector append state bounds retirement storage to at most32 events/bank; lack of a separate event FIFO is not an unbounded storage claim.
- Model write ACK precedes label/PV update; its word reservation lasts through all append events or the valid POP token and one RELEASE step. It does not reuse an old K1/no-ACK model.
- `pending17::old_op` and `packed_op` are checked together with frozen whole-pair semantics, including opcode7 four-sector updates. Stale POP does not publish a valid parent.
- The owner/subbank mapping is `2*(line&31)+((line>>5)&1)`, and all classes share the same32 physical port/credit ledgers. Scratch is not silently granted eight inflight commands.
- Main memory minimum16 clocks at200MHz and nominal issue gap1 are explicit; initialization counts actual canonical writes and a16384-clock PV initialization floor. These are useful conditional contracts, not frequency qualification.

## Evidence and allowed claim

The standalone final canonical fixture is F:1472 mixed operations,1988 physical requests,141-file portable evidence archive; `verify_trace.py` independently predicts the real canonical RTL stage/RR behavior exactly using observed boundary handshakes. `ram_template_equivalence.json` confirms17620 identical event records before/after the legal PV-inference fix. This validates the local implementation and its independent replay model. It does not automatically calibrate `model/finite.hpp`.

The parent's approximately262.607/265.890ms full-input results should remain explicitly **conditional model results**. No impact correction or rerun is produced by this audit. The known gaps have both directions, so the totals should not be labeled a conservative upper bound or a qualified hardware no-go. Full-kernel frequency/fit and global directory/router implementation remain separate evidence requirements.

Parent follow-up: publication-slot and completion-bandwidth violations are implementation bugs in the conditional timing model and must be corrected together with the separately identified output-export bandwidth issue before the next B freeze. They must not be hidden behind a general conditional qualification label. Findings and the held-PUB/one-completion policy were sent directly to the model worker. This audit worker remains read-only on model source; that worker owns the fix and affected full rerun. Remaining non-identical global arbitration/RAM-stage details still require explicit qualification after those correctness-of-capacity fixes.

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
