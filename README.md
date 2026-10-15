---
license: cc-by-4.0
pretty_name: Palatial NV Asset Library
language:
- en
tags:
- 3d
- robotics
- simulation
- isaac-sim
- usd
- articulated-objects
size_categories:
- 1K<n<10K
configs:
- config_name: default
  data_files:
  - split: train
    path: data/catalog.parquet
---

# Palatial NV Asset Library

The Palatial NV Asset Library was **generated and verified by Palatial in collaboration with NVIDIA Robotics** to support open robotics research.

**[Browse the visual gallery](https://palatialsim.github.io/palatial-nv-asset-library/) · [Source repository](https://github.com/PalatialSim/palatial-nv-asset-library) · [Download files](https://huggingface.co/datasets/PalatialSim/palatial-nv-asset-library/tree/main)**

This release contains **1,013 USD assets across 41 batches**, with textures, physics metadata, rendered and collision previews, and recorded simulation videos. The library is intended for researchers building simulation scenes and studying robotic perception, manipulation, and object interaction in NVIDIA Isaac Sim. The original source snapshot was approximately 28.9 GB; current package inventories record each published package’s file count and byte size.

The gallery is the quickest way to preview assets without downloading them or installing Isaac Sim. Search by name or asset ID, select a batch, filter authored moving joints, switch between rendered and collision views, and open a batch montage. The dataset table provides names and stable IDs, preview image paths, dimensions, an authored-joint indicator, USD paths and download links. The gallery displays the images.


<!-- standard-submission-report:start -->
## Current standard NVIDIA submission results

All **1,013** current packages have complete unchanged stock benchmark evidence. **955** have no failed tests and **58** retain **142 raw failures** for NVIDIA review. Eligibility skips remain separate from passes. No skip/ignore flags, test changes or benchmark parameter overrides were used. This is a submission for review, not NVIDIA approval or independent physical calibration.

See the [complete current inventory and exact failure reports](reports/releases/2026.10.15/standard-submission/README.md).
<!-- standard-submission-report:end -->


<!-- source-quality-follow-up:start -->
## Source-quality corrections — 15 October 2026

221 corrected source revisions have completed full stock validation and benchmarking. The corrections remove undefined zero normals and exactly zero-area faces, and replace impossible explicit mass properties with standard geometry-derived automatic properties. Point coordinates, surviving surfaces, textures, materials, mass, density and joint definitions are preserved. Geometry-derived properties are modeling approximations, not measurements.

The [source diffs and invariant checks](reports/releases/2026.10.15/source-quality/README.md) bind the corrected hashes to their actual evidence. Current batch downloads, logical packages, physics metadata, catalog and gallery use the same source hashes. Earlier internal qualification stays historical and is not reassigned to changed sources.
<!-- source-quality-follow-up:end -->

## Download an asset

Keep the complete asset folder together so relative texture, material, and behavior-script references remain available. Downloading the USD alone may omit its dependencies.

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="PalatialSim/palatial-nv-asset-library",
    repo_type="dataset",
    allow_patterns=["batch10/D00006 Bamboo Basket/**", "LICENSE*", "LICENSING.md"],
    local_dir="palatial-assets",
)
```

To download the whole library:

```bash
hf download PalatialSim/palatial-nv-asset-library --repo-type dataset --local-dir palatial-assets
```

To browse the catalog programmatically:

```python
from datasets import load_dataset

assets = load_dataset("PalatialSim/palatial-nv-asset-library", split="train")
print(assets[0]["name"], assets[0]["usd_path"])
```

`train` is the Hub table split name; this release does not define a machine-learning training/test partition.

## Organization

The original batch and asset folder paths are preserved. Each asset has one USD and a physics JSON, plus its textures, material files, behavior scripts where supplied, and simulation recording. `gallery/` contains preview images, montages, and the browser gallery. `data/catalog.parquet` contains one searchable row per asset with metadata and paths to rendered and collision images. Original preview images retain their source resolution. `data/catalog.jsonl` provides a readable index. The current release manifest records SHA-256 source identities and immutable package/evidence provenance per asset.

The gallery identifies 90 assets with enabled authored moving joints and 923 without. An authored-joint indicator does not mean a video exercises every joint. Bounds are transformed visual-mesh dimensions in X × Y × Z order, in metres; consult each USD and physics JSON for units and axis metadata.

## Verification and research use

All **1,013** current packages have complete unchanged stock benchmark evidence. **955** have no failed tests and **58** retain **142 raw failures** for NVIDIA review. Eligibility skips remain separate from passes. No skip/ignore flags, test changes or benchmark parameter overrides were used. This is a submission for review, not NVIDIA approval or independent physical calibration.

The [current release manifest](reports/current-release.json) binds current source hashes, physics JSONs, complete stock results and immutable package/raw-evidence URLs. Its readiness check verifies evidence and metadata for review; it does not waive a failed test or certify cooked contact behavior. The earlier 2026-10-13 internal release recorded 957 native passes and 56 separately documented SDK findings; those results retain their original source hashes.

Authored dimensions, mass, collision schema and joints are checked against the USD. Physical measurements are not independently calibrated. Corrected-source rendered thumbnails are fresh native authoring output. Older collision previews and simulation recordings are labeled historical and do not qualify the current revision. See [verification policy](VERIFICATION.md).

## License and attribution

Assets, metadata, previews, and recordings: **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)**. Software and automation: **[Apache 2.0](LICENSE-CODE)**. See [LICENSING.md](LICENSING.md) for the scope and [LICENSE](LICENSE) for the complete asset license.

Attribution: **Palatial Platforms — Palatial NV Asset Library**. Link to this dataset or the source repository and CC BY 4.0, and indicate modifications when sharing changed assets.

## Provenance

The current release is derived from the original GitHub revision `a8c65abbf0304a0e58b99157c80d59bd504c8484` and Hugging Face revision `154e2d76f519421b55c0a0f4f22e7b4a37b2cc90`. Original source assets were preserved during repair. The [release manifest](reports/current-release.json) records the exact metadata artifacts, source hashes, repaired USD hashes, native coverage and immutable package URLs. Textures and existing recordings retain their delivered bytes.

Each completed package appears in a logical asset folder such as `D00006/`. Preserve the complete folder when downloading; its USD, textures, thumbnail, validation and benchmark sidecars, package definition and bill of materials belong together. The original `batch*/` paths remain available for existing consumers.

```python
snapshot_download(
    repo_id="PalatialSim/palatial-nv-asset-library",
    repo_type="dataset",
    allow_patterns=["D00006/**", "LICENSE*", "LICENSING.md"],
    local_dir="palatial-simready-assets",
)
```

## Asset names and IDs

Assets use readable names alongside their stable identifiers, for example **Bamboo Basket (D00006)**. The gallery and Hugging Face catalog expose this paired display name. The [complete name-to-ID index](data/asset-names.csv) covers all 1,013 assets. Package folder names, package IDs, USD files and immutable download URLs retain their existing identifiers.

## Asset name update register

The complete [205-record handoff register](reports/rename-register-20261008.csv) includes original asset IDs, old and corrected names, and preview links.

All 205 originals were found in the canonical Palatial Library with their corrected names. 65 are matched to this NV export: 64 by original ID and Masticating Juicer (D00423) by verified package content. The other 140 have no confirmed NV mapping; use their original preview links. [Reconciliation evidence](reports/rename-reconciliation-20261008.md) documents the checks and remaining metadata gaps. The broader Library retains its own per-asset license and attribution.

The confirmed juicer rename and full source register were published from [source commit 5a123e7bdf44](https://github.com/PalatialSim/palatial-nv-asset-library/commit/5a123e7bdf445ccc0e2f2849586d700554668f0d), titled **release ready**. The NV collection contains 1,013 models and 65 confirmed handoff name matches; original model and recording bytes are preserved.
