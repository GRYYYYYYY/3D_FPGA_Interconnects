# Integration audit checkpoints

These are review findings. Final receipts and the delivery report define the measured scope.

* Whole-word reservation must outlive actual directory event handshakes. A completion FIFO admission alone is insufficient for the selected strict-retirement contract. The owner adapter was matched for both old/new variants; canonical holds PUB stable until final acknowledgment.
* Canonical model has one apply slot and one PV write port per subbank/cycle, matching the actual K8 datapath. A loop over eight contexts cannot imply eight transform units.
* Directory allocation is explicitly banked (64×8192 members, fixed total524288) rather than treating a global free-list vector as a free64-port memory. Perbank peaks/overflow must be recorded.
* Final frontend is eight independent eight-lane groups, one fork reservation/publication and one header/descriptor admission per group/cycle. Prior global RR tests are causal controls, not a secretly different final implementation.
* Enum occupied launch to external fragment transfer is7 clocks in no-stall unit evidence; II2 does not mean two-cycle latency. Four pipeline-valid records, raw register and FIFO16 are separate real storage.
* Consumed bits belong to every resident final line, not only spill IDs. Model wave-clear must clear ALL consumed bitmap bits over the explicitly charged256 bitmap-word cycles. Otherwise a later spill-only line could inherit a stale consumed bit and be skipped.
* Fixed80ns main memory contract and jitter/backpressure stress evidence must be distinguished. Large native owner projections prove local canonical behavior, not complete wire-map output; old native PV state is not injected through hidden RAM writes.

* Physical memory latency is measured issue-handshake to response-handshake, not inferred from TB due-time expressions. The original fixed integration runs measured17 cycles and are retained as superseded evidence. True80ns evidence must show16-cycle histograms.
* PV and occupied-list RAM inference repairs preserve complete unit interface traces; synth reports, not ram_style attributes, establish actual mapping.
* The complete new conditional model finished BNN40 and LSTM40 with exact golden outputs. FinalD conditional200MHz times (261.328010/264.444710ms) exceed the GPU targets; neither old enum5/K1 rejection nor the new weak bound is used as the measured result.

* Model A/B/C are superseded attempts: finalD adds held publication/one retirement, next-edge reuse, bounded eight-bank output packing with ACK-backed output, and complete three-beat cost initialization outside all sample output regions.
* Both local OOC processes hit Vivado2022.2 SIGABRT in Webtalk host-info/libudev collection immediately after routing; no final DCP/reports survived. Preserve tool failures separately and recover from frozen synthesis checkpoints with process-local library-loading workaround.
