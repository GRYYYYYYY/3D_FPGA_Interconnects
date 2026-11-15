# CPU_PRIMARY candidate-only word mux

`cp_candidate_wordmux_router.sv` is a fixed 64-input, 64-output, 96-bit module.
Its port names match `df_rr_router`; it has **no parameter overrides**. The
historical shared module is unchanged. Integration must replace only the
candidate network's router instance, remove that instance's old parameter
overrides, and include the new module in the production source closure. Other
users of `df_rr_router` must continue to use that historical implementation.

## Change and preserved contract

The original balanced tree's valid bits, `{index<cursor,index}` keys,
`left_wins`, `found` and 6-bit `selected` are retained. Its 96-bit data array
and data mux at every tree node are removed. A static generate loop wires all
64 payloads to three 32-bit unpacked arrays; the same `selected` indexes each
array and the result is concatenated as node / pair-high / pair-low.

With known, defined protocol signals, induction along the old key/data tree
gives `found -> data[root] == idata[selected]`. Static split and concatenation
preserve all 96 bits. No additional storage or register is introduced.

The output sequential block and input-ready block are unchanged:

- An empty output may accept even if its downstream ready is zero.
- An occupied blocked output retains valid, data and cursor; no input is
  accepted for it.
- Consume and replace occur at the same edge without an added bubble.
- When load is allowed but no winner exists, only output valid clears;
  data and cursor retain their previous values.
- Synchronous reset clears output valid and cursor, **not output data**.
  Input ready remains the historical combinational expression even while
  reset is asserted; reset does not constitute a data transfer in the test.
- Input/output FIFO depths, bank/source numbering, routing destination,
  network idle and all enclosing model service cycles are outside this change.

The old leaf slices were already static, and the old source shared
`left_wins` between key and payload. This rewrite does not claim to remove a
measured dynamic multiply or a proven unshared selector. A post-selection
64:1 payload read can map differently, including worse timing; actual complete
top reports are required for any resource or clock claim.

## Local behavioral verification

`run_candidate_wordmux.py <new-output-dir>` reuses the repository's XSim 2022.2
non-project compile / elaborate / run flow. It freezes the test sources and
requires the historical router's fixed reference SHA-256. The current candidate
network is also snapshotted and hashed as **context only, not compiled** into
this local router miter; its pre-integration instance/hash is not required.
All snapshotted files, including this context, must have unchanged hashes at
the end of the run. It records commands and per-stage logs and refuses to
reuse an output directory. The original completed `xsim_a` retains its frozen
driver and historical bindings; the replay-driver fix does not alter that run.
The 600-second per-command timeout and 2-ms simulated-time watchdog bound the
run. Three deterministic xorshift stimulus seeds are recorded; this does not
use constrained randomization or Vivado code-coverage metrics.

`tb_candidate_wordmux_miter.sv` instantiates old and new routers and an
independent behavioral scoreboard that scans inputs cyclically from each
cursor. Every edge checks all input-ready bits, output-valid bits, all 6,144
output data bits (including invalid holds), and all cursors. Before each edge
it also checks found/selected against the old router and, for found outputs,
against the independent winner and complete source payload. Initial unknown
output data are compared using case equality; arbitrary-X equivalence is not
claimed. A producer checker requires every stalled valid tuple to remain
unchanged until accepted or reset.

Each seed executes:

1. Empty cycles and all 4,096 source/destination single transfers. These also
   reach every cursor value at every destination using real handshakes.
2. Full 64-way contention at each of 64 destinations, asserting the exact
   cyclic service order as pending inputs drain.
3. Walking-one and walking-zero patterns across all 96 payload bits at all
   64 destinations, with 64 simultaneous independent transfers per cycle.
4. All-output empty filling with downstream not ready, 17 blocked cycles,
   simultaneous consume-and-replace, and occupied synchronous reset that
   checks retained output data.
5. 8,000 seeded traffic cycles mixing hotspot, random and permutation
   destinations, sparse producer valid, randomized ready, 19-cycle congestion
   windows and periodic resets. Pending producer tuples are retained.
6. Bounded complete drain and mandatory per-output functional counters.

The terminal gate requires every cursor/destination and source/destination
bin, both bit values at every payload bit/destination, and hold, replace,
clear, empty fill and occupied reset at each output. Actual verdicts, counts
and hashes belong to the run's `terminal.json` and delivery report; this
contract alone is not a PASS receipt.

This is bounded behavioral verification, not formal equivalence, gate-level
timing simulation, full-network/full-core regression, model recalibration,
resource measurement, routed clock qualification or board validation. Those
qualification decisions belong to the parent integration workflow.
