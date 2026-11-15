# Required packed output decoding: prepared, not formally measured

The production ABI requires a transformation if the consumer expects the
existing host `la::Cost {float delay, congestion;}`. `Graph::packed` and the RTL
store delay in bits63:32 and congestion in31:0. On this little-endian host,
raw memory therefore contains congestion before delay. Decode swaps the two
32-bit words of each64-bit pair, without byte swapping either word or doing
floating-point arithmetic. All NaN payloads and missing real cells are preserved.

Each sample has `ceil(cells/4)`32-byte output beats. The configured physical
sample stride may additionally round that beat count to a multiple of32 lines.
Only `cells` pairs are copied. Padding pairs and sample-stride gaps are skipped;
no padding is interpreted as a real cell. BNN40 has25088 cells/sample:6272 beats,
6272 aligned lines,200704 valid bytes/sample. LSTM40 has25538 cells/sample:6385
beats,6400 aligned lines,204304 valid bytes/sample,16 tail bytes and480 stride
bytes skipped. Complete outputs are8028160 and8172160 bytes respectively.

## Existing evidence and accounting

- `software/cpu.cpp` ends the resident timer before its `Graph::unpack` and
  file export. The packed CPU output needs the same host ABI conversion.
- `fpga_sparse_stream_r2/cuda_prepared_pop.cu` ends resident timing before D2H,
  INF-to-MISSING normalization, comparison, and final swap32/file export. This
  decoder does not measure that GPU-specific normalization or D2H.
- `model/main.cpp` converts `device_output` using `Graph::unpack`, then compares
  and exports. Its functional wall timer is not an isolated postprocess timer.
- `fixtures/run_full_core.py` decodes actual256-bit hex beats outside simulated
  hardware cycles. Parsing simulator text is research overhead, not production
  work. Existing model/fixture evidence establishes correctness, not standalone
  conversion latency.
- `vpr_bridge.cpp:la_import` already consumes host Cost order and assembles native
  maps using `add_cost_entry`. It also reads files and performs full input/golden
  validation, explicitly as an offline identity hook. That receipt must not be
  called a production decoding measurement. Existing native E2 is the whole
  MapLookahead build scope, with its native map assembly inside that scope; its
  whole time cannot be charged again as an isolated FPGA postprocess stage.
  No separately identified production raw-decode-plus-native-merge timer was
  found. Native E2/Process and transitive identity retain their original scope.

Conversion belongs outside resident for all three existing packed output
boundaries. Do not add it only to FPGA and compare against CPU/GPU resident.
Do not add research golden comparisons, SHA, archive, simulator parsing or
filesystem export to production E2. This task does not reconstruct VPR or
measure map assembly. Actual output DMA and board E2 remain unmeasured.

## Entry and timing boundary

`decode.cpp` accepts raw binary, cells, jobs, sample stride, an independent host
output for validation, output path, and `check` or `measure`. Inputs must have
exact lengths; stride must cover every actual beat. Conversion uses preallocated,
prefaulted destination storage. The measured interval includes only sample
iteration, reads, swap32 and compact host writes. `memcmp` and output writing
are outside it. Output allocation and first-touch zeroing are separately
recorded once per measured process. Input file loading/first-touch is outside
conversion; it is not a proxy for board DMA cost.

The bounded cohort is one pinned CPU, three independently launched processes,
each one warmup plus three formal repeats. There is no CPU tuning sweep.
Input/output are prefaulted; repeats follow conversion and validation, with no
cache flush. Treat this as repeated warm-cache behavior, not guaranteed residency
in a specific cache level or a cold post-DMA read. The process is the statistical
unit, not the nine within-process measurements. The coordinator must verify an
EDA-free window before invoking `measure`; the runner does not certify it.

## Input provenance and use

`prepare` copies/binds actual completed output and its completion receipt,
freezes/compiles these new sources and runs only functional checks. With
`--beats-dir`, raw input comes from actual RTL `sample_Q_actual_beats.hex`;
hex parsing happens before the conversion timer. With no beats directory, it
inversely packs the actual selected host output into the physical layout.
That mode is labelled **layout replay, not captured raw DMA**. Existing model
output files omit raw beats, so a replay may be necessary without changing or
rerunning the model. The host source must be the completed selected output,
never a golden-generated substitute. Copying a hash-bound receipt does not by
itself prove final selection; the coordinator checks that choice before GO.
Padding/unused stride bytes in replay are poisoned0xa5 and must be ignored.

Example preparation, once the selected complete output is available:

```sh
python3 accel/lookahead/fpga_cpu_primary/software/postprocess/run.py prepare ACTUAL_OUTPUT COMPLETION_RECEIPT NEW_RESULT_DIRECTORY --cells 25538 --jobs 40 --physical-stride
```

Only after explicit final-output/quiet-window GO:

```sh
python3 accel/lookahead/fpga_cpu_primary/software/postprocess/run.py measure PREPARED_DIRECTORY --cpu 0 --confirm-final-output-and-quiet-window
```

All result directories must be new. Source, binary, actual output and receipt
hashes are rechecked before formal measurement. No existing model, CPU, DUT,
GPU source or historical receipt is edited. There is no model/GPU/EDA launch.

## Current functional evidence

`results/fpga_cpu_primary_20261115/postprocess_prepare_a/native_d3` decodes8
actual RTL samples of18 cells, exercising partial beats and aligned physical
stride. `native_d4` decodes12 samples of32 cells with physical stride gaps.
Both match all corresponding actual host output bytes. Their raw source is
the existing `fixtures_full_b` actual RTL beats, not reconstructed golden data.
The bindings retain source/runner/compiler/binary/input/receipt hashes.
`directed/terminal.json` additionally records four tail-length shapes with
distinct NaN payloads, infinities, signed zero and poisoned stride gaps, plus
six rejections for invalid/overflowing dimensions, stride and file length.
Formal timing has **not** been started. No conversion latency or E2 advantage
is claimed by this preparation.
