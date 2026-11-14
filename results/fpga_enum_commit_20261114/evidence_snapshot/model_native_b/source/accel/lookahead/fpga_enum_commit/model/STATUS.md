# Model worker status

Full instruction read; no old enum5/K1 rejection used. Final new model frozen under `results/fpga_enum_commit_20261114/model_native_a/source`, binary/input closure in binding.json.

- Final small run: 40 sample runs (d3 eight / d4 twelve, each normal and response-jitter). All complete outputs equal golden and semantic parents/candidates/U/V equal full profiles.
- Exact shared enum control calibration: 64 no-stall, 64 stalled and one singleton; scan + fragment transfers cycle-exact. Scope excludes flush/DRAIN/init and scratch/canonical/top.
- Full BNN40 + LSTM40: running using 12 CPU sample workers; process ownership in model_native_a/runs/*/running_*.json. Do not duplicate or restart. Per-wave progress.jsonl, full sample terminal.json/receipt are checkpoints. Full input/native graph, no old POP/candidate trace in performance path, fresh spill counters.
- Final structural parameters and explicit conditional limitations: configuration_final.json. Initial architecture.json is retained implementation plan, not runtime configuration; compiled code and final configuration govern final run.
- No commit/push by model worker. Main handles integration/OOC and delivery.
