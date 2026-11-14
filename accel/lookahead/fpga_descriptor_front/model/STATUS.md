# Model worker terminal status

Final candidate: `results/fpga_descriptor_front_20261114/model_d`.
Full C0/F2 BNN40/LSTM40 completed at2026-11-14T16:40:14.091292+00:00.
All160 full native samples PASS;14 frozen D representative checkpoints reused,
146 new native samples completed. Independent verification PASS334 unique samples:
160 small regular/jitter +160 full native +14 other F1/F3 native representatives.
The28 four-grid representatives overlap the full results in14 C0/F2 samples.

C0/F2 BNN cycles72,347,012/71,238,001; LSTM73,374,604/72,236,324.
F2 improves1.5329%/1.5513%; conditional200MHz times0.356190005/0.361181620s
remain above reused GPU targets0.151799969444/0.15949799988888888s.
No whole-kernel frequency or assembled RTL cycle qualification; no board timing.

D freezes actual output service, registered32→2ACK collector, exporter start/done,
MinimumCollector, request/return network, front/backend contexts and finite widths.
Intermediate A80small, B160small/jitter, C160small/jitter+28representatives are
preserved with supersession records. D normal C-to-D checks:80small and28native
samples each+3cycles, native traffic/output/wave traces unchanged. D small jitter
exercises52 rejected ACKsource cycles in30cases, atmost2ACKretire/cycle.
Transport adapter shared-model equivalence PASS208sources/32ports/45071requests.

No optional K16/merge2/interleave candidate selected: see full_analysis.json and
RESULTS.md for actual critical-wait evidence and limits. No source edits or reruns
are pending. Owned model/runner processes absent at delivery scan; receipt in
model_d/delivery_terminal.json. Other workers' Vivado/CPU jobs are outside this
worker's terminal assertion. Parent owns final resource audit/archive/publication.
No commit/push by this worker.

Frozen binary SHA256:
`651023422a3d036f6119f1a6d13d4aa70e02d79727b90ff611c7467bd886ef13`.
