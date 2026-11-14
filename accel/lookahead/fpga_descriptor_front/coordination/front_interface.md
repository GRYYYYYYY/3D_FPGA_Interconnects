# Front leaf implementation contract (initial, 2026-11-14)
Owner front. Module df_front_group parameter L=4/8,C=4,B=8,T=2*L (F3 T8, F1 T16).
Tokens reserved BEFORE POP, separate reserve handshake returns token/gen. POP-result accepts immutable node/pair/epoch and stale; stale releases reserved token without DESC. Legal POP creates one DESC request. POP mechanism itself outside leaf.
DESC and EDGE have independent registered request holds and independent return payload/state writes, each max1/cycle, no coalescing. DESC 64/128bit format configurable, one parent per request, beat address base+floor(node/4 or node/2). Tags token/slot + generation. Returned DESC decoded into separate finite ready flags (T entries). Zero-degree adjacency hands off without allocating E. Target handshake uses immutable cell/pair; token releases only after both handoffs, next-edge reuse. Group target offer max1/cycle to shared8banks (outside leaf).
E/slots L*4/L*8, D1, balanced RR allocation. Precompute last-edge/last-beat (offset32 validated), narrow29bit beat indexes. Lane input is actual elastic operand bundle (dst,pair,cost,context,slot,gen,last), arithmetic pipeline SIX registers: capture; order/exponent; align/sticky; add/normalize; round; pack/error. Minimum capture-to-output 5 edge intervals; handshakes occupy 6 sequential stages, II1, all stages stallable. Old pair latency2 cannot be reused. Source edge cursor/slot may advance at operand capture because immutable operands/tags copied. Final drain includes every arithmetic/output stage.
Requests reserve slot before logical handshake; no same-edge released-slot reuse. RR moves only on success. Leaf does not claim complete POP/global network/directory/accumulator/output-bank timing calibration. Actual TB/context evidence forthcoming; exact timing trace will supersede prose if discrepancy found.

## Implemented register context (additional, not absorbed into network FIFO)
`front/df_front_context.sv`, `df_slice.sv`: one entry each reserve-command, reserve-tokenACK, POP-result129b, DESCrequest80b, EDGErequest80b, DESCreturn272b, EDGEreturn272b, target95b, and per-lane candidate128b. They add one edge, never bypass newly accepted entries, allow replacement on an OLD downstream handshake. All are additional to coreleaf T tokens/ready and services sourceFIFO4. Core target branch hands off to targetcapture; actual outputbank update occurs on its later consumer handshake. Token reserve core admission requires room in reserveACK capture. Config/counters also registered; config stable until drain.
Core exact minimum edges: legalPOP P->heldDESC P+1->logicalrequest handshakeP+2. DESCreturn R->decodeR+1->heldbranchselectR+2->actualE/target handoffR+3. Retire afterboth handoffs recorded, no sameedge token reuse. Six arithmetic stages captureC->ov atC+5->earliestconsumerC+6, plus contextcandidatecapture addsone. Pair operands hold selector ctx/slot when blocked; no extra data capacity.

## Candidate diagnostic tag and wave scope
The 32-bit candidate tag is `{epoch[7:0], generation8, slot8, context7,last}`.
Epoch is explicitly modulo256 diagnostic metadata, not a full16-bit ownership ID.
Single active wave/sample drains all candidates before advancing; actual request/
return ownership uses live slot plus its generation, so no active-wave alias is
accepted. No two-job interleaved top or full-job identity is claimed here. Such a
variant would need explicit job identity in every storage/route stage (guide7.3).
