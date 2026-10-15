# Source-quality corrections

221 source revisions have complete current stock evidence. The full correction set contains 221 assets: 3,188 undefined normal vectors repaired, 35,164 exactly zero-area faces removed, and 20 rigid bodies restored to standard geometry-derived automatic mass properties. All affected mesh subdivision schemes are explicitly none. Every removed face was independently proven exactly zero area.

All point coordinates, surviving surfaces and UV mappings, nonzero normals, materials, textures, transforms, mass/density and joint definitions are preserved. Removing degenerate faces from shared visual/collision meshes preserves their occupied surfaces. Automatic COM/inertia values are not measurements and remain null in JSON until actually computed.

[Repairs](repairs.json), [source invariants](source-invariants.json), [fresh metadata inspections](metadata-inspections.json) and [independent corrected-source verification receipts](correction-verifications.json) record exact provenance. [Current stock results](../standard-submission/README.md) retain all actual failures. Earlier internal metadata is retained under historical-physics; its native certificates are not copied to new source hashes.

[Evidence recovery and ancillary-log preservation limits](evidence-recovery.json) distinguish original completed receipts from inventories reconstructed and reverified against immutable Hub packages and stock BoMs. No native test was repeated for this recovery.
