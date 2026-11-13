# Methodology review: INF combination C

Vivado2022.2 text reports were used. The Ross skill requires2026.1+ for its
JSON workflow; no unsupported2026 JSON command or waiver was applied.
Actual5ns setup/hold/pulse slacks are+0.635/+0.041/+1.800ns; all10184 routable
nets are fully routed with0 routing errors. All12 check_timing categories are0.
Input/output min0.2ns,max1ns are explicit assumed integration contracts, not
board-measured budgets. Effective constraints are saved beside the source XDC.

Remaining warnings are retained, not waived:

- SYNTH-5(32): replacement-way metadata maps to256 distributed RAM LUTs.
  This is the small1024x2 replacement table, not the large payload/pending.
  Actual large memories are16URAM and16RAMB36+4RAMB18 across two subbanks.
- XDCC-4(2),XDCC-8(2): A/B/C source scripts reused one in-memory non-project
  session. All three clock declarations are identically5.000ns on clk.
  The effective constraints and timing clock summary confirm one5ns clock.
- Synth8-9873: C overwrote same-named A/B modules; log file paths identify
  C as the last definitions. Frozen C hashes equal passing E/G RTL sources.
  This is not a clean-session warning-free synthesis claim.
- RTSTAT-10(1):908 nets have no routable loads, including top-level outputs
  in this OOC design.2407 ports are implicitly routed in route_status.
  No unconstrained I/O endpoints are reported. This does not prove the timing
  or loading of a future connected32-owner router.

No TIMING-* violations or combinational loops appear in these reports.
The worst setup path is in the pending service, not the old last_way forward
path. Full-kernel, shared-router, actual directory and board timing remain
unqualified. The finite full-input schedule fails its software budget, so no
full candidate is replicated from this local physical result.
