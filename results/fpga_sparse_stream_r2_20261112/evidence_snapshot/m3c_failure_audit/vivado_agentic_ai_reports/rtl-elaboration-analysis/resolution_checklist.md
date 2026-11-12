# Resolution checklist

No per-ID resolution file is mapped by the installed dispatch table for 3391, 3936, 4767, 6014. The table and `resolution/uncovered-synth-messages.md` were read. `vivado_doc_search` is unavailable in this session; analysis uses the actual RTL and Vivado 2022.2 log, with a fresh synthesis required to establish RAM inference.

| ID | Severity | Source | Loaded |
|---|---|---|---|
|3391|ERROR|dispatch range + own RTL port analysis|yes|
|3936|WARNING|dispatch range + unused reserved bits|yes|
|4767|WARNING|dispatch range + RTL read/write port inspection|yes|
|6014|WARNING|uncovered-synth-messages.md + actual parameter/context|yes|
