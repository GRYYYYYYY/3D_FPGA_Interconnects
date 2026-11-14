# Descriptor/software ABI (worker-owned)

Namespace `dfdesc`, header `descriptor/packed.hpp`. LE byte representation:
8B `begin[31:0], degree[47:32], target_cell[62:48], valid[63]`;
16B four LE32 fields begin,end,target_cell,flags with only flags bit0 valid.
Invalid targets canonicalize cell to zero in both formats. Decode returns
`Decoded {uint32_t begin,end,cell; bool valid;}`. End checked with64-bit arithmetic.

`Admission(const Graph&)` scans complete graph and ALL sample metadata; selects
8B iff every degree<=65535, otherwise16B. All variants require prepared offsets
including end<=UINT32_MAX, cells<=32768, target cell<=32767, nodes<=4194304,
packed EDGE dst28/cost4, finite positive/+0 costs. No fallback weakens admission.
`encode_record` and `decode_record` are independent byte-wise integer routines.
`Image(const Graph&, sample, Admission, optional_format)` builds real packed bytes
for ONE sample for the finite model, independent of old row/meta after construction.
`Image::get(node)` decodes backing. `Image::bytes` includes zero padding.
`sample_stride_bytes=align(nodes*format,1024)`; four/two records per32B beat.
`Layout(base_bytes,nodes,jobs,format)` exposes byte address and physical32B line;
base aligned1024, arithmetic overflow checked in64bits. Model chooses shared global
base to keep its canonical/scratch/output/cost ranges disjoint; no free cache.

Full native conversion emits all-sample .desc with same stride, prepared edge.bin,
independent full decode report and exact addresses. CPU reads persisted descriptor
backing (loaded before resident timing), never reconstructs node descriptors in solve.
Functional/construction runs may contend; formal CPU timing awaits parent-selected
isolated window. No GPU rerun requested or launched.
