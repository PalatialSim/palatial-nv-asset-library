# Asset name update register — 2026-10-08

All **205 original assets** in the Drive handoff were located in the canonical Palatial Library. Their current names equal the supplied final names, their status is READY, and all have stored downloadable model packages. The handoff contains 204 name changes and one cover-only record, with 59 cover replacement requests.

**65 originals are matched to this 1,013-asset NV export:** 64 by original ID and one by verified model-package content. The additional match is **Masticating Juicer → D00423**, with 28 matching visual meshes, matching mass, bounds, colliders and joint metadata, and 96 byte-identical shared files. Only its name is updated; its delivered model and joint drive settings are preserved. [Juicer match evidence](juicer-name-match-20261008.json) records the comparison.

**140 original Library records have no confirmed NV mapping.** Their corrected names and original preview links are included in the register, without substituting another model that shares a D number or old name. No exact geometry match does not establish that every object is a completely new design; regenerated versions can differ in topology. A known original-ID match also has different current source geometry, showing that original packages may have changed since the NV export.

## Identity verification

- Compared the 139 originally unmatched USD packages against authored visual geometry in all 1,013 NV USD packages. Found the one juicer match above; no other exact or rounded geometry fingerprints matched.
- Compared the two remaining MuJoCo-only originals using their authored OBJ visual geometry and base-color textures. Neither matched the NV export.
- Checked all 205 original names against the Drive final-name column and all 205 original package inventories. Original asset IDs, links, and model bytes were preserved.

These checks establish the release mapping; they do not constitute a new native simulation or real-world physics qualification. Existing 59 cover requests apply to the originals in the broader Library; this recheck does not claim to have replaced or verified those covers.

## Browse or reuse the handoff

The [CSV](rename-register-20261008.csv) and [JSON](rename-register-20261008.json) contain every original ID, old name, corrected name, source preview link, and NV inclusion decision. The [searchable register](../gallery/rename-register.html) presents the same records.

The NV export retains its CC BY 4.0 license. Links to the broader Library do not relicense its models: follow the license and attribution supplied with each original asset. The original Library displays CC BY-NC 4.0, while individually traceable NVIDIA SimReady source packages may carry CC BY 4.0. The Library's general label is not a per-asset rights check. No additional original model packages are included in this release.

## Are the remaining originals complete?

The 140 originals without an NV mapping have downloadable model packages and legacy physics JSONs. Their geometry and simulation data provide a basis for a standardized release, but their metadata does not yet meet this NV release's schema: all 140 lack metadata bounds, up axis, asset ID, and verification fields, and nine lack an object type. The 138 remaining USDs contain authored rigid bodies, positive mass, collision geometry, and joint information where applicable. Two originals use MuJoCo XML and mesh packages. Omniverse MDL shader dependencies need the target runtime. Native simulation and per-asset licensing have not been requalified. [Original-package completeness audit](original-completeness-20261008.json) records these limits.
