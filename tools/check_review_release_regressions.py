"""Exercise review metadata semantics using real completed runs in local copies.

No SDK process, public artifact, original source, or result sidecar is changed.
Negative cases deliberately rebind metadata hashes so they test semantic gates,
not merely the presence of a checksum.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import time

import pyarrow as pa
import pyarrow.parquet as pq

spec = importlib.util.spec_from_file_location('review_contract', Path(__file__).with_name('review_release_manifest.py'))
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def load(path):
    return json.loads(path.read_bytes())


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def write_catalog(path, values):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in values))
    pq.write_table(pa.Table.from_pylist(values), path.with_suffix('.parquet'), compression='zstd')


def embedded(root):
    path = root / 'gallery/index.html'; text = path.read_text()
    start = text.index('const assets=') + len('const assets=')
    _, end = json.JSONDecoder().raw_decode(text[start:])
    path.write_text(text[:start] + json.dumps(load(root / 'gallery/assets.json'), ensure_ascii=False) + text[start+end:])


def rehash(root):
    path = root / 'reports/current-release.json'; manifest = load(path)
    report_path = root / manifest['asset_report']['path']; report = load(report_path)
    hashes = {}
    for row in report['assets']:
        value = hashlib.sha256((root / row['physics_path']).read_bytes()).hexdigest()
        row['physics_sha256'] = value; hashes[row['catalog_id']] = value
    save(report_path, report)
    cat_path = root / 'data/catalog.jsonl'; cats = records(cat_path)
    for row in cats:
        row['physics_sha256'] = hashes[row['catalog_id']]
    write_catalog(cat_path, cats)
    for item in manifest.values():
        if isinstance(item, dict) and 'path' in item and 'sha256' in item:
            item['sha256'] = hashlib.sha256((root / item['path']).read_bytes()).hexdigest()
    save(path, manifest)


def mutate_json(root, relative, callback):
    path = root / relative; value = load(path); callback(value); save(path, value)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('assembly', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if load(args.assembly / 'reports/current-release.json')['schema'] != contract.SCHEMA:
        print(json.dumps({'review_v2_active': False, 'historical_policy_unchanged': True}))
        return
    manifest, report, _ = contract.load_review_release(args.assembly)
    inventory_path = manifest['standard_inventory']['path']
    proofs_path = manifest['correction_verifications']['path']
    corrected = [a for a in report['assets'] if a['source_corrected']]
    assert corrected, 'At least one corrected-source receipt is required for these integration checks'
    failing = next((a for a in corrected if a['result_counts'].get('fail', 0)), corrected[0])
    results = [{'name': 'actual_1013_identity_metadata_and_completed_corrected_subset', 'passed': True}]
    if failing['result_counts'].get('fail', 0):
        results.append({'name': 'real_raw_failure_retained',
            'passed': failing['runtime_status'] == 'completed_with_failed_tests'})
    def check(name, change, message, ready=False, do_rehash=True):
        with tempfile.TemporaryDirectory(prefix='source-quality-contract-') as directory:
            dst = Path(directory)
            # Copy only metadata consumed by this verifier, never source USDs,
            # images, native artifacts or mutable production working files.
            for p in args.assembly.rglob('*'):
                if p.is_file() and p.suffix in {'.json', '.jsonl', '.parquet', '.html', '.png'}:
                    out = dst / p.relative_to(args.assembly); out.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(p, out)
            change(dst)
            if do_rehash:
                rehash(dst)
            try:
                contract.load_review_release(dst, require_ready=ready)
            except (ValueError, KeyError) as exc:
                assert message in str(exc), (name, str(exc), message)
                results.append({'name': name, 'passed': True, 'rejection': str(exc)})
            else:
                raise AssertionError('Invalid review metadata accepted: ' + name)
    check('incomplete_preview_cannot_be_ready', lambda r: mutate_json(r, inventory_path,
        lambda d: d.update(release_complete=False, local_preview_only=True)), 'preparation snapshot', ready=True)
    if failing['result_counts'].get('fail', 0):
        check('raw_fail_cannot_be_relabelled_passed', lambda r: mutate_json(r, failing['physics_path'],
            lambda d: d['validation']['runtime'].update(status='passed')), 'raw failure must remain')
    check('changed_source_cannot_reuse_historical_qualification', lambda r: mutate_json(r, failing['physics_path'],
        lambda d: d['validation']['historical_runtime'].update(applies_to_current_source=True)), 'Historical evidence cannot qualify')
    check('FPS_override_rejected', lambda r: mutate_json(r, failing['physics_path'],
        lambda d: d['validation']['runtime'].update(benchmark_parameter_overrides=['physics_fps=240'])), 'Default stock coverage')
    check('missing_raw_member_verification_rejected', lambda r: mutate_json(r, proofs_path,
        lambda d: d['assets'][0].update(every_raw_archive_member_independently_hashed=False)), 'Incomplete corrected-source evidence')
    check('custom_provider_rejected', lambda r: mutate_json(r, proofs_path,
        lambda d: d['assets'][0]['exact_declared_test_engine_pair_verification'].update(stock_provider_only=False)), 'Corrected test coverage')
    check('missing_declared_pair_rejected', lambda r: mutate_json(r, proofs_path,
        lambda d: d['assets'][0]['exact_declared_test_engine_pair_verification'].update(declared_test_engine_pairs=1)), 'Corrected test coverage')
    check('new_failure_requires_diagnosis', lambda r: mutate_json(r, proofs_path,
        lambda d: d['assets'][0].update(new_failing_test_engine_pairs=[['presence', 'isaac_sim']])), 'new failed pair needs causal diagnosis')
    check('stale_raw_archive_rejected', lambda r: mutate_json(r, failing['physics_path'],
        lambda d: d['validation']['runtime'].update(raw_archive_url=d['validation']['runtime']['package_url'])), 'Physics evidence URL differs')
    check('wrong_corrected_source_proof_rejected', lambda r: mutate_json(r, proofs_path,
        lambda d: d['assets'][0].update(source_usd_sha256='0'*64)), 'Corrected USD proof differs')
    check('duplicate_inventory_identity_rejected', lambda r: mutate_json(r, inventory_path,
        lambda d: d['assets'].__setitem__(0, copy.deepcopy(d['assets'][1]))), 'All 1,013 identities')
    def wrong_parquet(root):
        path = root / 'data/catalog.parquet'; values = pq.read_table(path).to_pylist()
        values[0]['name'] = 'Substituted display name'
        pq.write_table(pa.Table.from_pylist(values), path)
        m = load(root / 'reports/current-release.json')
        m['parquet']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        save(root / 'reports/current-release.json', m)
    check('parquet_JSONL_semantics_must_match', wrong_parquet, 'Parquet and JSONL records differ', do_rehash=False)
    def wrong_url(root):
        values = records(root / 'data/catalog.jsonl'); values[0]['usd_download_url'] = values[0]['usd_download_url'].replace('/resolve/', '/resolve/main/')
        write_catalog(root / 'data/catalog.jsonl', values)
    check('stale_legacy_source_URL_rejected', wrong_url, 'Legacy source download is stale')
    def escape(root):
        m = load(root / 'reports/current-release.json'); m['catalog']['path'] = '../outside.jsonl'
        save(root / 'reports/current-release.json', m)
    check('artifact_path_escape_rejected', escape, 'escapes', do_rehash=False)
    # Explicitly verify the readiness false/true claims are not enough to turn
    # an incomplete real subset into all 221 independently completed sources.
    def fake_completion(root):
        mutate_json(root, inventory_path, lambda d: d.update(release_complete=True, local_preview_only=False,
            corrected_source_count_verified=report['source_corrections_verified'] + 1))
    check('completion_flags_cannot_invent_missing_runs', fake_completion, 'Verified correction counts differ', ready=True)
    result = {'passed': all(r['passed'] for r in results), 'checks': results,
        'real_current_assets_exercised': len(report['assets']),
        'real_corrected_sources_in_subset': report['source_corrections_verified'],
        'GPU_used': False, 'publications_performed': False, 'native_tests_or_results_changed': False,
        'complete_221_ready_positive_still_required': report['source_corrections_verified'] < 221, 'epoch': time.time()}
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(results)}))


if __name__ == '__main__':
    main()
