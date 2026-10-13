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

This release contains **1,013 USD assets across 41 batches**, with textures, physics metadata, rendered and collision previews, and recorded simulation videos. The library is intended for researchers building simulation scenes and studying robotic perception, manipulation, and object interaction in NVIDIA Isaac Sim. The source snapshot is approximately 28.9 GB.

The gallery is the quickest way to preview assets without downloading them or installing Isaac Sim. Search by name or asset ID, select a batch, filter authored moving joints, switch between rendered and collision views, and open a batch montage. The dataset table provides a thumbnail, collision thumbnail, dimensions, authored-joint indicator, USD path, and download links for each asset.

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

The original batch and asset folder paths are preserved. Each asset has one USD and a physics JSON, plus its textures, material files, behavior scripts where supplied, and simulation recording. `gallery/` contains preview images, montages, and the browser gallery. `data/catalog.parquet` contains one searchable row per asset with embedded rendered and collision thumbnails, resized to fit within 512 × 512 pixels. Original preview images retain their source resolution. `data/catalog.jsonl` provides a readable index. The file manifest records Git blob hashes and byte sizes for the current source revision.

The gallery identifies 90 assets with enabled authored moving joints and 923 without. An authored-joint indicator does not mean a video exercises every joint. Bounds are transformed visual-mesh dimensions in X × Y × Z order, in metres; consult each USD and physics JSON for units and axis metadata.

## Verification and research use

The 2026-10-13 release uses NVIDIA Robotics-Prop 4.0.0 with separate single-body, multi-body and articulated checks in Isaac Sim 6.1.0.0 (PhysX). Current acceptance: **1,013 static profile passes, 95 native passes and 77 completed SimReady packages out of 1,013 assets.** The [release manifest](reports/current-release.json) binds the catalog, physics metadata and per-asset evidence. Native passes require complete planned test coverage, unchanged USD bytes, an independently checked black-background thumbnail and, for moving joints, independent joint-constraint checks.

Authored geometry dimensions, mass and collision data are checked against the USD. These properties are not independently calibrated from physical measurements. Existing simulation recordings remain available; the current release's native verdicts come from the new hash-bound test evidence. See [release notes](RELEASE_NOTES.md) and [verification policy](VERIFICATION.md).

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

## Asset name update register

The complete [205-record handoff register](reports/rename-register-20261008.csv) includes original asset IDs, old and corrected names, and preview links.

All 205 originals were found in the canonical Palatial Library with their corrected names. 65 are matched to this NV export: 64 by original ID and Masticating Juicer (D00423) by verified package content. The other 140 have no confirmed NV mapping; use their original preview links. [Reconciliation evidence](reports/rename-reconciliation-20261008.md) documents the checks and remaining metadata gaps. The broader Library retains its own per-asset license and attribution.

The confirmed juicer rename and full source register were published from [source commit 5a123e7bdf44](https://github.com/PalatialSim/palatial-nv-asset-library/commit/5a123e7bdf445ccc0e2f2849586d700554668f0d), titled **release ready**. The NV collection contains 1,013 models and 65 confirmed handoff name matches; original model and recording bytes are preserved.
