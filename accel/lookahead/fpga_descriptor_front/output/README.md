# Finite output and ACK service

The RTL implements the common output path for C0/F1/F2/F3. Existing group target
contexts feed the same cyclic RR router into eight banks. Each bank has a
4096x65-bit synchronous seen/whole-pair RAM, real sequential sample clear, three
finite pipeline positions, newest-result forwarding and whole-pipeline stall.
The RAM uses one explicit muxed write port and one synchronous read port. There
is no asynchronous RAM read or free same-cell completion.

The exporter drains all update positions before reading output. At most two
32-byte beats are formed per cycle; the sixteen packing reservations include
pending RAM/pack beats. Writes are a strict-prefix pair through the existing
shared memory network. A real 32-source/two-holder cyclic RR ACK collector adds
its registered edge and retains complete opaque metadata under backpressure.
Initialization, partial output, all writes and actual ACK retirement are counted.

Exact entry/exit/forwarding/queue timing is documented in
`../coordination/output_interface.md`. The C++ headers expose the same finite
contract; the full model consumes those headers. They were not modified for the
RAM inference template repair.

## Completed local evidence

All paths below are under `results/fpga_descriptor_front_20261114/`.

- `output_ack_a`: 304 cycles,384 actual ACK packets,32 simultaneous sources,
  blocked holder stability and at most two winners. C++/RTL exact.
- `output_c`: complete local RAM/export/collector closed loop,1413 cycles,
  1024 update completions,242 first writes,389 improvements,62 writes/ACKs,
  sixteen packing reservations, four coincident ACK sources, two reset epochs.
- `output_d`: single-write-port RAM template repair; both complete pin traces
  are byte-identical to C. Both frozen C++ replay executables pass unchanged.
- `output_ram_a`: negative actual full-capacity inference (116082 LUT,
  77824 LUTRAM, zero BRAM). Sources/logs/utilization and all153 synthesis warning
  occurrences are preserved. Multiple syntactic writes prevented BRAM mapping.
- `output_ram_b`: full-capacity synthesis passed with16971 LUT,7477 FF,
  zero LUTRAM,56 RAMB36E2+8 RAMB18E2=60 BRAM tiles,zero URAM/DSP/latches.
  `terminal.json` binds actual utilization and64 primitive records. Optional
  BRAM output registers remain disabled (DOA_REG=DOB_REG=0); this preserves
  the calibrated read edge and does not qualify routed clock timing.

Functional XSim uses reduced AW=4 to exhaust queues/conflicts cheaply. Full
resource synthesis uses G16/AW12 (32768 cells). These are distinct evidence
levels. Neither establishes a routed complete-kernel clock or board performance.
Raw xsim traces, source hashes, build/command receipts and negative attempts are
retained. Generated simulator databases and synthesis DCP may be regenerated;
retain their hashes and the reports when archiving.

## Reproduction

From a fresh result directory, source `output/run.tcl` in Vivado2022.2 (XSim),
then run `replay.cpp` and `replay_ack.cpp` built with `g++ -O2 -std=c++17` on
`output_cycles.txt` and `collector_cycles.txt`. `run_ack.tcl` uses the vector
produced by `test_ack.cpp`. `infer.tcl` synthesizes the complete output context
on xcu280-fsvh2892-2L-e and emits utilization and actual RAM primitive properties.
Use a fresh attempt directory to preserve all prior evidence. The dedicated
Vivado session used process-local LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1
for this host's Webtalk compatibility; no vendor/global files were edited.
