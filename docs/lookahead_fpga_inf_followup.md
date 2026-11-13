# INF followup after5af9908

This continues the existing isolated R2 branch; original/main/STRICT/goldens remain
unchanged. All previous failed receipts and directories are retained.

## Execution repairs

The original queued `job-7977d112-86f2-42f0-9c4e-6481294f1e30` was confirmed to
reference the defective worker, never started, and was stopped under the followup
authorization. Replacement `job-b0b53982-9534-405e-a441-83c777b9e93d` uses a frozen
worker and all10 compile inputs, with both CPU sources compiled successfully before
submission. CUDA compile is the first allocated-node stage. The current binding is
`config/current_software_run.json`; watcher/observer/finalizer resolve this config.
The worker records failed builds rather than leaving ambiguous empty output.

Native publication now checks cleanliness BEFORE observation, then permits only
its exact hash-bound generated manifest; regression checks reject unrelated edits,
index changes and manifest tampering. Only the old supervisors were replaced.
The six original solver processes and original Vivado run were not restarted.

## Original OOC chain

The original P8/F0 run completed with source exit1 and
`route_design Complete, Failed Timing & Nets!`. Actual10ns setup/hold slacks are
−8.895/−0.112ns,263299 nets have resource conflicts and522787 node overlaps remain.
Resources:786905 LUT,504703 FF,1064 RAMB36,296 RAMB18,288 URAM.
This is a negative complete-candidate result, not clock qualification. The gate
stopped before the slower-period loop; no frequency was inferred from WNS.

## Pending17 and the one targeted combination

`pending17.hpp` transcribes old node_state operations and independently encodes
present+version.1,049,148 operation checks pass, including4095 constructed wraps;
version0 is not absence. Both complete native40 workloads pass207135879/210880424
state-operation comparisons. All output bytes, wave work rows and closure records
match the old private-INF oracle.91 additional fixtures pass. These are functional
experiments, not performance measurements or STRICT equivalence claims.

The combined two-subbank RTL has BRAM metadata, flat URAM sector payload, whole68bit
pending-word RMW,32B scratch, finite2048-entry spilled lists and resident-direct
unique line commits. Pending label writes must ACK before PV/event retirement;
a bank-wide reservation prevents mixed old/new state from being observed. This
is conservative pending throughput, not a claim of a fully pipelined pending bank.
The accumulator reserves all in-flight sets; independent-set acceptance reaches
II1. Same-set traffic stalls explicitly.

The finite testbench shares ONE32B physical request channel across both subbanks'
scratch and canonical clients, with bounded credits, variable delays and reverse
ACK completion. No graph-sized canonical mirror exists in RTL. Canonical labels
are external packed64; testbench backing is finite. Micro tests initialize the
external test memory outside the core loop; full model initialization is counted.

The initial multidimensional RAM declaration failed Vivado2022.2 elaboration.
Independent RAM declarations remove that representation problem; all cycle logs
and output rows remain identical. A later directory-event audit corrected POP's
append indication and added argument validation and explicit MAX_N rejection.
All attempts remain separately frozen. OOC is performed with5ns clock and explicit
input/output min0.2ns,max1ns delays; no bare unconstrained-I/O qualification.

The original derived0.143656/0.145130s values remain partial conditional bounds.
Finite event schedule A was deliberately conservative in source-order port
reservation and is retained as a serialization diagnostic, not an architecture
ceiling. Schedule B uses64 finite chronological front-end contexts and recalculates
replacement/spill traffic. Neither is RTL calibrated; FPGA seconds remain null.

## Status

Original OOC terminal negative is audited. Native six-run and software result
chains remain independent; their completion does not imply each other completed.
New combination OOC and finite-service analysis are in progress. No full64-subbank
integration is authorized by the evidence yet. `board_measured=false` throughout.
