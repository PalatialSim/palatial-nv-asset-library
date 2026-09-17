# Asset gallery

1,013 assets across 41 batches (Batch 1 through Batch 41), with rendered views, collision views, and simulation videos. Search by name or ID, filter by batch or moving joints, and toggle collision views.

From the repository root, run `python3 -m http.server 8000`, then open `http://localhost:8000/gallery/`. Isaac Sim is not needed to browse. Keep this directory beside the repository batch folders: media is linked by relative path.

Collision images show the authored USD collision geometry. Batch 1 uses the delivered `PhysicsCollisionAPI` meshes (convex hulls where authored and SDF meshes where authored), with each rendered collision mesh assigned a distinct color. Videos show the recorded test behavior, including tipping where it occurs; they do not assert universal physical stability.
