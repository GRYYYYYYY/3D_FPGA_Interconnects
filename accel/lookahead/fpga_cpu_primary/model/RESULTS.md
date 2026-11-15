# Model subtask handoff

The current selected frozen model is `model_g`; its52-sample calibration and
registered-idle repair are described below. Actual clock qualification remains
separate. The earlier f evidence is retained as historical evidence.

## Historical revision f

The previously selected frozen model was `results/fpga_cpu_primary_20261115/model_f`.
Stress uses the identical verified binary in `model_f_stress`. Complete
comparison is in `model_comparison_f`; the scope contract and summary are in
`model_calibration_f/calibration_contract.json` and `SUMMARY.md`.

All32 complete native executions agree with independent deployed-configuration
RTL in output bytes, all12 request-kind totals and parent/candidate/commit/
event/retirement counters.19/32 complete logical request schedules also match
in every edge, source, kind, line, local identity and generation. Total-cycle
agreement alone is deliberately not used as the calibration criterion.

| Independent RTL comparison | Samples | Max absolute cycle error | Max total relative error | Max relative error excluding INIT |
|---|---:|---:|---:|---:|
| native d3 base | 8 | 1 | 0.004601% | 0.018681% |
| native d4 base | 12 | 13 | 0.057899% | 0.214203% |
| native d4 stalled | 12 | 18 | 0.068329% | 0.180741% |

The baseline residual discrepancies are in EXPAND. With a periodic external
issue gate, an earlier cycle difference can change subsequent sample memory
phase and thus COST/SEED/FINALIZE as well. All signed per-phase observations,
including cancellation between phases, remain in the comparison files.
The inherited model still visits service classes in `rotor%4` order with
explicit due-edge guards; it is not a complete immutable pre-edge evaluation
of every RTL process. The remaining mismatched request schedules are retained,
not fitted away. This is fixture-specific quantitative calibration, not formal
cycle equivalence or a universal error bound on BNN/LSTM.

The final semantics retain the RTL reset origin (`bank_rotor=t-1` after the
SRST edge) and forbid RELEASE scheduling on the edge that clears a member
hold. We did not choose the earlier variant merely because its net cycle
error was smaller. The corrections before that were explicit missing states:
L1 controlFIFO2s, bounded POP holds and capture, actual completion ACK timing,
serial admin costs, enum and scratch finish states, direct internal commit,
wave reopen and export completion. Historical/intermediate runs are preserved.

The final binary also passes d4 samples0/10 with125MHz,160ns latency and10ns
issue interval (`model_f_service`). This converts to20/2 actual cycles and
reruns the algorithm; it is a service-functionality check, not a hardware
frequency selection. Independent transport checks at125/200/333MHz, with
and without stalls, are in `model_transport_a` and include full32-bit identity
and generation, finite response blockage and credit conservation.

No full40 case has been run by this subtask. `qualified_clock_mhz` remains
null and `board_measured` false. The complete core's actual resource/routing
result, final frequency choice and subsequent full80 samples per declared
memory scenario belong to the coordinator's next stage. The runner requires
`--full-authorized` before selecting either40-sample input.

All source edits are confined to this new model directory; raw model artifacts
are under the new CPU_PRIMARY result tree. Nothing is committed or pushed by
this delegated subtask. Parent/coordinator owns final publication.


## Revision g: measured frontend-idle visibility repair

The unchanged DUT probe confirmed that raw frontend state becomes empty one
edge before the context idle register is visible. Revision g adds that actual
pre-edge snapshot/register, including every frontend-owned slice and edge
pipeline; it does not apply a per-wave cycle offset. Only finite.hpp changed
in the compiled closure. The52 native calibration samples (20 base,12 stress,
20 conservative) now match all complete output bytes, total cycles, all19
phase counts,12 request kinds, retirement counts and all72917 logical request
tuples including cycle/source/kind/address/id/generation. Every reported
residual in this scope is zero; no claim is made outside that observed scope.

Frozen g binary: `4ef2084643c48ad2937689ca02e9573bd342799f68555acf9bb1516f6cbce598`.
Contract: `results/fpga_cpu_primary_20261115/model_calibration_g/calibration_contract.json`,
SHA256 `e003f0b3210ad7abfa59402e2f2a03567e9780ab6031cf7788810135a3d0914d`.
The same directory retains the patch, all phase residuals and the q2/q0
edge/control evidence. Old f data, including its80-sample conditional run,
remain unchanged and must not be substituted for g full-batch results.
Qualified MHz stays null until separate complete-core timing evidence.
