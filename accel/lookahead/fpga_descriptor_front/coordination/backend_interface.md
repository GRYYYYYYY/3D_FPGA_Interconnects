# Backend context contract (implementation target, calibration pending)

Frozen base: ccec3da ec_backend_owner NEW=1, two subbanks, enum2/K8 and ec_tagged_port unmodified.
The new synthesizable df_backend_context inserts real finite boundaries:

* Candidate input: independent depth2 registered FIFO per subbank (96b). External handshake at edge t becomes core-visible during t..t+1 and can be consumed earliest edge t+1. No empty fallthrough; full queue rejects an enqueue even if popping on that edge. Simultaneous non-full push/pop allowed.
* Explicit canonical op input: same depth2 FIFO/bank, payload node22/op3/pair64/line256/arg28 =373bits.
* Shared physical request: depth2 registered FIFO, payload write1/line32/tag5/data256=294bits. Core port staging -> context enqueue -> external physical issue adds one edge minimum. Physical memory80ns starts at external issue, not at enqueue. Tags remain allocated across FIFO residence.
* Physical response: depth2 registered FIFO, tag5/data256=261bits. Actual memory response captured at t reaches frozen fabric earliest t+1. FIFO depth does not create credits. Frozen fabric still has returnFIFO4 and each-client registered response.
* Directory per bank: one held capture register with deferred acknowledgement. IDLE captures a valid stable core event at t (does not acknowledge it). PENDING presents to actual downstream consumer earliest t+1; on handshake goes ACK. ACK asserts upstream ready at t+2 earliest and returns IDLE. No early canonical word release on FIFO enqueue. No capture/reuse same edge as ACK. Three-edge minimum spacing; add two edges per event relative to direct-ready boundary. Capacity1/bank.
* Result/POP completion per bank: identical deferred-ACK capture, full payload node22/op3/status4/mask4/label64/events112/PV68=277bits. Even zero-event result must pass capture/consumer/ACK. Reservation is held through actual output consumption.
* flush registered one edge and held away from core until BOTH input candidate queues empty. sample_clear/node_count registered one edge; clear allowed only drained, as frozen protocol. Status/counter outputs captured one edge. done includes core done, queues empty, directory/result adapters IDLE, memory queues empty, no pending clear. No reset between waves.

No clock/I/O delay relaxation: actual5ns and old input/output min0.1/max0.8ns retained for first routed attempt. Parent launch/capture FF paths are included. External board paths remain excluded from this local context's scope.

Service worker owns global network. This local shared-port boundary adds only request/response FIFO2; it reuses frozen four clients xFIFO4/32tags/returnFIFO4. Model must include these local slices or explicitly replace them with identical shared-network boundary stages, never count twice. Exact event replay and final source hashes will follow.

## Global composition boundary and evidence scope

The local owner port clients are {canonical bank0, canonical bank1, scratch bank0,
scratch bank1}. The full common network instead groups {EDGE, control, canonical,
scratch} and adds source-class concentration and destination return arbitration.
These are different arbitration compositions despite identical FIFO4/tag32/return4
geometry. The full network replaces the local owner fabric at its four logical
client pins; it does not stack another implicitly free physical port. The common
network explicitly retains the physical request/return FIFO2 boundaries above.
Local native/backend timing and calibration do not establish full-network cycle
composition, full-kernel fit or frequency. Service-worker RTL/model replay owns
that separate qualification. Directory-ready at this context boundary means the
actual directory RAM operation has completed, not mere command admission.
