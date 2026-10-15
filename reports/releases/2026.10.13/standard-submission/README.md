# Standard SimReady submission results — 15 October 2026

This report records the completed stock submission pipeline for all **1,013** PalatialSim assets. It preserves the uploaded benchmark outcomes and immutable evidence; it does not claim NVIDIA approval.

| Result | Count |
|---|---:|
| Packages with benchmark results and raw archives | 1,013 |
| Assets with no failed benchmark tests | 955 |
| Assets with recorded failed tests | 58 |
| Passed test records | 18,184 |
| SDK eligibility skips | 2,043 |
| Failed test records | 142 |

The profile is **Robotics-Prop 4.0.0**, license **CC BY 4.0**, package version **2026.10.13_00**. Tests ran at stock defaults, with no skip/ignore flags. Both configured engines executed applicable tests. Eligibility skips are recorded SDK decisions; PhysX-authored assets do not claim Newton physics qualification.

## Inventory and evidence

- [Complete package inventory](inventory.json): each asset's immutable package URL, accepted USD SHA256, original benchmark-sidecar SHA256, raw archive/manifest URLs and execution-plan SHA256.
- [Exact failed results](known-findings.json), also available as [CSV](known-findings.csv): each asset, test, engine and unedited validator message, with source and evidence links.
- [Source-quality repair candidates](source-repair-candidates.json): nine isolated candidates, with exact changed properties and source hashes. All completed full default trials but still had runtime findings. They have **not** replaced the released assets or the package inventory above.

## Upstream reports

| Finding family | Assets | Report |
|---|---:|---|
| Millimetre-scale framing and visibility | 17 | [NVIDIA/simready-foundation#36](https://github.com/NVIDIA/simready-foundation/issues/36) |
| Material-probe colour ambiguity | 12 | [NVIDIA/simready-foundation#37](https://github.com/NVIDIA/simready-foundation/issues/37) |
| Physics bounds/contact measurement | 29 | [NVIDIA/simready-foundation#38](https://github.com/NVIDIA/simready-foundation/issues/38) |

These reports contain evidence and investigation limits. Their existence does not establish that every failure is an SDK defect or waive physical/visual asset correctness. In particular, authored-vertex observations do not independently certify cooked collision shapes or contact depths.

## Provenance

The submitted source remains pinned to dataset revision `36cfecf457965197df5de198abd72bbf713cb9b4`. The package URLs select the actual stock uploads at their own immutable commits. The seven-GPU run used up to two independent asset submissions per GPU and retained 16 previously verified stock submissions. Hugging Face transport was batched; SDK benchmark algorithms, thresholds and raw results were unchanged.

Two renderer-environment issues were corrected to shipped defaults and fully requalified (D00516 and D01034); their prior failed attempts remain archived. Six withdrawn configuration attempts are historical diagnostics only. Hugging Face main was restored from the six original stock packages, byte for byte; the inventory continues to reference their original immutable stock URLs.

The earlier internal native qualification (957 nonfailing assets and 56 assets with disclosed findings) is a separate historical run. The current standard results are the counts above. NVIDIA evaluates the submitted packages and findings during review.
