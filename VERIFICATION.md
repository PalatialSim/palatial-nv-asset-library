# Metadata verification

`verified` with `scope: authored_usd_*` means the metadata was checked against the delivered USD. It is separate from runtime simulation acceptance and real-world calibration. This release does not upgrade recorded videos into proof of stability or complete mechanism coverage.

For the 154 repaired assets, the evidence checks stage units and up axis, transformed visible-mesh bounds, positive authored rigid-body masses and part sums, joint existence and targets (including valid static frames), enabled state and ordered limits, collision API counts and finite mesh coordinates. No geometry, mass, friction or joint limits were inferred from object names. Only the orphan Cocktail Shaker joint was removed from a USD; other USD binaries were retained.

Each repaired JSON records `validation.scope`, a scope for each individual check, `validation.runtime.status`, and the delivered USD SHA-256. `asset.bounds` and `parts[].bounds` use the stage's world axes, metres and default authored pose. The two legacy unnumbered assets use their existing folder names for `asset_id`. Unlimited USD force/limit sentinels in raw attribute dictionaries use quoted Infinity strings for strict JSON interoperability.

Run the fast completeness and consistency audit from the repository root:

```sh
python3 tools/audit_metadata.py .
```

For the full repaired-assets USD and gallery parity check, install the OpenUSD dependencies in a virtual environment, retain complete asset folders, and run:

```sh
python3 -m venv .venv
.venv/bin/pip install -r tools/requirements-usd.txt
.venv/bin/python tools/verify_metadata_usd.py .
```

The full check reopens each repaired USD, recomputes bounds and authored physics metadata, checks JSON/gallery agreement and verifies report SHA-256 hashes. It does not run Isaac Sim, cook collision hulls, execute joint drives or measure real-world properties. The [repair report](reports/metadata-repair-20261008.json) records the exact inputs and results.
