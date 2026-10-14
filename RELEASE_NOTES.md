<!-- simready-release-20261013 -->
# 2026-10-13 SimReady completion

The 2026-10-13 release uses NVIDIA Robotics-Prop 4.0.0 with separate single-body, multi-body and articulated checks in Isaac Sim 6.1.0.0 (PhysX). Current acceptance: **1,013 static profile passes, 955 native passes, 56 native completions with disclosed SDK findings and 1,011 completed SimReady packages out of 1,013 assets.** The [release manifest](reports/current-release.json) binds the catalog, physics metadata and per-asset evidence. Native passes require complete planned test coverage, unchanged USD bytes, an independently checked black-background thumbnail and, for moving joints, independent joint-constraint checks.

The release repairs default prims, portable material connections and texture paths, semantics, invalid hulls and extents, reversed normals, unit metadata and joint limits. The basket uses speculative CCD after a failing slope-drop control. The steamer has an explicit articulation root and sufficient solver iterations, with all 15 moving joints independently checked. Source visual geometry and authored mass were preserved for those native repairs.

The original batch layout remains available. Completed logical asset folders add official WRAPP packages and immutable manifest URLs. All catalog and gallery status fields come from actual per-asset evidence. Earlier name and metadata release history follows below.

<!-- previous-release-notes -->
# Metadata release — 2026-10-08

Repaired and standardized metadata for 154 assets across the library. This includes every reported asset and three additional assets with the same legacy floating-joint classification issue.

- Restored D00722 Sesame Seeds total and part mass from the delivered USD: 1.5300000200113573e-7 kg. The USD was already positive; JSON rounding caused the zero.
- Added all 28 missing dimension bounds, all 37 missing up-axis values, 49 descriptions, 22 object types and both missing asset IDs. The two unnumbered mustard assets retain their existing folder identifiers; no numbered IDs were invented.
- Checked the 25 batch-1 assets' mass, scale and joint metadata against their delivered USDs. Checked the 36 batch-41 assets' scale, mass, collision-schema and joint metadata.
- Recomputed affected bounds from transformed visible mesh points in the USD stage's world axes, in metres. These may differ from older Blender-space dimensions. Part bounds use the same documented frame.
- Standardized verification scope, source paths and SHA-256 evidence. High confidence means the metadata matches the delivered USD; it does not establish calibrated real-world dimensions/mass, contact stability, friction or full joint actuation. `validation.runtime.status = not_revalidated` preserves that distinction. Existing simulation videos remain available.
- Corrected moving-joint classification: independent bodies described as legacy `floating` connections do not count as authored constraints. The gallery now identifies 90 assets with enabled moving joints and 923 without.
- Removed one orphan fixed joint from D00350 Cocktail Shaker that targeted absent `part_3`. The delivered bodies, mesh attributes, materials and other physics properties were preserved. This USD change has not received a fresh native simulation test.
- Converted non-finite USD sentinel values in raw metadata dictionaries to quoted `"Infinity"` / `"-Infinity"` strings so files remain strict JSON. These represent unlimited forces or bounds, not mass or dimension values.

The [machine-readable repair report](reports/metadata-repair-20261008.json) preserves original fields, hashes, per-asset evidence and verification scope. [Verification policy](VERIFICATION.md) explains how to reproduce the checks.

The 2026-10-08 Drive handoff also updates 64 asset names using exact source asset IDs and the supplied final names. All matching entries are name-only changes; covers and model packages remain as delivered. The other 141 handoff entries do not match this repository by source ID. [Name repair evidence](reports/name-repair-20261008.json) records the matches.

## Original Library reconciliation — 2026-10-08

All 205 handoff originals have been located and their current source names match the supplied final names. 64 original IDs are included in this NV export. The model-package comparison confirms one further match: Masticating Juicer maps to D00423, whose name is updated in physics metadata, gallery and catalogs. 140 originals have no confirmed NV mapping. The [205-record register](reports/rename-register-20261008.csv) preserves original IDs, old and corrected names, and original preview links; the [reconciliation report](reports/rename-reconciliation-20261008.md) records verification scope. No additional original models were added, and existing model, drive, cover, and recording bytes are preserved.
