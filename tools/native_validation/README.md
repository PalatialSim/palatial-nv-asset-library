# Native validation sources

These are the supplemental checks and packaging compatibility code used for this release. Code follows the repository's Apache-2.0 license. The NVIDIA SDK and test suite are installed separately; their source files and acceptance thresholds are unchanged.

`tests/black_thumbnail.py` renders an independently framed native thumbnail on black, binds it to the input USD hash, and checks visible geometry. `tests/joint_constraint_safety.py` runs NVIDIA's unchanged joint excitation while observing live joint frames, relative motion, authored limits and anchor closure.

With the documented NVIDIA foundation and Isaac Sim environments installed, add these checks to the installed foundation suite:

```bash
simready-benchmark --assets /absolute/path/to/asset.usd \
  --project-config /absolute/path/to/workspace/project_config.toml \
  --runtime isaac_sim --tests-path tools/native_validation/tests \
  --max-concurrent 2 --session-mode batch --no-stamp \
  --output-dir /absolute/path/to/native-results
```

`native_worker.py` is the queue adapter used in isolated GPU containers. Its manifest identifies every input by SHA-256; deployment-specific environment paths are rooted at `/workspace/simready`. It does not replace the official `simready-manage submit` contribution workflow.

`package_native_asset.py` calls the documented SDK validation and packaging APIs. It dispatches the unchanged bill-of-materials hash operation onto WRAPP's event loop and isolates pre-validation, package creation and post-validation in separate processes to avoid the SDK's cross-loop semaphore error. All phases must pass. It preserves original benchmark failures.

`native_tool_findings.py` and the probe verifiers check narrowly documented SDK findings against unmodified raw results. They never convert an NVIDIA failed result into a pass. Offline color masks, separately named actual-size camera and cyan control diagnostics, and exact live-vertex contact measurements are identified as independent evidence. The contact diagnostic calls the unchanged NVIDIA simulation functions with their original parameters and thresholds while replacing the conservative bounds measurement. Both ground settling and complete slope motion must pass; real bouncing, penetration and joint faults remain blockers. `variants/black_thumbnail_lighting_v14.py` changes only the supplemental thumbnail lights for dark source materials. See the release's `VERIFICATION.md` and per-asset certificates for the applicable evidence and limits.

`sources.json` identifies this source snapshot. Raw result archives are linked from each asset's release evidence. Real-world physical properties remain uncalibrated simulation inputs.
