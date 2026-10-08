# palatial-nv-asset-library

A library of USD assets (meshes, textures, physics configs, and Isaac Sim validation artifacts) for use with NVIDIA Isaac Sim.

**[Download on Hugging Face](https://huggingface.co/datasets/PalatialSim/palatial-nv-asset-library) · [Browse the visual gallery](https://palatialsim.github.io/palatial-nv-asset-library/)**

Assets are available under **CC BY 4.0**; gallery code and automation are available under **Apache 2.0**. See [LICENSING.md](LICENSING.md).

## Visual previews and simulation videos

Open the [live asset gallery](https://palatialsim.github.io/palatial-nv-asset-library/) to browse **1,013 assets across 41 batches (Batch 1–Batch 41)** without downloading the repository or installing Isaac Sim. [Batch 41](https://palatialsim.github.io/palatial-nv-asset-library/?batch=batch41) adds **36 assets (D01028–D01063)**, each with a rendered preview, collision preview, simulation video, USD package, and physics JSON.

Choose a batch or use the previous/next arrows. Search by name or ID, filter by moving joints, switch between rendered and collision views, and open a full-size montage. Hover a card to preview its video. [Batch montage images](gallery/montages/) are also in the repository.

To browse locally, run this from the repository root:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/gallery/>. Isaac Sim is not needed to view the gallery.

- **Scale:** Gallery dimensions are transformed visual-mesh bounds in X × Y × Z order, in metres. Batch 41 USDs declare `metersPerUnit = 1` and Z up.
- **Joints:** The moving-joints filter identifies 90 assets with enabled authored USD joints and 923 without. Batch 41 has 16 assets with moving joints (40 joints total) and 20 without. A video may not exercise every joint.
- **Collisions:** Collision images show authored collision geometry. Colors distinguish collision pieces.
- **Simulation videos:** Videos show recorded test behavior, including tipping where it occurs.

## Metadata release

The 2026-10-08 repair standardizes 154 affected assets and fixes all reported missing fields, mass rounding and verification gaps. Verification is scoped to consistency with the delivered USD. See [release notes](RELEASE_NOTES.md), [verification policy](VERIFICATION.md) and [per-asset evidence](reports/metadata-repair-20261008.json).

## Download assets

For selective or resumable asset downloads, use the [Hugging Face dataset](https://huggingface.co/datasets/PalatialSim/palatial-nv-asset-library). Its searchable catalog includes rendered and collision thumbnails plus per-asset folder and USD links.

```bash
hf download PalatialSim/palatial-nv-asset-library --repo-type dataset --local-dir palatial-assets
```

For the source repository and gallery code:

```bash
git clone https://github.com/PalatialSim/palatial-nv-asset-library.git
cd palatial-nv-asset-library
```

The current source snapshot stores the asset binaries directly in Git. A full clone is large; Git LFS is not required for these files. To preserve texture and behavior-script references, retain each complete asset folder when copying or downloading an asset.

## Repository layout

```text
batch10/D00006 Bamboo Basket/
├── IsaacSim_assets_<id>/
│   ├── IsaacSim_asset_<id>.usd
│   ├── physics_<id>.json
│   └── textures/
└── sim-video/
```

Asset layouts vary; the original supplied paths are retained. `gallery/` contains browser previews and batch montages.

## License

Copyright 2026 Palatial Platforms. Asset files, metadata, previews, and recordings are licensed under [CC BY 4.0](LICENSE). Software and automation are licensed under [Apache 2.0](LICENSE-CODE). See [LICENSING.md](LICENSING.md) for attribution and scope.

The 2026-10-08 Drive handoff also updates 64 asset names using exact source asset IDs and the supplied final names. All matching entries are name-only changes; covers and model packages remain as delivered. The other 141 handoff entries do not match this repository by source ID. [Name repair evidence](reports/name-repair-20261008.json) records the matches.

## Asset name update register

The complete [205-record handoff register](reports/rename-register-20261008.csv) includes original asset IDs, old and corrected names, and preview links. [Browse the searchable register](https://palatialsim.github.io/palatial-nv-asset-library/rename-register.html).

All 205 originals were found in the canonical Palatial Library with their corrected names. 65 are matched to this NV export: 64 by original ID and Masticating Juicer (D00423) by verified package content. The other 140 have no confirmed NV mapping; use their original preview links. [Reconciliation evidence](reports/rename-reconciliation-20261008.md) documents the checks and remaining metadata gaps. The broader Library retains its own per-asset license and attribution.
