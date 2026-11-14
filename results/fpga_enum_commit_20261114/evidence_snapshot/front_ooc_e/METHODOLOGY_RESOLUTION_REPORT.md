# Parent review of final frontend OOC E

Reviewed the actual Vivado2022.2 routed checkpoint reports with the Ross timing-methodology workflow. The skill's2026.1+ JSON commands were not used; text reports, explicit XDC and timing paths are the evidence. No new timing exceptions, waivers or clock changes were made.

| Check | Actual evidence | Disposition |
|---|---|---|
| TIMING-16 (5 warnings) | Internal same-clock5ns paths, worst overall setup−1.036ns; FP32/error paths also near−1ns | Unresolved structural/routing failure; not a missing inter-clock exception |
| XDCH-2 (1560 warnings) | Input/output min and max both0.5ns | Retained explicit leaf OOC boundary assumption; does not establish board/parent timing |
| RTSTAT-10 (785 nets) | Listed buses include exported pair/node/ml/tag/idle outputs without parent physical loads | Retained OOC physical-boundary limitation; no waiver or complete-top routing claim |

Worst setup path is pos_reg[29][7]/C to slot_state_reg[56][0]/R:18 logic levels,6 CARRY8,5.917ns data delay, including4.186ns routing. It corresponds to matched-beat selection/consumption and slot retirement in frontend_group.sv:58–72 and110–112. Requirement5ns, skew−0.010ns and uncertainty0.035ns do not support treating this as an erroneous sub-nanosecond requirement or unrelated-clock path. Actual FP32/error paths are separate residual structural failures. Earlier priority-chain/statistics/offset repairs are preserved as A–D source/measurement history; this remaining negative is not hidden by an exception.

Setup:8403 failing endpoints, WNS−1.036ns, TNS−2864.653ns. Hold:+0.043ns with zero failing endpoints; pulse:+1.968ns with zero failing endpoints. All12 check_timing categories are zero, including missing clocks/delays, unconstrained internal endpoints and loops. These coverage checks do not erase setup failure.

The saved route DCP and main reports survived E. Its original wrapper returned1 at an unsupported report-redirect command; a report-only recovery opened that same saved DCP and completed the missing reports with return0. final_terminal.json preserves both receipts. D's preceding SIGABRT in host-info/Webtalk collection remains a distinct tool failure. E's process-local libudev preload allowed the route callback and checkpoint/report writing to complete, without changing RTL/XDC or global tool configuration.

Allowed conclusion: finite leaf functionality and cycle replay passed;200MHz frontend timing did not. This leaf excludes full POP/fork/header/metadata/reducer, physical base/demux/global return routing and the complete64-lane top. The complete conditional model also misses its targets, so no full-top expansion is justified by this candidate's evidence. No further frontend variant was started.
