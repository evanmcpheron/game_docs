#!/usr/bin/env python3
"""Check phase integration coverage, shared assignments and preserved architecture identities."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from build_manual_indexes import build_outputs
from phase_integration import END, ENVIRONMENT_PAGE, START, load_integration

ROOT = Path(__file__).resolve().parents[1]
IDENTITY_FIELDS = ['name', 'type', 'parent', 'phase', 'folder', 'path', 'doc']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-report', action='store_true')
    arguments = parser.parse_args()
    data = load_integration()
    manifest = json.loads((ROOT / 'sources/current-asset-manifest.json').read_text())
    assets = {asset['name']: asset for asset in manifest}
    errors = []
    phases = data['phases']
    if [phase['phase'] for phase in phases] != list(range(12)):
        errors.append('Phase workflows must cover 0–11 exactly once in order.')
    required_sections = ['existing', 'configure', 'connect', 'world', 'run', 'failure', 'regression', 'deferred']
    for phase in phases:
        number = phase['phase']
        for section in required_sections:
            if section not in phase or (section != 'existing' and not phase[section]):
                errors.append(f'Phase {number}: missing operational section {section}.')
        for modification in phase['existing']:
            name = modification['asset']
            if name not in assets or assets[name]['phase'] >= number:
                errors.append(f'Phase {number}: {name} is not an earlier-phase existing asset.')
        path = ROOT / f'phases/phase-{number:02}.html'
        source = path.read_text()
        for anchor in ['integrate-existing', 'integrate-configure', 'integrate-hook-up', 'integrate-world',
                       'integrate-run', 'integrate-failure', 'integrate-regression', 'integrate-deferred', 'integrate-complete']:
            if source.count(f'id="{anchor}"') != 1:
                errors.append(f'{path.name}: missing/duplicate {anchor}.')
        if f'data-check="integrated-phase-{number:02}-3"' not in source:
            errors.append(f'{path.name}: no observed-run completion gate.')
    bindings = data['bindings']
    for binding in bindings:
        name = binding['asset']
        if name not in assets:
            errors.append(f'Unknown assigned asset: {name}.')
            continue
        if not assets[name]['phase'] <= binding['phase'] <= 11:
            errors.append(f'{name}: connection predates creation or is outside the roadmap.')
        for field in ['owners', 'slot', 'editor', 'runtime', 'missing', 'test']:
            if not binding.get(field):
                errors.append(f'{name}: incomplete assignment field {field}.')
        for owner in binding['owners']:
            if owner not in assets or assets[owner]['phase'] > binding['phase']:
                errors.append(f'{name}: unavailable owner {owner} in Phase {binding["phase"]}.')
                continue
            owner_source = (ROOT / assets[owner]['doc']).read_text()
            if name not in owner_source.split(START)[-1].split(END)[0]:
                errors.append(f'{name}: reverse integration is absent from {owner}.')
        for owner in binding['dependencies']:
            if owner not in assets or name not in assets[owner]['deps']:
                errors.append(f'{name}: direct dependency missing on {owner}.')
    types = {
        'Blueprint Actor Component': 'component', 'Blueprint Interface': 'interface',
        'Data Asset instance': 'definition', 'Input Action': 'input', 'Widget Blueprint': 'view',
    }
    for asset in manifest:
        name = asset['name']
        expected_kind = types.get(asset['type'])
        matching = [binding for binding in bindings if binding['asset'] == name]
        if expected_kind and not any(binding['kind'] == expected_kind for binding in matching):
            errors.append(f'{name}: no explicit {expected_kind} integration contract.')
        if name not in data['asset_notes'] and not matching:
            errors.append(f'{name}: no runtime/data/staged disposition.')
        note = data['asset_notes'].get(name)
        if note and not asset['phase'] <= note['first_active'] <= 11:
            errors.append(f'{name}: invalid activation phase.')
        source = (ROOT / asset['doc']).read_text()
        if source.count(START) != 1 or source.count(END) != 1 or source.count('id="phase-integration"') != 1:
            errors.append(f'{name}: missing/duplicate generated asset integration block.')
    required_staging = {'BP_GameInstance': 3, 'IA_Jump': 1, 'E_EquipmentSlot': 7, 'S_InventoryEntry': 4}
    for name, number in required_staging.items():
        if data['asset_notes'].get(name, {}).get('first_active') != number:
            errors.append(f'{name}: lost explicit staged activation in Phase {number}.')
    environment = (ROOT / ENVIRONMENT_PAGE).read_text()
    for phrase in ['L_MovementLab', 'L_Slice_A', 'L_Slice_B', 'L_SystemTests', 'L_Frontend',
                   'Default Pawn=None', 'not an alternate valid gameplay-area bootstrap', 'not executed gameplay results']:
        if phrase not in environment:
            errors.append(f'Test-environment boundary missing: {phrase}.')
    if build_outputs():
        errors.append('Generated integration/index pages are stale; run build_manual_indexes.py.')
    identity = [{field: asset[field] for field in IDENTITY_FIELDS} for asset in sorted(manifest, key=lambda asset: asset['name'])]
    identity_hash = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    identity_preserved = identity_hash == data['baseline']['asset_identity_sha256']
    if not identity_preserved:
        errors.append('Asset name/type/parent/phase/Content folder/path/page identity changed from the audited baseline.')
    preserved = {}
    for filename, expected_hash in data['baseline']['preserved_files'].items():
        preserved[filename] = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() == expected_hash
        if not preserved[filename]:
            errors.append(f'Preserved historical source or phase order changed: {filename}.')
    report = {
        'date': datetime.now(timezone.utc).date().isoformat(),
        'check': 'Incremental feature integration and development-world static documentation validation',
        'baseline_commit': data['baseline']['commit'], 'baseline_tree': data['baseline']['tree'],
        'phase_workflows': len(phases), 'asset_dispositions': len(manifest),
        'shared_bindings': len(bindings), 'binding_kinds': dict(sorted(Counter(binding['kind'] for binding in bindings).items())),
        'asset_identity_preserved': identity_preserved, 'preserved_files': preserved,
        'related_game_access': data['baseline']['related_game_access'],
        'errors': errors, 'blueprints_compiled': False, 'unreal_editor_run': False,
        'runtime_tests_run': False, 'packaged_game_run': False, 'installed_paperzd_compatibility_verified': False,
    }
    if arguments.write_report:
        (ROOT / 'sources/phase-integration-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Passed: {len(phases)} phase workflows, {len(manifest)} asset dispositions, {len(bindings)} shared assignments; identities, phase order and historical sources preserved.')


if __name__ == '__main__':
    main()
