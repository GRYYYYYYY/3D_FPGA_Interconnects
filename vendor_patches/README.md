# Native VTR variants

The complete VTR dependency trees are not stored in this repository. Each patch
in `manifest.json` is independently relative to the recorded upstream commit;
do not apply the four patches on top of one another.

Example (from this repository's root):

```bash
git clone https://github.com/verilog-to-routing/vtr-verilog-to-routing.git vendor/vtr_cpu_slices
git -C vendor/vtr_cpu_slices checkout 0b912334fdd83bb754b302146ac0d1ec9edc9a0e
git -C vendor/vtr_cpu_slices submodule update --init --recursive
git -C vendor/vtr_cpu_slices apply --check ../../vendor_patches/vtr_cpu_slices.patch
git -C vendor/vtr_cpu_slices apply ../../vendor_patches/vtr_cpu_slices.patch
```

Use the corresponding directory and patch name for the other variants. The
hybrid variant also uses this repository's `native/` headers. Original VTR and
its dependencies retain their licenses; see `VTR_LICENSE.md` and upstream.
Each patch was applied to pristine base files and the resulting bytes compared
against the local modified source before publication. This is a source
reconstruction check, not a fresh full VTR build.

The final flat/pipeline comparison additionally replaces the two translation
units with `results/native_flat_baseline_20261105/source/` and uses its diagnostic
header. Its build script preserves environment-specific compiler/linker
provenance; it requires a configured VTR build and is not a portable binary
installer. See `docs/native_cpu_paper_reproduction.md`.
