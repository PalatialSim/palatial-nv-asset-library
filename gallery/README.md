# Asset gallery

1,013 assets across 41 batches (Batch 1 through Batch 41), with rendered views, collision views, and simulation videos. Search by name or ID, step through batches with previous/next, filter by moving joints, and toggle collision views. The live gallery is at https://palatialsim.github.io/palatial-nv-asset-library/.

From the repository root, run `python3 -m http.server 8000`, then open `http://localhost:8000/gallery/`. Isaac Sim is not needed to browse. Keep this directory beside the repository batch folders: media is linked by relative path.

Collision images show the authored USD collision geometry. Batch 1 uses the delivered `PhysicsCollisionAPI` meshes (convex hulls where authored and SDF meshes where authored), with each rendered collision mesh assigned a distinct color. Videos show the recorded test behavior, including tipping where it occurs; they do not assert universal physical stability.

## Project branding and resources

The gallery includes the original Palatial and NVIDIA wordmarks, attribution to the robotics research collaboration, and links to the Hugging Face dataset, GitHub source, verification notes, release notes, issue tracker, and asset license. The header and footer adapt to narrow screens and support keyboard navigation. Brand asset sources and ownership are documented in [`brand/README.md`](brand/README.md).
