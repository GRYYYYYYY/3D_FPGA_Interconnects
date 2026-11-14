# Balanced frontend / enum2 / finite scratch / K8 candidate

Execution base: `1e312d6e4ffc5ea96f25c0b97931ad028e710584`.

The candidate implements and tests same-resource FIRST_FREE/LANE_RR allocation,
an elastic II2 enumerator, finite scratch fast/merge paths, real K8 whole-word
canonical transactions, and a tagged shared physical port. Frozen GPU, old-model,
CUDA and complete-profile evidence is reused; old enum5/K1 rejection is not applied
to the new structure.

Final complete conditional model: `model_native_d`, BNN40 and LSTM40 exact golden
outputs, respectively52,265,602 and52,888,942 cycles. At conditional200MHz these
are261.328010ms and264.444710ms, both slower than the reused GPU resident targets.
No measured FPGA runtime or universal FPGA no-go is claimed.

Final local timing: frontend OOC E setup−1.036ns/hold+0.043ns; backend OOC D
setup+0.024ns/hold−0.135ns. Backend negative holds are all OOC input interfaces.
The declared5ns contracts do not close overall; no full top was launched after
this candidate failed the complete-model and local-qualification gates.

- [Full report and evidence scope](../../../docs/lookahead_fpga_enum_commit.md)
- `front/`: causal controls, independent groups, real FP32 leaf and cycle calibration.
- `enumerator/`: elastic resident enumeration and finite scratch service.
- `canonical/`: K8 pending state, whole-word reservation and actual shared tagged port.
- `integration/`: matched old/new owner chain, native projections, finite TB and OOC.
- `model/`: continuous full-input finite model, receipts, independent checks and guarded runner.
- `delivery/`: independent verification, evidence qualification and compact archive tools.

`results/fpga_enum_commit_20261114/evidence_snapshot/manifest.json` is the compact
round archive. It retains intermediate failures/tool crashes and final receipts
with hashes, source bindings, inputs and complete outputs. Vendor build trees and
DCP binaries remain in the recorded server paths; the archive does not claim to
contain a complete Vivado project. All final qualification flags and stopped-job
checks are in `qualification.json` and `delivery_terminal.json` inside that archive.
