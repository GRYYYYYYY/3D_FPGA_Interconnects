# Local-fabric experiment (base 7dd79b2)

The complete report is [docs/lookahead_fpga_local_fabric.md](../../../docs/lookahead_fpga_local_fabric.md).
This directory contains only new/derived sources. Original modules are reused
by explicit source closures; none is edited in place.

- `network/`: actual208-source/32-port specialization, the one allowed radix4
  fallback, 74-bit identity adapters, finite-stage model and independent tests.
- `front/`: independent T/D/ready/target storage, real L4 context and native/stress tests.
- `publication/`: K8 journal and II2 synchronous directory, real enum/scratch
  backend contexts, independent directory oracle and native output checker.
- `model/`: full finite algorithm and checkpointed source-bound runner.
- `delivery/`: actual resource arithmetic, report extraction, historical identity
  reuse, evidence indexing and content-addressed archive/verification.

Final finite binary is `results/fpga_local_fabric_20261115/model_d/bin/model`.
The full selected configuration is L1, not the area-failing L2. Results are
conditional models, not board measurements or a full-top clock qualification.
See `service_contract.json` and every run's frozen binding before reproduction.
Derived scripts should only run before a new source freeze. The final compact
APPEND response storage retains all service edges/capacities and is proven
trace-identical; the model consumes status/order only.

## Observations and edge conventions

FIFO pushes test **pre-edge** fullness. A FIFO4 does not accept into a full
queue just because it also pops at that edge. Output holding registers may
consume/replace; logical transaction/credit/E/beat slots cannot be allocated
from the same edge's release. Per-group sources and real outer contexts are
separate, and one request from a group/class per cycle is preserved. The
radix model includes the stage0 source FIFO once, each later FIFO4, each held
output, the final admin merge, and local return paths. `test_radix.cpp` checks
packets against an independent destination/conservation oracle; XSim compares
all pre-edge visible signals against the resulting vectors.

`pool_service.json` lists exact column names. T total includes stale POP;
D total only valid parents. Request→return includes actual network and memory
service; ready→E includes downstream backpressure. Nonexclusive group cause
counts cannot be summed into wall time. Life histograms' last bin is >=1023,
while explicit maxima remain uncapped.

`finite.json` occupancy histograms are T, H/D, M, ready, E, beat per group.
The fixed expand observer uses lane/group/bank0, labels: actual operand emit,
FP32/candidate pending, E live, H/D live, T live, scratch busy, POP pending,
none. The finalize observer priority is actual retire, publication held,
K8 full, scratch busy, commit/op input pending, enum active, phase busy other,
idle. Each wave's critical-final observer chooses the bank with the latest
actual last-busy cycle; it is a diagnostic priority histogram, not a deletion
experiment or proof that a state can be removed. `radix_service.json` counts
link handshakes, FIFO-head not granted, blocked output and FIFO peak separately
for every stage and endpoint.

The selected80 native sample outputs are complete byte arrays. Sample wall
cycles are summed; parallel CPU workers do not overlap hardware samples. A
completed receipt is reused only with matching binary/source/input/output
identity. Live process birth checks and locks prevent duplicate restarts.
