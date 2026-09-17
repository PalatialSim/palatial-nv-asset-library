# palatial-nv-asset-library

A library of USD assets (meshes, textures, physics configs, and Isaac Sim validation artifacts) for use with NVIDIA Isaac Sim.

Large binary files (`.usd`, `.png`, `.mp4`, `.jpeg`, etc.) are stored with [Git LFS](https://git-lfs.com/). You **must** install Git LFS before cloning, otherwise you will only get small text pointer files instead of the real assets.

## Visual previews and simulation videos

Open the [live asset gallery](https://palatialsim.github.io/palatial-nv-asset-library/) to browse **1,013 assets across 41 batches (Batch 1–Batch 41)** without downloading the repository or installing Isaac Sim. [Batch 41](https://palatialsim.github.io/palatial-nv-asset-library/?batch=batch41) adds **36 assets (D01028–D01063)**, each with a rendered preview, collision preview, simulation video, USD package, and physics JSON.

Choose a batch or use the previous/next arrows. Search by name or ID, filter by moving joints, switch between rendered and collision views, and open a full-size montage. Hover a card to preview its video. [Batch montage images](gallery/montages/) are also in the repository.

To browse locally, run this from the repository root:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/gallery/>. Isaac Sim is not needed to view the gallery.

- **Scale:** Gallery dimensions are transformed visual-mesh bounds in X × Y × Z order, in metres. Batch 41 USDs declare `metersPerUnit = 1` and Z up.
- **Joints:** The moving-joints filter describes authored USD joints. Batch 41 has 16 assets with moving joints (40 joints total) and 20 without. A video may not exercise every joint.
- **Collisions:** Collision images show authored collision geometry. Colors distinguish collision pieces.
- **Simulation videos:** Videos show recorded test behavior, including tipping where it occurs.

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
