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
