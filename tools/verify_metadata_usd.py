"""Re-open actual USDs and check metadata, gallery and immutable evidence hashes."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
import math
from pathlib import Path

from inspect_usd import inspect


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9)


def verify(root):
    report = json.loads((root / 'reports/metadata-repair-20261008.json').read_text())
    gallery = {a['id']: a for a in json.loads((root / 'gallery/assets.json').read_text())}
    def check(asset):
        usd = root / asset['usd_path']
        path = root / asset['physics_path']
        data = json.loads(path.read_text())
        actual = inspect(usd)
        assert not actual['errors'], (asset['catalog_id'], actual['errors'])
        assert actual['usd_sha256'] == asset['usd_sha256'] == data['provenance']['usd_sha256']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == asset['repaired_physics_sha256']
        assert close(actual['total_mass_kg'], data['asset']['total_mass'])
        assert close(actual['total_mass_kg'], sum(p['mass'] for p in data['parts']))
        body_map = {b['path']: b for b in actual['bodies']}
        assert len(body_map) == len(data['parts'])
        for part in data['parts']:
            assert close(part['mass'], body_map[part['source_prim_path']]['mass_kg'])
        assert actual['up_axis'] == data['units']['up_axis'] == data['validation']['scale']['up_axis']
        assert actual['moving_joints'] == data['validation']['articulation']['moving_joints']
        assert len(actual['joints']) == len(data['articulation']['joints'])
        assert len(actual['colliders']) == data['validation']['collision']['shape_count']
        entry = gallery[asset['catalog_id']]
        assert entry['asset_id'] == data['asset_id']
        assert entry['moving_joints'] == actual['moving_joints']
        for key in ('min', 'max', 'size'):
            assert all(close(a, b) for a, b in zip(actual['bounds'][key], data['asset']['bounds'][key]))
            assert entry['bounds'][key] == data['asset']['bounds'][key]
        for key in ('scale', 'mass', 'articulation', 'collision'):
            assert data['validation'][key]['scope'].startswith('authored_usd_')
        return asset['catalog_id']
    with ThreadPoolExecutor(max_workers=4) as pool:
        passed = list(pool.map(check, report['assets']))
    return {'assets': len(passed), 'usd_metadata_and_gallery_parity': True, 'evidence_hashes_match': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = verify(args.root)
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
