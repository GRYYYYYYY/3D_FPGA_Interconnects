# h physical terminal audit — no qualified FPGA performance

The original h SSI replay reached its complete terminal at **2026-11-17 07:05:09 UTC**.
Placement and physical optimization completed; **routing failed** with
`Route 35-3`: global congestion level7. The original flow saved the error DCP
and completed all21 terminal report groups with zero collection failures.
This closes collection of a failed implementation, not timing signoff.
No new architecture, EDA, P2/P3 or performance experiment was launched.

The separate author-final paper remains at
`c8933bac394a1c177725bec6d9a0ccb6af3437a6` on
`paper/dac2027-dependency-revision-20261117`, following author-review
`bffa5626ac7e984f3018b5e9be9f4b95ac18541b`. Its requested two edits,
6+1-page PDF, anonymous source ZIP and remote-SHA verification are complete.
This h result is published separately; the paper and old freeze hashes are unchanged.

## Terminal identity and supervision

- Existing session: `vivado-20261115-113226-a1b5e8eb`, Vivado2022.2.
- Original PID1165972, start_ticks164991348, born2026-11-15 11:32:26UTC;
  boot`2c285022-7829-4b21-84d8-176f6732a754`.
- Replay started2026-11-16 21:58:41UTC. It is a non-project replay from
  the verified h post-opt DCP; the source project is
  `full_synth_h_return_wordmux/project/cp_full.xpr`.
- Route began2026-11-17 01:34:44UTC and returned1 at06:01:07UTC.
  Error DCP writing completed0 at06:04:25UTC. Terminal report collection
  finished0 at07:05:09UTC; the parent launch returned1.
- Fresh MCP check after terminal: command idle, completion1, queue0.
  The Vivado interpreter remains alive; that does not mean the task is running.
- Original read-only observer PID1602804/start_ticks177505615, born
  2026-11-16 22:18:09UTC, recorded the terminal at07:05:38UTC and exited
  normally. Current Codex conversation performed final audit and publication;
  no second observer or competing publisher was created.

The complete h log is sliced from byte4219527 of the original shared log,
through its actual MCP completion marker. Source/log/receipt association is
recorded in `terminal_audit_a/terminal.json`;31 frozen/live RTL sources and
all5 frozen flow scripts match their original bindings. No inputs were changed.

## Actual complete-core resources

All rows are actual complete-core U280 OOC reports, excluding a platform shell.
LUTRAM and SRL are components of total LUTs, not extra LUT allocations.

| Stage | LUT | Logic LUT | LUTRAM | SRL | FF | BRAM36 equivalent | URAM | DSP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Synthesis / before opt | 1223270 | 935214 | 286776 | 1280 | 749607 | 1148 | 640 | 0 |
| Standard opt | 1220068 | 932268 | 286776 | 1024 | 748933 | 1148 | 640 | 0 |
| SSI placement / terminal error state | 1212828 | 925700 | 286232 | 896 | 749091 | 1148 | 640 | 0 |

Standard opt saves3202LUT and674FF. The terminal footprint uses93.03% of
1303680LUTs, but162737/162960CLB sites (99.86%). BRAM comprises1016RAMB36
and264RAMB18. The actual hierarchy report is retained in full; no sum of
overlapping hierarchy rows is used as a global budget.

## Routing and timing failure

The final router trial reports zero failed nets **and5695749node overlaps**.
That is illegal routing. Its maximum directional congestion is north105.629%,
south87.1266%, east103.888%, west100.24%; global/short congestion is level7
and timing congestion level8. Estimated SLL demand was24098/23040 across
SLR1/2 and23772/23040 acrossSLR0/1, with localized columns up to194%.
These are router estimates, not successful physical crossing counts.

The saved error state reports1831203routable nets, only2fully routed and
1831201unrouted. Its zero `nets with routing errors` does not override those
unrouted counts or the failed command. The utilization/hierarchy header says
`Routed`, whereas the congestion report says `Fully Placed`; neither header
overrides the terminal route-status evidence. DRC reports one critical
RTSTAT-13 insufficient-routing violation.

| Terminal timing metric | Actual value |
|---|---:|
| WNS | −13.389ns |
| TNS | −2958995.250ns |
| Setup failing endpoints | 1340417 / 4357781 |
| WHS | −3.392ns |
| THS | −1497169.125ns |
| Hold failing endpoints | 1895887 / 4357781 |
| Internal register setup / hold worst slack | −13.389ns / −0.438ns |

The worst setup path is `fabric/ret177.hold_reg[323]/C` to
`admin/cost_word_reg[107]/D`:17.874ns reported data delay, including15.740ns
estimated route delay. The worst all-path hold endpoint is
`fabric/q120/mem_reg_0_3_336_349/RAMA/I`, launched from`cfg_scratch_base[5]`.
The internal hold path runs from`banks[43].bank/enumerator/raw_pairs_reg[248]/C`
to its fragment FIFO RAM input. Reports contain unset nets; these failed-state
path delays are diagnostics, not an achieved routed frequency.

## Clocks, warnings and limits

All/core/direct clock-pin sets agree at1237419pins, under`core_clock` on`clk`
with a5ns target. `HD.CLK_SRC=BUFGCE_X0Y144` is an unused external OOC source
site. Both actual BUFGCEs carry control signals: reset atBUFGCE_X0Y143 has
99129loads/0clock loads; the front state/enable atBUFGCE_X0Y194 has
2452loads/0clock loads. There is no instantiated core-clock BUFG in this OOC
snapshot. No synthetic clock was assigned to either control buffer.

All12check_timing categories report zero, including unconstrained internal
endpoints and missing I/O delay. There are no valid timing exceptions, but the
blanket I/O delays remain boundary assumptions.9097Route35-198 warnings record
missing partition pin locations; external platform timing/routing is unqualified.
The methodology report contains1024SYNTH-5,1000TIMING-15 and1000TIMING-16
violations. Full h replay diagnostics are classified:9108warnings,4critical
warnings and1error. Four critical Vivado12-4439 messages concern large report
collections; all report groups nevertheless completed. None is a timing waiver.

There are9681output-driver census entries and no blackboxes. The prior138
unproven generated synthesis aliases remain explicitly unproven. These reports
do not supply new formal equivalence or a complete functional proof.

## Performance qualification and claim ledger

**Qualified complete-core frequency: unavailable.** Consequently, achieved
BNN40/LSTM40FPGA seconds and speedups over the optimized64-worker CPU are
unavailable for both base and conservative storage scenarios. The5ns target
and failed-state WNS must not be converted to a performance result.

Existing52native RTL calibrations/11rejections and160model samples retain
their existing source/service bindings. Their200MHz/storage scenarios remain
conditional. Native eight-thread E2/Process,64-worker resident CPU and measured
GPU evidence are reused with their distinct scopes; none was rerun. No board
measurement, FPGA-over-CPU success or universal FPGA impossibility is claimed.

The machine-readable current ledger and review are under
`accel/lookahead/fpga_cpu_primary/h_terminal_20261117/`.
The failure evidence supports stopping this candidate; the current authorization
does not permit another architecture or EDA round.

## Evidence index and recovery

Raw root: `results/fpga_cpu_primary_20261115/full_impl_h_ssi_spreadslls_a/`.

- `run_a/run_receipt.txt`: actual EDA/checkpoint/collector terminal codes.
- `run_a/route_design_failure_reports/`:30 report/helper artifacts,21 completed
  groups, full resource hierarchy, all/internal paths, clocks, congestion and census.
- `run_a/cp_full_top_route_design_error.dcp`:632778209bytes,
  SHA256`1881dfad243210dec06edd402c4554888f50d22030cfb6c630837b0c01afdc43`;
  stable during streamed hashing. Retained in raw storage, not uploaded as a Git blob.
- `terminal_audit_a/`: complete h-only log, MCP status, process/observer receipts,
 31frozen sources, filename mapping, audit, manual review and warning classes.
- `frozen/` plus`launch.tcl`: unchanged reproducible Tcl and launch binding.
- `accel/lookahead/fpga_cpu_primary/h_terminal_20261117/`: current ledger,
  resource comparison, report manifest and review available directly in Git.
- `accel/lookahead/fpga_cpu_primary/evidence_snapshot/manifest.json`: refreshed
  content-addressed archive; prior objects and historical Git snapshots retained.

Recovery is read-only: inspect this terminal receipt and archive, never re-source
launch/replay or restart the observer. There is no queued follow-up experiment.
The paper chain is complete; h physical success is false. Audit/archive/publication
completion is separate from scientific implementation success and is finalized
by the publication receipt and verified remote SHA.
