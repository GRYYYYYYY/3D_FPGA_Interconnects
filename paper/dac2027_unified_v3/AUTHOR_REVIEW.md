# DAC 2027 Main3 author review

The revision is based on paper/dac2027-v3-fig3-editable-export at 426cdca323ae41594613aceac1c3ca21755dfec6. Its main.pdf has SHA256 b678a652503931410c28c0c3652f69e89a2cb278784eaf49dd28683784183805. That worktree is the rollback copy. The new worktree and branch are independent. The frozen V2 submission remains available. Author review is pending.

## Revision notes

| Original question | Change in the manuscript | Supporting evidence |
|---|---|---|
| What makes the problem layer-aware? | Four introduction paragraphs progress from fabric changes to recording dependencies, related work and two selectable designs. Fig. 1 shows both layer indices, resource types, displacements, the associated pair, native query and measured process. | Locked source and all nine Stock stage records |
| Where can scheduling change safely? | Figs. 2–4 and Proposition 1 separate issue order, context identity, native priority ties, ordered consumption and prescribed writes/fills. | Stock serial sample loop, bound worker code, Group/Flat/Pipeline controls and equal wire maps |
| Where does ALT change the answer? | Fig. 5 and Algorithm 2 trace snapshot proposals, whole-pair selection, same-bucket reopening and closure. Results separate changed congestion representatives from agreement between ALT backends. | CPU/GPU source, capture digests and three map-difference reports |
| What accounts for the time savings? | Section V reports integrated times first, then cross-group availability, shift granularity and same-rule backend gains. The 0.314 s observation is labeled Warm Complete-Batch Service. | Raw process records from B/C, matched repeats, separate BNN40 profiles and warm batches |
| Which routes support a QoR statement? | Section V-D distinguishes 54 formal routes, 65 distinct emitted routes and 62 with a matched Stock reference. Table IV uses maximum signed change and the common threshold. | Independent readback/STA records joined by original route digest |
| How broadly can these mechanisms be applied? | The manuscript specifies the dense admission rule and the limits of two layers, fixed samples and one seed. The ledger records what evidence would be needed for stronger claims. | Timed GPU source, workload manifests and qualification archive |

[Complete manuscript](main.pdf) · [Anonymous LaTeX and editable figures](anonymous_source.zip) · [Claim-to-evidence ledger and open questions](review/CLAIM_EVIDENCE.md) · [Page review](review/VISUAL_REVIEW.md) · [Clean build receipt](review/rebuild.json)

## Sources and provenance

The revision brief and replacement blocks in the rollback worktree have SHA256 6f00bccd3d36d01c0ef22c136815cfb58f732fefd5e5ff8953e40c983e5918e6 and 2f4e51e08bb0f0b63e87f7abd359ae69a79afe10525d38b1900e9343378e4cc3. The replacement blocks informed the abstract, four-paragraph introduction, method framing, results and conclusion. Router statements use the verified invocation records.

All seven publication figures compile directly from LaTeX/TikZ or PGFPlots. The current sources are [Fig. 1](figures/motivation.tex), [Fig. 2](figures/schedules.tex), [Fig. 3](sections/contracts_figure.tex), [Fig. 4](figures/strict_example.tex), [Fig. 5](figures/alt_example.tex), [Fig. 6](figures/native_times.tex) and [Fig. 7](figures/paired_speedups.tex). Earlier vector exports remain in the repository as historical assets. Fig. 1 uses both columns to keep the index, timing band and stage shares readable.

The formal corpus is Allocation B for GEMM/BNN and C for LSTM. The measured inputs, prior captures and raw records remain in those frozen commits. This revision only replayed the archive checks and built the paper. FPGA pause management was outside the editing workflow.
