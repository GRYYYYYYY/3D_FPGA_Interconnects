# Exact descriptor / corrected-service experiment

Start with [the report](../../../docs/lookahead_fpga_descriptor_front.md) and
[service_contract.json](service_contract.json). This directory is independent
of the frozen enum/commit implementation at
`ccec3da64b4c5be643809c2bdda94145c4bb8187`; historical sources and golden outputs
remain unchanged. The report distinguishes intermediate attempts from final
evidence and local calibration from complete-kernel qualification.

* `descriptor/`: exact 8/16-byte ABI, full native admission, conversion and
  independent decode/boundary checks.
* `software/`: same-semantics packed CPU, quiet-window timing and explicit
  historical/native identity reuse.
* `front/`: elastic FP32, finite descriptor/EDGE groups and actual parent context.
* `backend/`: unchanged enum2/K8 core wrapped in real launch/capture interfaces.
* `services/`: synchronous directory, minimum collector and finite shared networks.
* `output/`: synchronous output bank, finite export and registered ACK collector.
* `model/`: continuous native algorithm under the common finite service contract.
* `review/`: independent checks, failure findings and their evidence-backed closure.
* `delivery/`: historical reuse verification and content-addressed evidence archive.

The raw run root is `results/fpga_descriptor_front_20261114`. Each run binds
its frozen source, binary, commands, native inputs, golden, tool and terminal
status. Inputs are the existing large native captures on the shared filesystem;
their exact paths and SHA-256 values are in the bindings. They are not replaced
by representative traces. Large generated descriptor/edge images and Vivado
build trees can be regenerated and are not duplicated into Git.

Use a **new** `DF_MODEL_RUN` name when changing code or service assumptions.
The model runner rejects live duplicate launches and preserves sample attempts.
Finished source-bound samples are reused only within their matching freeze.
See each subdirectory's README/scripts for exact commands. CPU simulation
process parallelism does not reduce hardware cycles: a single active sample
configuration sums all forty sample times in order.

The final report names the evidence snapshot. From the repository root:

```sh
python3 accel/lookahead/fpga_descriptor_front/delivery/archive.py SNAPSHOT --verify
python3 accel/lookahead/fpga_descriptor_front/delivery/archive.py SNAPSHOT --restore /new/empty/path
```

The manifest maps original evidence paths to SHA-256 objects and records
compression and byte length. Verification checks every object and the final
source/report hashes. Restore first verifies, then reconstructs the original
relative paths in a new directory. Complete output binaries, timing reports,
stimuli, transaction traces and failed-attempt evidence are preserved; historical
archives are referenced rather than repackaged.

Formal CPU timing must wait for the model and EDA workloads to finish. Its
runner checks competing processes and records affinity, warm-ups and retained
process/repetition statistics. No script silently submits or repeats a GPU job.
There is no board-measured performance in this experiment.
