# Isolated same-cycle canonical changed flag

The candidate avoids comparing the selected min-result256-bit line against the old line after the four64-bit min muxes. No register, RAM, interface, arbitration or latency changes.

Case proof over defined binary inputs to the frozen transform:

- Opcode2 (POP) never changes a label, so changed=false regardless of validity/PV.
- Opcode3 rejects value>=old_label with status8. Otherwise value<old_label and the label necessarily differs; status is0 or1. Thus changed=(single_status!=8).
- Opcode5 (SEED) assigns label0; it changes a label exactly when the selected old label is nonzero, regardless of its always1 status.
- Opcode7 applies opcode3 independently to all four sectors. The whole line differs iff at least one sector's status is not8. Sector comparison remains whole-pair unsigned order; no independent component minima.
- Every other opcode leaves labels unchanged in the frozen transform, so changed=false.

This proof concerns the transform's bit-level selection semantics, not unsupported floating-point computations or four-state X inputs. The final functional fixture remains within the frozen positive ALT domain.

The formula TB mechanically extracts the actual candidate computed_changed body. It compares that body to the old result-label equality using actual pending17_transform instances. XSim2022.2 passed73728 cases:9216/opcode for all8opcodes; all4 sectors; equal/zero/INF/bucket/broad64-bit boundary values; PV absent/present/version0/version65535; fixed-seed random raw64-bit inputs. Changed21540 and unchanged52188 are both covered. Random raw patterns strengthen bit-selection checking without asserting they are numerical workload inputs.

The actual candidate module was also substituted into the complete two-subbank F owner fixture, not only the formula helper. It passed1472 frozen-reference mixed operations,1988 shared physical transactions, fullPV14 real initialization/two samples, OOO/backpressure/tag/event saturation and all1472 exact canonical stage replays. All17620 accept/issue/response/PV/event/retire records match baseline F byte-for-byte, including57693 completion cycles.

The baseline live module was not modified during these proofs. Candidate is only results/fpga_enum_commit_canonical_changeflag_probe_20261114/ec_pending_k8.sv; its hash and original live hash are bound in source_binding/equivalence JSON. Integration must preserve its actual C negative/recovery and bounded physical optimization evidence before choosing whether to apply this candidate. No timing improvement, setup/hold closure, board measurement or full-kernel qualification is claimed here.
