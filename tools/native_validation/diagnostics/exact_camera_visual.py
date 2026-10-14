"""Reframe tiny source geometry while preserving each official visual test and threshold."""
import ast,inspect
from simready_benchmark.core.decorator import test
from simready_benchmark_kit_suite.fet001_visual import presence,normals_xz
from simready_benchmark_kit_suite.fet006_materials import preview_surface_renders
from simready_benchmark_kit_suite.fet011_semantics import seg_labelled

def defaults(f,module):
 tree=ast.parse(inspect.getsource(f))
 for decorator in tree.body[0].decorator_list:
  for key in getattr(decorator,'keywords',[]):
   if key.arg=='config_defaults':return eval(compile(ast.Expression(key.value),'config_defaults','eval'),module.__dict__)
 raise RuntimeError('Cannot recover original visual parameters')

async def reframed(ctx,official,label):
 import hashlib,json,math
 from pathlib import Path
 from pxr import Gf,UsdGeom,Usd
 import omni.usd
 original=ctx.scene.auto_frame_camera;frames=[]
 def fit(padding=1.2):
  stage=omni.usd.get_context().get_stage();prim=stage.GetPrimAtPath(ctx.scene.asset.prim_path);cache=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render','proxy']);box=None
  for p in Usd.PrimRange(prim):
   if not p.IsA(UsdGeom.Mesh) or UsdGeom.Imageable(p).ComputeVisibility()==UsdGeom.Tokens.invisible:continue
   b=cache.ComputeWorldBound(p).ComputeAlignedRange()
   if b.IsEmpty():continue
   if box is None:box=b
   else:box.UnionWith(b)
  if box is None:raise RuntimeError('No visible bounds for independent camera')
  low=box.GetMin();high=box.GetMax();size=high-low;center=(high+low)*.5;diagonal=size.GetLength()
  if not math.isfinite(diagonal) or not 0<diagonal<.05:raise RuntimeError('Exact camera diagnostic is limited to tiny source assets')
  distance=diagonal*float(padding)*35/36;eye=center+Gf.Vec3d(.3,.8,.4).GetNormalized()*distance
  ctx.scene.set_camera(tuple(eye),tuple(center));frames.append({'size_m':list(size),'padding':padding,'distance_m':distance})
 ctx.scene.auto_frame_camera=fit
 try:await official(ctx)
 finally:
  ctx.scene.auto_frame_camera=original
  data={'schema':'palatial.exact-camera-visual.v1','official_test':label,'asset_usd_sha256':hashlib.sha256(Path(ctx.asset_path).read_bytes()).hexdigest(),
  'camera_framing_modified':True,'authored_asset_modified':False,'acceptance_thresholds_modified':False,'SDK_source_files_modified':False,
  'official_source_sha256':hashlib.sha256(Path(inspect.getsourcefile(official)).read_bytes()).hexdigest(),'independent_measurement_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  'camera_change':'Use actual visible bounds with the same padding, direction, 35 mm focal length and 36 mm aperture, removing only the SDK 0.1 m camera bounds and distance minimum.',
  'effective_config':dict(ctx.config),'frames':frames}
  (Path(ctx.output_dir)/'exact-camera-observations.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')

@test(features=[{'id':'FET_001_STANDARD','version':'>=0.1.0'}],name='palatial_exact_camera_presence',version='1.0.0',description='Independent presence using actual tiny-source bounds and unchanged SDK test.',expected_video='The unchanged tiny source asset fills the frame and passes the complete original visual check.',engine={'tags':['kit'],'version':'>=2024.2.0'},config_defaults=defaults(presence.test_presence,presence))
async def exact_presence(ctx):await reframed(ctx,presence.test_presence,'presence')
@test(features=[{'id':'FET_001_STANDARD','version':'>=0.1.0'}],name='palatial_exact_camera_normals_xz',version='1.0.0',description='Independent complete tilted rotation using actual tiny-source bounds and unchanged SDK normal test.',expected_video='The unchanged tiny source asset fills the frame and passes the complete original visual check.',engine={'tags':['kit'],'version':'>=2024.2.0'},config_defaults=defaults(normals_xz.test_normals_xz,normals_xz),max_duration=600)
async def exact_normals(ctx):await reframed(ctx,normals_xz.test_normals_xz,'normals_xz')
@test(features=[{'id':'FET_006_STANDARD','version':'>=0.1.0'}],name='palatial_exact_camera_preview',version='1.0.0',description='Independent full material controls using actual tiny-source bounds and unchanged SDK material test.',expected_video='The unchanged tiny source asset fills the frame and passes the complete original visual check.',engine={'tags':['kit'],'version':'>=2024.2.0'},config_defaults=defaults(preview_surface_renders.test_preview_surface_renders,preview_surface_renders))
async def exact_preview(ctx):await reframed(ctx,preview_surface_renders.test_preview_surface_renders,'preview_surface_renders')
@test(features=[{'id':'FET_011_STANDARD','version':'>=0.1.0'}],name='palatial_exact_camera_semantics',version='1.0.0',description='Independent semantic AOV using actual tiny-source bounds and unchanged SDK label test.',expected_video='The unchanged tiny source asset fills the frame and passes the complete original visual check.',engine={'tags':['kit'],'version':'>=2024.2.0'},config_defaults=defaults(seg_labelled.test_semantic_labels_seg_labelled,seg_labelled))
async def exact_semantics(ctx):await reframed(ctx,seg_labelled.test_semantic_labels_seg_labelled,'semantic_labels_seg_labelled')
