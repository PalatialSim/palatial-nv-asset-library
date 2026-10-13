"""Re-open actual USDs and check metadata, gallery and immutable evidence hashes."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
import math
from pathlib import Path

from inspect_usd import inspect
from release_manifest import load_current_release, require


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9)


def verify(root, release_manifest='reports/current-release.json', require_ready=False):
    _, report, gallery = load_current_release(root, release_manifest, require_ready)
    def check(asset):
        usd = root / asset['usd_path']
        path = root / asset['physics_path']
        data = json.loads(path.read_text())
        actual = inspect(usd)
        rid = asset['catalog_id']
        require(not actual['errors'], 'USD inspection errors: ' + rid + ': ' + str(actual['errors']))
        require(actual['usd_sha256'] == asset['usd_sha256'] == data['provenance']['usd_sha256'], 'USD hash differs: ' + rid)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == asset['repaired_physics_sha256'], 'Physics hash differs: ' + rid)
        require(close(actual['total_mass_kg'], data['asset']['total_mass']), 'Total mass differs: ' + rid)
        require(close(actual['total_mass_kg'], sum(p['mass'] for p in data['parts'])), 'Part mass sum differs: ' + rid)
        body_map = {b['path']: b for b in actual['bodies']}
        require(len(body_map) == len(data['parts']), 'Rigid body count differs: ' + rid)
        for part in data['parts']:
            require(close(part['mass'], body_map[part['source_prim_path']]['mass_kg']), 'Body mass differs: ' + rid)
        require(actual['up_axis'] == data['units']['up_axis'] == data['validation']['scale']['up_axis'], 'Up axis differs: ' + rid)
        require(actual['moving_joints'] == data['validation']['articulation']['moving_joints'], 'Moving joint count differs: ' + rid)
        require(len(actual['joints']) == len(data['articulation']['joints']), 'Joint count differs: ' + rid)
        require(len(actual['colliders']) == data['validation']['collision']['shape_count'], 'Collider count differs: ' + rid)
        entry = gallery[asset['catalog_id']]
        require(entry['asset_id'] == data['asset_id'], 'Gallery asset identity differs: ' + rid)
        require(entry['moving_joints'] == actual['moving_joints'], 'Gallery joints differ: ' + rid)
        for key in ('min', 'max', 'size'):
            require(all(close(a, b) for a, b in zip(actual['bounds'][key], data['asset']['bounds'][key])), 'USD bounds differ: ' + rid)
            require(entry['bounds'][key] == data['asset']['bounds'][key], 'Gallery bounds differ: ' + rid)
        for key in ('scale', 'mass', 'articulation', 'collision'):
            require(data['validation'][key]['scope'].startswith('authored_usd_'), 'Authored validation scope differs: ' + rid)
        return asset['catalog_id']
    with ThreadPoolExecutor(max_workers=4) as pool:
        passed = list(pool.map(check, report['assets']))
    return {'assets': len(passed), 'usd_metadata_and_gallery_parity': True, 'evidence_hashes_match': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--release-manifest', default='reports/current-release.json')
    parser.add_argument('--require-ready', action='store_true')
    args = parser.parse_args()
    result = verify(args.root, args.release_manifest, args.require_ready)
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
