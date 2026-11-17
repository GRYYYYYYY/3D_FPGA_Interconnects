# Primary-source positioning review (2026-11-17)

External publications establish prior contributions; all performance numbers in this manuscript come from this repository's separately bound experiments. No cross-paper speed ranking is inferred.

| Source | Verified contribution and manuscript treatment |
|---|---|
| [LaZagna arXiv metadata](https://arxiv.org/abs/2505.05579), DOI 10.1109/ICCAD66269.2025.11240893 | Formal ICCAD 2025 version, pp. 1–9; architecture generation/exploration, not a matched construction-speed control. Updated bibliography from preprint-only entry. |
| [Multi-die author manuscript, IV-B2](https://arxiv.org/html/2606.06421v3) | Intra-die lookahead plus die-crossing penalties; acknowledges layer/die-aware heuristic contributions. Execution organization is a different question. |
| [MultiQueue author publication page](https://www.alex-singer.com/publications/conference-papers/multiqueuebasedfpgarouting/) | FPT 2024; includes deterministic serially equivalent search variants. The paper does not claim all prior parallel routing sacrifices equivalence. |
| [Davidson et al. author page](https://mgarland.org/papers/2014/sssp/), [primary paper](https://escholarship.org/content/qt8qr166v2/qt8qr166v2.pdf) | Work-efficient GPU SSSP already studies frontier/bucket execution and extra-work/parallelism tradeoffs; not a newly invented general principle here. |
| [SPLAG author PDF](https://about.blaok.me/pub/fpga22-splag.pdf) | Chi, Guo, Cong, FPGA 2022, pp. 190–200, DOI 10.1145/3490422.3502358. Coarse priority queue and vertex cache for power-law SSSP; added hardware-related citation and scoped distinction. |
| [Current VPR options](https://docs.verilogtorouting.org/en/latest/vpr/command_line_usage/) | Sparse compressed_map sampling and compatible table reuse are relevant alternatives. Current documentation does not establish locked binary support on a two-layer graph; P1 records actual binary/help/source evidence. Separable is not ported or benchmarked. |
| [DAC 2027 manuscript instructions](https://dac.com/2027/program/research-manuscript-submissions) | Six content pages plus one reference page, anonymous IEEE format and AI content disclosure. Retained title pending author portal check; no external submission performed. |

The LaZagna DOI is the formal citation; its linked author/preprint metadata supports the publication identification. Existing PathFinder/VTR/3D placement references remain context rather than experimental baselines. Author review of novelty positioning remains explicitly required.
