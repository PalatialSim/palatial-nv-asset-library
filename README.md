# palatial-nv-asset-library

A library of USD assets (meshes, textures, physics configs, and Isaac Sim validation artifacts) for use with NVIDIA Isaac Sim.

Large binary files (`.usd`, `.png`, `.mp4`, `.jpeg`, etc.) are stored with [Git LFS](https://git-lfs.com/). You **must** install Git LFS before cloning, otherwise you will only get small text pointer files instead of the real assets.

## Visual previews and simulation videos

Open the [live asset gallery](https://palatialsim.github.io/palatial-nv-asset-library/) to browse **1,013 assets across 41 batches** without downloading the repository or installing Isaac Sim. [Batch 41](https://palatialsim.github.io/palatial-nv-asset-library/?batch=batch41) includes **36 assets (D01028–D01063)**, each with a rendered preview, collision preview, simulation video, USD package, and standardized physics JSON.

Choose a batch or use the previous/next arrows. Search within the selected batch, filter by moving joints, switch between rendered and collision views, and open a full-size montage. Hover over a card to preview its video; the simulation-video link also works on touch devices. [Batch montage images](gallery/montages/) are available directly in the repository.

- **Scale:** Batch 41 USDs declare `metersPerUnit = 1` and Z up. Gallery dimensions are transformed visual-mesh bounds in X × Y × Z order, in metres. This confirms file units and geometry dimensions; it does not independently verify the real product's dimensions.
- **Joints:** Batch 41 contains 16 assets with enabled moving joints (40 moving joints total) and 20 without moving joints. The filter describes authored USD joints; a video may not exercise every joint.
- **Mass and physics:** Each Batch 41 USD has a neighboring `physics_<asset-or-run-id>.json` using schema version `1.0`, with `asset`, `parts`, `articulation`, `units`, `simulation`, `provenance`, and `validation` sections. Total mass sums the authored rigid-body masses. Provenance links back to the repository-relative USD path and its SHA-256.
- **Collisions:** Collision images display authored collision geometry. Colors distinguish collision pieces; the shape count is the number of enabled collider prims, not necessarily the number of shapes cooked by the simulator.
- **Simulation videos:** Videos show recorded test behavior, including tipping where it occurs. They are supplied recordings, not a guarantee of stability for every placement or simulation setting. The metadata audit does not rerun Isaac Sim.

To browse locally, run `python3 -m http.server 8000` from the repository root and open [the gallery](http://localhost:8000/gallery/). The published gallery remains the easiest way to browse all linked media.

## 1. Install Git LFS

### Linux (Debian/Ubuntu)
```bash
sudo apt-get update
sudo apt-get install git-lfs
```

### Linux (Fedora/RHEL)
```bash
sudo dnf install git-lfs
```

### macOS (Homebrew)
```bash
brew install git-lfs
```

### Windows
Download and run the installer from https://git-lfs.com/, or:
```powershell
winget install GitHub.GitLFS
```

### Verify
```bash
git lfs version
```

## 2. Initialize Git LFS (once per user)

```bash
git lfs install
```

This sets up the LFS hooks in your global git config. You only need to run it once per machine.

## 3. Clone the repository

```bash
git clone https://github.com/PalatialSim/palatial-nv-asset-library.git
cd palatial-nv-asset-library
```

When `git lfs install` has been run beforehand, the clone will automatically fetch the LFS-tracked binaries.

### If you already cloned without LFS

If you cloned before installing Git LFS and your asset files look tiny (a few hundred bytes containing `version https://git-lfs.github.com/spec/v1`), pull the real files with:

```bash
git lfs install
git lfs pull
```

## 4. (Optional) Verify the assets

```bash
git lfs ls-files | head
```

You should see a list of LFS-tracked files (USD, PNG, MP4, etc.).

## Repository layout

Each asset lives in its own folder, e.g.:

```
D00060 Bowl Dish/
├── D00060_Bowl_Dish.usd
├── physics_<id>.json
├── textures/
│   ├── texture_base_color.png
│   ├── texture_metallic.png
│   └── texture_roughness.png
```

