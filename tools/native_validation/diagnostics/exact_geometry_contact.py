"""Independent contact checks using exact vertices, with NVIDIA's simulation and limits."""
import ast,inspect
from simready_benchmark.core.decorator import test
from simready_benchmark_kit_suite.fet003_physics import ground_drop,slope_drop

def defaults(function):
 tree=ast.parse(inspect.getsource(function))
 for decoration in tree.body[0].decorator_list:
  for keyword in getattr(decoration,'keywords',[]):
   if keyword.arg=='config_defaults':return ast.literal_eval(keyword.value)
 raise RuntimeError('Cannot recover the unchanged SDK contact configuration')

async def measured_contact(ctx,official,label):
 import hashlib,json,numpy as np
 from pathlib import Path
 from pxr import Usd,UsdGeom,UsdPhysics
 import omni.usd
 original=ctx.get_asset_bounds;samples=[];meshes=None
 def exact_bounds(*args,**kwargs):
  nonlocal meshes
  conservative=original(*args,**kwargs)
  if kwargs.get('authored'):return conservative
  stage=omni.usd.get_context().get_stage()
  if not stage or not ctx.scene.asset:return conservative
  if meshes is None:
   meshes=[];root=stage.GetPrimAtPath(ctx.scene.asset.prim_path)
   for prim in Usd.PrimRange(root):
    collision=prim.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get() is not False
    if collision and not prim.IsA(UsdGeom.Mesh):raise RuntimeError('Unsupported non-mesh collider needs separate evidence')
    if not prim.IsA(UsdGeom.Mesh):continue
    imageable=UsdGeom.Imageable(prim)
    visible=imageable.ComputeVisibility()!=UsdGeom.Tokens.invisible and imageable.ComputePurpose() in ['default','render','proxy']
    if visible or collision:
     points=np.asarray(UsdGeom.Mesh(prim).GetPointsAttr().Get(),dtype=np.float64)
     if not len(points) or not np.isfinite(points).all():raise RuntimeError('Missing or nonfinite exact mesh points')
     meshes.append((str(prim.GetPath()),points,visible,collision))
   if not meshes or not any(row[3] for row in meshes):raise RuntimeError('Exact collider coverage is missing')
  cache=UsdGeom.XformCache();low=np.full(3,np.inf);high=np.full(3,-np.inf);visible_z=np.inf;collider_z=np.inf
  for path,points,visible,collision in meshes:
   matrix=np.asarray(cache.GetLocalToWorldTransform(stage.GetPrimAtPath(path)),dtype=np.float64)
   world=points@matrix[:3,:3]+matrix[3,:3]
   if not np.isfinite(world).all():raise RuntimeError('Nonfinite live contact transform')
   low=np.minimum(low,world.min(axis=0));high=np.maximum(high,world.max(axis=0))
   if visible:visible_z=min(visible_z,float(world[:,2].min()))
   if collision:collider_z=min(collider_z,float(world[:,2].min()))
  samples.append({'sample':len(samples),'sdk_bbox_min_z':float(conservative.min[2]),'exact_min':low.tolist(),'exact_max':high.tolist(),
                  'exact_visible_min_z':visible_z,'collider_vertex_min_z':collider_z})
  return type(conservative)(tuple(low),tuple(high))
 ctx.get_asset_bounds=exact_bounds
 try:await official(ctx)
 finally:
  ctx.get_asset_bounds=original
  config=defaults(official)
  data={'schema':'palatial.exact-geometry-contact.v1','asset_usd_sha256':hashlib.sha256(Path(ctx.asset_path).read_bytes()).hexdigest(),
        'official_test':label,'official_source_sha256':hashlib.sha256(Path(inspect.getsourcefile(official)).read_bytes()).hexdigest(),
        'independent_measurement_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'simulation_modified':False,'thresholds_modified':False,'measurement_method':'Exact live transformed visible and collider mesh vertices; conservative SDK bounds retained alongside.',
        'official_config_defaults':config,'effective_config':dict(ctx.config),'mesh_coverage':[{'path':p,'vertex_count':len(v),'visible':visible,'collision':collision} for p,v,visible,collision in (meshes or [])],
        'samples':samples}
  (Path(ctx.output_dir)/'exact-contact-observations.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
  ctx.add_metric('exact_contact_samples',len(samples))

@test(features=[{'id':'FET_003_STANDARD','version':'>=0.1.0'}],name='palatial_exact_geometry_ground_drop',version='1.0.0',
      description='Independent ground-drop verification using exact live mesh vertices in the unchanged SDK simulation, with the unchanged pass/fail thresholds.',
      expected_video='Ground drop and settling with no exact geometry penetration.',engine={'tags':['kit'],'version':'>=2024.2.0'},config_defaults=defaults(ground_drop.test_ground_drop),max_duration=600)
async def exact_ground(ctx):await measured_contact(ctx,ground_drop.test_ground_drop,'ground_drop')

@test(features=[{'id':'FET_003_STANDARD','version':'>=0.1.0'}],name='palatial_exact_geometry_slope_drop',version='1.0.0',
      description='Independent full slope-drop verification using exact live mesh vertices in the unchanged SDK simulation, with the unchanged pass/fail thresholds.',
      expected_video='Ramp contact, downhill motion and the complete post-motion settling window without exact geometry penetration.',engine={'tags':['kit'],'version':'>=2024.2.0'},config_defaults=defaults(slope_drop.test_slope_drop),max_duration=600)
async def exact_slope(ctx):await measured_contact(ctx,slope_drop.test_slope_drop,'slope_drop')
