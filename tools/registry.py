"""Derive repeated registry records without creating any Unreal assets."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path


def derive_sources(root: Path) -> dict[str, object]:
    def load(name: str):
        return json.loads((root / 'sources' / name).read_text(encoding='utf-8'))
    manifest = deepcopy(load('current-asset-manifest.json'))
    assets = manifest['assets']
    indexed = {asset['id']: asset for asset in assets}
    if len(indexed) != len(assets):
        raise ValueError('Duplicate asset IDs; generation stopped.')
    features = load('feature-specifications.json')
    phases = load('phases.json')
    recipes = {record['phase']: record for record in load('phase-run-recipes.json')}
    integrations = deepcopy(load('phase-integration.json'))
    edges = []
    consumers = {identity: {asset['first_phase']} for identity, asset in indexed.items()}
    reverse = {identity: [] for identity in indexed}
    for asset in assets:
        for dependency in asset['dependencies']:
            if dependency not in indexed:
                raise ValueError(f"Unknown dependency {dependency} on {asset['id']}")
            if indexed[dependency]['first_phase'] > asset['first_phase']:
                raise ValueError(f"Future creation dependency {asset['id']} -> {dependency}")
            edges.append({'source': asset['id'], 'target': dependency, 'kind': 'creation', 'phase': asset['first_phase']})
        for reference in asset['references']:
            if reference['asset'] not in indexed:
                raise ValueError(f"Unknown reference {reference['asset']} on {asset['id']}")
            if reference['phase'] < max(asset['first_phase'], indexed[reference['asset']]['first_phase']):
                raise ValueError(f"Premature integration {asset['id']} -> {reference['asset']}")
            edges.append({'source': asset['id'], 'target': reference['asset'], 'kind': 'integration', 'phase': reference['phase'], 'assignment': reference['assignment']})
    for edge in edges:
        consumers[edge['source']].add(edge['phase'])
        consumers[edge['target']].add(edge['phase'])
        reverse[edge['target']].append({'asset': edge['source'], 'phase': edge['phase'], 'kind': edge['kind']})
    for asset in assets:
        asset['users'] = sorted(reverse[asset['id']], key=lambda user: (user['phase'], user['asset'], user['kind']))
        asset['phase_consumers'] = sorted(consumers[asset['id']])
        asset['last_phase'] = max(asset['phase_consumers'])
    creation = []
    available = set()
    for phase in phases:
        number = phase['number']
        pending = {asset['id'] for asset in assets if asset['first_phase'] == number}
        order = []
        while pending:
            ready = sorted(identity for identity in pending if set(indexed[identity]['dependencies']) <= available)
            if not ready:
                raise ValueError(f'Creation dependency cycle in phase {number}: {sorted(pending)}')
            for identity in ready:
                order.append(identity)
                available.add(identity)
                pending.remove(identity)
        creation.append({'phase': number, 'assets': order})
        integration = next(item for item in integrations['phases'] if item['phase'] == number)
        integration['new_assets'] = order
        integration['run_now'] = recipes[number]
        integration['configure'] = recipes[number]['prepare']
        integration['run'] = []
        integration['rejections'] = [{'feature': 'current-phase fixture', 'expected': text} for text in recipes[number]['reject']]
        integration['features'] = [feature['id'] for feature in features if feature['phase'] == number]
        integration['reopen'] = [dict(consumer=edge['source'], asset=edge['target'], change=edge['assignment']) for edge in edges if edge['kind'] == 'integration' and edge['phase'] == number]
    coverage = load('feature-coverage.json')
    for feature in coverage['features']:
        feature['assets'] = [asset['id'] for asset in assets if feature['id'] in asset['features']]
    return {
        'current-asset-manifest.json': manifest,
        'phase-creation-order.json': {'schema_version': 1, 'phases': creation},
        'dependency-edges.json': {'schema_version': 1, 'semantics': 'source requires target; creation DAG is distinct from phase-stamped runtime assignments', 'edges': edges},
        'phase-integration.json': integrations,
        'feature-coverage.json': coverage,
    }
