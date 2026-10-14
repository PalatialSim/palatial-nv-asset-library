"""Check complete, source-bound visual diagnostics for tiny-object camera failures."""
import hashlib, json, math, re
from pathlib import Path

TESTS = {'presence':'palatial_exact_camera_presence', 'normals_xz':'palatial_exact_camera_normals_xz',
         'preview_surface_renders':'palatial_exact_camera_preview', 'semantic_labels_seg_labelled':'palatial_exact_camera_semantics'}
CONFIGS = {
 'presence':dict(settle_frames=5,camera_padding=1.2,asset_load_timeout=30,min_diff_ratio=.01),
 'normals_xz':dict(steps=8,settle_frames=5,camera_padding=1.2,asset_load_timeout=30,dark_threshold=.15,max_problem_ratio=.5,min_problem_frames=2),
 'preview_surface_renders':dict(settle_frames=8,camera_padding=1.2,asset_load_timeout=30,min_silhouette_pixels=5000,mask_dominance_ratio=1.5,mask_dominance_floor=.2,frame_settle_tolerance=.01,frame_settle_attempts=4,min_material_coverage=.98),
 'semantic_labels_seg_labelled':dict(camera_padding=1.2,settle_frames=5,asset_load_timeout=30,render_subframes=4,on_coverage_min=.005)}

def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def verify_exact_camera_probe(c,root):
 root=Path(root).resolve()
 if c.get('static_validation_passed') is not True or c.get('manual_native_capture_review') is not True or c.get('benchmark_config_modified') is not False:
  raise RuntimeError('Exact-camera review proof is incomplete')
 dims=c['actual_visible_bounds_size_m']
 if len(dims)!=3 or not all(math.isfinite(v) and 0<v<=.005 for v in dims):raise RuntimeError('Exact-camera diagnosis is limited to tiny source geometry')
 archive=c['independent_evidence_archive']
 if not re.fullmatch('[0-9a-f]{40}',archive['hf_commit']) or not re.fullmatch('[0-9a-f]{64}',archive['sha256']) or '/resolve/'+archive['hf_commit']+'/' not in archive['url']:raise RuntimeError('Exact-camera archive is not immutable')
 def read(entry,parse=True):
  path=(root/entry['path']).resolve()
  if not path.is_relative_to(root) or sha(path)!=entry['sha256']:raise RuntimeError('Exact-camera evidence bytes differ')
  return json.loads(path.read_text()) if parse else None
 if set(c['independent_tests'])!=set(TESTS):raise RuntimeError('All four complete visual diagnostics are required')
 for original,name in TESTS.items():
  t=c['independent_tests'][original];r=read(t['result']);p=read(t['observations'])
  if r['status']!='pass' or r['test_name']!=name or r['test_version']!='1.0.0' or r.get('engine_unhealthy') or r['engine']!='isaac_sim' or r['engine_version']!='6.1.0.0' or r['asset'].split('/')[0]!=c['logical_asset']:
   raise RuntimeError('Complete independent visual test did not pass')
  if any('invalid physx transform' in x.get('message','').lower() for x in r.get('kit_logs',[])):raise RuntimeError('Invalid simulation evidence cannot receive a camera finding')
  if p['schema']!='palatial.exact-camera-visual.v1' or p['official_test']!=original or p['asset_usd_sha256']!=c['asset_usd_sha256'] or p['camera_framing_modified'] is not True or any(p[k] is not False for k in ['authored_asset_modified','acceptance_thresholds_modified','SDK_source_files_modified']):
   raise RuntimeError('Exact-camera diagnostic changed asset or thresholds')
  if p['official_source_sha256']!=c['sdk_visual_source_sha256s'][original] or p['independent_measurement_source_sha256']!=c['independent_measurement_source_sha256'] or p['effective_config']!=CONFIGS[original]:raise RuntimeError('Visual source or original thresholds differ')
  frames=p['frames']
  if not frames or (original=='normals_xz' and len(frames)!=9):raise RuntimeError('Complete camera or rotation coverage is missing')
  for frame in frames:
   size=frame['size_m'];distance=frame['distance_m']
   if len(size)!=3 or not all(math.isfinite(v) and 0<v<.01 for v in size) or frame['padding']!=1.2 or not math.isclose(distance,math.sqrt(sum(v*v for v in size))*1.2*35/36,rel_tol=1e-9):raise RuntimeError('Camera fit differs from diagnosed actual bounds')
  if any(not math.isclose(x,y,rel_tol=1e-6) for x,y in zip(frames[0]['size_m'],dims)):raise RuntimeError('Independent camera source bounds differ')
  if len(t['media'])!=len(r['media']) or {m['filename'] for m in t['media']}!={m['filename'] for m in r['media']}:raise RuntimeError('Complete diagnostic media is missing')
  for media in t['media']:read(media,False)
  m={k:v['value'] for k,v in r['metrics'].items()}
  if original=='presence' and (m['presence_passed']!=1 or m['presence_diff_ratio']<.01):raise RuntimeError('Independent presence measurement failed')
  if original=='semantic_labels_seg_labelled' and (m['semantic_labels_labelled_passed']!=1 or m['semantic_labels_on_coverage']<.005):raise RuntimeError('Independent semantic measurement failed')
  if original=='preview_surface_renders' and (m['universal_surface_silhouette_pixels']<5000 or not .98<=m['universal_surface_coverage']<=1):raise RuntimeError('Independent authored material coverage failed')
  if original=='normals_xz' and (m['normals_xz_passed']!=1 or m['normals_xz_problem_frames']!=0 or not 0<=m['normals_xz_max_dark']<=.5):raise RuntimeError('Complete normal rotation measurement failed')
 return True
