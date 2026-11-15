# Dispatcher calibration and integration review

DUT is `cp_pop_dispatch.sv`; frozen-source standalone test receipts are in
`verification.json`. Full-cookie ledger uses16 independent8-entry groups.
Result bank arbitration comes before each group's ledger read, avoiding64
asynchronous128-entry read ports. Ledger writes also partition by fixed group.

## Exact storage and handshakes

Each bank has one detached ptr14, one pending directory transaction and one
immutable member node32/arg28. Each frontend group has one bank launch record
(valid/sent/bank6) plus one token capture(valid/issued/bank6/token16). They can
refer to two different banks. Only8 POP command holds are valid globally.
Each group has one POP delivery register;128 live ledger slots retain full
16-bit token, node32 and bank6 until actual frontend input handoff. The ledger
has a separate returned bit to reject duplicate backend completions.

All credit/hold reuse observes pre-edge state; the implementation deliberately
has no same-edge refill for command holds, reservation capture or POP output.
Idle/done includes these holds, detached pointers, directory commands/replies,
members, reserved banks and all admitted-not-delivered slots. It does not
claim downstream T/D/E/FP32/candidate processing or delayed backend core ACK
has finished. Full top must include its separate downstream barriers.

## Differences from LF finite.hpp dispatch_pop()

- Fixed16 groups and64 banks, unchanged max8 POP actual accepts per edge.
- Bank scan starts from a core-clock rotor; group RR advances after each
  assigned member. The hardware can queue a new launch while the earlier
  token capture is still waiting to admit its POP, as in the two-stage model.
- The finite model's direct token allocation callback becomes actual av/ar,
  frontend reservation launch/capture, tv/tr handshakes. Capture is capped at
  eight token handshakes per edge. The real frontend token pool governs all
  capacity and generation; the dispatcher does not allocate speculative T.
- Hardware has eight global registered POP command holds. Holds are selected
  in ascending group order into pre-edge free capacity. Backpressured valid
  never moves/revokes. The old model directly tried enqueue_tx in ascending
  group order, potentially filling a released slot at its modeled later edge;
  it cannot be reused as an exact RTL clock schedule without this layer.
- Every response is arbitrated by per-group RR over64 banks into one held
  POP output. It cannot bypass or refill at its consumption edge. The old
  model's pop_context due edge must be mapped to this explicit register and
  lf_front_context's additional pop_launch slice.
- TAKE64 is a true response barrier. On start edgeS, TAKE command becomes
  visible afterS and can handshake atS+1. If the last TAKE reply handshakes atR,
  mode changes to RUN atR+1, a RELEASE command is registered atR+2, and it can
  handshake atR+3. Backend command/response FIFO2s are additional real stages.
- If a RELEASE reply enters the member hold atR, the earliest reservation
  launch registration isR+1 and av/ar handshakeR+2. For an otherwise unstalled
  lf_front_context, external token handshake isR+4, POP hold registrationR+5,
  and backend op handshakeR+6. These edge statements assume no prior capture
  or command-hold occupancy. They are not a claim of steady-state II6.
- A backend POP completion handshake atQ enters held pv; frontend pv/pr can
  handshake atQ+1 and its inner POP can reach the leaf atQ+2. Dispatcher ledger
  releases atQ+1; T itself remains owned by the frontend until its real
  stale/drop or immutable D copy. Backend deferred core retirement remains
  independently protected by cp_backend_bank and parent expansion_idle.

## Independent checks run

XSim2022.2, behavioral, 5ns testbench clock. No synthesis or routed timing
claim is made by this subtask. Positive finite endpoints cover3 waves,
192 TAKEs,508 RELEASE/POP operations,121 generation wraps, global max8 accepts
and128 peak admitted-not-delivered POPs. Long command and frontend backpressure
checks every held payload; per-bank response queues return independently.
The third wave is empty and still performs a full64-bank TAKE barrier.
Terminal at1236 cycles. Rejection test refuses pointer8193 and an unowned
full20-bit POP cookie. Tests compare node/pair/stale/token against an independent
scoreboard; endpoints do not implement the native graph algorithm.

## Read-only full-top/admin review

Reviewed cp_full_top.sv, cp_admin.sv, cp_candidate_network.sv,
cp_backend_bank.sv, minimum collector and output service. No edits outside
this owned dispatch directory were made.

- MIN_START/WAIT forces directory opcode3 before testing bank ctrl_ready;
  this avoids the backend's ctrl_op!=0 readiness gate. MIN retains all64
  actual replies and its real registered reduction tree.
- SEED_WAIT waits bank_idle, including operation FIFO, canonical lifecycle,
  publication, real directory and deferred completion, plus network drain.
- REOPEN pulse only follows every bank_done. It drops latched flush, allowing
  enumerator FINISH→RUN and scratch END_WAVE→CLEAR. REOPEN_WAIT waits actual
  256-word scratch bitmap clear via initialized/expansion_idle.
- EXPAND includes dispatcher pops_done and all front/candidate/backend/net/
  output idle conditions. The dispatcher alone is insufficient and is not
  used as a replacement for them.
- Admin output collision guard is valid for this strict-prefix exporter:
  write_v1 implies write_v0 and consecutive line addresses. It would require
  revision if reused with two arbitrary independent producers.
- Export ACKs pass through the held collector before output acked_count
  advances; export_done waits those ACKs, and top additionally waits network
  and banks. No ACK-at-enqueue completion was found.
- Cost settle2 covers context capture then leaf cost-table write.
- Calibration must include independent per-port INIT indices (old finite
  global-next stalls later sources), serialized cost reads and up-to4 cost
  write edges per beat plus settle, and REOPEN edge handoffs.

Concrete admission limitation reported to parent: df_edge_group has16 cost
entries with neither reset initialization nor cost_count input. cp_admin loads
only indices<cfg_costs. A runtime edge using a larger nibble can read unknown
or stale state. Frozen admitted native inputs are valid, but complete arbitrary
input rejection needs either an explicit source-bound admission guarantee or
checking the selected consumed edge in a copied leaf. Checking all eight
words of a returned EDGE beat can incorrectly reject unconsumed padding.
Parent owns resolution; no unfounded assertion that this malformed input is
currently rejected is made here.
