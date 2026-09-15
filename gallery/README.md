# Asset gallery

963 assets across 39 batches, with rendered views, collision views, and simulation videos. Search by name or ID, filter by batch or moving joints, and toggle collision views.

From the repository root, run `python3 -m http.server 8000`, then open `http://localhost:8000/gallery/`. Isaac Sim is not needed to browse. Keep this directory beside the repository batch folders: existing media is linked by relative path.

Cyan views show authored collision geometry. Videos show the recorded test behavior, including tipping where it occurs; they do not assert universal physical stability.
