"""Read delivered USD authoring without inferring simulation or real-world accuracy."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from pxr import Usd, UsdGeom, UsdPhysics


def inspect(path):
    stage = Usd.Stage.Open(str(path))
    if not stage:
        raise ValueError('USD did not open: ' + str(path))
    meters = UsdGeom.GetStageMetersPerUnit(stage)
    kg = UsdPhysics.GetStageKilogramsPerUnit(stage)
    axis = str(UsdGeom.GetStageUpAxis(stage))
    xforms = UsdGeom.XformCache()
    lows, highs, bodies, joints, colliders = [], [], [], [], []
    body_points = {}
    bad = []
    visual_count = 0
    for prim in stage.Traverse():
        prim_path = str(prim.GetPath())
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            mass_api = UsdPhysics.MassAPI(prim)
            mass = mass_api.GetMassAttr().Get()
            inertia = mass_api.GetDiagonalInertiaAttr().Get()
            bodies.append({'path': prim_path, 'name': prim.GetName(), 'mass_kg': None if mass is None else float(mass) * kg,
                           'mass_authored': bool(mass_api.GetMassAttr().HasAuthoredValueOpinion()),
                           'enabled': bool(UsdPhysics.RigidBodyAPI(prim).GetRigidBodyEnabledAttr().Get()),
                           'kinematic': bool(UsdPhysics.RigidBodyAPI(prim).GetKinematicEnabledAttr().Get()),
                           'inertia_kg_m2': [float(v) * kg * meters ** 2 for v in inertia] if inertia is not None else None})
        if prim.IsA(UsdPhysics.Joint):
            joint = UsdPhysics.Joint(prim)
            record = {'id': prim.GetName(), 'source_prim_path': prim_path, 'joint_type': prim.GetTypeName(),
                      'body0': [str(v) for v in joint.GetBody0Rel().GetTargets()],
                      'body1': [str(v) for v in joint.GetBody1Rel().GetTargets()],
                      'joint_enabled': bool(joint.GetJointEnabledAttr().Get())}
            for name in ('axis', 'lowerLimit', 'upperLimit', 'localPos0', 'localPos1', 'localRot0', 'localRot1'):
                attr = prim.GetAttribute('physics:' + name)
                value = attr.Get() if attr else None
                if value is not None:
                    if isinstance(value, (int, float, str, bool)):
                        record[name] = value
                    elif hasattr(value, 'GetReal'):
                        record[name] = [float(value.GetReal()), *map(float, value.GetImaginary())]
                    else:
                        record[name] = list(map(float, value))
            dynamic_sides = 0
            static_frames = []
            for side in ('body0', 'body1'):
                if len(record[side]) > 1:
                    bad.append('multiple joint body targets: ' + prim_path)
                for target in record[side]:
                    body = stage.GetPrimAtPath(target)
                    if not body:
                        bad.append('joint target does not exist: ' + target)
                        continue
                    target_prim = body
                    while body and not body.HasAPI(UsdPhysics.RigidBodyAPI):
                        body = body.GetParent()
                    if body and body.HasAPI(UsdPhysics.RigidBodyAPI):
                        dynamic_sides += 1
                    elif target_prim.IsA(UsdGeom.Xformable):
                        static_frames.append(target)
                    else:
                        bad.append('joint target is not a transformable frame: ' + target)
            if not dynamic_sides:
                bad.append('joint has no rigid body: ' + prim_path)
            record['static_frames'] = static_frames
            if record.get('lowerLimit', -float('inf')) > record.get('upperLimit', float('inf')):
                bad.append('reversed joint limits: ' + prim_path)
            joints.append(record)
        collision = prim.HasAPI(UsdPhysics.CollisionAPI)
        if collision:
            colliders.append({'path': prim_path, 'enabled': bool(UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get()),
                              'approximation': str(UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get()) if prim.HasAPI(UsdPhysics.MeshCollisionAPI) else None})
        if prim.IsA(UsdGeom.Mesh):
            mesh = UsdGeom.Mesh(prim)
            points = np.asarray(mesh.GetPointsAttr().Get(), dtype=np.float64)
            if points.size == 0 or not np.isfinite(points).all():
                bad.append('empty or nonfinite mesh: ' + prim_path)
                continue
            imageable = UsdGeom.Imageable(prim)
            purpose = imageable.ComputePurpose()
            visible = imageable.ComputeVisibility() != UsdGeom.Tokens.invisible
            # Authored colliders may also be visible meshes; include these if
            # they belong to the default/render purpose and are visible.
            if visible and purpose in (UsdGeom.Tokens.default_, UsdGeom.Tokens.render):
                transformed = np.column_stack((points, np.ones(len(points)))) @ np.asarray(xforms.GetLocalToWorldTransform(prim))
                world = transformed[:, :3] * meters
                lows.append(world.min(axis=0)); highs.append(world.max(axis=0)); visual_count += 1
                body = prim
                while body and not body.HasAPI(UsdPhysics.RigidBodyAPI):
                    body = body.GetParent()
                if body:
                    body_points.setdefault(str(body.GetPath()), []).append((world.min(axis=0), world.max(axis=0)))
    if not lows:
        bad.append('no visible mesh bounds')
        bounds = None
    else:
        low = np.min(lows, axis=0); high = np.max(highs, axis=0)
        bounds = {'min': low.tolist(), 'max': high.tolist(), 'size': (high - low).tolist(), 'units': 'm'}
    for body in bodies:
        points = body_points.get(body['path'])
        if points:
            low = np.min([p[0] for p in points], axis=0); high = np.max([p[1] for p in points], axis=0)
            body['bounds'] = {'min': low.tolist(), 'max': high.tolist(), 'size': (high - low).tolist(), 'units': 'm'}
        if body['mass_kg'] is None or body['mass_kg'] <= 0 or not np.isfinite(body['mass_kg']):
            bad.append('missing/nonpositive authored body mass: ' + body['path'])
    return {'usd_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'up_axis': axis,
            'axis_authored': stage.HasAuthoredMetadata('upAxis'), 'meters_per_unit': meters,
            'length_units_authored': UsdGeom.StageHasAuthoredMetersPerUnit(stage), 'kilograms_per_unit': kg,
            'mass_units_authored': UsdPhysics.StageHasAuthoredKilogramsPerUnit(stage),
            'bounds': bounds, 'visual_meshes': visual_count, 'bodies': bodies, 'joints': joints,
            'colliders': colliders, 'total_mass_kg': sum(b['mass_kg'] or 0 for b in bodies),
            'moving_joints': sum(j['joint_enabled'] and j['joint_type'] != 'PhysicsFixedJoint' for j in joints),
            'errors': bad}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('usd', type=Path)
    args = parser.parse_args()
    def standard_json(value):
        if isinstance(value, dict):
            return {k: standard_json(v) for k, v in value.items()}
        if isinstance(value, list):
            return [standard_json(v) for v in value]
        if isinstance(value, float) and not math.isfinite(value):
            return 'Infinity' if value > 0 else '-Infinity' if value < 0 else 'NaN'
        return value
    print(json.dumps(standard_json(inspect(args.usd)), indent=2, allow_nan=False))
