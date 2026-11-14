# Pending concurrency / same-wave streaming: initial configuration no-go

This run read `CODEX_FPGA_INF_NEXT_AFTER_A64C934.md` in full and resumed the
existing `accel/lookahead-inf-pending-stream-20261114` worktree at
`a64c934956be6514a27f66fd1a46f09ef4a2fab9`. Stage A is complete. Stage B found a
**decisive necessary-bound failure for the initial 64-context, single outstanding
edge-read/context frontend**. The conditional stop rule applies before building
new RTL or a complete kernel. Stages C–E were not entered. This is not a rejection
of architectures with more edge-read concurrency or actual edge-data reuse.

## Decisive budget

At the assumed 200 MHz, the fixed 80 ns memory response contract is 16 cycles.
A 32B edge response carries at most eight 32-bit candidate descriptors. In the
retained frontend, each of the 64 contexts has at most one edge read in flight.
Integrating the number of outstanding edge reads over time gives

```
64 * C >= 16 * ceil(N_candidate / 8)
```

This bound does not use the old schedule's replacement/spill counts. Candidate
work is unchanged under ALT wave fences and was reconfirmed by new full native
capture/output verification. The bound already assumes every beat is full and
ignores row/metadata reads, FP32, candidate emission, initialisation, scratch,
canonical finalize, directory, output traffic, all conflicts and all tails.
Adding those costs cannot rescue the configuration.

| Complete 40-sample input | Wait-only lower bound, cycles | Conditional lower bound at 200 MHz | Qualified GPU target |
|---|---:|---:|---:|
| BNN | 40,216,786 | 0.201083930 s | 0.151799969444 s |
| LSTM | 40,922,272.25 | 0.20461136125 s | 0.15949799988888888 s |

These are arithmetic necessary bounds, **not FPGA runtime measurements**.
The bound exceeds the targets by 32.47% / 28.28%. Even granting perfect overlap
of edge-wait time with candidate emission leaves this wait-only failure. That
is an optimistic arithmetic relaxation, not an implemented double-buffer RTL
experiment. The earlier 135/137 ms port bounds remain correct but insufficient:
they omit the finite frontend's outstanding-read limit.

At least 85 / 83 simultaneous edge reads would be necessary just to fit this
wait-only budget; those values are not sufficient configurations. A future
candidate must explicitly implement more edge-read slots, or reduce requests
through verified edge reuse, then recount traffic and resources. Increasing
pending contexts from 8 to 16 cannot change this frontend limit. No broad scan
or automatic expansion into another frontend/cache architecture was performed.

The source basis is `InfFiniteService::expand` (phase 2 read before phase 3
candidate emission) and `sparse_frontend` (`EDGE_WAIT` before `EMIT`). The latter
also has only one edge read in flight per context. No local 200 MHz OOC evidence
was transferred to this candidate.

## Implemented and executed

- `stage_a.py`: complete base/software/input binding, exact Decimal budgets,
  native representative selection, and append-only CUDA source supplement.
- `capture_reference.cpp` / `trace_capture.hpp`: the frozen pending17 native
  oracle with trace hooks. No ALT FP32, comparison, pending or closure semantics
  changed. All four complete outputs match old goldens byte for byte, including
  both 40-sample BNN/LSTM batches. The new captures contain immutable POP labels,
  pending versions, parent-to-edge sequences and complete expected final lines.
- `screen.cpp`: bounded by-word POP contexts, FIFO arbitration of ready requests
  over 32 physical ports, 32 shared credits/tags per port, 64-request queues,
  64 frontend contexts, and a 64-token streaming FIFO. Valid POP reserves token
  capacity before pending clear/word release. Stale POP does not emit a parent.
  Same-word input order and tag/credit conservation are asserted.
- `run_screen.py`: 94 executed cases, all passed. Five matched configurations
  (`K=1` separated; `K=8/16` separated and streaming) over 17 actual native waves;
  nine additional small-graph cases apply deterministic response jitter and
  256-cycle token-consumer backpressure. No repeated short-trace concatenation.
- `analyze.py`: independent binary trace inspection, capacity/flow checks,
  per-bank/per-port evidence references, comparisons and the necessary-bound
  decision. Its bound checks also pass for every selected large-wave replay.

The initial worktree checkout was interrupted before writing its index. The
existing worktree was retained: the abandoned empty lock was preserved, the
index was loaded from HEAD and only missing files were checked out. No reset,
clean, rebase, alternate worktree or restarted old experiment was used.

## Dependency argument and limits

All POPs use canonical state from the wave entry. Expansion reduces proposals
only; canonical labels cannot change until every POP, parent and candidate has
finished. A valid POP token carries the captured whole-pair label, so changing
parent service order cannot change the FP32 additions captured from the original
oracle. Whole-pair minimum on admitted positive finite values is associative and
commutative, including equal pairs. Final canonical comparison occurs once per
line. Same-word POPs retain their original logical order across all four sectors;
the reservation is released only after the pending update and token publication.
Present remains independent of version, and the original pending17 transform is
called directly. No replacement numerical implementation is introduced.

For shared target cells, a complete future implementation must also serialize or
atomically reduce the whole output pair and preserve first-seen accounting. The
old full native oracle still checks those outputs and bucket completion. The new
partial scheduler does not implement the output RMW path and does not claim that
its proposal comparisons prove that path. It drains every modeled response,
context and token before ending a replay; this is a modeled POP/expand fence,
not verification of a new complete two-wave RTL fence.

## Representative evidence and causal scope

Four native waves per large input were selected using existing complete wave
statistics: largest frontier, highest old-B spill count, largest bank skew
among waves with at least 10,000 candidates, and greatest near-line reuse.
Selection inputs and trace SHA256s are archived. Exact set/word distributions
were then calculated from new traces, so the near-line metric is not presented
as proof of same-set contention. Selected waves span 13,236–2,501,149 candidates;
the largest-frontier BNN/LSTM waves contain 99,491 / 103,713 extra POPs sharing
already represented canonical words. Hot-set and per-bank counts are in
`analysis_a/trace_selection_verified.json`.

The table below is a **partial, relaxed POP/frontend schedule**, not complete
batch time. It holds all modeled service rules fixed, and is not compared
numerically with the old complete B model. K=1 is an additional matched
serialization diagnostic; the original B evidence is separately reused.

| Native wave | K=1 separated | K=8 separated | K=8 streaming | K=16 separated | K=16 streaming |
|---|---:|---:|---:|---:|---:|
| BNN sample 2 / wave 38 | 281,044 | 233,515 | 224,985 | 231,908 | 225,919 |
| LSTM sample 7 / wave 36 | 285,122 | 237,250 | 228,763 | 235,645 | 229,080 |

Concurrency reduces POP serialization; overlap adds a smaller gain. K=16 is
not automatically faster than K=8 because token backpressure and ready-order
interleaving change. Streaming FIFO peak is 64; pending context peaks reach
8/16. Fixed-latency physical credit peaks reach 16, not the configured capacity
32. Reports distinguish context occupancy sums, phase endpoints, observed
backpressure and post-POP tails; overlapping busy times are not added as total
elapsed time. `same_word_observations` and `context_full_observations` count
blocked scheduling attempts, not stall cycles. `parent_full_context_cycles`
is the sum of blocked context residence, not a count of distinct wall cycles.

## Deliberate exclusions and stage gate

The new screen implements concurrent **POP only**, not concurrent SEED/COMMIT,
canonical write ACKs or four-event retirement. Candidate whole-pair reduction
uses a verification map with zero modeled routing/accumulator/scratch latency.
It does not pretend that this map is finite on-chip hardware. Target/output
memory, full directory event service and finalize time are omitted. Response
callbacks consume ready returns immediately; there is no calibrated return
pipeline. Per-wave replay starts from captured state; it is not continuous
new-RTL execution across all waves. New-order spill counts are **not** claimed
or substituted with old counts. These optimistic omissions are acceptable for
this rejection screen, never for qualification or a success claim.

Consequently the requested new COMMIT/scratch/arbiter RTL, tag and write-ACK
regression, two-subbank OOC, complete new finite batches, full resource ledger
and full-kernel OOC are **not implemented/run**. Their omission follows the
necessary-bound gate, not a claim that the old RTL calibrates the new model.
No new full phase/stall statistics, simulated FPGA speedup, CPU/VPR ranking or
physical feasibility is asserted. `fpga_seconds=null`,
`complete_kernel_clock_qualified=false`, `board_measured=false` remain in force.
The old 864 URAM / 1888 BRAM36-equivalent reservation is not promoted to a
resource estimate for an unimplemented concurrent RTL design.

## Reused terminal evidence and maintenance

Software evidence is bound to `a64c934...`, with independent GPU archive
`cc71869709bcf3124ae81ebfdcd8f36819c4c90d`. All 254 GPU receipts and the six old
P8/F0 full batches were already terminal and were not rerun. Old timestamped
queued/running notes are retained as history. CUDA source hashes were checked
against the frozen software binding and appended under
`stage_a_v2/cuda_source_supplement`; the publisher's suffix whitelist now includes
`.cu`. Old snapshots and goldens are unchanged.

Stage-A attempt 1 used a profiling field unavailable in the older profile;
its failure receipt is retained. Stage-A v2 uses fields actually present and
new trace analysis supplies exact word/set counts. No failed result was
relabelled successful.

Reproduction: run `stage_a.py`, `capture.py`, `run_screen.py`, then `analyze.py`
in a fresh result namespace (directories are append-only). The capture runner
uses existing input paths in the frozen receipts. The evidence bundle retains
compressed traces, per-run commands, exit codes, source/binary hashes, complete
output identities and all screen reports. Full traces are actual native waves,
not reconstructed from sampled throughput. No new experiment remains running.
