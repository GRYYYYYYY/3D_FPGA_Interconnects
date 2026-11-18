# Timing terminology audit

**Frozen comparison point** is 1ebcba19cc8513240c1a1d25b400a896e3f57214. The anonymous ZIP and extracted PDF were checked for the standalone historical identifiers E1 and E2. Neither occurs in either artifact. The frozen CSV column names and archival diagnostics retain their original spelling.

| Manuscript term | Boundary or estimator |
|---|---|
| Lookahead Construction Time | Complete MapLookahead::compute call timed with the common monotonic timer. Includes conversion, preparation, service, output handoff, group merge, interpolation, source/OPIN processing and derived minima. The frozen formal records encode this interval as E2_ns. |
| End-to-End Process Time | Native process launch to exit, including RR XML loading, initialization, construction, routing, checking, STA and serialization. Packing, placement, RR graph generation, input preparation and independent route readback fall outside the interval. The frozen full-process records encode it as Process_ns. |
| Lookahead Construction Speedup and End-to-End Process Speedup | For the named interval, divide the numerator configuration's time by the denominator configuration's time within each repeat. Report mean and sample SD across the three matched ratios per workload. |
| Warm Complete-Batch Service | Separate BNN40 shift 0/20 diagnostic, including reset, search, closure and output materialization with device synchronization and readback. Loading, preparation and verification are excluded. The statistic is the median of three process medians over three warm batches each. |

The historical E1 service diagnostic on CUDA stopped before the final ABI output copy. Its records remain in the frozen experiment archive. Group and Flat in the formal matrix measure the complete construction call.

The five review CSVs agree byte for byte with the terminology revision. The time and speedup figures use all 30 and 39 mean/SD pairs, respectively, from the verified CSVs. The QoR table retains its numerical rows.
