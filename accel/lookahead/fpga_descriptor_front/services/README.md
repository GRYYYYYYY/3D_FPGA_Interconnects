# Bounded shared services for descriptor controls

These sources replace the historical final-D abstract directory and globalFIFO64
with explicit synchronous RAM operations and registered, finite networks. C0/F1/F2/F3
share the same organization. They are local implementation/calibration evidence;
no service in this directory grants a complete-kernel clock or fit qualification.

## Exact execution contract

`directory_model.hpp` and `df_directory_bank.sv` implement one bank with8192
member slots and4096 bucket heads/tails. Payload(node32,arg32) is a separate64bit
URAM; next14, free13 and packedhead/tail28 use separate BRAM arrays. The bucket
bitmap is64x64 synchronous distributed RAM plus a64bit upper summary. Reset
charges8192 writes, initializing free stack/headtail/bitmap in parallel. Payload
is never read before allocation. The free stack allocates descending IDs; this
changes storage identity, not linked-list order.

One operation and one held response are permitted per bank. An APPEND accepted
at C reads RAMs on that edge, consumes read outputs at C+1, writes newmember and
head/bitmap at C+2, links the old tail at C+3, then presents response after C+4
(earliest handshake C+5). TAKE detaches and clears a bucket; RELEASE reads a
detached member and returns its slot; each can respond earliest C+3. Nonempty
MIN has earliest response C+2; empty MIN and explicit capacity errors respond
at C+1. No request is accepted on the previous response-consumption edge.
Serialization resolves head/tail/free-list hazards without speculative
forwarding. There is no implicit dual write to one next-pointer RAM. Publication
must await APPEND completion, and released POP payload requires a finite hold
until token/canonical admission. Arbitrary double releases are outside the legal
client contract; invalid pointers and empty/full resource errors are explicit.

`df_min_collect.sv` and `MinimumCollector` issue exactly oneMIN per bank after a
quiescent fence, collect64 held responses, and drive the actual registered binary
`df_min_tree.sv`/`MinimumTree`. Start at C exposes bankcommands next edge. Last
response capture T permits treeinput at T+1 and earliest output handshakeT+7.
Empty leaves carry sentinel4096. The tree has six registered reductions and
holds all stages when its output is blocked. No fixed-delay substitute is used.

`df_rr_router.sv` implements a balanced priority AND payload reduction tree per
output. The priority key `{index<cursor,index}` selects the suffix beginning at
the cursor, then wraps. Cursor advances only upon a real input handshake into
that output's registered hold. Old held output may be replaced on its actual
handshake; a newly arrived input cannot bypass a source FIFO. The executable
`RegisteredRouter` uses the equivalent minimum cyclic rank in O(inputs+outputs)
work and is independently checked against direct cyclic enumeration.

`df_memory_network.sv` has sourceFIFO4 -> registered RR(port,class) hold ->
fourFIFO4 clients per physicalport -> held physicalrequest with32 allocatedtags
-> physicalFIFO2 -> external memory. Return is externalFIFO2 -> physicalreturn
FIFO4 -> oneclient register -> registered RR/source hold -> consumer. Every
stage backpressures; no fullFIFO accepts just because it pops on that edge.
Tags are allocated at physicalrequest-register fill and remain busy through
both requestFIFO2 residence and responseFIFO2 residence. Tag release is the
accepted transfer into the internal physicalreturnFIFO4; that tag is reusable
only on a later edge. `df_tagged_port` is a width-parameterized version of the
frozen four-client logic, with an opaque32-bit local ID and separate8-bit source.
The tested transport preserves these actual wire bits. A complete-top packing
adapter from the model's separate kind/id/gen fields is still required. Review
confirmed active model generation paths wrap to8bits like the leaf; an unused
legacy helper with an unmasked increment is not an active-path defect. Actual
wire packing and complete-top integration remain separate qualification work.

Actual default geometry is208sources/32physicalports. SourceIDs0..15EDGE,
16..31H/D,32..47META,48..111canonical,112..175scratch,176..207per-portMISC.
Classes are EDGE0, H/D/META/MISC1, canonical2, scratch3. The full resource wrapper
`df_memory_network_full.sv` hardwires these classes. It replaces the old owner's
local fabric at CAN/SCR logical boundaries; it is not cascaded on top of it.
`network_model.hpp::MemoryNetwork` composes exactly the same stages. Memory
latency is an external assumption:80ns begins at externalissue, never at an
internal enqueue. The local stress uses delayed/OOO responses, not measuredHBM.

`df_candidate_network.sv` is the full64lane/64bank topology: FIFO4 perlane ->
registered RR winner perbank -> FIFO16 perbank. Bank mapping is
`2*((node/4)&31)+(((node/4)>>5)&1)`. It does not add arithmetic lanes or E/beat
slots; its extra queue/control area is explicitly counted.

## Executed verification

Final source-bound regression: `results/fpga_descriptor_front_20261114/services_b`.

| Circuit | Exact RTL/C++ cycles | Checks |
|---|---:|---|
| Directorybank |173877|24610 commands;8192 saturation;overflow status;detach then samebucket append;free reuse;MIN word boundaries;49220 blocked response cycles|
| Complete memorynetwork,8sources/2ports |2184|2048 unique requests;1698 out-of-order selections;all4client queues depth4,returnFIFO4,32credits reached;payload/ID/order/conservation/drain|
| Candidate network,64lanes/64banks |2817|4096 unique candidates;contention/hotbank and all destinations;FIFO16 reached;conservation/drain|
| Min tree,64leaves |1200|533 transactions;empty/mixed leaves;output stalls;exact six-stage behavior|
| MINcollector +64actualdirectorybanks |8824|32 complete queries;8192 initialization clocks;staggered empty/nonempty bank responses;held output|

Additional `services_payload_c` and `services_payload_d` replay the same2184 network cycles with
independent non-echo256bit physical returns and distinct64bit segments, so
request-data echo or return-lane swaps cannot masquerade as valid payloads.
D also XORs every local ID with0xa5c00000 to exercise high opaqueID bits.
The RTL and all shared model headers are unchanged. Reproduce D with
`verify_return_payload.py NEW_OUTPUT_DIRECTORY --id-xor 0xa5c00000`. C's original
verifier source is preserved under its `source/`; D binds the current verifier.

Directory tests use an independent software list/free ownership oracle before
emitting cycle-model expectations. Network tests enforce request/response ID
and payload conservation separately from the model. HDL checks every external
ready/valid and every valid payload against generated pre-edge expectations.
The complete208source/32port model adapter is independently replayed by the model
owner; that result is separate from the reduced-geometry RTL network test.

Reproduce in a NEW directory:

```
python3 accel/lookahead/fpga_descriptor_front/services/run_tests.py \
  results/fpga_descriptor_front_20261114/services_replay_unique
```

The runner binds/copies sources, compiles C++ references, emits deterministic
stimuli, runs all five XSim testbenches under Vivado2022.2 and requires explicit
TEST_PASS without Fatal/ERROR. Each case has a watchdog. Existing output
folders are rejected. Header APIs were frozen before final model integration.

## Physical evidence and remaining limits

Actual xcu280-fsvh2892-2L-e resource-only synthesis (no clock constraint):

* Directorybank:794LUT(including64LUTRAM),379FF,9BRAM36+2BRAM18,2URAM,0DSP.
  The RAM cell report identifies each payload/next/free/head array.64bank
  arithmetic is50816LUT,24256FF,640BRAM36 equivalents,128URAM; it excludes
  collector/inter-bank routing/reset/control placement.
* Full64x64 candidate network:250969LUT(including7168LUTRAM),7872FF,0BRAM/URAM/DSP.
  This significant cost is real synthesis, not a cheap ideal crossbar.
* MINcollector +six-stage tree:1666LUT,1787FF,0RAM/DSP.
* Full208source/32port network: separate actual synthesis receipt under
  `services_memory_synth`; do not scale the8source/2port test into a fit claim.

Resource reproduction is `vivado -mode batch -source ABS/services/synth_resources.tcl
-tclargs df_memory_network_full` from a new result directory, with the configured
Vivado2022.2 executable; choose another listed top for its isolated resource point.
Actual historical commands and source hashes are preserved in the run receipts.

The directoryURAM synthesis warning reports no optional internal URAM output
pipeline. The RTL has synchronous reads and serialized capture, but200MHz has
not been established. Candidate/memory networks likewise have no routed timing
qualification here. Full budget must remove the old localfabric before adding
the replacement commonnetwork, and include frontFP32, output, controller and
all real state. Resource sums are bookkeeping, not placement proof.

Two setup mistakes are retained in `services_a`: a Tcl property value beginning
with '-' required explicit `-name/-value/-objects`; the first candidate run used
the prior active simset's vector option. Explicit `current_fileset -simset`
fixed the latter, after preserving its cycle0Fatal. Neither is a hardware
negative result. The final fresh-project regression verifies the fixes.

All run-time mutation is confined to the new candidate worktree. Historical
sources and evidence remain read-only. No complete kernel, software speedup,
board measurement, or FPGA-wide no-go is asserted by these service results.


Final full-network evidence is `services_memory_synth/mapped_resource_audit.json`:
actual technology mapping completes with9736935logic LUT primitives, whose
optimistic physical-LUT lower bound4868468 already exceeds1303680 device LUTs.
The subsequent DB import is stopped by this resource evidence; no completed
full synth command/utilization/DCP/route-clock is claimed. All512 warnings are
Synth8-7186 ignored distributed attributes for qmem. See the self-contained
report and replacement-aware resource_budget_final.json for precise scope.
Original owned processes are terminal, with identities verified; historical
sessions remain untouched.
