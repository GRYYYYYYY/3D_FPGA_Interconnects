# Descriptor frontend leaf

This directory implements the actual descriptor/token fork, 4/8-lane EDGE engine,
positive normal/+0 FP32 whole-pair datapaths, and a finite launch/capture context.
It is local RTL evidence, not a complete kernel or board measurement.

`df_front_group` reserves tokens before external POP completion. A stale POP returns
its reservation without DESC. A legal POP generates exactly one descriptor request;
8B and exact 16B fallback decode are checked. Adjacency and target each hand off once;
only both recorded handoffs release the token. Zero-degree targets remain live.
DESC/EDGE request holds and response writes are separate. Addresses are 64-bit
32B line addresses; EDGE includes the actual configured base. E4 and beat8 per lane,
D1, and T=2*L descriptor/token/ready entries preserve the specified totals.

`df_pair_lane` has six elastic register stages (capture, ordering/exponent,
align/sticky, add/normalize, round, pack/error), II1. Each operand carries destination,
epoch-mod256/context/slot/generation/last diagnostic tag. Only one wave is active
and drained before advancing; this tag is not a full16-bit epoch or interleaved-job
ownership identifier. Arithmetic legality travels with the data.
A 30-bit next-beat cursor includes an exhausted sentinel beyond the largest legal
29-bit physical beat; UINT32_MAX endpoints are tested. Last-edge/last-beat are
precomputed, avoiding the old pos+1/end carry chain on slot release.

`df_front_context` adds one-entry elastic registers on reserve command and tokenACK,
POP result, each request and return channel, target, and each lane candidate.
These are additional capacity/latency, not silently absorbed into global FIFO4.
The model owner was sent this contract before complete-model source freeze.
See `service_contract.json` and `../coordination/front_interface.md`.

## Functional evidence

Raw results are under `results/fpga_descriptor_front_20261114/front_*`.
Final H leaf tests use a >=16-edge memory agent with deterministic jitter, OOO
returns, backpressure and finite flights. F and earlier had an actual 17-edge
minimum and are preserved as superseded test-agent evidence.

* Arithmetic: 4,400 directed/boundary/random pair operands, all 6,248 interface
  cycles independently modeled, valid/tag/error and supported numeric bits exact.
  Illegal subnormal/negative/NaN/Inf inputs require error, not a numeric result.
* Final leaf4/8: 128 reservations, 8 stale, 120 DESC requests, 309 EDGE requests,
  1,735 exact candidates and 80 targets; 8B then16B epochs without reset.
  Full composed descriptor/token + E/beat + six-stage FP32 cycle models match
  1,084/838 cycles, respectively. Token peaks8/16. Largest legal edge offset tested.
* Actual registered context4: same workload passes in1,130 cycles. External
  functional equivalence verified; its every internal register is not yet replayed
  against the complete native model, so do not transfer whole-kernel calibration.
* Native contiguous prefixes BNN2/wave38 and LSTM7/wave36: both descriptor formats
  and no-reset epochs produce3,974/4,182 exact candidate pairs. Additional real
  target windows include53/51 zero-degree and44/35 valid-target parents per128;
  their two-format outputs3,212/3,316 match exactly. LSTM target window uses L8.
  These are functional projections, not full native batch performance workloads.
* Six malformed descriptors reject without E/target handoff: overflow,end<begin,
  target out-of-range, invalid nonzero cell, negative validcell,reserved flags.
  The degree65536 fallback test checks decode and first request only, not complete
  expansion of that synthetic long parent.

`calibrate_pair.py` and `calibrate_leaf.py` independently replay clock-step state
from external stimulus. Leaf composition uses observed E-ready in descriptor replay
and independently proves that same E-ready in edge replay. No observed internal
scheduler state is imported as the expected state.

Reproduce with Vivado2022.2 through `sim_pair.tcl`, `sim_leaf.tcl` (set `df_out`,
`df_lanes`, `df_tb` first), and bounded self-checking TBs. `run_final_sims.tcl` lists
final invocations; new result directories are required rather than overwriting old
projects. Native fixtures come from the descriptor worker's source-bound JSON,
not copied full graphs. `gen_vectors.py`, `gen_leaf.py`, `gen_native.py` generate
portable inputs. Source snapshots/receipts and every initial failure are retained.

## Physical qualification

OOC A/B preserve actual setup failures (-0.650/-0.335ns). Final OOC C is
**LOCAL_RTL_TIMING_QUALIFIED** at5ns for L4 plus real register context:
setup+0.255ns,hold+0.019ns,pulse+1.968ns,all12 check_timing categories zero,
methodology0. Route DRC has RTSTAT-10 on857 external-output-only nets; actual
object audit finds zero internal consumers on these stubs and all15550 routable
nets routed. No real path is waived and no clock/IO delay is relaxed.

C uses9247LUT (1278 LUTRAM),8761FF,0BRAM/URAM/DSP. The sixteen-copy arithmetic
bookkeeping is147952LUT/140176FF; it excludes global interconnect and all other
kernel services and is not a complete fit claim. L8 clock has not been routed.
`front_ooc_c/METHODOLOGY_RESOLUTION_REPORT.md` gives critical paths, all IO
assumptions and retained A/B script-tail failures/recovery. Vivado2022.2 text
commands replace skill2026.1 JSON reporting. Full-kernel clock qualified=false.

Global POP,32-port arbitration/credits/returns, shared8bank output RAM, candidate
router, directory and backend are outside this leaf. The TB target consumer checks
exact cell/pair and rejects duplicate/missing handoffs under backpressure; it does
not qualify the shared output-bank RAM timing. Full-model/native qualification is
reported separately by the task parent.
