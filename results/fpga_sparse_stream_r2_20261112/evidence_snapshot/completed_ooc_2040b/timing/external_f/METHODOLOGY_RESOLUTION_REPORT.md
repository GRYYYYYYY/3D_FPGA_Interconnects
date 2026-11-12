# R2 timing methodology audit (in progress)

Vivado2022.2 on xcu280-fsvh2892-2L-e. The Ross skill targets2026.1+ JSON reports; this audit uses the available2022.2 text report_methodology/report_timing_summary/report_clock_interaction. No waiver, false path or multicycle exception was introduced.

The opened external_f synthesized design has an actual5ns clock, input/output delays, zero no_clock/unconstrained internal endpoints and zero mapped loops. Its old automatic posthook report has no clocks and infinite slack, and is invalid for qualification. Opened valid timing is WNS-4.876ns/WHS+.025ns. The critical ready path has36logic levels from a state-request BRAM output to physical response ready.

Both methodology_before.rpt and methodology_clock_assumed.rpt report1000 TIMING-16 large setup violations. Adding HD.CLK_SRC=BUFGCE_X0Y144 (device site exists in regionX4Y6) supplies an explicit external OOC clock-route assumption; it does not repair the logic path, and the opened timing remains unchanged. This is not shell/board clock evidence.

The concrete structural repair is registered FIFO free-space readiness, with one full-to-nonfull acceptance bubble; complete8F1/F0 each97 independent RTL/model cycle traces pass. The separately frozen complete many8_reg_b synthesis has WNS-3.017ns/WHS+.025ns,358396LUT214592FF368RAMB36+112RAMB18. It is a changed topology and source, not a constraints-only improvement. Routing is active and no full-kernel frequency is qualified.

A further owner MSHR single-write RAM repair passes unchangedwarm/stress traces and reduces actual standalone6909LUT3236FF from24036LUT12460FF. Full integration OOC remains in progress.

Clock-source rationale: https://docs.amd.com/r/2022.1-English/ug905-vivado-hierarchical-design/I/O-and-Clock-Buffers (HD.CLK_SRC estimates external OOC global-clock routing).
