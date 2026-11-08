# Lookahead acceleration — round two

Goal: FPGA better than each baseline. CUDA may be slower than CPU. FPGA superiority remains unverified.

## Same complete native tiny graph: RTL and routed cores

| Variant | csim / synth / cosim / impl flow | Cycles | Routed setup / hold ns | Verified target MHz | LUT / FF / DSP / BRAM18 / URAM |
|---|---|---:|---:|---:|---|
| hls_resident_heap127 | passed / passed / passed / not_run | 289381 | not routed | — | not implemented |
| hls_resident_labels | passed / passed / passed / not_run | 275305 | not routed | — | not implemented |
| hls_resident | passed / passed / passed / passed | 265241 | +0.441 / +0.019 | 200.0 | 27154 / 31004 / 4 / 49 / 0 |
| hls_interleaved1_v3 | passed / passed / passed / passed | 509446 | +0.428 / +0.021 | 200.0 | 18872 / 18111 / 14 / 55 / 0 |
| hls_interleaved4_v3 | passed / passed / passed / passed | 514988 | -1.149 / +0.019 | — | 33839 / 33659 / 12 / 73 / 0 |
| hls_interleaved2_distance | passed / passed / passed / not_run | 450184 | not routed | — | not implemented |
| hls_interleaved4_distance | passed / passed / passed / passed | 451782 | -0.830 / +0.019 | — | 28741 / 34192 / 12 / 73 / 0 |

An impl flow marked passed means the tool completed; negative routed slack still fails the target frequency. Core OOC only: internal setup/hold and unconstrained endpoints are checked; this does not establish shell timing or board throughput.

## Bounded synthetic memory replay

| Variant | Verdict | RTL cycles | All result ports bitwise match |
|---|---|---:|---|
| bounded_f0_final | passed | 2091704 | True |
| bounded_cacheoff_final | passed | 2625249 | True |
| bounded_heap31_minimal | passed | 1211614 | True |
| bounded_dual_final | passed | 1063676 | True |
| bounded_resident_final | passed | 996173 | True |
| bounded_interleaved1 | passed | 1396523 | True |
| bounded_interleaved4 | passed | 1410463 | True |
| bounded_distance | passed | 1346628 | True |

Memory assumption: 64-cycle request latency; one shared bank; one native R or W beat per four clocks; two outstanding requests per direction/port; one finite read return slot per port. The bank is shared by both dual engines. Narrow beats consume a full slot. This is a controlled synthetic sensitivity experiment, not calibrated HBM.

## Real CPU/CUDA in the native builder

| Backend | Resident kernel median s | Complete wire builder median s | Complete router lookahead median s |
|---|---:|---:|---:|
| cpu | 0.037030 | 0.05 | 0.06 |
| cuda | 0.679714 | 1.10 | 1.11 |

Three independent native processes per backend, no warmup, same worker and eight physical cores on one NUMA node. Complete-builder times include native conversion, cold backend preparation/upload, computation, compact readback, ordered merge and downstream fill. The outer router timer additionally includes source/OPIN construction. Native log resolution is 0.01 s. No offline golden map or CPU oracle is called by the live bridge. Every final wire map matches the frozen reference. One routing iteration is a component test, not a routing-success claim.

Native controls on the same worker (wire-builder scope):
- flat: wire 0.05 s (range 0.04–0.06); complete router lookahead 0.05 s.
- per_group: wire 0.07 s (range 0.06–0.09); complete router lookahead 0.07 s.
- pipeline: wire 0.04 s (range 0.04–0.06); complete router lookahead 0.04 s.
- stock: wire 0.21 s (range 0.21–0.22); complete router lookahead 0.21 s.

## Limits

- Small native RTL graphs do not establish FPGA superiority on tseng/BNN. No linear extrapolation or uncalibrated large-graph performance number is reported.
- Live E2 is measured for CPU/CUDA. FPGA E2, physical memory placement and a calibrated large-graph model remain unverified.
- Shared context rotation without dependence distances has a negative result; engine replication and shared scheduling are separate experiments.
- Prior CPU paper/results and round-one records are retained. Failed synth/cosim/model attempts are retained in the round-two directory and explained in engineering_notes.json.

Reproduction: scripts/la_accel_hls.py, scripts/la_accel_bounded.py, scripts/la_accel_live.py and scripts/la_accel_live_gpu_job.py.
