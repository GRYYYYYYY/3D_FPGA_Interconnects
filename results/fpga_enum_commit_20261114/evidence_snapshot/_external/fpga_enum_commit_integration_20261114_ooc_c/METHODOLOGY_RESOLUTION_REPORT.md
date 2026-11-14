# Local backend OOC audit (Vivado2022.2)

The routed C implementation and one bounded post-route physical optimization
both fail the declared5ns timing point. No clock, I/O delay or exception was
changed, and no waiver was created. The later same-cycle RTL control fix is
measured separately in OOCd.

| Check | C before physical fix | C after physical fix | Meaning |
|---|---:|---:|---|
| Setup WNS | -0.413ns | -0.298ns | Internal pending apply/control critical path remains negative |
| Setup failing endpoints | 34 | 24 | Actual routed paths, not arithmetic estimates |
| Hold WHS | -0.135ns | -0.135ns | Declared external input budget does not close on virtual OOC stubs |
| Hold failing endpoints | 671 | 666 | Five inserted hold buffers reduce some violations |
| Pulse WPWS | +1.800ns | +1.800ns | No pulse-width failures |
| Missing clock/delay/internal constraints | 0 | 0 | All12check_timing categories zero |
| Routable-net errors | 0 | 0 | All routable nets routed |
| SYNTH-5 | 32 warnings | 32 warnings | Explicitly retained distributed replacement RAM mapping |
| RTSTAT-10 | 1warning,674nets | 1warning,674nets | External output stubs, audited individually |

The installed Ross timing-methodology skill requires2026.1+ for its JSON
workflow; this2022.2 flow uses the native text report and actual objects.
There is no supplied SYNTH-5/RTSTAT-10 resolution reference for this version.
The generic analysis process is applied without unsupported commands or waivers.

SYNTH-5 is identified by the actual report: all32 instances are the two banks'
replicated `core/replacement_reg_r1/r2_*`2-bit replacement arrays. In
`enum2_bank.sv`, `chosen=replacement[sets[0]]` is an asynchronous replacement
lookup and updates are clocked; it is not the occupied/meta/payload RAM path.
Vivado selected distributed RAM for its timing. Actual LUTRAM/replication is in
the resource ledger. Replacing it with BRAM would change that lookup's latency
and is not silently performed.

For RTSTAT-10, the read-only Tcl audit obtains the exact674nets from the DRC
object, expands every hierarchical net segment, and queries every leaf driver,
internal input-pin sink and top port. **All674 have zero internal input-pin
sinks and drive public external output ports.** These include request data,
result PV/old-pair fields, directory arguments/nodes and protocol flags. Output
aliases can associate multiple top bits with one affected net. The warning is
therefore not a missing internal consumer in this local design. It remains an
external physical integration limitation: no parent `HD.PARTPIN_LOCS` or board
routing is supplied. The original warnings are preserved, not waived.

The same audit queries every negative hold endpoint (`nworst1`, max10000),
obtaining exactly666paths, matching the after-fix report. All start at external
inputs (including sd,op_pair,in_pair,in_node,op_arg,flush,etc.); none is an
internal-to-internal negative hold path in this report. The worst op_arg path
has zero modeled/routed input-stub delay before its RAMD32 pin. The min0.1ns
input contract, clock skew and uncertainty are not satisfied. This does not
become a timing PASS merely because the missing stub is outside the local
netlist. The router explicitly states that unroutable/partition pins cannot be
hold-fixed with routing detours. We do not increase the input min to hide it.

Detailed evidence: `physopt_a/net_connectivity.csv`,
`physopt_a/hold_failure_classification.csv`, `connectivity_audit.json`, both
complete timing reports, DRC/methodology/route reports and checkpoint hashes.
