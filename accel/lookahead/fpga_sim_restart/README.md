# ALT_LINE_OWNER_REDUCE_V1 restart

The frozen contract and supplied YAML are in `config/`. The first delivery implements one owner service.
The subsequent [closed-loop prototype](closed_loop/README.md) adds a complete runtime
graph controller, 8/64-owner RTL, full-batch model, calibration and native round trip.
Its serial graph front end and projected clock are explicit limitations.

`rtl/owner_service.sv` implements 4 ways × 32 sets × 32-byte lines, round-robin
replacement with explicit lowest-index invalid-way selection, 32 line-matched MSHRs, 16 acknowledged dirty-write slots, and 64-entry
request and memory-response FIFOs. All tags, data, masks and queues are physical
RTL state. A cache miss locks its way until the corresponding response. Incoming
whole FP32 pairs merge into the MSHR while that read is outstanding. A pending
dirty write blocks all accesses to that line until its acknowledgement. The
request FIFO is ordered, so this can cause head-of-line blocking. Memory requests
remain stable under backpressure. IDs 0–31 identify MSHRs; IDs 32–47 identify dirty
slots. This is a bounded ready/valid transaction protocol, **not an AXI4 adapter**.

For `OWNER_BITS=k`, set = `(global_line >> k) & 31`; the caller must route the low
k bits to the proper owner. The isolated tests use k=0. No 64-owner crossbar or
32-channel shared controller is hidden behind this interface.

Input pairs are already computed. Encoding is `{delay_bits, congestion_bits}`;
only +0 and positive normal FP32 words are admitted, as in the original ALT
contract. This unit performs exact whole-pair selection, not FP32 addition.
MSHR fill compares all four sectors with the actual memory response. `retired`
counts reduced requests, not persistent writes. `fence_done` is the persistence
barrier: request FIFO, MSHRs, dirty writes, response FIFO and the command register
must all drain; all 128 cache lines are scanned and invalidated. A subsequent
sample may reset only after that barrier. Reset clears all identity state and
spends 128 actual cycles initializing replacement state. There is no epoch wrap
alias. External proposal-home initialization is outside this module and is implemented
and timed by the closed-loop graph controller. An invalid pair sets sticky
`error` and suppresses successful fence publication. Reset during live memory
transactions is outside the interface contract.

The testbench is a finite 64-outstanding memory server, 32-byte transactions,
16 abstract banks, eight-cycle bank reissue gap, four-cycle read/write turnaround,
two-cycle shared read/write link gap, delayed/reordered responses and periodic
request/response service stalls. It checks same-address RAW exclusion and the last
write acknowledgement. These values are **assumed stress scenarios**, not U280
measurements and not the YAML's full 32-channel central scenario. At 200 MHz its
one-channel link ceiling is 3.2 GB/s. Functional memory backing is finite (2048
lines). Golden data are never supplied to the DUT.

Reproduce from repository root (Vivado 2022.2):

```bash
python3 accel/lookahead/fpga_sim_restart/scripts/generate_directed.py /absolute/run
bash accel/lookahead/fpga_sim_restart/scripts/run_xsim.sh /absolute/run 600 800
```

The run path must exist. `check_rtl.py` requires the explicit terminal PASS,
accepted/retired equality, full-memory byte equality, and reached capacities for
the directed test. `cycles.csv` records every cycle, including reset/drain. The
source also has a one-million-cycle watchdog. Real-wave tests additionally load
`initial.hex` into the *testbench* memory and replay two complete waves from qid0;
this is not complete graph RTL or model calibration.

For the final OOC, run `scripts/run_ooc_v2.sh`. It uses a per-process libudev
preload to avoid the reproduced post-route allocator crash and runs
`scripts/ooc_v2.tcl` on the final runtime-fed RTL with 5 ns constraints.
`scripts/ooc.tcl` and `recover_ooc.tcl` preserve the earlier attempts. Raw setup, hold, unconstrained-path and DRC reports must be read;
a successful tool exit is not timing closure. Boundary OOC paths do not establish
shell/interface timing. No old kernel frequency is inherited.

`cache_replay.cpp` uses the original ALT algorithm and complete original job sets,
with a new 4-way line cache for F1 and explicit line RMW for F0. Every wave compares
all proposal-home pairs with committed labels; every sample also runs an
independent original ALT search and compares its entire output. It writes complete
batch outputs only on success. This sequential functional replay has **no finite
concurrent MSHR timing model**: its hit/traffic counts are diagnostics of that
schedule, not RTL-calibrated large-graph performance. `extract_resident.py` retains
actual historical resident timers and their JSON paths; it never renames E1 or
pretends cold native observations are the requested warm cohort.


`owner_model.py` is an independent finite cycle model of the single owner and
stress memory server. It reads only stimulus, initial memory and expected output;
RTL cycle logs do not drive scheduling. `compare_model.py` compares each phase
separately, so a short phase failure cannot be hidden inside a long-run total.
The initial model/RTL mismatch is archived: the first loop-based RTL selected
way 3 in XSim when all ways were invalid, whereas the model and software replay
selected way 0. The final RTL spells out priority explicitly and agrees with
that policy. The source and failing comparisons remain under `attempts/`.
This is an observed implementation discrepancy, not a claimed vendor root cause.
The d4 wave trace was kept out of that repair. Neither trace is a complete
small-graph RTL batch, and this unit comparison does not qualify a 64-owner
architecture model.
