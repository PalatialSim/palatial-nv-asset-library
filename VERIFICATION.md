# Asset verification

All **1,013** current packages have complete unchanged stock benchmark evidence. **955** have no failed tests and **58** retain **142 raw failures** for NVIDIA review. Eligibility skips remain separate from passes. No skip/ignore flags, test changes or benchmark parameter overrides were used. This is a submission for review, not NVIDIA approval or independent physical calibration.

The current versioned contract is `palatial.library-review-release.v2`. It checks all 1,013 logical identities, source and physics hashes, immutable stock package and raw-evidence provenance, exact declared test/engine coverage, unchanged default parameters, and matching catalog/gallery result counts. Every raw FAIL remains `completed_with_failed_tests`; a complete publication is not a passing benchmark. Inapplicable tests retain their SDK eligibility skips. PhysX-authored assets do not claim Newton physics qualification.

Corrected-source evidence includes independent verification of every package file and every raw-archive member, current Robotics-Prop 4.0.0 validation, the original default stock plan and work pool, and the exact result sidecar. Unchanged packages retain the independently verified initial standard submission provenance. A new failed test/engine pair blocks correction promotion pending causal diagnosis. No stock test, threshold or acceptance meaning is modified by the metadata contract.

Source corrections and property-by-property invariants are published in the [source-quality report](reports/releases/2026.10.15/source-quality/README.md). Historical native qualification and old metadata keep their original hashes. They cannot qualify a changed USD. Geometry-derived automatic mass properties are explicitly identified; numerical inertia is not invented.

Known benchmark blockers are linked to [framing](https://github.com/NVIDIA/simready-foundation/issues/36), [material probes](https://github.com/NVIDIA/simready-foundation/issues/37) and [contact measurements](https://github.com/NVIDIA/simready-foundation/issues/38). Bounds-versus-authored-vertex observations do not independently certify cooked collision shapes or contact depths, and not all contact failures are proven SDK defects.

Run the metadata and evidence-consistency checks from the repository root:

```sh
python3 tools/audit_metadata.py .
python3 tools/release_manifest.py . --require-ready
```

The historical v1 release policy remains available with the 2026-10-13 reports and its original repository/dataset revisions. It describes that earlier qualification, not the current source release.
