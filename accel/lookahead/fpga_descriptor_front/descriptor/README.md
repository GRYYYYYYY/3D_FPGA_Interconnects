# Exact packed descriptors

`packed.hpp` implements the guide's integer ABI with explicit little-endian byte
encoding and an independent checked decoder. Eight-byte records contain begin32,
degree16, target-cell15 and valid1. Sixteen-byte records contain begin32, end32,
cell32 and flags32 (only valid bit0). Invalid cell bits are zero in both formats.
Degree overflow selects16B for the whole graph. Fallback never relaxes offset32,
cell32768, node4194304 or cost/destination encoding admission. Address calculations
and begin+degree checks use64bits; no FP32 precision changes are made.

`dfdesc::PackedDescriptors(g,q)` materializes one sample's actual packed bytes.
`decode(node)` returns `{begin,end,cell,valid}`; `line(node)` gives the physical32B
line. Fields include `formatbytes`, `stride_lines`, `base_line`, `layout` and
`bytes`. To avoid repeated full admission, construct `Admission(g)` once and pass
it as the third argument. All samples reserve independent device regions even
when independent CPU model processes materialize only their own sample.
Sample stride is `align(nodes*formatbytes,1024)` bytes. The default base is
`32*Graph::align(g.metabase+jobs*g.metastride)`, after all old metadata ranges;
models must place canonical/scratch/output/cost beyond the full descriptor range.
Four/two records in a beat do not imply coalescing or a free cache.

All four native graphs and all100samples passed complete conversion/admission and
independent decode. Native max degree is16/26/249/249, so all select8B. The two
small graphs also ran complete20sample CPU output checks with forced16B.

| Native graph | Nodes | Prepared edges | Cells | Padded8B descriptor bytes |
|---|---:|---:|---:|---:|
| native_d3_w8 |654|1360|18|49152|
| native_d4_w8 |1592|3592|32|159744|
| BNN40 |4102608|38342776|25088|1312849920|
| LSTM40 |4166724|38985028|25538|1333370880|

BNN/LSTM strides are32821248/33334272bytes; address intervals are
[1499042816,2811892736) and [1522646016,2856016896). These are modeled device
addresses, not host pointers or proof of final device capacity. Raw unpadded8B
bytes are1312834560/1333351680, exactly the guide's arithmetic. Address ends
already exceed signed32-bit in the8B cases. Full admission checks every sample's
target cells; max valid cell is24970/25419 for the large inputs. Their40011940/
40740044 valid IPIN records are all zero-degree and are retained, not deleted.

`test.cpp` passed52 boundary checks, including end carry atUINT32_MAX,65535/65536
degree, invalid normalization, reserved flags, cell32767/capacity32768,64-bit
layout and rejected overflow. `fallback_fixture.py` additionally built a real
degree65538 graph: automatic16B selection, full two-sample CPU output exact,
force8 explicit rejection. It covers SINK break, skipped trailing eligible edge,
zero-degree/invalid/duplicate targets, equal-delay congestion tie, source target
and unreachable target. This is functional verification, not an RTL timing test.

Reproduce from this worktree:

```
python3 accel/lookahead/fpga_descriptor_front/descriptor/run.py
python3 accel/lookahead/fpga_descriptor_front/descriptor/fallback_fixture.py
python3 accel/lookahead/fpga_descriptor_front/descriptor/verify.py
```

Existing complete source-bound runs are reused by `run.py`; partial attempts are
preserved and refused instead of overwritten. Result roots are `descriptor_a`,
`descriptor_fallback_a`, `software_functional_a`, and two
`descriptor_native_projection*` directories under the new results root.
The512 projected native parents comprise128-prefix and128-target-window cases
for each large graph. They include actual packed records, every addressed edge
beat, actual costs/FP32 candidates and target operands; all candidate values match
the frozen native trace. These are local RTL inputs only, never full-model timing
drivers. The target windows retain53/51 zero-degree and44/35 valid targets.

Full backing files `descriptors.bin`, `edges.bin`, `rows.bin` are regenerable and
large; their exact hashes and construction commands are in conversion receipts.
Do retain the full `output.bin` results, small fixtures, reports and hashes.
Historical source/trace/input/golden/map files were read only. No GPU was launched.
