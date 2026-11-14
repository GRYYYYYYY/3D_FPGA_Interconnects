# Source-local request identity budget

This is a read-only width-feasibility audit of frozen model D, not an implemented or calibrated complete-top packing adapter. The common network actually carries opaque32-bit local ID and8-bit source. Its physical tag is separate. Source identifies group/bank/class; address and256-bit data are separate network fields.

The active frozen paths already wrap generations to8 bits: `dispatch_pop` token allocation, `allocate_E`, ROW header allocation, META allocation and canonical transaction allocation all use `(generation+1)&255`. The unmasked `reserve_token()` helper has no caller in the frozen source. Do not report a wide-generation mismatch based on that dead helper. Eight-bit generation alone is not a proof of safe reuse; ownership, outstanding-response drain and slot reuse restrictions remain essential.

| Logical source | Feasible local ID fields | Bits | Scope |
|---|---|---:|---|
| EDGE | group-local beat slot6 + generation8 |14|up to64 slots/group|
| ROW/DESC | local header/token4 + generation8 + row-half1 + format-kind1 |14|up to16 headers/tokens per group; half retained explicitly if required|
| META | local slot4 + generation8 |12|up to16 META slots/group|
| CAN | transaction slot3 + generation8 + request-kind2 |13|bank recovered from source; POP/CAN read/write|
| SCR | scratch line20 + read/write1 |21|admission nodes<=2^22, hence lines<2^20; bank recovered from source|
| MISC output/init/cost | output beat13 + sample6 + kind2 |21|native40 samples and<=32768 cells; INIT/COST do not consume id/gen|

Each fits32 bits, so no width overflow was established. The MISC sample budget is specific to the native40 workload, not arbitrary job counts. Any later interleaved job design must explicitly implement job identity and all other context fields instead of inheriting this single-active-sample scope.

The28 completed D representative sample runs have a largest observed POP count of2,617,444 (C0,LSTM sample18; parents2,617,444,stale0). This is a measured representative bound, not a full-batch bound and not the basis for the8-bit generation representation. Full-batch observations can be added once their actual terminal receipts exist.

No complete-top packing/unpacking adapter is currently implemented and calibrated. The C++ Request struct retains separate kind/id/gen fields. Width feasibility and exact opaque-bit transport calibration therefore do not certify complete-top metadata integration, arbitrary tag generation wrapping, or whole-kernel timing. No frozen model/header changes or experiment reruns were requested by this audit.

Complete-batch addendum: the subsequent independent160-sample C0/F2 full audit found maximum POP2,621,038 at C0 LSTM sample24. See results/review/model_d_unique_full_batch_audit.json. The earlier representative measurement remains preserved; neither count is a universal bound over arbitrary workloads.
