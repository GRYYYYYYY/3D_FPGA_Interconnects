# Enumerator worker interface and finite storage

`enum2_bank.sv` module `enum2_bank` has the same named ports as the frozen
`inf_flat_bank`, plus optional `scan_issued[31:0]`. `SET_BITS=10` by default.
It still accepts original full node addresses; owner/subbank range checks belong
to the owner wrapper, as before. Four ways/set, four 64-bit sectors/line.

Expand is copied from the old four-stage set-reserved RMW pipeline. It emits
non-final eviction fragments in exactly the same input order/replacement policy.
After `flush`, it drains candidate stages, then launches occupied reads every
second **enabled** cycle. The pipeline has synchronous occupied read, synchronous
metadata read, synchronous four-sector payload read and a registered extraction
stage. All valid/slot/data state and RAM read enables freeze together on a full
output path. Metadata is invalidated only when extracted data enters the bounded
raw output register. Payload remains in the original synchronous URAM-style arrays.

Finite storage beyond resident RAM is: four enumeration stage valid records,
one raw fragment register, and `fragment_fifo` with total capacity16 (including
its synchronous RAM read/output stage). Each fragment is293 bits
`{final1,line32,mask4,pairs256}`. Pipeline register widths are in the actual RTL;
RAM outputs/control registers are additional real storage, not hidden capacity.
`scan_issued` counts launched occupied reads; `enumerated` counts insertion into
raw output. `done` waits all enumeration state/raw/FIFO drain. Hold `flush` high
until the complete owner finishes, then deassert it to begin the next wave.

`scratch_finalize.sv` module `scratch_finalize` keeps the exact named interface of
old `inf_scratch_boundary`; optional `ID_BITS=11` yields2048 unique spill IDs.
All lines are logical original20-bit canonical line numbers. The physical wrapper
adds a scratch base multiple of32 lines; it must retain `line &31` owner mapping.
The memory client is untagged because **at most one scratch request is outstanding**
in either phase. Use a constant local tag0 behind the tagged physical arbiter.
`rv/rr` acknowledges a write as well as supplying a read response; no new request
is issued until that response is accepted. There are no outstanding generation
aliases. Reset/phase change is forbidden while an external request remains live.

Expand preserves one spill RMW: lookup bitmap, optional read, whole-pair min,
write, wait ACK. First-spill IDs and spilled bits become persistent only with the
same serialized protocol; `ID_CAP` overflow is sticky and enters HALT with
`done=0,ir=0,mv=0`, requiring reset/recovery. A protocol non-final fragment after
resident finalize begins also enters HALT. This is explicit failure, not success.

The first final fragment is accepted only after expand ACK drain. Finalize has:

* one registered spilled-bitmap query record;
* `merge_fifo`, capacity16×277 bits (`residual1,line20,pairs256`);
* one active merge record/request, holding its response until canonical admission;
* common `commit_fifo`, capacity16×276 bits (`line20,pairs256`), shared fairly by
  unspilled query fast path and completed merge. There is no separate fast FIFO.

Both FIFOs use the existing synchronous `sparse_fifo`, total configured capacities
include their read/output staging. When both inputs are ready, central admission
alternates; one fast/merge enqueue maximum per cycle. A merge read waiting80ns
never holds the commit arbiter or a bitmap-word lock, so unspilled queries proceed
until a real finite queue fills. Resident order may change relative to old service.

On resident admission into the safe common commit FIFO, consumed updates enter a
single-read/single-write BRAM pipeline: read word, atomic OR next cycle; a prior
write forwarding register handles adjacent A/A and A/B/A collisions. One atomic
update/cycle maximum. Spilled/consumed are separate256×64-bit BRAM arrays. Expand
writes spilled; finalize only reads it. The consumed read port is shared by atomic
updates in RESIDENT and residual scans in RESIDUAL, with no overlapping phases.
No whole bitmap-word lock spans a scratch request. A resident merge is marked
consumed only when its merged line has actually entered the commit FIFO.

`finish` is the enum bank's drained `done && flush`; it cannot be asserted by a
TB that still has unaccepted resident fragments. After `finish`, residual IDs
start only when query, merge queue/record, commit FIFO and atomic update pipeline
have drained. Consumed IDs are skipped; other IDs issue one scratch read and
commit the result. Residual IDs are unique and are not re-marked consumed.

Scratch `done` means all queued lines have been accepted at `cv && cr`, not that
canonical ACK/PV/events retired. Owner completion MUST additionally require the
canonical service's idle/completion. Only then drop `finish/flush`; scratch clears
both bitmaps over256 real cycles, as the old implementation did. Wait for the
next fragment input `ir` (or a conservative260 clocks) before a new wave. Counters
are cumulative across wave clears; no free per-wave reset is used.

`accepted/retired` count incoming fragments (resident retired when safely enqueued
for canonical, expand retired after write ACK). `committed` counts `cv && cr`,
including residual-only lines. Canonical retirement statistics belong downstream.
The standalone scratch TB validates commit acceptance and exact whole pairs; it
does not claim canonical event retirement or full-kernel timing qualification.

## Runnable unit tests

Source `run_enum.tcl` or `run_scratch.tcl` in a new/owned Vivado2022.2 Tcl session.
The scripts use `xcu280-fsvh2892-2L-e`, bounded XSim runtime and watchdogs. Results
are under `results/fpga_enum_commit_enum_20261114_a/`. Frozen old modules are compiled
alongside the candidate. Testbench PASS is required, not only Tcl exit0.

`enum_tb`: full four-way/16-set occupied list, four waves without reset including
empty and one-entry waves, exact
mask/sector payloads, no-stall interval5/2 and long output backpressure recovery.
`scratch_tb`: exact full-line oracle, repeated expand spill RMW, resident/spilled
intersection, scratch-only residual IDs, held commit ready, fast progress during
merge wait, five consecutive waves (including empty) with real bitmap clear, same-word atomic updates,
A/B/A word updates and actual2048-ID capacity overflow branch (2049th unique spill halts).
The passing final16-cycle-memory test observes27 adjacent same-word OR updates and36 A/B/A
word update sequences, and checks both final consumed RAM words exactly.

Parent integration owns the complete enum/scratch/canonical/tagged-port wrapper,
full retirement tests and OOC. No commits/pushes are performed by this worker.


Final authoritative unit projects are `enum_project_e` and `scratch_project_i`.
Earlier projects preserve failed testbench builds, a testbench ACK race, and
17-cycle-memory intermediate tests; use only the final i scratch timings for the
80ns/5ns contract. Final i request→response delta is exactly16 cycles for all40
requests in each old/new matched instance. These unit memory interfaces are separate
per baseline/candidate; they do not claim two subbanks share a physical port.
That shared interface is verified by the integration worker.

No-stall enumeration launch→fragment transfer is7 clocks: occupied launch t,
metadata read t+1, payload read/selected metadata t+2, extraction t+3, raw register
capture t+4, FIFO enqueue t+5, FIFO synchronous read t+6, transfer t+7. Backpressure
adds real queue/pipeline waiting; no finite latency bound exists without a downstream
liveness assumption. Earliest unspilled scratch fragment→commit transfer is3 clocks;
its consumed update applies2 clocks after incoming fragment (one clock after safe
commit FIFO enqueue). These are interface clock observations, not canonical latency.

Final CSVs: `enum_project_e/enum_unit.sim/sim_1/behav/xsim/enum_ticks.csv` captures
every positive edge's reset/flush/iv/ir/node/pair/fv/fr/line/pairs/done/scan/index/FIFO.
`enum_trace.csv` and final i `scratch_trace.csv` retain handshake/event rows with
`time_ps,variant,wave,event,line,flag,data`. `%0t($time)` uses rounded ns then displays
ps, adding a constant500ps offset; timestamp differences remain exact5000ps/tick.
Model calibration must replay pins/finite queues, not align only total cycles.
