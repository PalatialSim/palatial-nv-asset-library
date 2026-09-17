"""Extract Batch 41 physics sidecars and gallery facts from composed USD stages.

Run with an OpenUSD Python environment containing numpy, from the repo root:
    python tools/standardize_batch41.py

Reads source USD blobs from the Git index so sparse checkouts are supported.
This records authored properties; it does not run a physics simulation.
"""
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from pxr import Usd, UsdGeom, UsdPhysics

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def value(attr, scale=1.0):
    if not attr or not attr.HasAuthoredValueOpinion():
        return None
    v = attr.Get()
    if v is None:
        return None
    if isinstance(v, (float, int)):
        return float(v) * scale
    try:
        return [float(x) * scale for x in v]
    except TypeError:
        return str(v)


def mesh_bounds(stage, meters):
    cache = UsdGeom.XformCache()
    lows, highs = [], []
    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Mesh):
            continue
        mesh = UsdGeom.Mesh(prim)
        if (mesh.ComputeVisibility() == UsdGeom.Tokens.invisible
                or mesh.ComputePurpose() not in (UsdGeom.Tokens.default_, UsdGeom.Tokens.render)):
            continue
        points = np.asarray(mesh.GetPointsAttr().Get())
        if not points.size:
            continue
        mat = np.asarray(cache.GetLocalToWorldTransform(prim))
        world = (points @ mat[:3, :3] + mat[3, :3]) * meters
        lows.append(world.min(axis=0))
        highs.append(world.max(axis=0))
    if not lows:
        raise ValueError("No visible default/render mesh points found")
    low = np.min(lows, axis=0)
    high = np.max(highs, axis=0)
    return {"min": low.tolist(), "max": high.tolist(), "size": (high-low).tolist()}


def extract(path, tmp):
    source = git("show", f":{path}")
    if source.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise ValueError(f"USD must be hydrated before audit: {path}")
    tmp.write_bytes(source)
    stage = Usd.Stage.Open(str(tmp))
    if stage.GetRootLayer().GetExternalReferences():
        raise ValueError(f"External USD layers require full package resolution: {path}")
    meters = UsdGeom.GetStageMetersPerUnit(stage)
    kilograms = UsdPhysics.GetStageKilogramsPerUnit(stage)
    axis = str(UsdGeom.GetStageUpAxis(stage))
    prims = list(stage.Traverse())
    colliders = [p for p in prims if p.HasAPI(UsdPhysics.CollisionAPI)
                 and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get()]
    joints = []
    for p in prims:
        if not p.IsA(UsdPhysics.Joint):
            continue
        j = UsdPhysics.Joint(p)
        joints.append({"id": p.GetName(), "path": str(p.GetPath()),
                       "type": p.GetTypeName(),
                       "enabled": bool(j.GetJointEnabledAttr().Get()),
                       "body0": [str(v) for v in j.GetBody0Rel().GetTargets()],
                       "body1": [str(v) for v in j.GetBody1Rel().GetTargets()],
                       "lower_limit": value(p.GetAttribute("physics:lowerLimit")),
                       "upper_limit": value(p.GetAttribute("physics:upperLimit"))})
    moving = [j for j in joints if j["enabled"] and j["type"] != "PhysicsFixedJoint"
              and (j["lower_limit"] is None or j["lower_limit"] != j["upper_limit"])]
    bodies = [p for p in prims if p.HasAPI(UsdPhysics.RigidBodyAPI)]
    parts = []
    for p in bodies:
        mass = UsdPhysics.MassAPI(p)
        shapes = [c for c in colliders if c.GetPath().HasPrefix(p.GetPath())]
        approximations = sorted({str(UsdPhysics.MeshCollisionAPI(c).GetApproximationAttr().Get())
                                 for c in shapes if c.HasAPI(UsdPhysics.MeshCollisionAPI)})
        parts.append({"id": p.GetName(), "name": p.GetName(),
                      "mass": value(mass.GetMassAttr(), kilograms),
                      "density": value(mass.GetDensityAttr(), kilograms / meters**3),
                      "inertia": value(mass.GetDiagonalInertiaAttr(), kilograms * meters**2),
                      "center_of_mass": value(mass.GetCenterOfMassAttr(), meters),
                      "physics_type": "rigid", "source": {"prim_path": str(p.GetPath())},
                      "collision": {"shape_count": len(shapes), "approximations": approximations},
                      "reasoning": None})
    # A missing explicit mass may be computed by the simulator from density/volume.
    known_masses = [p["mass"] for p in parts if p["mass"] is not None and p["mass"] > 0]
    total = sum(known_masses) if len(known_masses) == len(parts) and parts else None
    bounds = mesh_bounds(stage, meters)
    did = re.search(r"D\d{5}", path).group()
    name = re.sub(r"_simready$", "", Path(path).parts[1]).replace("_", " ")
    approximations = sorted({str(UsdPhysics.MeshCollisionAPI(c).GetApproximationAttr().Get())
                             for c in colliders if c.HasAPI(UsdPhysics.MeshCollisionAPI)})
    validation = {
        "overall": "partial",
        "scale": {"status": "recorded", "confidence": "medium", "units": "m",
                  "up_axis": axis, "bounds_m": bounds["size"]},
        "mass": {"status": "recorded" if total is not None else "not_checked",
                 "confidence": "medium" if total is not None else "low", "value_kg": total},
        "collision": {"status": "recorded", "confidence": "medium",
                      "shape_count": len(colliders), "approximations": approximations},
        "articulation": {"status": "recorded", "confidence": "medium", "moving_joints": len(moving)},
    }
    data = {"schema_version": "1.0", "asset_id": did,
            "asset": {"name": name, "object_type": "articulated" if moving else "rigid_bodies",
                      "total_mass": total, "bounds": bounds},
            "parts": parts, "articulation": {"has_joints": bool(moving), "joints": joints},
            "units": {"length": "m", "mass": "kg", "up_axis": axis}, "simulation": {"fix_base": None},
            "provenance": {"source_schema": "authored_usd", "usd_path": path,
                           "usd_sha256": hashlib.sha256(source).hexdigest(),
                           "source_meters_per_unit": meters, "source_kilograms_per_unit": kilograms,
                           "source_up_axis": axis, "bounds_method": "transformed_visual_mesh_points",
                           "reasoning_available": False,
                           "verification_note": "Authored USD properties and transformed visual bounds only. Real-world dimensions, mass, and runtime stability are not independently verified by this extraction."},
            "validation": validation}
    # Preserve the existing physics_<run-id>.json convention where a run ID exists.
    match = re.search(r"IsaacSim_asset_([a-f0-9]+)\.usd$", path)
    suffix = match.group(1) if match else did
    output = ROOT / Path(path).parent / f"physics_{suffix}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    return data


def main():
    paths = git("ls-files", "-z", "batch41").decode().split("\0")
    paths = sorted(p for p in paths if p.endswith(".usd"))
    assert len(paths) == 36, len(paths)
    assets_path = ROOT / "gallery/assets.json"
    assets = json.loads(assets_path.read_text())
    report = []
    with tempfile.TemporaryDirectory(prefix="batch41-physics-") as temp:
        for path in paths:
            d = extract(path, Path(temp) / (re.search(r"D\d{5}", path).group() + ".usd"))
            a = next(a for a in assets if a["batch"] == "batch41" and d["asset_id"] in a["id"])
            a.update(name=d["asset"]["name"], display_name=d["asset"]["name"][7:],
                     bounds={**d["asset"]["bounds"], "units": "m"},
                     bounds_status="recorded", bounds_method="transformed_visual_mesh_points",
                     up_axis=d["provenance"]["source_up_axis"],
                     moving_joints=d["validation"]["articulation"]["moving_joints"],
                     mass_kg=d["asset"]["total_mass"],
                     articulation="yes" if d["articulation"]["has_joints"] else "no",
                     collider_prims=d["validation"]["collision"]["shape_count"])
            report.append({"id": d["asset_id"], "bodies": len(d["parts"]),
                           "moving_joints": d["validation"]["articulation"]["moving_joints"],
                           "bounds_m": d["asset"]["bounds"]["size"],
                           "mass_kg": d["asset"]["total_mass"]})
    assets_path.write_text(json.dumps(assets, separators=(",", ":"), ensure_ascii=False) + "\n")
    index = ROOT / "gallery/index.html"
    html = index.read_text()
    # Preserve existing deployed URL convention while replacing the inline facts.
    for a in assets:
        for key in ("render_url", "collision_url", "video_url"):
            url = a.get(key)
            if url and not url.startswith(("http://", "https://")):
                a[key] = "https://palatialsim.github.io/palatial-nv-asset-library/" + url.removeprefix("../").lstrip("/")
    html, count = re.subn(r"const assets=\[.*?\];let collision=",
                         lambda _: "const assets=" + json.dumps(assets, separators=(",", ":"), ensure_ascii=False) + ";let collision=",
                         html, count=1, flags=re.S)
    assert count == 1
    index.write_text(html)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
