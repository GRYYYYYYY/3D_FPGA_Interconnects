# Complete-core runtime and memory interface

`cp_full_top` is fixed production64 candidate lanes,16 front groups and64
backend banks. All payload vectors pack item i at `[i*WIDTH +: WIDTH]`.
The physical memory bus has32 independent32-byte ports and32 tags per port.
There is one physical credit pool per port shared by all logical traffic.

After global reset, program each job through `cfg_job_we/index/source/targets`.
The256-entry job table retains its configuration across batches. `targets` is
the count of unique eligible target metadata cells, obtained from immutable
input admission, not from expected output. Hold global configuration stable
from start through done; job writes are accepted only while !busy. Assert
start while idle for one edge. `sample_done` follows all actual output ACKs;
batch done follows the final sample completion. Error is sticky until reset or
a new accepted start. Configuration rejection produces done/error without any
physical memory request. A runtime protocol error stops the batch with error;
it does not promise recovery of outstanding external transactions.

All bases and strides are in32-byte lines. Bases are32-line aligned. Inputs
are admitted disjoint readonly descriptor/edge/cost regions; canonical and
scratch use ceil(nodes/4) mutable lines. Each sample has its own descriptor
stride and output stride. Output padding contains whole-pair MISSING
`0x7fc000007fc00000`; canonical initialization uses whole-pair infinity
`0x7f8000007f800000`. Runtime limits: nodes≤4194304,cells≤32768,costs≤16,
jobs≤256. Node/edge encoding and cost-index validity are host admission
invariants. Upper address bits/end-range overflow are rejected before a line
is handed to the32-bit network.

| Logical source | Request kind | localID32 | generation32 |
|---|---|---|---|
| EDGE0..15 | 2 | zero-extended edge token low8 | zero-extended edge token high8 |
| DESC16..31 | 11 | zero-extended descriptor token low8 | zero-extended descriptor token high8 |
| META32..47 | inactive in L1 | zero | zero |
| CAN48..111 | 4 POP read,5 canonical read,6 write | K8 slot0..7 | full32-bit per-slot generation |
| SCR112..175 | 7 read,8 write | bank0..63 | actual relative line (≤20 meaningful bits under node limit) |
| ADMIN176..207 | 0 INIT | relative canonical line | sample0..255 |
| ADMIN176..207 | 10 COST | cost beat0..3 | sample0..255 |
| ADMIN176..207 | 9 OUTPUT | full absolute output line | sample0..255 |

The wire retains source6/kind4/generation32/localID32. Local CAN/SCR/ADMIN
source routing is additionally bound to the actual physical owner port;
source codes48..52 are per-port codes, not ambiguous global208-source IDs.
Frontend token narrowing is explicit and checked: upper returned ID/gen bits
must be zero before reconstruction. Tokens are reused only after their actual
lifetime drains, including generation wrap tests. No arbitrary full-width
canonical generation is truncated. Full leaf addresses are checked before
network32-bit conversion. The tag RAM retains the complete physical identity.

External service accepts `mv[p]&&mr[p]`, holds its response stable when
`sv[p]&&!sr[p]`, and returns exactly one response for the live tag. Writes
complete on response handshake; their data return is zero. Reusing a tag before
its completion is illegal. `lf_tagged_port` owns live-tag tracking and returns
the stored identity through finite response queues. The core's per-source
outstanding counters and explicit service-idle signals fence sample resets.
`cp_admin` checks its kind/status/gen and cost beat/port, relying on that trusted
network for exact-once transport rather than duplicating a second tag table.

Phase values used by the full-core traces:

| Code | Phase |
|---:|---|
|0|IDLE|
|1|SRST (actual per-sample hardware reset)|
|2|LOAD runtime job|
|3|INIT canonical/PV/directory/output|
|4|COST reads and actual coefficient writes|
|5|SEED enqueue|
|6|SEED_WAIT through real retirement|
|7|MIN_START|
|8|MIN_WAIT|
|9|WAVE_START|
|10|EXPAND including directory detach/member fetch/POP and all frontend work|
|11|FLUSH|
|12|FINALIZE through K8/publication and memory drain|
|13|REOPEN|
|14|REOPEN_WAIT actual scratch bitmap clear|
|15|EXPORT_START|
|16|EXPORT_WAIT output writes/ACK drain|
|17|COMPLETE sample transition|
|18|FAULT|

Counters exposed on ports are real hardware state. Additional hierarchical
phase/service counters read by the behavioral testbench may be optimized away
when unconnected; they are not claimed as retained physical telemetry. L1 has
no active META requests and no16-byte descriptor arm. Such constant
specialization is legitimate; resource audit must still show all64 banks,
16 active EDGE/DESC frontends and32 physical memory ports.
