# CPU/GPU algorithm paper for author review

This narrative revision is based on frozen V2 commit `b0587c7e310073d04b1ba1e85e26a40ae0212389`. See `CHANGES_FOR_AUTHOR_REVIEW.md` for the three manuscript edits and validation.

## V2 provenance

Independent successor of frozen V1 commit
`4d0c4e88c1823ae554d6b4a891b53875b438cdec`. V1 was delivered at
20:04:35 UTC before new experiments began and remains unchanged.

Manuscript: `main.tex` and `main.pdf`. Anonymous, independently rebuilding
source package: `submission_source.zip`. The PDF has six body pages and one
reference page with unchanged template fonts and margins.

V2 adds only qualified matched GEMM/BNN evidence: three fresh processes for
each of Stock, Pipeline and original ALT CUDA per case, 18 formal runs total,
eight qualification processes and 26 independent FULL/STA route readbacks.
LSTM remains a separate historical cohort; DLA and s38417 are not rerun.
The original native implementation and all original samples/inputs are kept.

Read `THESIS_AND_ALGORITHM_MAP.md`, `CLAIM_EVIDENCE_MATRIX.csv`,
`CHANGES_FROM_V1.md` and `AUTHOR_REVIEW.md`. `EVIDENCE_PUBLICATION.md` binds
the complete software evidence branch. `paper_freeze.json` binds artifacts
and checks; `review/VISUAL_REVIEW.md` records all seven inspected pages.
The V2 publication receipts on the experiment branch bind the original V2 remote SHA
without embedding a self-referential commit hash in this directory.

`recompute.py` and `recompute_matched.py` read completed evidence only.
`build.py --tectonic /path/to/tectonic --bundle /path/to/tex-bundle` compiles,
checks and rebuilds the anonymous archive in a clean temporary directory.
The frozen tool is Tectonic 0.16.0; compiler digest and the exact checks are
in `review/checks.json`. No solver or EDA process is launched by this build.
The source ZIP includes its independent compilation instructions.

All scheduled software work is complete. Author approval and external
submission remain with the authors. FPGA remains paused under the separate
pause controller and is never resumed by publication or a budget deadline.
