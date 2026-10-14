"""Verify separately named cyan control evidence; preserve official magenta failures."""
import hashlib,json,math,re
from pathlib import Path
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify_cyan_probe(c,root):
 root=Path(root)
 if any(c.get(k) is not True for k in ['static_validation_passed','all_visible_meshes_resolve_preview_surface','manual_native_capture_review']) or c.get('benchmark_config_modified') is not False:
  raise RuntimeError('Cyan material proof is incomplete')
 archive=c['independent_evidence_archive']
 if not re.fullmatch('[0-9a-f]{40}',archive['hf_commit']) or not re.fullmatch('[0-9a-f]{64}',archive['sha256']) or '/resolve/'+archive['hf_commit']+'/' not in archive['url']:raise RuntimeError('Cyan archive is not immutable')
 def read(entry,json_file=True):
  path=root/entry['path']
  if not path.resolve().is_relative_to(root.resolve()) or sha(path)!=entry['sha256']:raise RuntimeError('Cyan diagnostic evidence bytes differ')
  return json.loads(path.read_text()) if json_file else None
 for field in ['captures','cyan_captures']:
  if set(c[field])!={'baseline','weak','strong'}:raise RuntimeError('Complete material controls are missing')
  for entry in c[field].values():read(entry,False)
 tests=c['independent_tests']
 if set(tests)!={'cyan_coverage'}:raise RuntimeError('Cyan test coverage differs')
 r=read(tests['cyan_coverage']['result']);p=read(tests['cyan_coverage']['observations'])
 if r['status']!='pass' or r['test_name']!='palatial_cyan_preview_surface_coverage' or r.get('engine_unhealthy') or r['engine']!='isaac_sim' or r['engine_version']!='6.1.0.0' or r['asset'].split('/')[0]!=c['logical_asset']:raise RuntimeError('Independent cyan material test did not pass')
 if p['schema']!='palatial.cyan-material-probe.v1' or p['asset_usd_sha256']!=c['asset_usd_sha256'] or any(p[k] is not False for k in ['SDK_source_files_modified','acceptance_thresholds_modified','authored_asset_modified']):raise RuntimeError('Cyan diagnostic changed source assets or thresholds')
 if p['control_color']!=[0,1,1] or p['control_channels']!=[1,2] or p['official_source_sha256']!=c['sdk_surface_source_sha256'] or p['independent_measurement_source_sha256']!=c['independent_measurement_source_sha256']:raise RuntimeError('Independent control source differs')
 cfg=p['official_config_defaults']
 if p['effective_config']!=cfg or cfg['min_material_coverage']!=.98 or cfg['min_silhouette_pixels']!=5000 or cfg['mask_dominance_ratio']!=1.5 or cfg['mask_dominance_floor']!=.2:raise RuntimeError('Independent material coverage thresholds differ')
 m={k:v['value'] for k,v in r['metrics'].items()};v=c['cyan_measurements']
 strong=m['universal_surface_silhouette_pixels'];weak=m['universal_surface_uncovered_pixels'];coverage=m['universal_surface_coverage']
 if strong<5000 or weak<0 or not .98<=coverage<=1 or not math.isclose(coverage,1-weak/strong) or v!={'silhouette_pixels':strong,'uncovered_pixels':weak,'coverage':coverage}:raise RuntimeError('Cyan controls do not establish complete authored coverage')
 if c['measurements']['weak_default_pixels']<=0 or c['measurements']['strong_default_pixels']<5000:raise RuntimeError('Original magenta result does not establish the diagnosed ambiguity')
 return v
