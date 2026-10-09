#!/usr/bin/env python3
"""Validate documentation integrity. This never runs or validates Unreal gameplay."""
from __future__ import annotations
import argparse
from collections import Counter, deque
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

DEFAULT_ROOT = Path(__file__).resolve().parents[1]

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.identifiers = []
        self.links = []
        self.heading_count = 0
        self.language = None
        self.remote_resources = []
        self.text = []
    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        if 'id' in values:
            self.identifiers.append(values['id'])
        if tag == 'html':
            self.language = values.get('lang')
        if tag == 'h1':
            self.heading_count += 1
        for attribute in ['href', 'src']:
            if values.get(attribute):
                self.links.append(values[attribute])
        if tag in ['script', 'img', 'iframe', 'link', 'video', 'audio']:
            resource = values.get('src', values.get('href', ''))
            if resource.startswith(('http:', 'https:', '//')):
                self.remote_resources.append(resource)
    def handle_data(self, text):
        self.text.append(text)

def validate(root: Path) -> dict:
    root = root.resolve()
    errors = []
    warnings = []
    def error(code, message):
        errors.append({'code': code, 'message': str(message)})
    def load(name):
        try:
            return json.loads((root / 'sources' / name).read_text(encoding='utf-8'))
        except (OSError, ValueError) as exception:
            error('JSON', f'{name}: {exception}')
            return None
    pages = {}
    for path in sorted(root.rglob('*.html')):
        relative = path.relative_to(root).as_posix()
        parser = PageParser()
        try:
            parser.feed(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeError) as exception:
            error('HTML_READ', f'{relative}: {exception}')
            continue
        pages[relative] = parser
        if parser.heading_count != 1 or parser.language != 'en' or 'main' not in parser.identifiers:
            error('HTML_STRUCTURE', f'{relative}: require one h1, lang=en and main landmark ID')
        duplicates = [identifier for identifier, count in Counter(parser.identifiers).items() if count > 1]
        if duplicates:
            error('DUPLICATE_ANCHOR', f'{relative}: {duplicates}')
        if parser.remote_resources:
            error('REMOTE_RESOURCE', f'{relative}: {parser.remote_resources}')
    graph = {path: set() for path in pages}
    internal_links = 0
    for name, parser in pages.items():
        for target in parser.links:
            parsed = urlsplit(target)
            if parsed.scheme in ['http', 'https', 'mailto'] or target.startswith('//'):
                continue
            if parsed.scheme:
                error('UNSUPPORTED_LINK', f'{name}: {target}')
                continue
            resolved = ((root / name).parent / unquote(parsed.path)).resolve() if parsed.path else root / name
            if not resolved.is_relative_to(root):
                error('ESCAPING_LINK', f'{name}: {target}')
                continue
            internal_links += 1
            if not resolved.is_file():
                error('BROKEN_LINK', f'{name}: {target}')
                continue
            destination = resolved.relative_to(root).as_posix()
            if destination in pages:
                graph[name].add(destination)
                if parsed.fragment and unquote(parsed.fragment) not in pages[destination].identifiers:
                    error('BROKEN_FRAGMENT', f'{name}: {target}')
    reachable = set()
    queue = deque(['index.html'])
    while queue:
        page = queue.popleft()
        if page in reachable:
            continue
        reachable.add(page)
        queue.extend(graph.get(page, set()) - reachable)
    for orphan in sorted(set(pages) - reachable):
        error('ORPHAN_PAGE', orphan)
    for path in (root / 'sources').glob('*.json'):
        load(path.name)
    manifest = load('current-asset-manifest.json')
    features = load('feature-specifications.json')
    coverage = load('feature-coverage.json')
    ownership = load('ownership-records.json')
    edges_record = load('dependency-edges.json')
    verification = load('verification.json')
    counts = {'html_pages': len(pages), 'internal_links_checked': internal_links}
    if all(value is not None for value in [manifest, features, coverage, ownership, edges_record, verification]):
        assets = manifest['assets']
        indexed = {asset['id']: asset for asset in assets}
        counts.update(assets=len(assets), features=len(features), ownership_records=len(ownership), dependency_edges=len(edges_record['edges']))
        for field in ['id', 'path', 'page']:
            for value, count in Counter(asset[field] for asset in assets).items():
                if count > 1:
                    error('DUPLICATE_ASSET', f'{field} {value}: {count}')
        feature_ids = {feature['id'] for feature in features}
        for asset in assets:
            for field in ['type', 'parent', 'category', 'owner', 'replication_role', 'persistence_role', 'lifespan', 'evidence', 'maturity']:
                if not asset.get(field):
                    error('ASSET_CONTRACT', f"{asset['id']}: missing {field}")
            if asset['page'] not in pages:
                error('ASSET_PAGE', asset['id'])
            expected_page = f"assets/{asset['category']}/{asset['id']}.html"
            if asset['page'] != expected_page:
                error('ASSET_FOLDER', asset['page'])
            planned_path = asset['path']
            if not planned_path.startswith(('Content/Game/', 'Source/RPG/', 'Backend/GameService/', 'Tests/Acceptance/', 'Config/Tags/')) or '..' in Path(planned_path).parts:
                error('ASSET_PATH', f"{asset['id']}: {planned_path}")
            if planned_path.startswith('Content/Game/'):
                expected_object = '/Game/' + str(Path(planned_path).with_suffix('')).removeprefix('Content/') + '.' + asset['id']
                if asset.get('object_path') != expected_object:
                    error('OBJECT_PATH', asset['id'])
            if asset['parent'] in indexed and asset['parent'] not in asset['dependencies']:
                error('PARENT_DEPENDENCY', f"{asset['id']} requires {asset['parent']} before creation")
            for feature_id in asset['features']:
                if feature_id not in feature_ids:
                    error('UNKNOWN_FEATURE', f"{asset['id']}: {feature_id}")
            if not 0 <= asset['first_phase'] <= asset['last_phase'] <= 23:
                error('ASSET_PHASE', asset['id'])
            if asset['maturity'] != 'planned_contract_not_implemented':
                error('UNSUPPORTED_RUNTIME_CLAIM', asset['id'])
        expected_edges = []
        for asset in assets:
            expected_edges += [(asset['id'], target, 'creation', asset['first_phase']) for target in asset['dependencies']]
            expected_edges += [(asset['id'], reference['asset'], 'integration', reference['phase']) for reference in asset['references']]
        actual_edges = [(edge['source'], edge['target'], edge['kind'], edge['phase']) for edge in edges_record['edges']]
        if Counter(expected_edges) != Counter(actual_edges):
            error('EDGE_DRIFT', 'dependency-edges differs from manifest')
        for identity, asset in indexed.items():
            expected_users = Counter((source, phase, kind) for source, target, kind, phase in expected_edges if target == identity)
            actual_users = Counter((user['asset'], user['phase'], user['kind']) for user in asset['users'])
            if expected_users != actual_users:
                error('REVERSE_USERS', identity)
        coverage_ids = {feature['id'] for feature in coverage['features']}
        if len(coverage_ids) != len(coverage['features']) or coverage_ids != feature_ids:
            error('COVERAGE_IDS', 'coverage registry does not match unique feature specifications')
        for feature in features:
            for field in ['purpose', 'ui_states', 'fields', 'commands', 'flow', 'editor_steps', 'failures', 'tuning', 'observability']:
                if not feature.get(field):
                    error('FEATURE_DEPTH', f"{feature['id']}: missing {field}")
            for field in ['owner', 'definition', 'widget']:
                if feature[field] not in indexed:
                    error('FEATURE_ASSET', f"{feature['id']}: {field}={feature[field]}")
            if feature['page'] not in pages:
                error('FEATURE_PAGE', feature['id'])
        for feature in coverage['features']:
            for target in [feature['chapter'], feature['ui'], feature['naming']]:
                if target not in pages:
                    error('FEATURE_LINK', f"{feature['id']}: {target}")
            expected = {asset['id'] for asset in assets if feature['id'] in asset['features']}
            if set(feature['assets']) != expected:
                error('FEATURE_ASSETS', feature['id'])
        required_ownership = ['authoritative_owner', 'runtime_cache', 'replication_owner', 'persistence_store', 'stable_identity', 'source_of_changes', 'validation_path', 'revision', 'failure_policy', 'ui_observer', 'model_asset', 'owner_asset']
        for record in ownership:
            for field in required_ownership:
                if not record.get(field):
                    error('MISSING_OWNERSHIP', f"{record['id']}: {field}")
            for field in ['model_asset', 'owner_asset', 'ui_observer']:
                if record.get(field) not in indexed:
                    error('OWNERSHIP_ASSET', f"{record['id']}: {field}={record.get(field)}")
        model_ids = {asset['id'] for asset in assets if asset['type'] == 'Database model'}
        if model_ids != {record['model_asset'] for record in ownership}:
            error('MODEL_OWNERSHIP', 'every registered durable model must have a fact owner record')
        for field in ['engine_compile', 'blueprint_compile', 'database_integration', 'packaged_client_server', 'multiplayer_runtime', 'load_benchmark']:
            if verification.get(field) != 'not_run':
                error('UNSUPPORTED_RUNTIME_CLAIM', f'{field}: attach real evidence and update validator policy before changing status')
        if verification['archive']['status'] == 'not_available' and verification['archive']['actual_png_count'] is not None:
            error('FABRICATED_ARCHIVE_COUNT', 'missing archive cannot have a measured count')
    for path in root.rglob('*'):
        if path.is_file() and path.suffix.lower() in ['.uasset', '.umap', '.uproject', '.cpp', '.h', '.dll', '.exe']:
            error('FORBIDDEN_ARTIFACT', path.relative_to(root))
    javascript = (root / 'site/app.js').read_text(encoding='utf-8')
    if re.search(r'\bfetch\s*\(|XMLHttpRequest|https?://', javascript):
        error('ONLINE_JS_DEPENDENCY', 'app.js must not require remote/network fetch')
    for required in ['README.md', 'AGENTS.md', 'UNVERIFIED.md', 'sources/asset-archive-inventory.csv', 'tools/audit_asset_archive.py', 'tools/check_phase_integration.py']:
        if not (root / required).is_file():
            error('REQUIRED_FILE', required)
    warnings += [
        'Static integrity does not prove prose completeness, valid Unreal APIs, Blueprint compilation, backend correctness or multiplayer behavior.',
        'Source archive, licenses, installed plugin compatibility and source-derived asset enumeration remain unverified.',
        'Individual contract depth/content production still require specialist implementation review; see reports/content-depth-review.json.',
    ]
    return {'status': 'pass' if not errors else 'fail', 'summary': f"{len(errors)} structural errors; source/runtime completion remains blocked.", 'scope': 'Offline documentation structural integrity only', 'generated_at': datetime.now(timezone.utc).isoformat(), 'counts': counts, 'errors': errors, 'warnings': warnings}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--write-report', action='store_true')
    arguments = parser.parse_args()
    report = validate(arguments.root)
    report['command'] = 'python tools/validate_docs.py' + (' --write-report' if arguments.write_report else '')
    if arguments.write_report:
        target = arguments.root / 'reports/static-validation.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(report['status'].upper() + ': ' + report['summary'])
    for error in report['errors'][:50]:
        print(error['code'] + ': ' + error['message'])
    return 0 if report['status'] == 'pass' else 1

if __name__ == '__main__':
    raise SystemExit(main())
