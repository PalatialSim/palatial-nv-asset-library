"""Verify full exact-geometry contact evidence; never changes SDK raw results."""
import hashlib,json,math,re
from pathlib import Path
TESTS={'ground_drop':'palatial_exact_geometry_ground_drop','slope_drop':'palatial_exact_geometry_slope_drop'}
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify_contact_probe(c,root):
 root=Path(root)
 if c.get('static_validation_passed') is not True or c.get('manual_native_capture_review') is not True or c.get('simulation_or_acceptance_thresholds_modified') is not False:
  raise RuntimeError('Contact proof is incomplete')
 archive=c['independent_evidence_archive']
 if not re.fullmatch('[0-9a-f]{40}',archive['hf_commit']) or not re.fullmatch('[0-9a-f]{64}',archive['sha256']) or '/resolve/'+archive['hf_commit']+'/' not in archive['url']:
  raise RuntimeError('Contact diagnostic archive is not immutable')
 if set(c['independent_tests'])!=set(TESTS):raise RuntimeError('Both complete contact tests are required')
 summaries={}
 for official,name in TESTS.items():
  item=c['independent_tests'][official]
  def load(key):
   entry=item[key];path=root/entry['path']
   if not path.resolve().is_relative_to(root.resolve()) or sha(path)!=entry['sha256']:raise RuntimeError('Independent contact evidence bytes differ')
   return json.loads(path.read_text())
  result=load('result');proof=load('observations')
  if result['test_name']!=name or result['status']!='pass' or result.get('engine_unhealthy') or result.get('engine')!='isaac_sim' or result.get('engine_version')!='6.1.0.0':raise RuntimeError('Exact contact test did not pass in the required engine')
  if result['asset'].split('/')[0]!=c['logical_asset'] or proof['schema']!='palatial.exact-geometry-contact.v1' or proof['asset_usd_sha256']!=c['asset_usd_sha256'] or proof['official_test']!=official:
   raise RuntimeError('Independent contact input differs')
  if proof['simulation_modified'] is not False or proof['thresholds_modified'] is not False or proof['official_source_sha256']!=c['sdk_contact_source_sha256s'][official] or proof['independent_measurement_source_sha256']!=c['independent_measurement_source_sha256']:
   raise RuntimeError('Contact measurement changed simulation or thresholds')
  defaults=proof['official_config_defaults']
  if any(proof['effective_config'].get(k)!=v for k,v in defaults.items()) or defaults['physics_fps']!=240 or defaults['simulation_seconds']!=10 or defaults['floor_margin']!=.1:
   raise RuntimeError('Exact contact configuration differs from the original SDK defaults')
  coverage=proof['mesh_coverage'];normalized=[{**m,'path':m['path'].replace('/World/AssetRoot/Asset',c['source_default_prim'])} for m in coverage]
  if sorted(normalized,key=lambda m:m['path'])!=c['expected_mesh_coverage'] or not any(m['collision'] for m in coverage) or not any(m['visible'] for m in coverage):raise RuntimeError('Exact contact mesh coverage is incomplete')
  samples=proof['samples']
  minimum_samples=720 if official=='slope_drop' else 600
  if len(samples)<minimum_samples:raise RuntimeError('Full contact and settling observations are missing')
  for sample in samples:
   values=[*sample['exact_min'],*sample['exact_max'],sample['sdk_bbox_min_z'],sample['exact_visible_min_z'],sample['collider_vertex_min_z']]
   if not all(math.isfinite(v) for v in values) or any(lo>hi for lo,hi in zip(sample['exact_min'],sample['exact_max'])):raise RuntimeError('Nonfinite or inconsistent contact geometry')
  exact_min=min(s['exact_min'][2] for s in samples);sdk_min=min(s['sdk_bbox_min_z'] for s in samples)
  if exact_min<-.01:raise RuntimeError('Exact geometry penetrates more than the independent 1 cm review limit')
  metrics={k:v['value'] for k,v in result['metrics'].items()}
  if metrics[official+'_passed']!=1 or metrics[official+'_penetrated']!=0 or metrics['exact_contact_samples']!=len(samples):raise RuntimeError('Contact result contradicts its observations')
  if official=='ground_drop':
   if metrics['ground_drop_touched']!=1 or metrics['ground_drop_stable']!=1 or metrics['ground_drop_rest_time']<2:raise RuntimeError('Complete stable ground settling was not observed')
  else:
   if any(metrics.get(k)!=v for k,v in {'slope_drop_contact_detected':1,'slope_drop_horiz_detected':1,'slope_drop_slope_penetrated':0,'slope_drop_excessive_separation':0,'slope_drop_uphill_motion':0,'slope_drop_separation_frames':0}.items()):raise RuntimeError('Independent ramp motion remains unsafe')
  if official in c['raw_failed_result_sha256s'] and sdk_min>=-.1:raise RuntimeError('Conservative bounds do not reproduce the reported floor failure')
  summaries[official]={'samples':len(samples),'minimum_exact_geometry_z_m':exact_min,'minimum_SDK_bounds_z_m':sdk_min}
 if summaries!=c['contact_measurements']:raise RuntimeError('Contact certificate measurements differ')
 return summaries
