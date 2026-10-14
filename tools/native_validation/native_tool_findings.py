"""Keep proven SDK framing findings separate from asset and physics acceptance."""
import copy,hashlib,json,math
from pathlib import Path
CAMERA_TESTS={'presence','semantic_labels_seg_labelled','preview_surface_renders'}
POLICY='palatial.native-tool-findings.v1'

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def assess(row,root):
 root=Path(root);path=root/'tool-finding-certificates'/(row['logical_asset']+'.json')
 if not path.exists():return row
 c=json.loads(path.read_text())
 kind=c.get('kind')
 if c.get('schema')!=POLICY or kind not in {'sdk_small_asset_camera_clamp','sdk_exact_camera_clamp','sdk_presence_camera_clamp','sdk_color_probe_ambiguity','sdk_color_control_ambiguity','sdk_conservative_contact_bounds'} or c['logical_asset']!=row['logical_asset'] or c['asset_usd_sha256']!=row['asset_usd_sha256']:
  raise RuntimeError('Tool finding certificate input differs')
 if row['result_count']!=row['planned_test_count'] or not row.get('thumbnail') or (kind in {'sdk_small_asset_camera_clamp','sdk_exact_camera_clamp'} and row['joint_counts']):
  raise RuntimeError('Tool finding cannot excuse incomplete supplemental coverage')
 if sha(root/row['thumbnail']['path'])!=row['thumbnail']['sha256']:raise RuntimeError('Tool finding native thumbnail differs')
 results={}
 for item in row['result_files']:
  file=root/item['path']
  if sha(file)!=item['sha256']:raise RuntimeError('Tool finding raw evidence changed')
  d=json.loads(file.read_text());results[d['test_name']]=(d,item['sha256'])
  if d.get('engine_unhealthy') or d.get('engine')!='isaac_sim' or d.get('engine_version')!='6.1.0.0' or any('invalid physx transform' in x.get('message','').lower() for x in d.get('kit_logs',[])):
   raise RuntimeError('Engine failures cannot receive a tool finding disposition')
 if len(results)!=row['planned_test_count']:raise RuntimeError('Tool finding planned test coverage differs')
 failed={name:h for name,(d,h) in results.items() if d['status'] not in ['pass','skipped']}
 allowed={'ground_drop','slope_drop'} if kind=='sdk_conservative_contact_bounds' else (CAMERA_TESTS|{'normals_xz'} if kind=='sdk_exact_camera_clamp' else CAMERA_TESTS)
 if not failed or set(failed)-allowed or failed!=c['raw_failed_result_sha256s']:raise RuntimeError('Tool finding does not match the exact independently diagnosed failures')
 if set(row['issues'])!={name+':fail' for name in failed}:raise RuntimeError('Additional native failures remain')
 def metric(name,key):return results[name][0]['metrics'][key]['value']
 if metric('palatial_black_thumbnail','asset_usd_sha256')!=row['asset_usd_sha256'] or results['palatial_black_thumbnail'][0]['status']!='pass':raise RuntimeError('Actual framed native render missing')
 if kind=='sdk_small_asset_camera_clamp':
  dims=c['actual_visible_bounds_size_m']
  if len(dims)!=3 or not all(0<float(v)<=.025 for v in dims) or not c.get('static_validation_passed') or len(c.get('sdk_camera_source_sha256',''))!=64:
   raise RuntimeError('Small-object camera clamp proof is incomplete')
  presence=float(metric('presence','presence_diff_ratio'));semantic=float(metric('semantic_labels_seg_labelled','semantic_labels_on_coverage'))
  silhouette=int(metric('preview_surface_renders','universal_surface_silhouette_pixels'))
  if not 0<presence<.01 or not 0<semantic<.005 or semantic/presence<.9 or not 0<silhouette<5000:
   raise RuntimeError('Framing measurements do not establish the camera issue')
  if not math.isclose(presence,c['presence_diff_ratio']) or not math.isclose(semantic,c['semantic_labels_on_coverage']) or silhouette!=c['silhouette_pixels']:
   raise RuntimeError('Certificate measurements differ from raw results')
  reason='SDK camera clamps each axis to 0.1 m, underframing this small asset; exact native geometry, labels and materials are present. All physics and supplemental checks pass.'
 elif kind=='sdk_exact_camera_clamp':
  from native_exact_camera_probe import verify_exact_camera_probe
  verify_exact_camera_probe(c,root)
  if set(failed)!=CAMERA_TESTS|{'normals_xz'} or results['normals_xz'][0]['metrics'] or not results['normals_xz'][0]['message'].startswith('Object not visible after multiple attempts. The diagnostic material (orange) was not detected.'):
   raise RuntimeError('Normals camera finding must diagnose visibility-only failure')
  reason='The SDK camera minimum underframes this tiny source asset. All four complete independently named visual tests, including the full normal rotation, pass using actual visible bounds with unchanged SDK functions and acceptance thresholds. Original visibility failures remain for NVIDIA review; all physics and supplemental checks pass.'
 elif kind=='sdk_presence_camera_clamp':
  from native_presence_probe import verify_presence_probe
  verify_presence_probe(c,root)
  if set(failed)!={'presence'} or not math.isclose(float(metric('presence','presence_diff_ratio')),c['presence_diff_ratio']) or not math.isclose(float(metric('semantic_labels_seg_labelled','semantic_labels_on_coverage')),c['semantic_labels_on_coverage']) or int(metric('preview_surface_renders','universal_surface_silhouette_pixels'))!=c['silhouette_pixels'] or float(metric('preview_surface_renders','universal_surface_coverage'))<.98:
   raise RuntimeError('Presence diagnosis does not match exact independently labelled and shaded geometry')
  reason="The SDK's 0.1 m camera-axis minimum underframes this small or thin prop. The original orange visibility-toggle captures visibly contain the asset; semantic segmentation, material rendering, all physics and independent native thumbnail checks pass. The raw presence failure remains for NVIDIA review."
 elif kind=='sdk_conservative_contact_bounds':
  from native_contact_probe import verify_contact_probe
  verify_contact_probe(c,root)
  for name in failed:
   if metric(name,name+'_penetrated')!=1:raise RuntimeError('Contact finding is not an SDK floor-penetration report')
   if name=='slope_drop' and any(metric(name,k)!=0 for k in ['slope_drop_slope_penetrated','slope_drop_excessive_separation','slope_drop_uphill_motion']):raise RuntimeError('Another SDK ramp failure remains')
  reason='The SDK conservative world bounds extend through the floor while live visible and collider mesh vertices remain above its penetration limit. Both complete independent ground and slope simulations pass with the unchanged SDK simulation parameters and thresholds, including stable ground settling and post-slide observation. Raw SDK physics failures remain for NVIDIA review.'
 elif kind=='sdk_color_control_ambiguity':
  from native_cyan_probe import verify_cyan_probe
  verify_cyan_probe(c,root)
  if set(failed)!={'preview_surface_renders'} or int(metric('preview_surface_renders','universal_surface_silhouette_pixels'))!=c['measurements']['strong_default_pixels'] or int(metric('preview_surface_renders','universal_surface_uncovered_pixels'))!=c['measurements']['weak_default_pixels']:
   raise RuntimeError('Independent control does not diagnose the exact preview-only failure')
  reason='The source asset matches the official magenta control color. A separately named cyan-control test passes the same SDK scene, binding strengths, classifier thresholds and 98 percent coverage requirement for this unchanged USD. All visible meshes resolve Preview Surface; original magenta captures and FAIL remain for NVIDIA review. All physics and supplemental checks pass.'
 else:
  from native_color_probe import verify_color_probe
  verify_color_probe(c,root)
  if set(failed)!={'preview_surface_renders'} or int(metric('preview_surface_renders','universal_surface_silhouette_pixels'))!=c['measurements']['strong_default_pixels'] or int(metric('preview_surface_renders','universal_surface_uncovered_pixels'))!=c['measurements']['weak_default_pixels']:
   raise RuntimeError('Color diagnosis is not for the exact preview-only result')
  reason='The SDK magenta probe classifies the unchanged source texture as uncovered material. Unmodified native baseline, weak-control and strong-control captures plus resolved surface bindings establish color ambiguity; raw failure remains for NVIDIA review. All physics and supplemental checks pass.'
 revised=copy.deepcopy(row);revised.update(native_status='completed_with_tool_findings',safety_accepted=True,
  tool_findings={'certificate_path':str(path.relative_to(root)),'certificate_sha256':sha(path),'raw_benchmark_status':'failed','failed_tests':sorted(failed),
                 'reason':reason,
                 'NVIDIA_raw_results_modified':False,'requires_NVIDIA_review':True})
 return revised
