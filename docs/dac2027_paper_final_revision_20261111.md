# DAC 2027 finite final revision — 2026-11-11

Revision base: `7e63b917f37273f80c03327e024d86b797ee221b`.
Branch: `paper/dac2027-final-revision-20261111`.
Research evidence base remains `ea1d0d793f7655d421595fcf2ee961c9cdc9af92`.
This is a manuscript-only revision. No GPU, solver, HLS, RTL, OOC or performance
experiment was started. The original `paper/dac2027`, research sources, frozen
results, main branch and original worktree's untracked documents are preserved.

## Delivered changes

- IV-A now says LSTM did not participate in preceding ALT shift/cache/directory
  tuning and was frozen before its own new ALT qualification/timing. The
  `holdout_selection.json` reason and freeze timestamp support this wording;
  it does not imply freezing before the earlier tuning campaign. Its prior CPU
  use, same-family scope, measured outcomes and input identities remain explicit.
- III-A and Fig. 1 share logical sample identity/layers/recording context. STRICT
  reads native RRGraphView; only ALT exports CSR/costs. Frozen
  `vendor_patches/vtr_cpu_paper.patch` and `accel/lookahead/vpr_live.cpp` are bound
  in `method_binding.json`. No code or timer boundary was changed.
- The AI section discloses substantive title/abstract/body, code, diagram and
  script generation. Local session contexts and associated write events verify
  the exact identifiers `gpt-6-astra` and `gpt-6.1-sol` in OpenAI Codex. Selected
  event hashes/timestamps are in `ai_usage_evidence.json`, not the anonymous
  source ZIP. No public-name mapping or completed human review is asserted.
  Earlier-history completeness and final author validation are separately
  recorded in [AUTHOR_CHECKS.md](../paper/dac2027_integrated/AUTHOR_CHECKS.md).
- Development-round names and internal hardware-state flags were removed from
  the body; experimental groups remain distinguished by case, worker and phase.
  Hardware discussion is shorter and retains the unverified-superiority,
  absent board/frequency/memory-service evidence and conditional-model bounds.
- IV-A identifies the frozen BNN/LSTM Beyond Flatland BLIF download and the
  project's KOIOS-derived two-layer architecture. Input manifests bind the
  actual paths and matching architecture SHA, without claiming a new input.
- LaZagna now cites **ICCAD 2025, pp. 1–9**, DOI
  `10.1109/ICCAD66269.2025.11240893`, as verified in the author-deposited
  [v4 record](https://arxiv.org/abs/2505.05579v4).

## New quantitative prose and existing evidence

| Addition | Frozen records and calculation | Scope |
|---|---|---|
| Full BNN shift0/20: 19,691/2,161 waves; 1,282,443,890/1,286,937,147 eligible-edge visits | `results/lookahead_accel_round6_20261109T150000Z/evidence_snapshot/large/bnn_export_s{0,20}.log`; sum the 40 per-sample profile records and cross-check `profile_summary.json`; `bnn_export_preflight.json` binds complete input SHA | Independent offline instrumented operation diagnostic; elapsed time excluded from formal performance; frontier width is not GPU occupancy |
| Wave reduction 9.11×; eligible-edge increase 0.35% | `19691/2161`; `100*(1286937147/1282443890-1)`; generated without intermediate rounding | Scheduling opportunity, not less edge work or measured hardware speedup |
| Eight-core BNN Group/Flat/Pipeline: 17.41±0.33 / 9.32±0.15 / 9.36±0.11 s | `paper/dac2027/evidence/expanded_20261105/results__native_flat_baseline_20261105__summary.json` and `__plan.json`; component_formal/bnn/8; raw seconds Group [17.09,17.74,17.41], Flat [9.36,9.15,9.45], Pipeline [9.46,9.25,9.38]; arithmetic mean/sample SD | Nine observations, three per arm; same executable SHA `ad49e82282e8805271030091292086dd38708537501fcabbc6cce9cb1a948cd9`; construction-only, independent of Fig. 2 and all native GPU comparisons |

`generate.py` derives these values and macros from the frozen records, extends
the claim ledger with `BNN_FLAT_CONTROL`, `BNN_OFFLINE_WORKLOAD` and
`BENCHMARK_ORIGIN_HOLDOUT`, and retains raw rows, input/binary identities and
cohort boundaries. There are now 22 claims and 34 bound frozen inputs. The prior
19 claims and all 17 prior computed statistics are exactly preserved. The
original three table fragments and the two performance figure rasters are
unchanged. LSTM/Pipeline E2 and Process gains, BNN control, small-input negative
result, ALT congestion differences and unverified FPGA boundary remain intact.

## Acceptance and delivery

The final [PDF](../paper/dac2027_integrated/main.pdf) has **6 content pages and
1 references-only page**, IEEEtran conference/10pt/letter/two columns. Automated
checks pass for page bounds, embedded fonts, absent author metadata/private
paths, resolved citations and no overfull boxes. Model visual inspection covered
all seven pages, including the revised diagram, numeric prose, table/figure
placement, AI section and formal LaZagna reference. It is not author review.
The AI section occupies page 6; page 7 contains references only. Space remains
on page 6 for later camera-ready author material.

The [source ZIP](../paper/dac2027_integrated/submission_source.zip) was rebuilt
and compiled in a clean temporary extraction. Its resulting page count and
page text match the delivered PDF. Internal provenance and author-check notes
are excluded from that anonymous typesetting package and retained in Git.
`format_check.json`, `source_archive_build_check.json`, `visual_review.json` and
`final_revision_check.json` bind the delivered artifacts. The official
[DAC requirements](https://dac.com/2027/program/research-manuscript-submissions)
were checked on 2026-11-11; structural checks do not certify the unresolved
author-confirmation items. No conference submission was made.

Reproduce with Python plus numpy/matplotlib/PyMuPDF and Tectonic 0.17.0:

```sh
python paper/dac2027_integrated/build.py --tectonic /path/to/tectonic
python paper/dac2027_integrated/check_final_revision.py
```

Both commands regenerate/check publication artifacts only. The acceptance
script compares frozen inputs, method sources, prior statistics/claims, table
fragments and performance-figure rasters against the requested paper base.
Build logs are retained. This revision ends after committing, pushing the
independent branch and verifying its remote SHA; it schedules no follow-on work.
