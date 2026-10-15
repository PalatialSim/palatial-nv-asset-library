"""Verify a stock-result review release without relabeling failures as passes.

The historical v1 manifest describes an earlier internal qualification. This
contract describes current immutable sources and complete stock evidence sent
for NVIDIA review; it does not grant physical acceptance or NVIDIA approval.
"""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote


SCHEMA = 'palatial.library-review-release.v2'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strict_json(data):
    return json.loads(data, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def load_review_release(root, relative='reports/current-release.json', require_ready=False):
    root = Path(root).resolve()
    def inside(path):
        value = Path(path)
        require(not value.is_absolute(), 'Release paths must be relative')
        value = (root / value).resolve()
        require(value.is_relative_to(root), 'Release path escapes the repository')
        return value
    def checked(spec, parse=True):
        data = inside(spec['path']).read_bytes()
        require(hashlib.sha256(data).hexdigest() == spec['sha256'], 'Release artifact hash differs: ' + spec['path'])
        return strict_json(data) if parse else data
    def immutable(url):
        return isinstance(url, str) and re.fullmatch(
            r'https://huggingface.co/datasets/PalatialSim/palatial-nv-asset-library/resolve/[0-9a-f]{40}/[^?#]+', url)
    manifest = strict_json(inside(relative).read_bytes())
    require(manifest['schema'] == SCHEMA, 'Unsupported review release schema')
    require(manifest['qualification_scope'] == 'unchanged_stock_results_for_NVIDIA_review', 'Unsupported qualification scope')
    require(manifest['asset_count'] == 1013 and manifest['NVIDIA_approval'] == 'pending', 'Invalid review scope or asset count')
    require(re.fullmatch('[0-9a-f]{40}', manifest['content_revision']) is not None, 'Unpinned content revision')
    report = checked(manifest['asset_report'])
    inventory = checked(manifest['standard_inventory'])
    findings = checked(manifest['known_findings'])['findings']
    gallery = checked(manifest['gallery'])
    catalog = [strict_json(line) for line in checked(manifest['catalog'], False).splitlines() if line.strip()]
    checked(manifest['parquet'], False)
    import pyarrow.parquet as parquet
    require(parquet.read_table(inside(manifest['parquet']['path'])).to_pylist() == catalog,
            'Parquet and JSONL records differ')
    repairs = checked(manifest['source_repairs'])['assets']
    invariants = checked(manifest['source_invariants'])
    corrections = checked(manifest['correction_verifications'])['assets']
    original_audit = checked(manifest['original_standard_audit'])
    original_inventory = checked(manifest['original_standard_inventory'])
    require(original_audit['artifact_verification_passed'] is True and original_audit['verified_assets'] == 1013
            and original_audit['evidence_failures'] == [], 'Original immutable evidence audit failed')
    require(original_audit['all_uploaded_files_raw_archives_and_default_plans_verified'] is True,
            'Original default-plan or archive audit incomplete')
    require(hashlib.sha256(inside(manifest['original_standard_audit']['path']).read_bytes()).hexdigest() ==
            inventory['original_all_asset_immutable_audit_sha256'], 'Inventory baseline audit differs')
    require(invariants['passed'] and invariants['assets'] == len(repairs), 'Source invariants failed')
    repairs_by_name = {r['asset']: r for r in repairs}
    proof_by_name = {r['asset']: r for r in corrections}
    original_by_name = {r['asset']: r for r in original_inventory['assets']}
    require(len(repairs_by_name) == len(repairs) == 221, 'Source repair identities missing or duplicated')
    require(len(proof_by_name) == len(corrections), 'Correction proof identities duplicated')
    require(len(original_by_name) == len(original_inventory['assets']) == 1013, 'Original identities missing or duplicated')
    require(set(r['asset'] for r in invariants['checks']) == set(repairs_by_name), 'Source invariant coverage differs')
    require(invariants['candidate_sources_changed_by_verifier'] is False and invariants['native_tests_or_thresholds_changed'] is False,
            'Source verification or benchmark modified acceptance inputs')
    page = inside('gallery/index.html').read_text(); marker = 'const assets='
    require(page.count(marker) == 1, 'Embedded gallery is missing or duplicated')
    embedded, _ = json.JSONDecoder().raw_decode(page[page.index(marker) + len(marker):])
    require(embedded == gallery, 'Embedded gallery differs from assets.json')
    assets = {a['catalog_id']: a for a in report['assets']}
    gallery_by_id = {a['id']: a for a in gallery}
    catalog_by_id = {a['catalog_id']: a for a in catalog}
    stock_by_id = {a['asset']: a for a in inventory['assets']}
    require(len(report['assets']) == len(assets) == len(gallery) == len(gallery_by_id) ==
            len(catalog) == len(catalog_by_id) == len(stock_by_id) == len(inventory['assets']) == 1013,
            'All 1,013 identities are required')
    require(set(assets) == set(gallery_by_id) == set(catalog_by_id), 'Catalog identities differ')
    require({a['logical_asset'] for a in assets.values()} == set(stock_by_id) == set(original_by_name), 'Logical identities differ')
    require(inventory['skip_or_ignore_flags'] == [] and inventory['benchmark_parameter_overrides'] == [],
            'Inventory uses benchmark exceptions')
    require(inventory['profile'] == {'id': 'Robotics-Prop', 'version': '4.0.0'} and inventory['license'] == 'cc-by-4.0',
            'Profile or license differs')
    require(inventory['SDK_versions'] == original_inventory['SDK_versions'], 'Current release changes the stock SDK revision')
    require(inventory['NVIDIA_approval'] == report['NVIDIA_approval'] == 'pending', 'Review is not NVIDIA approval')
    require(report['historical_qualification_not_reassigned'] is True, 'Historical source qualifications reassigned')
    ids = json.dumps(sorted(assets), ensure_ascii=False, separators=(',', ':')).encode()
    require(hashlib.sha256(ids).hexdigest() == manifest['catalog_ids_sha256'], 'Catalog identity hash differs')
    totals = {'pass': 0, 'fail': 0, 'skipped': 0}
    for identity, asset in assets.items():
        entry = gallery_by_id[identity]; cat = catalog_by_id[identity]
        stock = stock_by_id[asset['logical_asset']]
        name = asset['logical_asset']
        data = inside(asset['physics_path']).read_bytes()
        require(hashlib.sha256(data).hexdigest() == asset['physics_sha256'], 'Physics JSON hash differs: ' + identity)
        physics = strict_json(data)
        old_physics = checked(asset['historical_physics'])
        require(old_physics['provenance']['usd_sha256'] == original_by_name[name]['source_usd_sha256'],
                'Historical physics source differs: ' + identity)
        source = asset['usd_sha256']
        require(source == stock['source_usd_sha256'] == physics['provenance']['usd_sha256'] ==
                entry['usd_sha256'] == cat['usd_sha256'], 'Current source revisions differ: ' + identity)
        require(entry['logical_asset'] == cat['logical_asset'] == name, 'Logical source mapping differs: ' + identity)
        require(asset['static_profile_status'] == entry['static_validation_status'] == cat['static_validation_status'] == 'passed',
                'Static profile incomplete: ' + identity)
        require(cat['physics_sha256'] == asset['physics_sha256'], 'Catalog physics hash differs: ' + identity)
        require(unquote(cat['usd_download_url'].split('?')[0]) ==
                'https://huggingface.co/datasets/PalatialSim/palatial-nv-asset-library/resolve/' + manifest['content_revision'] + '/' + asset['usd_path'],
                'Legacy source download is stale: ' + identity)
        require(cat['source_revision'] == manifest['content_revision'], 'Catalog content pin differs: ' + identity)
        require(entry['moving_joints'] == physics['validation']['articulation']['moving_joints'], 'Joint metadata differs: ' + identity)
        require(entry['mass_kg'] == physics['asset']['total_mass'] == cat['total_mass_kg'], 'Mass metadata differs: ' + identity)
        require(entry['bounds'] == physics['asset']['bounds'], 'Bounds metadata differs: ' + identity)
        native = physics['validation']['runtime']
        counts = stock['test_result_counts']
        require(set(counts) <= set(totals) and sum(counts.values()) > 0 and
                all(type(v) is int and v >= 0 for v in counts.values()), 'Invalid or empty stock results: ' + identity)
        for status, value in counts.items():
            totals[status] += value
        failed = counts.get('fail', 0)
        require(stock['requires_review'] is bool(failed) and native['requires_NVIDIA_review'] is bool(failed),
                'Review status differs from raw results: ' + identity)
        status = 'completed_with_failed_tests' if failed else 'passed'
        require(native['status'] == entry['native_validation_status'] == cat['runtime_status'] == status,
                'A raw failure must remain a failure: ' + identity)
        require(native['usd_sha256'] == source and native['result_counts'] == counts, 'Runtime source or counts differ: ' + identity)
        require(asset['result_counts'] == entry['stock_result_counts'] == counts and
                json.loads(cat['stock_result_counts_json']) == counts, 'Catalog or report counts differ: ' + identity)
        require(native['stock_provider_only'] is True and native['benchmark_parameter_overrides'] == [] and
                native['skip_or_ignore_flags'] == [] and native['declared_test_coverage_verified'] is True,
                'Default stock coverage is incomplete: ' + identity)
        require(native['configured_engines'] == ['isaac_sim', 'isaac_sim_newton'], 'Configured engine coverage differs: ' + identity)
        require(native['NVIDIA_approval'] == 'pending', 'A submission is not NVIDIA approval: ' + identity)
        for key in ['package_url', 'raw_archive_url', 'raw_manifest_url']:
            require(immutable(stock[key]), 'Unpinned or incorrect artifact URL: ' + identity)
            require(native[key] == stock[key], 'Physics evidence URL differs: ' + identity)
        for key in ['benchmark_sidecar_sha256', 'raw_archive_sha256', 'default_stock_plan_sha256']:
            require(re.fullmatch('[0-9a-f]{64}', stock[key]) is not None, 'Missing artifact hash: ' + identity)
            require(native[key] == stock[key], 'Physics evidence hash differs: ' + identity)
        require(entry['package_manifest_url'] == cat['package_manifest_url'] == stock['package_url'], 'Package identity differs: ' + identity)
        require(entry['package_status'] == cat['package_status'] == 'completed', 'Package publication incomplete: ' + identity)
        require(cat['package_file_count'] == stock['package_file_count'] > 0 and cat['package_bytes'] == stock['package_bytes'] > 0,
                'Package counts differ: ' + identity)
        if failed:
            require(stock['requires_review'] is True and native['requires_NVIDIA_review'] is True,
                    'Failed results need explicit review: ' + identity)
            finding = findings[asset['logical_asset']]
            require(finding['source_usd_sha256'] == source and finding['package_url'] == stock['package_url'] and
                    len(finding['failed_tests']) == failed and all(r['status'] == 'fail' for r in finding['failed_tests']),
                    'Failure evidence differs: ' + identity)
            require(finding['raw_archive_url'] == stock['raw_archive_url'], 'Failure raw evidence differs: ' + identity)
        else:
            require(asset['logical_asset'] not in findings, 'A passing asset has stale active failure evidence: ' + identity)
        historical = physics['validation'].get('historical_runtime')
        if historical and historical['usd_sha256'] != source:
            require(historical['applies_to_current_source'] is False,
                    'Historical evidence cannot qualify a changed source: ' + identity)
        corrected = name in proof_by_name
        require(asset['source_corrected'] is corrected, 'Correction flag differs: ' + identity)
        if corrected:
            proof = proof_by_name[name]; repair = repairs_by_name[name]
            require(source == proof['source_usd_sha256'] == repair['candidate_usd_sha256'], 'Corrected USD proof differs: ' + identity)
            require(proof['original_usd_sha256'] == repair['original_usd_sha256'] == original_by_name[name]['source_usd_sha256'],
                    'Original source lineage differs: ' + identity)
            require(proof['package_url'] == stock['package_url'] and proof['sidecar_sha256'] == stock['benchmark_sidecar_sha256'] and
                    proof['archive_url'] == stock['raw_archive_url'] and proof['manifest_url'] == stock['raw_manifest_url'],
                    'Corrected immutable evidence differs: ' + identity)
            for flag in ['every_package_file_immutable_hash_verified', 'every_raw_archive_member_independently_hashed',
                         'default_stock_plan_and_declared_counts_verified', 'stock_static_profile_and_no_blocking_failures_verified',
                         'no_result_or_threshold_modification']:
                require(proof[flag] is True, 'Incomplete corrected-source evidence: ' + identity + '/' + flag)
            declared = proof['exact_declared_test_engine_pair_verification']
            require(declared['all_actual_declared_pairs_represented'] is True and declared['stock_provider_only'] is True and
                    declared['parameter_overrides'] == [] and declared['discovery_errors'] == [] and
                    declared['declared_test_engine_pairs'] == sum(counts.values()), 'Corrected test coverage differs: ' + identity)
            require(proof['result_counts'] == counts and len(proof['failed_results']) == failed, 'Corrected result counts differ: ' + identity)
            require(not proof['new_failing_test_engine_pairs'], 'A new failed pair needs causal diagnosis before publication: ' + identity)
            require(historical is not None and historical['applies_to_current_source'] is False and
                    historical['usd_sha256'] == repair['original_usd_sha256'], 'Changed-source historical evidence was relabeled: ' + identity)
            media = entry['render_provenance']
            require(media['usd_sha256'] == source and media['package_url'] == stock['package_url'],
                    'Current thumbnail source differs: ' + identity)
            require(cat['render_image_path'] == 'gallery/' + entry['render_url'], 'Thumbnail catalog paths differ: ' + identity)
            checked({'path': cat['render_image_path'], 'sha256': media['image_sha256']}, parse=False)
        else:
            require(source == original_by_name[name]['source_usd_sha256'] and
                    all(stock.get(key) == value for key, value in original_by_name[name].items()) and
                    stock['asset_version'] == original_inventory['asset_version'],
                    'Unchanged package differs from verified original: ' + identity)
    require({k: v for k, v in totals.items() if v} == inventory['test_result_totals'], 'Aggregate result counts differ')
    require(len(findings) == inventory['assets_with_failed_tests'], 'Finding asset counts differ')
    require(len(proof_by_name) == inventory['corrected_source_count_verified'] == report['source_corrections_verified'],
            'Verified correction counts differ')
    if require_ready:
        require(inventory['release_complete'] is True and inventory['local_preview_only'] is False,
                'A preparation snapshot cannot be promoted')
        require(inventory['corrected_source_count_verified'] == inventory['corrected_source_count_expected'] == len(repairs),
                'Every corrected source needs complete stock evidence')
        require(report['all_current_immutable_artifacts_verified'] is True,
                'Immutable publication audit is incomplete')
        require(set(proof_by_name) == set(repairs_by_name), 'Every corrected source requires exact evidence')
        require('legacy_content_publication' in manifest, 'Legacy source content publication is not verified')
        require('legacy_source_aliases' in manifest, 'All legacy source aliases must be verified')
        aliases = checked(manifest['legacy_source_aliases'])
        require(aliases['passed'] is True and aliases['commit'] == manifest['content_revision'] and
                aliases['source_assets'] == 1013 and aliases['corrected_sources_included'] is True and
                aliases['every_legacy_source_and_dependency_verified'] is True and aliases['errors'] == [],
                'Legacy source alias verification is incomplete')
        require(aliases['source_usd_sha256'] == {name: s['source_usd_sha256'] for name, s in stock_by_id.items()},
                'Legacy source alias hashes differ from current stock packages')
        publication = checked(manifest['legacy_content_publication'])
        require(publication['commit'] == manifest['content_revision'] and publication['every_written_file_immutable_hash_verified'] is True,
                'Legacy source publication verification differs')
        published = {f['path']: f['sha256'] for f in publication['files']}
        require(len(published) == len(publication['files']), 'Published content paths duplicated')
        for asset in assets.values():
            require(published.get(asset['physics_path']) == asset['physics_sha256'],
                    'Published legacy physics differs: ' + asset['catalog_id'])
            if asset['source_corrected']:
                require(published.get(asset['usd_path']) == asset['usd_sha256'],
                        'Published legacy USD differs: ' + asset['catalog_id'])
                entry = gallery_by_id[asset['catalog_id']]
                require(published.get('gallery/' + entry['render_url']) == entry['render_provenance']['image_sha256'],
                        'Published current thumbnail differs: ' + asset['catalog_id'])
    return manifest, report, gallery_by_id
