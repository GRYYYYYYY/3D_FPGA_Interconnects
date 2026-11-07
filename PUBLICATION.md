# Public repository contents

This repository publishes the source, documentation, manuscript materials,
lightweight experimental summaries, figures, and native VTR patches from the
research workspace. It is not a byte-for-byte backup of the compute instance.

Included:

- C++/CUDA/HLS prototype sources, Python experiment/analysis scripts and tests.
- Current CPU lookahead method, evidence index and separated comparison tables.
- Manuscript sources, figures and extracted supporting evidence in `paper/`.
- Selected small result summaries, provenance records and source snapshots.
- Four VTR variant patches against an exact commit, including added source files.

Excluded from Git:

- Virtual environments, build trees, binaries, static libraries and external tool bundles.
- Large RR graphs, netlists, routes, runtime datasets and repeated raw outputs.
- Full VTR dependency copies (replaced by `vendor_patches/`).
- Instance-specific job submission manifests, credentials and authentication state.
- Redundant manuscript preview images and generated source ZIP archives.

The standalone CPU example can be built using the root README. Historical native
experiments require the original external benchmarks, architecture descriptions,
VTR runtime dependencies and frozen inputs. Absolute paths and SHA256 references
in historical evidence document the original environment; publishing a summary
does not make its omitted raw inputs available. Consequently, historical audit
scripts cannot all run on a bare clone. Do not treat missing raw artifacts as
newly verified or change frozen hashes merely to match another machine.

`HANDOFF.md` contains chronological research notes; its newest terminal section
takes precedence over older running-state notes. `paper/dac2027/` is a working
manuscript directory, not a statement of submission or acceptance.

Licensing: no new blanket license has been assigned to the project's original
work by this publication step. Third-party VTR-derived code retains upstream
notices and license terms; see `vendor_patches/VTR_LICENSE.md`. Public visibility
does not replace an explicit license grant.
