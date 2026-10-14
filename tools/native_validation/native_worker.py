"""Hash-bound, resumable queue for one GPU; official suite remains unchanged."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    os.replace(temporary, path)


def utc():
    return datetime.now(timezone.utc).isoformat()


def safe_path(root, relative):
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Input path escapes its content root')
    return target


def fetch_inputs(manifest, assets, root):
    from huggingface_hub import hf_hub_download
    from threading import Lock
    content = root / 'workspace/content'
    source_locks={r['source_hf_path']:Lock() for asset in assets for r in asset['resources'] if r['source_hf_path']}
    def fetch(record):
        target = safe_path(content, record['relative_path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file():
            if not record['source_hf_path']:
                # Desktop upload and native processing overlap; .upload is never consumed.
                until=time.monotonic()+7200
                while not target.is_file() and time.monotonic()<until:
                    time.sleep(2)
                if not target.is_file():
                    raise FileNotFoundError('Missing desktop input after bounded upload wait: ' + record['relative_path'])
            else:
                # Multiple diagnostic variants can share a source-cache file.
                # Keep cache replacement and hardlink creation in one lock.
                with source_locks[record['source_hf_path']]:
                    downloaded = hf_hub_download(repo_id=manifest['source_hf_repo'], repo_type='dataset',
                                                 revision=manifest['source_hf_revision'], filename=record['source_hf_path'],
                                                 token=False, local_dir=str(root / 'source-cache'))
                    temporary = target.with_name(target.name + '.download')
                    temporary.unlink(missing_ok=True)
                    os.link(downloaded, temporary)
                    os.replace(temporary, target)
        if target.stat().st_size != record['size'] or sha(target) != record['sha256']:
            raise RuntimeError('Input checksum mismatch: ' + record['relative_path'])
    resources = {record['relative_path']: record for asset in assets for record in asset['resources']}
    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(fetch, resources.values()))


def run(command, logfile, env, timeout):
    with logfile.open('w') as output:
        try:
            return subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, env=env, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            return 124


def qualify(run_root, assets, root):
    """Require every planned test, unchanged input, native thumbnail, and joint safety."""
    from simready.manage.backends.benchmark_backend import BenchmarkBackend
    plan_path = run_root / 'plan.json'
    if not plan_path.is_file():
        raise RuntimeError('Native plan missing')
    plan = json.loads(plan_path.read_text())
    tests = {item['id']: item for item in plan['tests']}
    expected = {}
    for item in plan['assets']:
        path = Path(item['path'].replace('$PLAN_DIR', str(run_root))).resolve()
        relative = str(path.relative_to(root / 'workspace/content'))
        expected[relative] = {tests[identity]['name'] for identity in item['tests']}
    grouped = {}
    for path in run_root.rglob('result.json'):
        data = json.loads(path.read_text())
        grouped.setdefault(data['asset'], []).append((path, data))
    receipts = []
    for asset in assets:
        relative = asset['relative_usd']
        usd = root / 'workspace/content' / relative
        results = grouped.get(relative, [])
        issues = []
        actual = [data['test_name'] for _, data in results]
        wanted = expected.get(relative, set())
        if not wanted or set(actual) != wanted or len(actual) != len(set(actual)):
            issues.append('planned_test_coverage_incomplete_or_duplicate')
        if sha(usd) != asset['usd_sha256']:
            issues.append('input_usd_changed')
        numerical_warnings = []
        thumbnail = None
        joint_counts = None
        joint_safety = not asset['moving_joints']
        for path, data in results:
            name = data['test_name']
            if data['status'] not in {'pass', 'skipped'}:
                issues.append(name + ':' + data['status'])
            if data.get('engine_unhealthy'):
                issues.append(name + ':engine_unhealthy')
            if data.get('engine') != 'isaac_sim' or data.get('engine_version') != '6.1.0.0':
                issues.append(name + ':runtime_differs')
            if any('invalid physx transform' in entry.get('message', '').lower() for entry in data.get('kit_logs', [])):
                issues.append(name + ':invalid_physics_transform')
            metrics = {key: value.get('value') for key, value in data.get('metrics', {}).items()}
            if name == 'joint_movement' and data['status'] == 'pass':
                joint_counts = {key: metrics.get(key) for key in ('jm_joints_total', 'jm_joints_passed', 'jm_joints_failed')}
                if not joint_counts['jm_joints_total'] or joint_counts['jm_joints_passed'] != joint_counts['jm_joints_total'] or joint_counts['jm_joints_failed'] != 0:
                    issues.append('joint_movement:incomplete_joint_coverage')
                if any(isinstance(value, (int, float)) and value > 100000 for key, value in metrics.items() if key.endswith('_trans_pct')):
                    numerical_warnings.append('official_relative_translation_requires_independent_anchor_check')
            if name == 'palatial_joint_constraint_safety':
                joint_safety = (not asset['moving_joints'] and data['status']=='skipped') or (data['status'] == 'pass' and metrics.get('joint_constraint_failures') == 0)
                if joint_counts and metrics.get('observed_joint_count') != joint_counts['jm_joints_total']:
                    issues.append('independent_joint_coverage_differs')
            if name == 'palatial_black_thumbnail' and data['status'] == 'pass':
                image = path.parent / 'package-thumbnail.png'
                if not image.is_file() or metrics.get('asset_usd_sha256') != asset['usd_sha256'] or sha(image) != metrics.get('thumbnail_sha256'):
                    issues.append('thumbnail:hash_binding_failed')
                else:
                    thumbnail = {'path': str(image.relative_to(root)), 'sha256': sha(image)}
        if not thumbnail:
            issues.append('verified_native_thumbnail_missing')
        if not joint_safety:
            issues.append('independent_joint_safety_missing_or_failed')
        # Each official sidecar receives only this asset's unmodified raw results.
        isolated = run_root / 'sidecar-inputs' / asset['logical_asset']
        isolated.mkdir(parents=True, exist_ok=True)
        for index, (path, _) in enumerate(results):
            target = isolated / str(index) / 'result.json'
            target.parent.mkdir(exist_ok=True)
            if not target.exists():
                os.link(path, target)
        metadata = usd.parent.parent / '.metadata'
        metadata.mkdir(exist_ok=True)
        sidecar = metadata / (usd.stem + '_benchmark.json')
        ok, _ = BenchmarkBackend().synthesize_sidecar(isolated, usd.stem, sidecar)
        if not ok:
            issues.append('official_benchmark_sidecar_missing')
        receipts.append({'catalog_id': asset['catalog_id'], 'logical_asset': asset['logical_asset'],
                         'asset_usd_sha256': asset['usd_sha256'], 'native_status': 'passed' if not issues else 'failed',
                         'safety_accepted': not issues, 'planned_test_count': len(wanted), 'result_count': len(results),
                         'issues': sorted(set(issues)), 'warnings': numerical_warnings, 'joint_counts': joint_counts,
                         'thumbnail': thumbnail, 'benchmark_sidecar_sha256': sha(sidecar) if ok else None,
                         'result_files': [{'path': str(path.relative_to(root)), 'sha256': sha(path)} for path, _ in results],
                         'completed_at': utc()})
    return receipts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--chunk-size', type=int, default=20)
    parser.add_argument('--deadline-utc', required=True)
    args = parser.parse_args()
    root = args.manifest.resolve().parent
    if sha(args.manifest) != args.manifest_sha256:
        raise RuntimeError('Queue manifest differs from launch commitment')
    manifest = json.loads(args.manifest.read_text())
    if manifest['profile'] != 'Robotics-Prop' or manifest['profile_version'] != '4.0.0' or manifest['runtime'] != 'isaac_sim':
        raise RuntimeError('Queue acceptance contract differs')
    deadline = datetime.fromisoformat(args.deadline_utc.replace('Z', '+00:00')).timestamp()
    env = dict(os.environ)
    for name in ('PYTHONPATH', 'PYTHONHOME', 'PXR_PLUGINPATH_NAME', 'LD_LIBRARY_PATH'):
        env.pop(name, None)
    env.update(PXR_AR_DEFAULT_SEARCH_PATH='/isaac-sim/kit/mdl/core/Base', HF_HUB_DISABLE_PROGRESS_BARS='1')
    os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
    tools = Path('/workspace/simready/.venv-tools/bin')
    receipts = []
    progress = root / 'native-progress.json'
    started = utc()
    for start in range(0, len(manifest['assets']), args.chunk_size):
        if time.time() >= deadline - 1800:
            raise RuntimeError('Queue deadline reached before another bounded chunk')
        assets = manifest['assets'][start:start + args.chunk_size]
        batch = root / ('native-batch-%03d' % (start // args.chunk_size))
        receipt_path = batch / 'qualification.json'
        if receipt_path.exists():
            receipts.extend(json.loads(receipt_path.read_text()))
            continue
        if batch.exists():
            if not (batch/'benchmark/plan.json').exists() and not list(batch.rglob('result.json')):
                # A planning failure never launched a GPU test; retain its logs and
                # retry preparation on the same frozen queue after configuration repair.
                os.rename(batch,root/('preflight-interrupted-'+batch.name+'-'+str(time.time_ns())))
            else:
                raise RuntimeError('Interrupted native output requires explicit fresh retry')
        batch.mkdir()
        save(progress, {'shard': manifest['shard'], 'phase': 'download', 'completed': len(receipts),
                        'total': len(manifest['assets']), 'started_at': started, 'updated_at': utc(), 'receipts': receipts})
        fetch_inputs(manifest, assets, root)
        paths = [str(root / 'workspace/content' / asset['relative_usd']) for asset in assets]
        listing = batch / 'assets.txt'
        listing.write_text('\n'.join(paths) + '\n')
        validation = batch / 'validation.json'
        code = run([str(tools / 'simready-validate'), '--asset_list', str(listing), '--profile', 'Robotics-Prop',
                    '--version', '4.0.0', '--output', str(validation)], batch / 'validation.log', env, 1200)
        if code != 0 or not validation.exists():
            raise RuntimeError('Fresh official static validation failed')
        raw = json.loads(validation.read_text())
        if set(raw) != set(paths):
            raise RuntimeError('Fresh static input coverage differs')
        for path, item in raw.items():
            if item['profile_id'] != 'Robotics-Prop' or item['profile_version'] != '4.0.0' or any(value.get('blocking_failure') for value in item['features_summary'].values()):
                raise RuntimeError('Fresh official static gate failed')
            usd = Path(path)
            save(usd.parent.parent / '.metadata' / (usd.stem + '_validation.json'), {path: item})
        save(progress, {'shard': manifest['shard'], 'phase': 'native', 'completed': len(receipts),
                        'total': len(manifest['assets']), 'started_at': started, 'updated_at': utc(), 'receipts': receipts})
        run_root = batch / 'benchmark'
        supplemental=manifest.get('supplemental_tests_path','/workspace/simready/native-supplemental-tests')
        if supplemental!='/workspace/simready/native-supplemental-tests' and Path(supplemental)!=root/'supplemental-tests':
            raise RuntimeError('Unexpected supplemental test directory')
        command = [str(tools / 'simready-benchmark'), '--assets', *paths, '--project-config', str(root / 'workspace/project_config.toml'),
                   '--engines-toml', '/workspace/simready/native-engines.toml', '--runtime', 'isaac_sim',
                   '--tests-path', supplemental, '--max-concurrent', '1',
                   '--session-mode', 'batch', '--no-stamp', '--output-dir', str(run_root)]
        code = run(command, batch / 'benchmark.log', env, min(7200, max(1, int(deadline - time.time()))))
        # A nonzero official exit preserves genuine failed results and continues the queue.
        batch_receipts = qualify(run_root, assets, root)
        save(receipt_path, batch_receipts)
        receipts.extend(batch_receipts)
        save(progress, {'shard': manifest['shard'], 'phase': 'between_batches', 'last_benchmark_exit_code': code,
                        'completed': len(receipts), 'total': len(manifest['assets']), 'started_at': started,
                        'updated_at': utc(), 'receipts': receipts})
    save(progress, {'shard': manifest['shard'], 'phase': 'completed', 'completed': len(receipts),
                    'total': len(manifest['assets']), 'started_at': started, 'updated_at': utc(), 'receipts': receipts})
    save(root / 'worker.finished.json', {'completed_at': utc(), 'manifest_sha256': args.manifest_sha256,
                                         'assets': len(receipts), 'passed': sum(r['native_status'] == 'passed' for r in receipts)})


if __name__ == '__main__':
    main()
