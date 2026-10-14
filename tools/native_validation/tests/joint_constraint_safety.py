"""Observe real joint frames while running NVIDIA's unchanged excitation test."""
import ast
import inspect
import math

from simready_benchmark.core.decorator import test
from simready_benchmark_kit_suite.fet004_multibody import joint_movement as official


def official_defaults():
    tree = ast.parse(inspect.getsource(official.test_joint_movement))
    for decoration in tree.body[0].decorator_list:
        for keyword in getattr(decoration, 'keywords', []):
            if keyword.arg == 'config_defaults':
                return ast.literal_eval(keyword.value)
    raise RuntimeError('Cannot recover unchanged NVIDIA excitation configuration')


@test(features=[{'id': 'FET_004_STANDARD', 'version': '>=0.1.0'}],
      name='palatial_joint_constraint_safety', version='1.0.0',
      description='Observes finite live body poses, joint anchor closure, authored travel limits and actual relative motion during the unchanged NVIDIA joint excitation.',
      expected_video='Every movable joint moves within its authored limits while connected anchors remain coincident.',
      engine={'tags': ['kit'], 'version': '>=2024.2.0'},
      config_defaults=official_defaults(), max_duration=360)
async def joint_constraint_safety(ctx):
    import json
    from pathlib import Path
    from pxr import Gf, Usd, UsdGeom, UsdPhysics
    import omni.usd
    from simready_benchmark_kit_suite.fet004_multibody.joint_discovery import discover_joints

    samples = {}
    failures = set()
    original_step = ctx.physics_step
    discovered = None
    meters = 1.0

    def observe():
        nonlocal discovered, meters
        stage = omni.usd.get_context().get_stage()
        if not stage or not ctx.scene.asset:
            return
        if discovered is None:
            meters = UsdGeom.GetStageMetersPerUnit(stage)
            discovered = [joint for joint in discover_joints(stage, ctx.scene.asset.prim_path)
                          if official._joint_dof_locked(stage, joint['prim_path']) is None
                          and stage.GetPrimAtPath(joint['prim_path']).GetAttribute('physics:jointEnabled').Get() is not False]
        for item in discovered:
            name = item['name']
            prim = stage.GetPrimAtPath(item['prim_path'])
            joint = UsdPhysics.Joint(prim)
            frames = []
            for side in (0, 1):
                targets = (joint.GetBody0Rel() if side == 0 else joint.GetBody1Rel()).GetTargets()
                body = stage.GetPrimAtPath(targets[0]) if targets else None
                world = UsdGeom.Xformable(body).ComputeLocalToWorldTransform(Usd.TimeCode.Default()) if body else Gf.Matrix4d(1)
                if not all(math.isfinite(float(world[r][c])) for r in range(4) for c in range(4)):
                    failures.add(name + ':nonfinite_body_pose')
                    continue
                position = (joint.GetLocalPos0Attr() if side == 0 else joint.GetLocalPos1Attr()).Get() or Gf.Vec3f(0)
                rotation = (joint.GetLocalRot0Attr() if side == 0 else joint.GetLocalRot1Attr()).Get() or Gf.Quatf(1)
                local = Gf.Matrix4d(1)
                local.SetRotate(Gf.Quatd(rotation))
                local.SetTranslateOnly(Gf.Vec3d(position))
                frames.append(local * world)
            if len(frames) != 2:
                continue
            # Gf uses row vectors: child * inverse(parent) is invariant to common world motion.
            relative = frames[1] * frames[0].GetInverse()
            translation = relative.ExtractTranslation() * meters
            axis_index = {'X': 0, 'Y': 1, 'Z': 2}[item['axis']]
            axial = float(translation[axis_index])
            transverse = math.sqrt(sum(float(translation[i]) ** 2 for i in range(3) if i != axis_index))
            closure = float(translation.GetLength())
            quaternion = relative.ExtractRotationQuat().GetNormalized()
            angle = math.degrees(2 * math.atan2(float(quaternion.GetImaginary()[axis_index]), float(quaternion.GetReal())))
            lower = prim.GetAttribute('physics:lowerLimit').Get()
            upper = prim.GetAttribute('physics:upperLimit').Get()
            prismatic = prim.IsA(UsdPhysics.PrismaticJoint)
            revolute = prim.IsA(UsdPhysics.RevoluteJoint)
            coordinate = axial if prismatic else angle
            if revolute and lower is not None and upper is not None and math.isfinite(lower) and math.isfinite(upper):
                coordinate += 360 * round(((lower + upper) / 2 - coordinate) / 360)
            value = samples.setdefault(name, {'frames': 0, 'type': item['type_name'], 'min': coordinate, 'max': coordinate,
                                             'max_anchor_error_m': 0.0,
                                             'lower': lower if lower is not None and math.isfinite(lower) else None,
                                             'upper': upper if upper is not None and math.isfinite(upper) else None})
            value['frames'] += 1
            value['min'] = min(value['min'], coordinate)
            value['max'] = max(value['max'], coordinate)
            error = transverse if prismatic else closure
            value['max_anchor_error_m'] = max(value['max_anchor_error_m'], error)
            if error > 0.002:
                failures.add(name + ':anchor_error_over_2mm')
            if (prismatic or revolute) and lower is not None and upper is not None and lower < upper:
                scale = meters if prismatic else 1
                tolerance = 0.002 if prismatic else 2.0
                if coordinate < lower * scale - tolerance or coordinate > upper * scale + tolerance:
                    failures.add(name + ':authored_limit_exceeded')

    async def observed_step(*args, **kwargs):
        result = await original_step(*args, **kwargs)
        observe()
        return result

    ctx.physics_step = observed_step
    try:
        await official.test_joint_movement(ctx)
    finally:
        ctx.physics_step = original_step
    if not discovered:
        ctx.skip('No unlocked movable joints to observe')
        return
    for item in discovered:
        value = samples.get(item['name'])
        if not value or value['frames'] < 2:
            failures.add(item['name'] + ':missing_live_samples')
        elif item['type_name'] in {'PhysicsRevoluteJoint', 'PhysicsPrismaticJoint'}:
            threshold = 0.001 if item['type_name'] == 'PhysicsPrismaticJoint' else 1.0
            if value['max'] - value['min'] < threshold:
                failures.add(item['name'] + ':no_actual_relative_motion')
    receipt = {'schema': 'palatial.live-joint-safety.v1', 'joint_count': len(discovered),
               'failures': sorted(failures), 'joint_samples': samples}
    target = Path(ctx.output_dir) / 'joint-constraint-observations.json'
    target.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    ctx.add_metric('observed_joint_count', len(discovered))
    ctx.add_metric('joint_constraint_failures', len(failures))
    if failures:
        ctx.fail('Live joint safety failed: ' + ', '.join(sorted(failures)))
    else:
        ctx.step('Every movable joint had finite, bounded relative motion and closed anchors')
