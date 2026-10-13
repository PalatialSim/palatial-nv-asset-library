# Asset verification

The 2026-10-13 release uses NVIDIA Robotics-Prop 4.0.0 with separate single-body, multi-body and articulated checks in Isaac Sim 6.1.0.0 (PhysX). Current acceptance: **1,013 static profile passes, 355 native passes, 5 native completions with disclosed SDK findings and 250 completed SimReady packages out of 1,013 assets.** The [release manifest](reports/current-release.json) binds the catalog, physics metadata and per-asset evidence. Native passes require complete planned test coverage, unchanged USD bytes, an independently checked black-background thumbnail and, for moving joints, independent joint-constraint checks.

The metadata audit verifies stage units and up axis, visible-mesh bounds, positive authored masses and part sums, collision APIs, enabled states, finite mesh coordinates, joint references and ordered limits. These checks establish agreement with the authored USD. They do not measure physical mass, friction or real-world dimensions.

Native acceptance uses the unmodified NVIDIA benchmark suite and two explicitly identified Palatial tests. Every planned result must exist exactly once for the same USD SHA-256 in Isaac Sim 6.1.0.0. Asset findings, invalid PhysX transforms, incomplete coverage, missing native thumbnails and failed independent joint constraints prevent release readiness. Tests skipped by NVIDIA for inapplicable features are recorded separately from passes. Full raw results, logs and media are retained in immutable Hugging Face evidence archives; release metadata links each asset to its qualification.

`completed_with_tool_findings` records a completed run with a separately certified SDK issue. It is not a benchmark pass. Currently this disposition is limited to very small assets underframed by the SDK's 0.1-metre minimum camera bounds. The exact source USD, static receipt, raw failed results, native thumbnail, camera-source revision and measured framing evidence are bound by SHA-256 in a per-asset certificate. All physical tests and Palatial checks must pass or be explicitly inapplicable; engine, joint, collision, culling and other asset failures cannot receive this disposition. NVIDIA's original failed benchmark sidecars remain in the packages. These findings require NVIDIA review, consistent with [REVIEW.003](https://github.com/NVIDIA-Omniverse/simready-central/blob/main/docs/acceptance-criteria.md#review003---asset-path-carries-no-benchmark-results).

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
