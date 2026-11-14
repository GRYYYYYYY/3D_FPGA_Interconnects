# Final local D routed methodology disposition

Vivado 2022.2 completed synthesis through route and all reports with command code 0.
This is the actual two-subbank owner with enum2, scratch finalize, K8 canonical
and the one-port tagged arbiter. It is not a complete kernel or board timing result.

At the unchanged 5 ns clock, uncertainty 0.1 ns, input/output max0.8/min0.1 ns
budget, setup WNS is +0.024 ns (TNS0, zero failing endpoints), hold WHS is
-0.135 ns (THS-71.713 ns, 669 failing endpoints), pulse slack +1.8 ns.
Overall local timing qualification **fails**. No exception, waiver or I/O-budget
relaxation was introduced. All twelve check_timing categories are zero and all
33000 routable nets are fully routed with zero route errors.

The worst setup path is pending bank1 state_reg[7][0] to new_pvs RAMD32 input,
13 logic levels, data delay4.777 ns (logic1.106, route3.671). The same-cycle
changed-flag predicate removed the old redundant 256-bit post-min comparison;
it changes neither latency nor storage. Paired native simulation CSVs are
byte-identical to the previous candidate. Setup closure alone cannot qualify
the declared interface or a whole kernel clock.

The 32 SYNTH-5 warnings identify enumerator replacement_reg r1/r2 arrays chosen
as distributed RAM for timing. Source reads replacement[sets[0]] asynchronously
and updates it synchronously. These are counted LUTRAM resources; they are not
the repaired occupied BRAM or canonical PV URAM. No memory-init waiver is used.

The one RTSTAT-10 warning covers674 distinct nets. The read-only audit expands
every affected net's hierarchy segments and queries leaf input-pin consumers
and top ports. Every net has zero internal input-pin consumers and drives public
top output ports. See net_connectivity.csv and connectivity_audit.json for all
674, including aliases with multiple exported bits. There is no missing internal
consumer in this affected set. OOC has no parent HD.PARTPIN_LOCS/board routes,
so external output stub qualification remains absent. The warning is retained.

All669 negative hold paths were enumerated with max_paths10000/nworst1, matching
the reported endpoint count; all begin at declared top inputs, zero are internal.
The worst path is op_arg[2] to pending bank0 args RAM input at -0.135 ns.
Unanchored OOC input stubs explain the interface limitation, but do not satisfy
the declared minimum delay contract. No claim of timing pass follows from it.

The installed Ross methodology skill's newer JSON command is not available in
2022.2; native text reports were audited. Existing SYNTH-5/RTSTAT-10 objects and
all connectivity were inspected without suppressing warnings. The verified
process-local libudev preload workaround is documented in OOCc's
KNOWN_ISSUE_RESEARCH.md/workaround.json; D used the same workaround and completed.

Final status is ROUTED_LOCAL_TIMING_FAIL. Resource ledger:16024 LUT,14853 FF,
12 BRAM36+4 BRAM18 (14 BRAM36-equivalent),16 URAM,0 DSP. Replication arithmetic
excludes frontend, complete directory/output, global routing and controllers;
it is not a fit, complete-kernel frequency or board measurement claim.
