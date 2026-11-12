# Large-state integration contract (implementation in progress)

The tested `r2_node_state` has a finite 4-way x32-set x32B cache,32 miss
contexts,16 reserved dirty slots, request/response/result FIFOs and explicit
physical read/write ACKs. It stores two128-bit records per line:
`{flags32 (bit0 changed), pending32, lexical_label64}`.

For L=2^OWNER_BITS, map node n to owner `(n>>2)&(L-1)`, local index
`((n>>(OWNER_BITS+2))<<2)|(n&3)`. Proposal/row/cell-metadata line n>>2
naturally uses that owner. Node-state address is
`state_base + (((n>>(OWNER_BITS+2))*2 + ((n>>1)&1))*L) + owner`, record n&1.
The state base must reserve the padded bank layout. This is an actual 32-bit
address path, not an on-chip array sized to millions of nodes.

Ops READ, MARK_CHANGED, VALID_POP, COMMIT, CLEAR_CHANGED and SEED return the old
record plus status. VALID_POP atomically checks pending valid/version/key and
clears only a matching pending word; its returned label is the wave-start POP
snapshot. COMMIT performs strict whole-pair improvement and returns append-needed
status; a same-bucket pending record keeps its original version. CLEAR_CHANGED
must follow directory/member publication. No cache-line-local bit may replace
external persistent membership.

The next full tile must connect a fair bank/changed request arbiter to this
service (tag high bit selects client), replace label/pending arrays, widen changed
and member node IDs, stream actual proposal and node-state initialization, and
count every operation/ACK in shared physical traffic. Use the same interfaces in
small RTL and large models. Complete graph integration and model calibration are
not yet claimed by the standalone 4M-address test.

`r2_external_changed` reserves32 result mailboxes before atomic MARK issue,
serializes membership through the node-state service and appends first marks to a
finite global-ID FIFO. Overflow must stop success publication, not lose a mark.
A full worklist of repeated marks remains legal because duplicate responses need
no extra FIFO slot. The module is newly written and awaits composition tests.

For integration, reserve a member slot before a COMMIT that may append, return
unused reservation on same-bucket updates, and publish directory/member links
before issuing CLEAR_CHANGED. Tags remain occupied until the final clear ACK.
For POP, reserve output FIFO credit for each in-flight validation; stale responses
release their reservation without generating front/reducer events.

Required remaining evidence: complete8-lane external-state loop, full backing
visibility at fences, capacity/alias/adversarial response tests, independent
module+tile calibration, actual scalable shared-channel topology, complete
candidate OOC, and BNN/LSTM complete40-sample finite architecture runs.
