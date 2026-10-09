#!/usr/bin/env python3
"""Check creation order, consumers, phase recipes and original world adjacency."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]

def check(root: Path) -> dict:
    def load(name):
        return json.loads((root / 'sources' / name).read_text(encoding='utf-8'))
    errors = []
    def error(code, message):
        errors.append({'code': code, 'message': str(message)})
    assets = load('current-asset-manifest.json')['assets']
    indexed = {asset['id']: asset for asset in assets}
    order = load('phase-creation-order.json')['phases']
    integrations = load('phase-integration.json')['phases']
    phases = load('phases.json')
    edges = load('dependency-edges.json')['edges']
    if [phase['phase'] for phase in order] != list(range(24)) or [phase['phase'] for phase in integrations] != list(range(24)):
        error('PHASE_SET', 'Require sequential phases00–23')
    created = set()
    encountered = []
    for phase in order:
        number = phase['phase']
        for identity in phase['assets']:
            encountered.append(identity)
            if identity not in indexed:
                error('UNKNOWN_ASSET', identity)
                continue
            asset = indexed[identity]
            if asset['first_phase'] != number:
                error('WRONG_CREATION_PHASE', identity)
            if not set(asset['dependencies']) <= created:
                error('CREATION_ORDER', f"{identity}: missing earlier prerequisites {sorted(set(asset['dependencies']) - created)}")
            created.add(identity)
        integration = integrations[number]
        if integration['new_assets'] != phase['assets']:
            error('PHASE_ORDER_DRIFT', number)
        if integration['map'] not in indexed or indexed[integration['map']]['first_phase'] > number:
            error('FUTURE_MAP', integration['map'])
        if not integration.get('run_now'):
            error('MISSING_RUN_RECIPE', number)
        else:
            for field in ['prepare', 'steps', 'success', 'reject', 'deferred']:
                if not integration['run_now'].get(field):
                    error('RUN_RECIPE_DEPTH', f'{number}: {field}')
        declared = Counter((edge['source'], edge['target'], edge['assignment']) for edge in edges if edge['kind'] == 'integration' and edge['phase'] == number)
        actual = Counter((record['consumer'], record['asset'], record['change']) for record in integration['reopen'])
        if actual != declared:
            error('UNDECLARED_CONSUMER', f'phase{number}: reopen records differ from manifest integration edges')
        for record in integration['reopen']:
            for identity in [record['consumer'], record['asset']]:
                if identity not in indexed or indexed[identity]['first_phase'] > number:
                    error('FUTURE_CONSUMER', f'{number}: {identity}')
        if integration['runtime_status'] != 'not_run':
            error('UNSUPPORTED_RUNTIME_CLAIM', number)
        if any(dependency >= number for dependency in phases[number]['prerequisites']):
            error('PHASE_PREREQUISITE', number)
    if Counter(encountered) != Counter(indexed.keys()):
        error('CREATION_COVERAGE', 'Every asset must be created exactly once')
    for edge in edges:
        if edge['source'] not in indexed or edge['target'] not in indexed:
            error('UNKNOWN_EDGE', edge)
        elif edge['phase'] < max(indexed[edge['source']]['first_phase'], indexed[edge['target']]['first_phase']):
            error('FUTURE_DEPENDENCY', edge)
    zones = load('world-catalog.json')['zones']
    zones_by_id = {zone['id']: zone for zone in zones}
    for zone in zones:
        for target, outgoing, returning in zone['routes']:
            if target not in zones_by_id or [zone['id'], returning, outgoing] not in zones_by_id[target]['routes']:
                error('ZONE_RETURN_PATH', f"{zone['id']} -> {target} ({outgoing})")
    classes = load('class-catalog.json')
    for class_record in classes:
        nodes = {node['id']: node for node in class_record['talents']}
        resolved = set()
        while len(resolved) < len(nodes):
            ready = {identity for identity, node in nodes.items() if identity not in resolved and set(node['requires']) <= resolved}
            if not ready:
                error('TALENT_DAG', class_record['name'])
                break
            resolved.update(ready)
    return {'status': 'pass' if not errors else 'fail', 'summary': f"{len(errors)} creation/integration/world-graph errors; runtime recipes not executed.", 'generated_at': datetime.now(timezone.utc).isoformat(), 'counts': {'phases': len(phases), 'assets': len(assets), 'edges': len(edges), 'zones': len(zones)}, 'errors': errors}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--write-report', action='store_true')
    arguments = parser.parse_args()
    report = check(arguments.root)
    report['command'] = 'python tools/check_phase_integration.py' + (' --write-report' if arguments.write_report else '')
    if arguments.write_report:
        (arguments.root / 'reports/phase-integration-validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(report['status'].upper() + ': ' + report['summary'])
    for error in report['errors'][:50]:
        print(error['code'] + ': ' + error['message'])
    return 0 if report['status'] == 'pass' else 1

if __name__ == '__main__':
    raise SystemExit(main())
