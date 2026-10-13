"""Verify the current release metadata and its immutable artifact hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strict_json(data):
    return json.loads(data,parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def load_current_release(root, relative='reports/current-release.json', require_ready=False):
    root=Path(root).resolve()
    def inside(path):
        path=Path(path)
        require(not path.is_absolute(),'Release paths must be relative')
        resolved=(root/path).resolve()
        require(resolved.is_relative_to(root),'Release path escapes repository: '+str(path))
        return resolved
    def checked(spec, parse=True):
        data=inside(spec['path']).read_bytes()
        require(hashlib.sha256(data).hexdigest()==spec['sha256'],'Artifact SHA256 mismatch: '+spec['path'])
        return strict_json(data) if parse else data
    manifest=strict_json(inside(relative).read_bytes())
    require(manifest.get('schema')=='palatial.library-release.v1','Unsupported release manifest schema')
    report=checked(manifest['asset_report'])
    gallery=checked(manifest['gallery'])
    catalog=[strict_json(line) for line in checked(manifest['catalog'],False).splitlines() if line.strip()]
    checked(manifest['parquet'],False)
    assets=report['assets']; asset_ids=[asset['catalog_id'] for asset in assets]
    gallery_ids=[row['id'] for row in gallery];catalog_ids=[row['catalog_id'] for row in catalog]
    n=manifest['asset_count']
    require(n==1013 and len(asset_ids)==n and len(set(asset_ids))==n,'Release asset count or identity mismatch')
    require(len(gallery_ids)==n and len(set(gallery_ids))==n,'Gallery count or identity mismatch')
    require(len(catalog_ids)==n and len(set(catalog_ids))==n,'Catalog count or identity mismatch')
    require(set(asset_ids)==set(gallery_ids)==set(catalog_ids),'Evidence/gallery/catalog asset sets differ')
    canonical=json.dumps(sorted(asset_ids),ensure_ascii=False,separators=(',',':')).encode()
    require(hashlib.sha256(canonical).hexdigest()==manifest['catalog_ids_sha256'],'Release catalog identities changed')
    page=inside('gallery/index.html').read_text();marker='const assets='
    require(page.count(marker)==1,'Embedded catalog missing or duplicated')
    embedded,_=json.JSONDecoder().raw_decode(page[page.index(marker)+len(marker):])
    require(embedded==gallery,'Inline gallery differs from assets.json')
    gallery_by_id={row['id']:row for row in gallery}; catalog_by_id={row['catalog_id']:row for row in catalog}
    for asset in assets:
        rid=asset['catalog_id'];row=gallery_by_id[rid];cat=catalog_by_id[rid]
        data=inside(asset['physics_path']).read_bytes()
        require(hashlib.sha256(data).hexdigest()==asset['repaired_physics_sha256'],'Physics SHA256 mismatch: '+rid)
        physics=strict_json(data)
        require(asset['usd_sha256']==physics['provenance']['usd_sha256']==row['usd_sha256']==cat['usd_sha256'],
                'USD evidence revisions differ: '+rid)
        require(row['moving_joints']==physics['validation']['articulation']['moving_joints'],'Joint metadata differs: '+rid)
        require(row['mass_kg']==physics['asset']['total_mass']==cat['total_mass_kg'],'Mass metadata differs: '+rid)
        require(row['bounds']==physics['asset']['bounds'],'Bounds metadata differs: '+rid)
        static=asset['validation'];native=asset['native'];package=asset['package']
        require(static['status']=='passed' and static['profile']=='Robotics-Prop' and static['version']=='4.0.0',
                'Static acceptance missing: '+rid)
        require(static['usd_sha256']==asset['usd_sha256'],'Static receipt revision differs: '+rid)
        require(row['native_validation_status']==cat['runtime_status']==native['status'],'Native status differs: '+rid)
        require(row['package_status']==cat['package_status']==package['status'],'Package status differs: '+rid)
        if require_ready:
            review=native['status']=='completed_with_tool_findings'
            require(native['status'] in {'passed','completed_with_tool_findings'} and native.get('supplemental_accepted') is True,'Native acceptance missing: '+rid)
            require(native.get('usd_sha256')==asset['usd_sha256'],'Native receipt revision differs: '+rid)
            require(native.get('result_count',0)>0 and native.get('result_count')==native.get('planned_test_count'),
                    'Native coverage incomplete: '+rid)
            archive=native.get('evidence_archive',{})
            require(re.fullmatch('[0-9a-f]{40}',archive.get('hf_commit','')) is not None and
                    re.fullmatch('[0-9a-f]{64}',archive.get('sha256','')) is not None and
                    '/resolve/'+archive['hf_commit']+'/' in archive.get('url',''),'Durable native archive missing: '+rid)
            if review:
                finding=native['tool_findings'];certificate=checked({'path':finding['release_certificate'],'sha256':finding['certificate_sha256']})
                require(certificate['schema']=='palatial.native-tool-findings.v1' and certificate['kind'] in {'sdk_small_asset_camera_clamp','sdk_color_probe_ambiguity'},
                        'Unsupported tool finding disposition: '+rid)
                require(certificate['asset_usd_sha256']==asset['usd_sha256'] and certificate['logical_asset']==asset['logical_asset'],
                        'Tool finding certificate asset differs: '+rid)
                require(finding['NVIDIA_raw_results_modified'] is False and finding['raw_benchmark_status']=='failed' and
                        finding['requires_NVIDIA_review'] is True and native['failed']==len(finding['failed_tests'])>0,
                        'Raw benchmark failures must remain disclosed: '+rid)
                require(set(finding['failed_tests'])==set(certificate['raw_failed_result_sha256s']) and
                        set(finding['failed_tests'])<= {'presence','semantic_labels_seg_labelled','preview_surface_renders'},
                        'An asset or physics failure cannot be excused: '+rid)
                if certificate['kind']=='sdk_small_asset_camera_clamp':
                    require(all(0<v<=0.025 for v in certificate['actual_visible_bounds_size_m']) and certificate['static_validation_passed'] is True,
                            'Small-object camera proof is incomplete: '+rid)
                    require(0<certificate['presence_diff_ratio']<0.01 and 0<certificate['semantic_labels_on_coverage']<0.005 and
                            certificate['semantic_labels_on_coverage']/certificate['presence_diff_ratio']>=0.9 and 0<certificate['silhouette_pixels']<5000,
                            'Camera proof measurements do not support the finding: '+rid)
                else:
                    require(set(finding['failed_tests'])=={'preview_surface_renders'} and certificate['static_validation_passed'] is True and
                            certificate['all_visible_meshes_resolve_preview_surface'] is True and certificate['manual_native_capture_review'] is True and
                            certificate['benchmark_config_modified'] is False,'Color diagnosis cannot excuse a missing surface or another failure: '+rid)
                    require(set(certificate['release_captures'])=={'baseline','weak','strong'},'Color diagnostic capture coverage differs: '+rid)
                    for capture in certificate['release_captures'].values():checked(capture,False)
                    m=certificate['measurements']
                    require(m['strong_default_pixels']>=5000 and m['weak_default_pixels']>0 and
                            abs(m['baseline_default_pixels']-m['weak_default_pixels'])/m['weak_default_pixels']<=0.05 and
                            m['baseline_weak_overlap_ratio']>=0.9 and m['strong_footprint_retained_ratio']>=0.98 and
                            m['stricter_diagnostic_coverage']>=0.98,'Color evidence does not establish probe ambiguity: '+rid)
            else:require(native.get('failed',1)==0,'Native failures remain: '+rid)
            if row['moving_joints']:
                require(native.get('joint_status')=='passed' and native.get('joints_failed',1)==0 and
                        native.get('joints_passed')==native.get('joints_total'), 'Joint acceptance incomplete: '+rid)
            require(package['status']=='completed' and package.get('usd_sha256')==asset['usd_sha256'],
                    'Package acceptance missing: '+rid)
            require(re.search(r'/resolve/[0-9a-f]{40}/',package.get('manifest_url','')) is not None,
                    'Package URL must pin an immutable commit: '+rid)
    return manifest,report,gallery_by_id


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('root',type=Path)
    parser.add_argument('--release-manifest',default='reports/current-release.json')
    parser.add_argument('--require-ready',action='store_true')
    args=parser.parse_args()
    manifest,report,_=load_current_release(args.root,args.release_manifest,args.require_ready)
    print(json.dumps({'release_id':manifest['release_id'],'assets':len(report['assets']),
                      'metadata_hashes_and_catalog_parity':True,'ready_gate_required':args.require_ready}))
