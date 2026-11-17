# Dependency-aware DAC 2027 revision

Independent manuscript revision from `986149c07bc7b8be54d99e8a2e2a47327ec143b5`; prior frozen submission remains unchanged.

- Read `main.pdf` (six content pages + one reference page).
- Submit-ready anonymous **source** artifact: `submission_source.zip`; external submission has not been performed.
- Scientific positioning: `THESIS_AND_POSITIONING.md`, `CLAIM_EVIDENCE_MATRIX.csv`.
- Executed/skipped evidence: `SUPPLEMENT_RESULTS.md`, `SUPPLEMENT_PLAN_FROZEN.json`.
- Differences and remaining author decisions: `CHANGES_FROM_986149C.md`, `AUTHOR_REVIEW.md`.
- Source bindings and full retained process records: `evidence/bindings.json`; old frozen results are inputs, not overwritten experiments.
- Compiler/package/layout checks: `review/checks.json`, `review/VISUAL_REVIEW.md`.

Recompute retained statistics and PGFPlots data without any solver:

```sh
python3 recompute.py
python3 build.py --tectonic /path/to/tectonic
```

Tectonic 0.17.0 and Poppler tools are required. The first compilation may download standard TeX packages. The source ZIP builds independently with `tectonic main.tex`; its rendered text is checked against the repository build. Repository checks also verify the protected prior submission and bind older evidence paths in this branch.

h is **not** owned by this paper workflow. `evidence/h_readonly_snapshot.json` identifies the still-active original session and process birth. No new solver, CUDA or EDA jobs were launched; no hardware input was modified. Resume paper review from this branch, not by restarting h. Do not automatically start a follow-up research round.
