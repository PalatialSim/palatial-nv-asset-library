"""Independent material coverage using a cyan control for magenta source objects."""
from simready_benchmark.core.decorator import test
from simready_benchmark_kit_suite.fet006_materials import _scene,_surface_test,surfaces

@test(features=[{'id':'FET_006_STANDARD','version':'>=0.1.0'}],name='palatial_cyan_preview_surface_coverage',version='1.0.0',
 description='Independent universal surface coverage using cyan control material and the same SDK scene, binding strengths, pixel thresholds and 98 percent coverage requirement.',
 expected_video='Authored materials remain visible under the weak cyan control; the strong cyan control measures the complete silhouette.',
 engine={'tags':['kit'],'version':'>=2024.2.0'},config_defaults=dict(_scene.SCENE_DEFAULTS),max_duration=600)
async def cyan_material_coverage(ctx):
 import hashlib,inspect,json
 from pathlib import Path
 old_color=_surface_test.PROBE_COLOR;old_channels=_surface_test.MAGENTA_CHANNELS
 _surface_test.PROBE_COLOR=(0.0,1.0,1.0);_surface_test.MAGENTA_CHANNELS=(1,2)
 try:
  await _surface_test.run_coverage_test(ctx,context=surfaces.UNIVERSAL,requirement='com.nvidia.usd.VM.PS.001',fix_hint='Every visible Gprim must resolve the authored UsdPreviewSurface.')
 finally:
  _surface_test.PROBE_COLOR=old_color;_surface_test.MAGENTA_CHANNELS=old_channels
  data={'schema':'palatial.cyan-material-probe.v1','asset_usd_sha256':hashlib.sha256(Path(ctx.asset_path).read_bytes()).hexdigest(),
        'SDK_source_files_modified':False,'acceptance_thresholds_modified':False,'authored_asset_modified':False,
        'control_color':[0.0,1.0,1.0],'control_channels':[1,2],
        'official_source_sha256':hashlib.sha256(Path(inspect.getsourcefile(_surface_test)).read_bytes()).hexdigest(),
        'independent_measurement_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'official_config_defaults':dict(_scene.SCENE_DEFAULTS),'effective_config':dict(ctx.config)}
  (Path(ctx.output_dir)/'cyan-material-observations.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
