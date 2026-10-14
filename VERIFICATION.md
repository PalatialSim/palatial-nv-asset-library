# Asset verification

The 2026-10-13 release uses NVIDIA Robotics-Prop 4.0.0 with separate single-body, multi-body and articulated checks in Isaac Sim 6.1.0.0 (PhysX). Current acceptance: **1,013 static profile passes, 911 native passes, 45 native completions with disclosed SDK findings and 837 completed SimReady packages out of 1,013 assets.** The [release manifest](reports/current-release.json) binds the catalog, physics metadata and per-asset evidence. Native passes require complete planned test coverage, unchanged USD bytes, an independently checked black-background thumbnail and, for moving joints, independent joint-constraint checks.

The metadata audit verifies stage units and up axis, visible-mesh bounds, positive authored masses and part sums, collision APIs, enabled states, finite mesh coordinates, joint references and ordered limits. These checks establish agreement with the authored USD. They do not measure physical mass, friction or real-world dimensions.

Native acceptance uses the unmodified NVIDIA benchmark suite and two explicitly identified Palatial tests. Every planned result must exist exactly once for the same USD SHA-256 in Isaac Sim 6.1.0.0. Asset findings, invalid PhysX transforms, incomplete coverage, missing native thumbnails and failed independent joint constraints prevent release readiness. Tests skipped by NVIDIA for inapplicable features are recorded separately from passes. Full raw results, logs and media are retained in immutable Hugging Face evidence archives; release metadata links each asset to its qualification.

`completed_with_tool_findings` records a completed run with a separately certified SDK finding. It is not a benchmark pass. This disposition covers bounded camera and color diagnoses: small or thin assets underframed by the SDK's 0.1-metre minimum camera bounds, including presence-only findings with independently passed semantic and surface checks, and an exact-camera diagnostic for millimetre-sized source geometry that must pass all four complete visual tests, including normal rotation, using unchanged SDK functions and thresholds. Only an original normals visibility failure with empty diagnostic metrics qualifies for that camera finding. Color ambiguity occurs where the preview-surface magenta probe also selects the asset's unchanged source texture. The latter is an inference from manually inspected, unmodified baseline, weak-control and strong-control native captures, fully resolved source material bindings and independently repeated pixel measurements. For source colors indistinguishable from that magenta control, a separately named native cyan-control diagnostic must pass the same SDK scene, binding strengths, classifier thresholds and 98 percent coverage requirement. Its result, observations and controls are archived separately and never replace the official result. A stricter mask is used only for offline diagnosis; the official benchmark configuration and thresholds are unchanged. The exact source USD, static receipt, raw failed results, native thumbnail and supporting captures or framing measurements are bound by SHA-256 in per-asset certificates. For camera and color findings, all physical tests and Palatial checks must pass or be explicitly inapplicable. A separately certified contact-bounds finding requires both complete independent ground and slope simulations to pass using unchanged NVIDIA simulation functions, parameters and thresholds, with every live visible and collider mesh vertex included in the measurement. The SDK conservative world bounds must reproduce the original floor-penetration report while exact geometry stays within the independent 1 cm review limit. Stable ground settling and post-slide observation are required. The original NVIDIA floor-penetration failures remain disclosed. Engine faults, real bouncing or penetration, joint faults, culling and additional asset failures cannot receive this disposition. NVIDIA's original failed benchmark sidecars remain in the packages. These findings require NVIDIA review, consistent with [REVIEW.003](https://github.com/NVIDIA-Omniverse/simready-central/blob/main/docs/acceptance-criteria.md#review003---asset-path-carries-no-benchmark-results).

Packaging uses the official WRAPP packager with required pre-validation, bill-of-materials validation and post-validation. Published package manifests use full immutable Hugging Face commit hashes. Catalog, gallery, physics metadata and release report must agree on the repaired USD hash and acceptance status before publication.

The packaging driver isolates the SDK's pre-validation, creation and post-validation phases in separate processes and dispatches unchanged BOM hashing to WRAPP's event loop. This avoids the installed SDK's cross-loop semaphore failure on large asset folders. It changes neither SDK files nor validation or hash algorithms; all three phases remain required.

Run the metadata and current-release checks from the repository root:

```sh
python3 tools/audit_metadata.py .
python3 tools/release_manifest.py . --require-ready
```

To reopen all delivered USDs and recompute authored geometry and physics metadata:

```sh
python3 -m venv .venv
.venv/bin/pip install -r tools/requirements-usd.txt
.venv/bin/python tools/verify_metadata_usd.py .
```

## Recorded limitations

NVIDIA's installed joint-movement test computes a relative transform in an order that can turn common world translation into a large relative-translation metric. The unmodified results are retained. The release therefore also checks actual joint-local anchor closure, finite poses, ordered limits and measurable joint movement. The independent checks do not replace failed official test verdicts. The reproduction and per-joint observations are included in the release evidence.

D00241's passive hinge mechanisms are validated. Its original nonlinear magnetic-latch behavior script is not part of the portable SimReady package or its certified behavior. Existing legacy simulation recordings retain their original provenance and are not new native acceptance evidence.
