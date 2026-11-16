# Return payload wordmux candidate

This is the single minimal RTL followup to the actual SSI Route35-3 congestion
failure. `dispatch_return_wordmux_a/decision.json` under the CPU-primary raw
results root records the decision before the source change, the saved failure
DCP hash, actual resources and the completed placed critical-path evidence.
Error-state report collection continues independently against the unchanged
original netlist. No global resource saving or timing gain is assumed.

The alternate dispatcher keeps its original module name so the full top and
all other30 DUT files remain byte-identical. Use this directory's explicit
`sources.json`; do not compile both dispatcher definitions. The default
`delivery/sources.json` still identifies the historical f source.

The only datapath change packs `{token16,node32,label64,status4}` into116 bits
per bank. The existing one-hot winner still determines the six-bit bank index;
that index selects the packed payload, or zero when there is no winner.
Eligibility, RR, full identity/ledger rejection, no-fallback error behavior,
acknowledgement, all sequential logic and all capacities remain unchanged.
Under defined binary control, the winner is one-hot or zero; selecting its
indexed word gives the same fields as the previous masked OR. Arbitrary
four-state input equivalence and formal proof are not claimed.

Local verification reuses the existing original-reference protocol, rejection,
selector and lifecycle tests, without weakening assertions. Both the prior f
dispatcher and this candidate are checked against that reference. These are
bounded simulations, not exhaustive equivalence or timing validation.

```sh
python3 accel/lookahead/fpga_cpu_primary/dispatch/return_wordmux/run_local.py \
  results/fpga_cpu_primary_20261115/dispatch_return_wordmux_local_NEW
```

Every output directory must be new. Selected-source full-core calibration and
actual synthesis/implementation remain required before performance claims.
