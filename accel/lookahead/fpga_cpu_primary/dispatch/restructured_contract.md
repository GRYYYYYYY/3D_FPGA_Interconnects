# Restructured dispatcher contract and equivalence argument

`cp_pop_dispatch_restructured.sv` implements the same ports and finite service
contract as [interface.md](interface.md). The original `cp_pop_dispatch.sv`
remains the reference, not a second controller instantiated in the full core.
The parent selected the new module in `cp_full_top` and its 30-file source
closure after the local checks below. That selection does not establish new
resource, timing or full-core calibration qualification.

| Source | SHA-256 |
|---|---|
| Original | `b1f566c826593388b06d73c3733446a3918bc449db98fb5f5264b2287e0bade4` |
| Restructured | `bf78b3d09ac0bd4ead802d1f4d7105a1119ad74bcd74f01c88a2e18c52eff7fb` |

This document describes those exact versions. No RTL change accompanied it.
The source reasoning below uses defined binary state/control and defined
payload where valid. The sequential tests start at reset and use the original
protocol. Arbitrary X propagation, formal equivalence and exhaustive coverage
of every input/state combination are not claimed.

## Request assignment order

For pre-edge state, list banks in circular order from `bank_rotor`, retaining
only `member_valid && !bank_reserved`; call the resulting ordered list B.
List groups in circular order from `group_rr`, retaining only
`!launch_valid`; call this list G. Let N = min(8, |B|, |G|).

The original nested scan assigns B[i] to G[i] for i=0..N−1:

- Each bank is visited once, so setting `used_banks` after a grant cannot
  remove a different later bank from B.
- After selecting a group, the original advances its search to that group's
  successor and marks it used. Subsequent choices therefore visit the next
  remaining groups in G, including wraparound; they cannot revisit a chosen
  group.
- The limit is checked against completed assignments, so exactly the first N
  pairs are formed. With N=0, no assignment occurs and `group_rr` holds.

The new prefix sums implement these same ranks. `bank_prefix` uses seven-bit
unsigned counts (0..64), and `group_prefix` five-bit counts (0..16), without
saturation or overflow. The rank-bank table has eight entries. A group reads
it only when its inclusive rank is 1..N, so the three-bit rank-minus-one index
is in 0..7; truncation cannot select an unrelated entry. `next_group_rr` is
the successor of G[N−1], not `group_rr + N` when occupied groups create holes.
Unassigned `assign_bank` entries remain zero as in the reference.

Both versions gate assignment with pre-edge `!error && mode==RUN`. The new
eligibility includes no extra `ar`, `tv`, `capture_valid`, or frontend-ready
condition. A launch freed by token capture at the current edge is unavailable
until the next edge. The bank rotor continues to increment on every nonreset
edge, including IDLE and error. The existing token-capture limit, operation
hold/fill limit and group-order filling are unchanged.

## Independent return selection

For group g, eligible bank b requires valid POP opcode2, cookie.group=g,
legal slot0..7 and status0 or1. The new implementation computes the same
format-error mask once using static bank slices. It then picks the smallest
eligible bank at or above `result_rr[g]`; if that set is empty, it picks the
smallest eligible bank below the cursor. These two sets partition the same
circular scan used by the original. Prefix OR creates one winner or none;
`!error && !pv[g]` gates capture using the same pre-edge state. A held output
consumed by `pr[g]` at this edge is not immediately reused.

The original writes a ledger-error bit into `bad_result[b]` after selecting
group g, and later groups read that updated vector. Removing this dependency
is valid under the stated binary-input scope: the newly marked bank has
cookie.group=g, while every other group h requires cookie.group=h. It cannot
be eligible for two distinct groups. Thus each group's winner is unaffected
by earlier groups' ledger-error additions. The new `metadata_bad` plus OR of
independent `group_bad` vectors produces the same final error mask.

Only the selected bank undergoes the ledger decision. The check retains all
of `live`, `!returned`, the full 16-bit token, six-bit bank identity and full
32-bit node. The local ledger address is g*8+slot[2:0], and a prior format
check makes that low-bit indexing safe. Group is not inferred from a narrowed
or recycled token. A bad selected ledger entry asserts its error but accepts
**no fallback bank**, even if another bank for that group is valid.

Format errors are detected independently of output occupancy. Ledger errors
affect the externally aggregated error only when a winner exists and the
group's output is free, as in the reference; speculative combinational ledger
values when no winner exists have no acceptance/error effect. Error remains
a register updated at the edge: a newly discovered bad return in one group
does not cancel a concurrent valid return in another group during that edge.
Non-POP results retain the existing top-level routing and are not accepted by
this dispatcher.

Static unpacking preserves the complete input cookie, node, label and status.
The selected bank uses a separate valid flag and six-bit index, replacing the
signed −1 sentinel and runtime cookie index×20 expressions. Payload selection
uses that same one-hot winner. On success both versions capture identical
`pt/pn/pp/stale`, mark the same ledger entry returned, and advance result_rr to
the bank successor modulo64. A rejected or blocked result does not advance RR.

## Register lifetimes and drains

The rewrite introduces no register, queue, reservation or pipeline boundary.
Directory TAKE/RELEASE handling, launch reservation, token capture, operation
hold filling, live-ledger admission and final frontend handoff retain their
original clocked transitions and statement ordering. In particular:

- An admitted operation creates the full live token/node/bank identity;
  capturing its return marks `returned` but does not free `live`.
- Only the held POP's actual frontend `pv && pr` delivery clears live/returned.
  Delivery uses the held token, not new return-bus data.
- Member/bank reservations release only at the original operation handshake.
  No same-edge release/reallocation shortcut was introduced.
- `outstanding`, admission/return/delivery counters, stale count, and all
  completion conditions count the same events. POP completion still does not
  imply frontend expansion, candidate traffic or backend retirement is done.

Given identical state and inputs, the request and return arguments above
provide identical events and captured payloads to the existing clocked
transitions. This is the intended inductive equivalence argument; the tests
provide bounded evidence, not a machine-checked proof of that induction.

## Completed local evidence and limits

Raw results are under
`results/fpga_cpu_primary_20261115/full_synth_d_no_timing/dispatch_mapping_review/`.
`restructured_delivery.json` and `lifecycle_delivery.json` bind both versions,
renamed frozen reference copies, test sources, commands and complete logs.

| Check | Observed result |
|---|---|
| Protocol output miter | 30 external ports and selector observations match at all1236 checked rising edges |
| Error output miter | 10 checked edges; pointer8193 and malformed full-cookie rejection match |
| Assignment selectors | 8192 cases: all64 bank rotors ×16 group rotors ×8 mask patterns |
| Return selectors | 640 cases: all64 cursors ×10 cases, including blocked outputs, metadata/ledger faults and non-POP |
| No-fallback directed case | Bad selected bank suppresses good same-group alternative; independent group still accepts |
| Standalone unchanged regressions | Both pass with staged module-name substitution only |
| Lifecycle miter | All1236 checked edges match for 30 outputs, control/valid masks, 64-bank state/held payload arrays, 16-group reservation/cursor arrays and128 ledger entries |

The reachable protocol run includes3 waves,192 TAKEs,508 RELEASE/POPs,
121 generation wraps, peak8 admissions and128 outstanding records, with the
same1236 cycles as the reference. Held external payloads, lifecycle arrays and
counters are explicitly compared. The selector tests deliberately deposit
known state to isolate combinational decisions; not every such snapshot is
claimed reachable. These patterns do not exhaust all masks, all ledger fault
combinations or every bank-identity mismatch. The bank/node/token comparisons
remain explicit in both sources; this source reasoning is not represented as
additional executed test coverage.

No further implementation mismatch was identified in this review. Remaining
qualification is separate: new-source complete RTL integration, model
calibration, actual full-resource synthesis and applicable physical timing.
Old g model and52-sample evidence remain bound to their original sources until
the parent joins the corresponding integration evidence. The baseline's
1103-level return-error path motivated the rewrite, but neither the prefix
source structure nor behavioral PASS proves a new LUT count, DSP count,
critical-path depth, frequency or performance improvement.
