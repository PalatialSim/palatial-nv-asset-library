"""Verify Batch 41 index blobs, metadata parity and media decoding.

Requires OpenUSD, numpy, Pillow and ffmpeg/ffprobe. Run from any directory.
Source-package warnings are reported separately from publication checks.
"""
import hashlib
import io
import json
import posixpath
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image
from pxr import Sdf, Usd, UsdGeom, UsdPhysics
from standardize_batch41 import ROOT, git


def main():
    indexed = set(git("ls-files", "-z").decode().split("\0"))
    assets = json.loads((ROOT / "gallery/assets.json").read_text())
    rows = [a for a in assets if a["batch"] == "batch41"]
    assert len(assets) == 1013 and len(rows) == 36
    assert len({a["id"] for a in assets}) == len(assets)
    inline = json.loads(re.search(r"const assets=(\[.*?\]);let collision=",
                                 (ROOT / "gallery/index.html").read_text(), re.S)[1])
    for a, b in zip(assets, inline, strict=True):
        assert {k: v for k, v in a.items() if not k.endswith("_url")} == {
            k: v for k, v in b.items() if not k.endswith("_url")}
    sidecars = {json.loads(p.read_text())["asset_id"]: p
                for p in (ROOT / "batch41").rglob("physics_*.json")}
    assert len(sidecars) == 36
    report = {"publication_checks": "passed", "native_simulation": "not_rerun",
              "assets": [], "source_warnings": []}
    with tempfile.TemporaryDirectory(prefix="batch41-verify-") as folder:
        temp = Path(folder)
        for row in rows:
            did = re.search(r"D\d{5}", row["id"])[0]
            d = json.loads(sidecars[did].read_text())
            path = d["provenance"]["usd_path"]
            data = git("show", f":{path}")
            assert hashlib.sha256(data).hexdigest() == d["provenance"]["usd_sha256"]
            usd = temp / f"{did}.usd"
            usd.write_bytes(data)
            stage = Usd.Stage.Open(str(usd))
            assert UsdGeom.GetStageMetersPerUnit(stage) == 1.0
            assert str(UsdGeom.GetStageUpAxis(stage)) == "Z"
            assert all(np.isfinite(row["bounds"]["size"])) and all(v > 0 for v in row["bounds"]["size"])
            assert row["bounds"]["size"] == d["asset"]["bounds"]["size"]
            assert row["mass_kg"] == sum(p["mass"] for p in d["parts"])
            assert row["articulation"] == ("yes" if d["articulation"]["has_joints"] else "no")
            assert row["collider_prims"] == d["validation"]["collision"]["shape_count"] > 0
            warnings = []
            for prim in stage.Traverse():
                for rel in prim.GetRelationships():
                    if rel.GetName().startswith("material:binding"):
                        for target in rel.GetTargets():
                            if not stage.GetPrimAtPath(target):
                                warnings.append({"kind": "unresolved_material_binding",
                                                 "prim": str(prim.GetPath()), "target": str(target)})
                for attr in prim.GetAttributes():
                    v = attr.Get()
                    if isinstance(v, Sdf.AssetPath) and v.path:
                        raw = v.path
                        if raw == "OmniGlass.mdl":
                            continue  # Isaac Sim's built-in material module.
                        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), raw))
                        if resolved not in indexed:
                            warnings.append({"kind": "missing_asset_reference", "prim": str(prim.GetPath()), "path": raw})
            media = {}
            for key in ("render_url", "collision_url", "video_url"):
                path = posixpath.normpath(posixpath.join("gallery", unquote(row[key])))
                assert path in indexed, path
                raw = git("show", f":{path}")
                if key == "video_url":
                    video = temp / "video.mp4"
                    video.write_bytes(raw)
                    probe = json.loads(subprocess.check_output([
                        "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                        "-of", "json", str(video)]))
                    assert float(probe["format"]["duration"]) > 0
                    assert any(s.get("codec_type") == "video" and s.get("width", 0) > 0 for s in probe["streams"])
                    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(video),
                                    "-map", "0:v:0", "-f", "null", "-"], check=True)
                    media["duration_s"] = float(probe["format"]["duration"])
                else:
                    with Image.open(io.BytesIO(raw)) as im:
                        im.verify()
                media[key] = {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            report["assets"].append({"id": did, "usd_sha256": d["provenance"]["usd_sha256"], **media})
            if warnings:
                report["source_warnings"].append({"id": did, "findings": warnings})
            print(did, "passed", len(warnings), "source warnings", flush=True)
        for kind in ("render", "colliders"):
            with Image.open(ROOT / f"gallery/montages/batch41-{kind}.jpg") as im:
                im.verify()
    (ROOT.parent / "nv-batch41-verification-private.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Verified 36 USD hashes, physics sidecars, 72 images, 36 decoded videos and 2 montages.")


if __name__ == "__main__":
    main()
