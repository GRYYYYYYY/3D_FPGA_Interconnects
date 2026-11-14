# Descriptor-front independent review

Scope: read-only implementation audit; reviewer owns only this directory and results/fpga_descriptor_front_20261114/review/. No full experiments or implementation edits.

## Checkpoint 0: prior implementation and required new boundaries

Read the complete current instruction, frozen final-D README/configuration/finite source, actual prior frontend_group/ec_tagged_port, integration README, MODEL_AUDIT including corrections, prepared Graph and workload ABI. At this checkpoint new implementation consists of coordination/interface drafts; the checks below are review requirements, not assertions of defects in not-yet-written code.

* Canonical held publication, PV capture+1, request eligibility+3, separate RR cursors, one completion/bank, and next-edge word/slot reuse were already repaired in final D. Do not reopen historical A findings.
* Actual tagged port has four FIFO4 clients, one physical request holder, 32 busy tags allocated at holder fill, FIFO4 physical responses, four client response holders. Full queue rejects same-edge replacement, tags freed by an accepted response are unavailable to same-edge allocator, response holder can be replaced on actual consumption. An outer registered finite concentrator is needed for many source clients; merely keeping one request/port/cycle does not implement this topology.
* Historical finite front frees E/beat/H state before later allocation in the same C++ step. New source must derive all non-elastic allocations from pre-edge state or match explicitly implemented elastic replacement. Do not infer permission from canonical's correctly repaired slot reuse. Same applies to memory callbacks consumed before front service.
* New 8x8/16x4 configurations need independent group quotas for request generation, enqueue, issue and return writeback. H/M and descriptor/EDGE independent writes require real separate banks/holders. Global accepted_port or id%64 return masks alone are insufficient.
* D1 means outstanding EDGE request per parent, not one resident beat total; slot and request reservation lifetimes must be specified separately.
* Frozen raw graph conversion uses eligible skip/break and stable edge order. New descriptor must preserve both, use checked offset32 with wide begin+degree and physical byte arithmetic, retain zero-degree valid-target updates, and make invalid cell bits canonical zero.
* Front initial interface reports six elastic FP32 stages, copied operand bundles, and T token/ready entries; model must charge actual capacity and stage backpressure, not just change latency=6 while retaining a two-entry FIFO.
* Directory requires concrete sync RAM port ownership for head/tail, member.next, free-list, min-selection. One service/bank/cycle plus arbitrary added due time does not establish those accesses.
* Complete-model qualification must remain conditional until these exact scopes, actual whole-top timing and fit are established. Local FPGA gains are not complete-batch gains.

Notifications: sent model/front/services pre-edge reuse and topology requirements and parent checkpoint status. Subsequent checkpoints will bind actual new sources and list confirmed findings, fixes, and remaining scope.

## Checkpoint 1: emerging front and shared interfaces

Confirmed DF-R001 in the saved draft df_edge_group source: the 29-bit nextbeat cursor wraps after issuing the highest legal beat. Legal offset32 admission allows end UINT32_MAX, therefore this is within supported bounds. Notified front and parent; a wider cursor or exhausted flag and a directed final-beat/backpressure test are required. The snapshot and SHA are in checkpoint_01.json.

DF-R002 is a cross-interface gap: local backend owner retains can0/can1/scratch0/scratch1 client queues while the proposed full network uses EDGE/control/canonical/scratch classes. Explicitly expose logical backend clients when replacing the old fabric, or account both actual fabrics; do not transfer whole-owner calibration from geometry alone. Sent all three owners.

DF-R003 requests policy alignment: emerging edge request arbitration is fixed priority while the new contract calls RR. The implementation and model must settle the same actual policy. This is not a claim of functional output failure.

Read the six-stage FP32 datapath: stage valids/data/rounding/zero bypass/error all have explicit elastic storage. No concrete arithmetic defect found by source inspection; directed independent arithmetic checks and RTL timing remain the owner's required evidence. This review did not run a simulation.

## Checkpoint 2: repaired leaf and synchronous service primitives

DF-R001 source repair observed: nextbeat is now30 bits with physical lastbeat29. DF-R003 now has persistent lane request RR advancing when filling the actual request hold. DF-R004: operand selector formerly recomputed under blocked valid and last flag depended on ready; front owner added held context/slot and ready-independent last. Functional boundary/stability test receipts remain required before closing these findings.

Inspected descriptor encode/decode/admission, finite serialized synchronous directory and its executable counterpart, registered router, physical port counterpart, and backend context slices. No further concrete functional defect found in those draft primitives by source review. The directory serializes operations, finishes previous tail linking before append ACK, and returns detached members through actual synchronous reads. The physical port uses pre-edge capacity/tag decisions; newly freed tags cannot be allocated at the same edge. A diagnostic peak-credit counter phase difference was sent to its owner.

DF-R002 remains open: the two different physical client mappings require explicit integration/scope. Full model source is still being edited, so copied historical transport/directory portions are not reported as frozen candidate defects. Model owner has acknowledged full pre-edge and new pipeline requirements; review is pending its actual runnable checkpoint.

## Checkpoint 3: first full-model integration pass

DF-R005/006 identify actual free service in the first candidate router: changing a source head inside the destination loop permits multiple transfers from one lane in a clock; post-pop full tests also allow a full source FIFO to accept same-edge input contrary to the selected nonelastic queue contract. Owner was notified before any new performance run.

DF-R007/008 identify front composition gaps. The actual descriptor leaf has response capture, decode, held branch selection, then E/target handshake; the initial model jumps from response to either handoff at +1. It must retain held choices under backpressure, actual token retirement and real outgoing request holders, or provide an explicitly implemented alternative architecture instead of inheriting that leaf's calibration.

DF-R009 identifies callback ordering hazards: EDGE response clears D1 before same-step EDGE generation, and scratch write ACK clears busy before same-step scratch admission. These transitions need pre-edge availability or due guards matching actual RTL. Directory member capture was separately raised; the owner reports a +1 guard repair and actual response-to-upstream ACK next edge.

The transport adapter does preserve pre-edge source capacity, registered request and return routers, port FIFO4/tag allocation, launch/capture FIFO2, and fixed80ns from physical issue. Its source/class topology explicitly differs from the old local owner and still requires the DF-R002 mapping declaration. These source-level observations do not certify end-to-end timing.

## Checkpoint 4: explicit context and remaining pre-freeze boundaries

Independent read-only leaf trace audit closes DF-R001 within the tested domain: front_leaf_c has exactly309 EDGE requests, with highest legal beat0x1fffffff issued once at cycle376 and returned402. Existing RTL receipt verifies1735 candidates and all128 parents, including stale and zero-degree cases. Frozen source SHA and trace SHA are in front_boundary_trace_audit.json.

Source repairs observed for DF-R005/006/007/008/009: single-source route guard, pre-edge lane FIFO full snapshot, raw/decode/held selectors, actual front one-entry context paths, next-edge response eligibility. Global token allocation (not just command enqueue) is capped8, and canonical request eligibility is adjusted for the newly explicit held request. Directory now uses a real minimum-tree counterpart instead of a CPU min plus arbitrary timer.

Two additional full-FIFO boundaries were sent before B: merge FIFO dequeue before qspill enqueue violates actual sparse_fifo REGISTERED_READY=1 when previously full; export packed FIFO similarly tests post-pop capacity despite the nonelastic-full contract. These must be fixed before using new timing results.

DF-R002 is resolved as an explicit scope limitation: global fabric replaces the local owner port at logical CAN/SCR clients. Local four-client owner composition is not claimed to match global four-class composition, and no extra local fabric is free or secretly cascaded. Full RTL integration remains separate. The inherited accumulator's immediate state update/fixed set lock is also not an exact model of the stalled RTL pipeline; retain this qualification limit even after finite-capacity fixes.

The first A small run is preserved as bringup. No reviewer launched a model or Vivado experiment. New performance results require the source-bound corrected run and separate output/capacity/conservation verification.

## Checkpoint 5: source fixes closed; result audit

The merge/export FIFO pre-edge fixes are present. Actual token allocation is capped8/cycle, and canonical request-holder timing now corresponds to PV capture+1, holder fill+2, client admission+3. Global directory MIN uses the exact MinimumCollector state machine: start/QUERY, pre-edge sent/accepted masks, finite response captures, actual6-stage tree, and result handshake. The previous early start issue is resolved. No additional blocking capacity/service defect was found in this reviewed source; that is a bounded review conclusion, not a proof of complete hardware equivalence.

An independent read-only artifact audit checked model_b's160 small normal/jitter sample runs: all output bytes match each sample slice of frozen golden,17 frozen source hashes and binary match, phase and fixed-observer sums agree, traffic and ACK counts conserve, and reported group/FIFO/context/credit/directory peaks obey capacities. The exact results are in model_b_receipt_audit.json; verify_model_receipts.py reproduces the audit without launching any model. Newer MIN collector source requires its own affected run rather than relabeling B.

Next checkpoint is the corrected frozen model's representative and complete sample receipts. Full-chain accumulator timing, full kernel frequency/fit, actual memory rather than stated contract, and local-versus-global composition remain separate qualification limitations.

## Checkpoint 6: frozen C output service and receipts

The new output service has8 actual finite synchronous banks, a registered group-to-bank router, three positions/bank, same-cell newest-result and last-write forwarding,4096 charged initialization writes, and completion-driven first-seen accounting. Frozen C calls it once per real cycle and waits target holds and the entire service to drain before bucket target decisions/export. Its packed export reserves at most16 total pending+ready beats and reads at most8 distinct banks/cycle. Source review found no additional output-update functional or capacity defect.

Independent C artifact audits pass160 small normal/jitter runs,23 frozen source files and binary, exact golden bytes, phase/traffic/capacity identities. Extended checks also pass output admitted=retired, first=recorded, weighted lane-emission population=candidates, and per-wave selected-bank exclusive observer sums=finalize wall cycles. These identities do not prove that the selected-bank label is a causal bottleneck.

Two export integration issues are grouped for one D repair. DF-R013: RTL export_start is an actual edge before first RAM read, and export_done is registered after final ACK count; C's abstract loop omits those controller edges. DF-R014: RTL has2 ACK lanes, while C's common-network sink accepts up to32 output source returns without a global2 limit. Two requests/cycle do not bound return coincidence: the recorded arithmetic example under the existing jitter contract has3 simultaneous returns. Add a real finite selection/backpressure collector and match its exact boundaries. C is preserved as functional/intermediate evidence, not silently relabeled final D.

## Checkpoint 7: registered export and finite ACK repair

DF-R013/014 are closed at source integration and separately calibrated primitive scope. Actual exporter trace starts at622, first write valid625, final ACK710, registered done visible712; second epoch repeats the same boundaries. Thus start/read/pack/write and final ACK/done are charged by the corrected D model. The32-source ACK collector has exactly two actual holding registers, accepts at most two old-source returns per edge, advances RR only on those accepts, and retires newly captured returns no earlier than the next edge. The global return network retains rejected source payloads. Independent Python cyclic-RR/state checks reproduce all304 supplied vectors; the existing RTL comparison passes384 ACKs and44 cycles with both output holders blocked. No new simulation was launched by the reviewer.

D small160 runs independently pass25 frozen source hashes, binary/input/output receipts, exact golden slices, all earlier conservation/capacity checks and maximum2 consumed ACKs/cycle. Independent comparison against actual C runs finds all80 normal runs +3 cycles; D has52 rejected-source cycles across30 jitter runs, proving the backpressure path is exercised. These are actual rerun comparisons, not analytic timing substitutions. Combined exporter/collector RTL-loop evidence remains pending its owner; full-kernel timing/fit remains unqualified.

Also independently verified C's28 representative sample receipts and all12 front before/after trace pairs byte-for-byte with recorded hashes. The latter supports preserving modeled capacities/latency after the bounded front repair, but is not a route timing result. Current single-active-wave front carries epoch modulo256 as diagnostic data; do not claim full16-bit epoch ownership or interleaved-job support.

Final comparison scope: best main F2 retains separate ROW/META with16x4 lanes. The descriptor-based F3 group/context whole-pin calibration and local timing do not qualify F2 whole-front timing. Only the actually shared six-stage FP32 and EDGE module evidence transfers at module scope. No additional F2 RTL variant was requested by this review; retain this limitation in any conditional performance table.

## Checkpoint 8: actual combined output RTL closure

The owner supplied output_c with actual output RAM/exporter plus32-to2 ACK collector connected. Independent read-only Python audit of its raw1413-cycle pin traces verifies the cyclic selection against old holding-register state, unchanged rejected source payloads, exact one-clock capture-to-consume, and final complete drain. There are62 ACKs, up to4 simultaneous source offers and6 rejected-source cycles. Both sample epochs retain first-write-valid=start+3 and done-visible=last-ACK+2. Existing RTL functional scoreboard and full output model replay also pass1024 updates,62 exact exported beats and packing peak16. DF-R013/014 are therefore closed at this actual combined local RTL scope.

This closes the pending combined-loop item from checkpoint7. It does not extend descriptor-leaf timing qualification to F2's separate ROW/META front, certify whole-kernel accumulator timing, establish board memory behavior, or turn the conditional finite model into a measured FPGA runtime.

## Checkpoint 9: D representatives and local front timing

D representative28 sample runs pass the same independent frozen-source/binary/receipt, golden-byte, capacity and conservation audit as the160 small runs. The actual D full batches remain separate required evidence.

Front OOC C independently passes25 frozen source hashes and8 report hashes. Raw reports give5ns clock, WNS+0.255ns, WHS+0.019ns, pulse slack+1.968ns, zero failing endpoints, all12 check_timing counts zero, methodology violations zero and15550/15550 fully routed nets with no route errors. This certifies the reported local L4 descriptor df_front_context timing scope only. It does not qualify F2 separate ROW/META wholefront or the complete64-lane kernel. The reviewer inspected reports without running Vivado.

## Checkpoint 10: output RAM inference repair

The first actual full-size output-context synthesis used116082 LUT,77824 LUTRAM and no BRAM. That negative attempt is retained. Using the Ross elaboration-analysis skill in read-only mode, the reviewer reused the owner's per-attempt report and independently verified all153 non-INFO warning occurrences appear exactly once (100 ID3917,48 ID6849,3 ID6014,2 ID4767). No duplicate synthesis or RTL edit was performed by the reviewer.

The owner replaced two mutually exclusive RAM write statements with one explicit write-enable/address/data mux. Reset, initialization priority, synchronous read-first behavior, state capacity and pipeline edges are unchanged by source inspection. Both complete output and collector pin traces from actual output_d are byte-identical to output_c;16 frozen source hashes per repaired simulation/inference attempt were checked. Frozen C++ model headers are unchanged.

Actual output_ram_b synthesis now reports16971 LUT,7477 FF,zero LUTRAM,56 RAMB36E2 plus8 RAMB18E2 (60 BRAM36 equivalents),zero URAM/DSP. Primitive inventory contains8 RAM primitives in each of8 banks. Source, report and terminal receipts independently pass. This is successful local RAM/resource inference and behavioral preservation; no output route-clock or complete-kernel timing qualification follows.

Additional final scope: actual common-network calibration preserves opaque32-bit local ID and8-bit source exactly. The complete model uses separate unsigned kind/id/generation members. Without an implemented per-source packing and generation-wrap adapter, those C++ fields do not establish32-bit full-kernel wire equivalence. Local opaque-payload transport calibration remains valid; complete-top adapter qualification is explicitly outstanding.

Output RAM B raw synthesis log independently contains155 warnings (150 ID3917,3 ID6014,2 ID4767), with the old ID6849 absent. Use raw counts over the MCP digest count; no RAM inference failure remains in that report.

Correction to earlier metadata-scope concern: inspection of frozen D confirms all active front/canonical generation paths already wrap to8 bits. The unmasked reserve_token helper is unused. Thus no actual wide-generation mismatch or32-bit overflow was established. See packing_budget.md and results/review/packing_budget_audit.json for source-local feasible widths and the explicitly unimplemented complete-top packing adapter.

## Checkpoint 11: complete D batches and resource arithmetic

All334 unique D sample receipts pass independent verification;14 repeated references across small/representative/full terminal manifests are identical. Actual workload and golden files were rehashed, and four complete output files equal both the ordered concatenation of40 actual sample outputs and the frozen complete golden. All phase sums, per-sample counts, traffic matrices, directory/spill peaks, ACK bounds and wave-level exclusive histograms agree with the complete summaries. No model simulation was launched by the reviewer.

C0→F2 complete cycles are72,347,012→71,238,001 for BNN and73,374,604→72,236,324 for LSTM. This is1.5329%/1.5513% fewer conditional cycles, primarily pop/expand reductions of1,107,891/1,137,285; finalize changes are only1,120/995 cycles. Selected last-active bank histograms spend79.625%/79.865% of finalize cycles in the publication-held priority category. Those are state observations, not a controlled causal attribution or predicted gain from adding slots.329 BNN and328 LSTM waves per configuration have no finalize work and select bank0 by default with last_busy=0; do not count those as evidence that bank0 is critical. All histograms include the actual256-cycle clear per wave. Full-batch maximum observed POP count is2,621,038 (C0 LSTM sample24), superseding the smaller representative observation without changing the8-bit generation statement.

Static resource-budget parsing and replacement subtraction pass against actual hierarchical/flat reports. Each two-bank backend retains12,956 LUT and12,018 FF after removing its distinct replaced fabric and physical request/response FIFOs. Before adding the still-pending full memory network, common modules without frontend total735,014 LUT/425,968 FF/1,148 BRAM36 equivalents/640 URAM; adding16 actual synthesized L4 descriptor contexts gives885,222 LUT/566,144 FF. These are incomplete arithmetic compositions, not a fit certificate. F2 separate ROW/META wholefront remains unsynthesized in this composition, and its area is not borrowed from F3.
