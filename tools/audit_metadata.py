"""Fast, unattended regression check for asset-library metadata completeness."""
import argparse
from collections import Counter
import json
import math
import re
from pathlib import Path
from urllib.parse import unquote


def audit(root):
    gallery = json.loads((root / 'gallery/assets.json').read_text())
    problems = []
    statuses = {key: Counter() for key in ('scale', 'mass', 'articulation', 'collision')}
    physics = list(root.glob('batch*/**/physics*.json'))
    def normalize(value):
        return re.sub(r'[^a-z0-9]', '', value.lower())
    for entry in gallery:
        folder = root / entry['batch']
        candidates = [p for p in physics if p.parts[len(root.parts)] == entry['batch'] and normalize(p.relative_to(folder).parts[0]) == normalize(entry['name'])]
        if not candidates and entry.get('video_url', '').startswith('../' + entry['batch'] + '/'):
            asset_folder = unquote(entry['video_url']).split('/')[2]
            candidates = [p for p in physics if p.parts[len(root.parts)] == entry['batch'] and p.relative_to(folder).parts[0] == asset_folder]
        if len(candidates) != 1:
            problems.append({'asset': entry['id'], 'issue': 'physics_path_ambiguous', 'paths': [str(p) for p in candidates]})
            continue
        path = candidates[0]
        try:
            data = json.loads(path.read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        except ValueError as error:
            problems.append({'asset': entry['id'], 'physics_path': str(path.relative_to(root)), 'issue': 'nonstandard_json', 'error': str(error)})
            continue
        asset, validation = data.get('asset', {}), data.get('validation', {})
        def fail(issue, **details):
            problems.append({'asset': entry['id'], 'physics_path': str(path.relative_to(root)), 'issue': issue, **details})
        if not str(data.get('asset_id') or '').strip():
            fail('missing_asset_id')
        for key in ('description', 'object_type'):
            if not str(asset.get(key) or '').strip():
                fail('missing_' + key)
        bounds = asset.get('bounds')
        if not bounds or not all(isinstance(bounds.get(k), list) and len(bounds[k]) == 3 for k in ('min', 'max', 'size')):
            fail('missing_bounds')
        elif not all(math.isfinite(v) for k in ('min', 'max', 'size') for v in bounds[k]) or not all(v > 0 for v in bounds['size']):
            fail('invalid_bounds')
        axis = data.get('units', {}).get('up_axis') or validation.get('scale', {}).get('up_axis')
        if axis not in ('Y', 'Z'):
            fail('missing_up_axis')
        if any(j.get('joint_type') == 'floating' for j in data.get('articulation', {}).get('joints', [])):
            fail('legacy_floating_joint')
        masses = [('asset', asset.get('total_mass'))] + [(part.get('id'), part.get('mass')) for part in data.get('parts', [])]
        for part, mass in masses:
            if not isinstance(mass, (int, float)) or not math.isfinite(mass) or mass <= 0:
                fail('nonpositive_mass', part=part, value=mass)
        if all(isinstance(m, (int, float)) and math.isfinite(m) for _, m in masses):
            if not math.isclose(masses[0][1], sum(m for _, m in masses[1:]), rel_tol=1e-5, abs_tol=1e-6):
                fail('mass_sum_mismatch')
            value = validation.get('mass', {}).get('value_kg')
            if value is not None and not math.isclose(value, masses[0][1], rel_tol=1e-5, abs_tol=1e-6):
                fail('validation_mass_mismatch')
        for key in statuses:
            status = validation.get(key, {}).get('status', 'missing')
            statuses[key][status] += 1
            if key != 'collision' and status in ('not_checked', 'recorded', 'missing'):
                fail('unverified_' + key, status=status)
    return {'assets': len(gallery), 'issue_counts': dict(Counter(p['issue'] for p in problems)), 'status_counts': {k: dict(v) for k, v in statuses.items()}, 'problems': problems}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = audit(args.root)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'problems'}, indent=2))
    raise SystemExit(bool(report['problems']))
