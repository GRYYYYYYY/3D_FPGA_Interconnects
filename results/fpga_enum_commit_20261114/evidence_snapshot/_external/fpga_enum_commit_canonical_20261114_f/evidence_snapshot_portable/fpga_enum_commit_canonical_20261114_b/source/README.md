# K8 canonical / pending and shared tagged physical port

Owned source boundary: this directory. Parent owns integrated enum/scratch/owner and OOC.

Planned modules (implementation in progress):

* `ec_pending_k8`: one subbank, K=8, frozen `pending17_transform` from `fpga_sparse_stream_r2/rtl/pending17_service.sv`. Parameters OWNER_ID (node[6:2]), SUBBANK (node[7]), WORD_BITS (default14), LABEL_BASE_LINE (32-bit). Nodes remain full22-bit; reduced WORD_BITS rejects out-of-range addresses. PV indexing=node[21:8], no owner alias. One actual synchronous 68-bit PV read port + one write port; no replicated state. Clear has real `2**WORD_BITS` cycles. `sample_clear` only accepted when idle.
* `ec_tagged_port`: four clients, one physical32B port, 32 total tags/credits; clients0/1 canonical subbanks0/1, clients2/3 scratch subbanks0/1. `cv/cr/cw/cl/cid/cd`, `rv/rr/rid/rd` packed per-client. cl32 is physical line and must have low5 bits OWNER_ID. Local cid/rid11={generation8,slot3}; a single-outstanding scratch client may use any fixed local ID. Physical interface mv/mr/mw/ml32/mtag5/md256 and sv/sr/stag5/sd256. Credits release upon physical response acceptance. Per-client finite request FIFO4 and physical return FIFO4; registered request and per-client response boundaries. Fair RR request selection. Backpressured head response may block other return clients, honestly finite.

`ec_pending_k8` request mirrors old service: iv/ir, node22, opcode3, operand64, line_operand256, argument28; node_count32 mandatory. Memory interface mv/mr/mw/ml32/md256/mid11 and rv/rr/rd256/rid11. Completion ov/ordy atomically carries result_node22, result_opcode3, status4, old_label64, event_argument28, event_arguments112, append_mask4, result_pv68. `result_pv` is a diagnostic copy from the retiring transaction, not an extra memory port. Completion of opcode2 with status[0] is the immutable valid POP token. Stale POP has no token/event. Consumer must reserve all append_mask directory slots before asserting ordy. No private directory storage is claimed here.

Each accepted transaction reserves four finite event/retirement slots (8x4=32 total); valid POP publication also uses its reserved transaction storage. Word reservation remains until canonical ACK (if any), actual PV write edge, and atomic completion handshake. `accepted/retired`, `live_count`, `event_reserved`, peaks, `idle`, address/protocol errors expose conservation. Scratch integrations must wait for canonical idle and physical arbiter idle at relevant wave/sample fences; ordinary independent transactions can overlap.

Final tested interfaces and results will be appended below.
