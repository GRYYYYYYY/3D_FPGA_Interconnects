# R5.1 bounded independent-service experiment

`lookahead_services51` is a runtime-loaded, five-process classic DATAFLOW
mechanism, with two resident heaps and finite depth-4 channels. Its fixed
32-node/128-edge/8-job/8-cell capacity is deliberately small; it is **not** the
full native-batch performance kernel. Independent modules and neighbor overlap
are verified by actual generated-RTL FIFO handshakes. The old R4/R5 code remains
unchanged. The budget gate stops native-batch RTL/OOC.

- `services51.hpp/.cpp`: heap, CSR/FP32, label/lifecycle, map owners and loader.
- `tb51.cpp`: strict oracle, backpressure, warm/version/error/empty tests.
- `fixtures51.cpp`: existing fixtures within capacity, no replicated jobs.
- `heap51.hpp`: separately evaluated exact Floyd path forwarding; it is not
  integrated into the measured service prototype.
- `heap_test51.cpp`, `heap_profile51.cpp`: complete heap and bounded native checks.
- `heap_hls51.cpp`, `heap_hls_tb51.cpp`, `run_heap_hls51.py`, `heap_report51.py`:
  isolated POP baseline/path RTL and measured contract.

Top command: 0 load-only, 1 warm search, 2 load-and-search. Graph/cost version and
shape must match on warm calls. Invalid load invalidates residency. Only +0 or
positive normal finite eligible costs within the loader exponent bound are
admitted. `capacity` is logical heap capacity (1..129), not FIFO space. Statistics
are six uint64 words/job: pushes, pops, logical edges, expanded, peak, status.
Map entries remain at qid*8+cell. `heap_hold` and `map_hold` are bounded synthetic
cycle stressors, zero for the undelayed mechanism replay. Every call joins/drains
all services; generation tags are not used as uninitialized-RAM epochs.

The C simulation uses mutex-protected bounded queues and host threads because
sequential C calls cannot execute this feedback network. C wall time is never
hardware timing. Synthesis selects hls::stream and classic DATAFLOW, not threads.
Each service is its RAM's sole writer. A second read-only node image explicitly
pays for edge/map concurrency under Vitis HLS 2022.2's static-array rules.

From repository root:

```sh
python3 scripts/la_accel_hls5_1.py --output /fresh/hls
python3 scripts/la_accel_monitor5_1.py --hls /fresh/hls --output /fresh/observer
python3 scripts/la_accel_monitor5_1.py --hls /fresh/hls --output /fresh/zero --zero-hold
python3 scripts/la_accel_cosim5_1_probe.py --hls /fresh/hls --output /fresh/protocol
```

Full conclusions and limitations: [round report](../../../docs/lookahead_accel_round5_1.md).
Neither HLS frequency estimates nor synthetic mechanism cycles are native FPGA
E1 times. `board_measured=false` throughout.
