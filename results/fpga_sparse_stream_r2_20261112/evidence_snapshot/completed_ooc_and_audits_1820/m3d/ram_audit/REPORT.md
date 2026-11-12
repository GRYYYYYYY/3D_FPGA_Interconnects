# M3d RAM inference interim audit

Source: frozen pipe_full_d_build/source, Vivado 2022.2 synthesis snapshot. Run not complete. All current diagnostics are retained in diagnostics.json; counts below. No resource or timing qualification inferred from an unfinished synthesis.

8-6849: actionable reducer memory fallback. Each bank 4096x65 became 1920 RAM64M8 primitives in preliminary mapping, despite block attribute. Actual reducer lines 20-25 have separately addressed read and write statements for update/export and initialize/update. Replace with explicit single read address/enable and single write address/enable/data before the clocked RAM process. Preserve one-cycle read and forwarding. Verify BRAM mapping with focused synthesis before repeating full tile.

8-4767: reviewed small multi-context owner/frontend tables; multiple accesses require registers, charge actual utilization. 8-3936: high three pending bits reserved zero and unused. 8-3848: active_context only read in unreachable legacy serial-CACK path; closed_q used only POP_REDUCE=0, which is false for this frozen candidate. Remove obsolete paths in subsequent code rather than constraints. 8-6014: dead parameterized closed-fold state and procedural temporaries, expected removal. Do not add KEEP, false paths or change dissolve limits.

No amd-doc-search tool is installed; fixes based on inspected RTL and actual inference diagnostics. Scope is current snapshot; final run must be re-audited.

{
  "Synth 8-6014": 32,
  "Synth 8-3936": 9,
  "Synth 8-3848": 16,
  "Synth 8-4767": 4,
  "Synth 8-7217": 16,
  "Synth 8-3917": 233,
  "Synth 8-6849": 64
}

Additional reviewed diagnostics: 8-3917 constants on upper commit-node bits match the 4096-node M3 tile address cap; constant memory-write ports are read-only front/metadata. Inspect detailed diagnostics.json for every occurrence; no full-node-capacity claim applies to this tile. 8-7217 member-next two-write/one-read inferred-port warning: reads occur only POP after commit/control-neutral/min transitions, more than two cycles after final publication. No POP/COMMIT concurrent access is permitted. New-entry and old-tail writes address distinct allocated IDs. This phase separation must remain asserted in subsequent variants.
