# Pending17 mapping and atomic retirement contract

The domain is positive-FP32 ALT whole-pair ordering and SHIFT20 bucket keys.
For reachable old records, a present pending word stores the bucket equal to
label[63:52]. An absent word is allzero. Flags for changed-list deduplication are
not part of the canonical representation; unique occupied/spilled enumeration
replaces their purpose at the original wave boundary.

Encoding: old P(bit28),V(bits27:12),K(bits11:0) maps to P:V in17bits.
Decoding uses the same logical old label: P?{3'b0,1'b1,V,label[63:52]}:0.
Present is independent of V, including the constructed P=1,V=0 wrap state.

Induction over operations:

- Init gives INF/P0/V0; SEED gives label0/P1/V1.
- Invalid POP changes nothing. Valid POP checks P,V and the old-label-derived K,
  returns old label and clears all17 PV bits.
- Non-improving COMMIT changes neither field and preserves the old rejection bit.
- Same-bucket improvement with P1 changes only label; no new event or version.
- Absent or migrating improvement changes label/P/V together, increments V modulo
  65536 and publishes exactly the corresponding directory event.

Between valid POPs, bucket-changing improvements strictly decrease a12bit key;
there can be at most4096 increments. Valid POP resets V. Natural traces therefore
do not justify changing the16bit contract. Constructed V65535→0 checks retain P1.
The functional experiment checks old32 reconstruction after every operation,
including full BNN/LSTM40, and compares complete outputs and all wave-work rows.

Four nodes share one68bit URAM word. The micro locks the whole subbank from request
acceptance until response/directory acceptance; this conservatively includes every
pending-word hazard. A full-line COMMIT performs four whole-pair comparisons and
one32B canonical write if needed. It waits for write ACK; then updates the entire
PV word on the same edge as the event handshake. Output append masks distinguish
POP success from append. The output consumer must reserve all indicated directory
slots before accepting the atomic event. While blocked, outputs remain stable and
no new POP/COMMIT can observe the partial transaction. The lock is intentionally
stronger than a multi-entry scoreboard and its throughput must not be called II1.

The accumulator separately reserves every in-flight set across all four stages.
Tag/metadata updates use one write per accepted candidate. Independent sets can
advance each cycle; same-set accesses stall. No single last-write bypass is used
as a substitute for the full pipeline hazard condition.

The32B scratch service does not read uninitialized first-spill payload. It holds
its reservation until ACK, so a later fragment cannot repeat first-write and lose
a minimum. Distinct subbanks may complete ACKs in reverse order. Two bitmap bits
per line track spilled and already-committed state. Resident rows merge scratch
when needed and commit once; spilled-ID enumeration skips that consumed
intersection. The finite2048-ID list rejects overflow. Each new wave clears all256
bitmap words; payload need not be zeroed because valid sectors are masked to INF.

The wave fence requires accumulator drain, sparse enumeration completion, no
pending service transaction, and accepted directory events. This contract assumes
all canonical readers for an owner pass through its service. An independent DMA
reader during a transaction would violate that interface contract. Board behavior,
full32-owner arbitration and integrated directory capacity are not established by
this microprototype.
