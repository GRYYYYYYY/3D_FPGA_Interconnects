# Descriptor-front continuous finite model

This implementation executes the complete native ALT algorithm and compares its
full acknowledged output with the existing frozen golden. Historical parents,
candidates and spill traces never drive the performance path. C0 is a fresh run
under the new common service contract, not historical final D relabeled.

C0/F1 use8 groups of8 lanes; F2/F3 use16 groups of4 lanes. F1/F3 read the actual
packed per-sample descriptor backing. C0/F2 retain aligned ROW reads (two when
node%4==3) and META reads. All variants reserve the same descriptor address region
before canonical/scratch/output/cost memory, so downstream address striping is not
an accidental experimental variable. Every configuration has64 arithmetic lanes,
256 E contexts,512 beat slots,128 fork tokens and128 ready capacity. The fused D
records remain in their token slots until both independent branches hand off.

The six-stage arithmetic pipeline is elastic stage by stage; it is not a FIFO
with a nominal due delay. An immutable operand capture releases E/beat state only
for the next edge. Its output crosses the real one-entry parent context before
per-lane FIFO4, a registered RR winner per destination, bankFIFO16 and the backend
candidateFIFO2. At most one candidate leaves each source lane and enters each
bank per cycle. The exact whole-pair FP32 operation remains the frozen positive/
+0 numerical contract; no precision reduction is part of descriptor packing.

The front parent context includes one-entry elastic reserve command, token ACK,
POP, request, response, target and candidate boundaries. These are additional to
the leaf and common network. Descriptor response, decode, held branch selection
and handoff occupy distinct edges. A blocked target or adjacency offer remains
held; a younger zero-degree parent cannot bypass it. Actual token allocations,
new reservation requests and POP canonical admissions are globally limited to8
per cycle independently of group count.

`transport_adapter.hpp` uses the exact shared `PhysicalPort` and registered router
primitives. Its composition was independently compared cycle by cycle against
`services/MemoryNetwork`:208 logical sources,32 ports,45071 requests and more than
12000 cycles passed. It includes sourceFIFO4, registered request RR, fourFIFO4
clients/port, physical request/tag register, requestFIFO2, physical memory,
responseFIFO2, returnFIFO4, client return registers and registered source return
RR. A tag is released only when the port accepts its response into returnFIFO4;
a tag freed on an edge cannot be reallocated on that edge. The fixed memory
assumption is80ns/5ns at assumed200MHz; the jitter stress may return transactions
out of order. Front and canonical source request holding registers are explicit;
scratch and INIT/output/cost FSMs directly hold their FIFO input payload.

The global fabric replaces the old local backend fabric at its logical clients.
It does not cascade a second set of32 tags or transfer a different local client's
arbitration timing wholesale. No source FIFO is unbounded and no beat is served
to unrelated parents for free.

`directory_adapter.hpp` instantiates64 exact synchronous `DirectoryBank` FSMs
and the actual `MinimumCollector`/six-stage `MinimumTree`. Each bank has8192
members,4096 head/tail pairs and real serialized free-list/member/bitmap RAM
accesses. APPEND retirement waits its actual response. RELEASE captures one
finite member holding register/bank, eligible for POP reservation next edge.
There is no direct asynchronous linked-list or bitmap access on the runtime path.
All-bank MIN collection is charged before bucket decisions; TAKE is separate.
Initialization performs8192 actual directory write cycles, overlapping independent
PV/output/canonical initialization as specified.

Canonical input crosses FIFO2 before K8 acceptance. It preserves held whole-word
locks through physical write ACK, PV update, actual directory events and result
retirement. The parent context uses deferred ACK, not enqueue-based word release.
Enum2, finite consumed bitmap, single expand scratch RMW, single finalize merge,
mergeFIFO16 and common commitFIFO16 remain explicit. FIFO acceptance uses pre-edge
fullness. Registered expansion status/flush and final done observation are charged.
The accumulator retains the finite1024-set/four-way model; its full physical
pipeline and whole-top timing are still outside complete RTL calibration.

Every sample performs actual canonical initialization writes and ACKs, all cost
reads, PV/output/directory/bitmap initialization and complete output export ACKs.
CPU processes may simulate independent samples concurrently; hardware times are
summed in sample order. No hardware interleaving or overlap is inferred from CPU
parallelism. Every full sample is a restart checkpoint with exact binary/source,
input, golden, command, PID identity, log and terminal receipt. Attempts are
preserved and a live matching task is never launched twice.

## Counters and interpretation

`finite.json` partitions complete cycles into init, POP+expand, finalize, export
and other (seed/MIN/bucket/control drain). The partition sums exactly to cycles.
`waves.csv` gives each wave's functional work and exclusive phase boundaries.
`wave_services.jsonl` gives fresh group request/return, physical-port traffic and
lane-emission deltas. Complete source conservation and full output hashes are
checked independently by `verify.py`.

Per-group occupancy histograms have the order fork,H-or-D,M,ready,E,beat. They
sample all ordinary `step()` edges; explicit initialization/export loops are
separately charged and are not falsely included in that denominator. Per-source
counters distinguish sourceFIFO rejection from leaf request-holder stalls.
Per-bank pending-full, publication and scratch-busy counters overlap across banks
and must never be summed and divided by frequency as elapsed time.

The fixed observer in expand is lane0/group0, with exclusive priority labels:
0 actual operand emission;1 arithmetic/candidate routing;2 live E awaiting feed;
3 H/D;4 fork/POP;5 bank0 scratch;6 directory work elsewhere;7 other/drain. Finalize
observes bank0:0 retirement;1 publication;2 K8 full;3 scratch;4 commit/input;
5 enum;6 other-bank/tail;7 bitmap/drain. The per-wave critical-tail observer chooses
the bank with latest actual busy/retirement cycle, then retains that bank's same
exclusive histogram. `emit_population_histogram` counts actual captures0..64.
These are diagnostic observations, not a counterfactual proof that increasing a
particular capacity improves wall time. Optional candidates require parent review
of complete results and a one-variable finite implementation.

## Execution

From this worktree, choose a new result name whenever timing/source changes:

```
DF_MODEL_RUN=model_d python3 accel/lookahead/fpga_descriptor_front/model/run.py small --configs C0,F1,F2,F3 --jitter --workers 4
DF_MODEL_RUN=model_d python3 accel/lookahead/fpga_descriptor_front/model/run.py representative --configs C0,F1,F2,F3 --workers 8
DF_MODEL_RUN=model_d python3 accel/lookahead/fpga_descriptor_front/model/run.py full --configs C0,F2 --workers 12
python3 accel/lookahead/fpga_descriptor_front/model/verify.py results/fpga_descriptor_front_20261114/model_d
```

Representatives were frozen before new timings: BNN2/19/35 plus31, LSTM7/19
plus18. Additional tails minimize candidates in the last completed historical D
wave; exact paths/hashes and selection rule are in `representatives.json`.
Completed source-bound receipts are reused. The runner takes global/per-sample
flock locks and checks PID/argv/boot/start identity before any launch.

All resulting seconds remain `conditional_seconds` at the stated assumed clock
and memory contract. `complete_kernel_clock_qualified=false`,
`estimated_seconds_at_qualified_clock=null`, `board_measured=false` and
`board_measured_seconds=null` until the corresponding evidence actually exists.
Local primitive calibration does not qualify the complete assembled kernel.

## Calibration boundary and tag lifetime

The208-source/32-port adapter check is C++ composition equivalence to the shared
network model. Actual network RTL stress is at8sources/2ports; full208/32 geometry
has separate synthesis evidence, not a complete native RTL run. The candidate
router and64-bank directory/MIN tests have their own explicit geometries and
receipts. Output bank/forwarding/export/ACK local replay likewise does not join a
complete graph kernel. C0/F2 ROW/META control, whole native assembly, physical
opaque32-bit kind/id/generation packing adapters and the full accumulator pipeline
remain outside end-to-end RTL qualification. Aggregate timing error has no proven
sign in either direction; this is not a conservative upper/lower timing bound.

Active fork/E/header/metadata generation increments use8-bit wrap. A token or
context cannot be released until all its required responses/branch handoffs have
completed; last E operand checks no outstanding response, and physical tags cannot
be reused until their actual return acceptance. Next-edge slot/word reuse prevents
same-edge aliasing. Thus no old live transaction survives the corresponding
context's generation reuse. The unused legacy reserve_token helper is not called
by dispatch_pop and does not define the active generation policy. The actual
32-bit wire packing adapter is not implemented by this C++ metadata structure;
field-fit bookkeeping must not be described as an RTL implementation or proof of
complete fabric frequency.

## Final result

Final D completed all160 C0/F2 full native samples and passed334 unique sample
checks. See `RESULTS.md` for actual phase totals, matched representatives,
qualification limits and the complete negative result. No model process remains
at delivery; no optional parameter candidate or complete top was launched by
this worker. Frozen core sources and binary are unchanged after the D run.
