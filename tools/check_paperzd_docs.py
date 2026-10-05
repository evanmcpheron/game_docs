#!/usr/bin/env python3
"""Validate the current animation register, generated indexes and migration boundaries."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from build_cpp_standard import plain_text
from build_manual_indexes import build_outputs
from check_cpp_standard import PageParser

ROOT = Path(__file__).resolve().parents[1]
RETIRED = {'BPC_FlipbookAnimator', 'BPDA_AnimationSet', 'E_AnimState',
           'S_AnimationSnapshot', 'DA_Anim_PlayerTest', 'DA_Anim_TestHelmet'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-report', action='store_true')
    args = parser.parse_args()
    errors = []
    manifest = json.loads((ROOT / 'sources/current-asset-manifest.json').read_text())
    assets = {a['name']: a for a in manifest}
    if len(assets) != len(manifest) or RETIRED.intersection(assets):
        errors.append('Current asset identities duplicated or retired assets still registered.')
    pages = {a['doc'] for a in manifest}
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'assets').rglob('*.html') if p.name != 'index.html'}
    if pages != actual:
        errors.append(f'Asset page coverage mismatch: {sorted(pages.symmetric_difference(actual))}')
    for asset in manifest:
        source = (ROOT / asset['doc']).read_text()
        identity = re.search(r'<h2 id="identity">.*?(?=<h2)', source, re.S)
        identity_text = plain_text(identity[0]) if identity else ''
        for field in ['name', 'type', 'parent', 'folder', 'path']:
            if asset[field] not in identity_text:
                errors.append(f'{asset["name"]}: identity missing {field}={asset[field]}')
        for dependency in asset['deps']:
            if dependency not in assets:
                errors.append(f'{asset["name"]}: unknown dependency {dependency}')
        expected_users = sorted(a['name'] for a in manifest if asset['name'] in a['deps'])
        if asset['users'] != expected_users:
            errors.append(f'{asset["name"]}: inconsistent reverse dependencies')
        if 'PaperZDCharacter' in asset['parent'] and asset['name'] not in {
                'BP_PlayerCharacter', 'BP_EnemyBase', 'BP_Enemy_MeleeBasic', 'BP_Enemy_RangedBasic'}:
            errors.append(f'{asset["name"]}: unintended character reparenting')
    orders = json.loads((ROOT / 'sources/phase-creation-order.json').read_text())
    ordered_names = [name for names in orders.values() for name in names]
    if Counter(ordered_names) != Counter(assets.keys()):
        errors.append('Phase creation orders do not cover current assets exactly once.')
    for phase, names in orders.items():
        if any(assets[name]['phase'] != int(phase) for name in names):
            errors.append(f'Phase {phase}: asset classified in wrong phase.')
        positions = {name: index for index, name in enumerate(names)}
        for name in names:
            asset = assets[name]
            if asset['type'] in ['PaperZD Animation Sequence', 'PaperZD Animation Blueprint']:
                source = next(d for d in asset['deps'] if assets[d]['type'] == 'PaperZD Animation Source')
                if source in positions and positions[source] >= positions[name]:
                    errors.append(f'{name}: source must precede sequence/AnimBP.')
    if build_outputs():
        errors.append('Generated manual tables/counts are stale.')
    active = sorted(p for p in ROOT.rglob('*.html') if 'content' not in p.relative_to(ROOT).parts and p.name != 'original-roadmap.html')
    for path in active:
        source = path.read_text()
        page = PageParser()
        page.feed(source)
        if len(page.ids) != len(set(page.ids)) or (page.heading_count, page.main_count, page.title_count) != (1, 1, 1):
            errors.append(f'{path.relative_to(ROOT)}: invalid landmarks or duplicate IDs')
        if path.name != 'animation-migration.html' and any(name in source for name in RETIRED):
            errors.append(f'{path.relative_to(ROOT)}: stale custom animation reference')
        for target in page.references:
            if 'dev.epicgames.com' in target and '/PaperZD' in target:
                errors.append(f'{path.relative_to(ROOT)}: fabricated Epic PaperZD API reference')
    search = json.loads((ROOT / 'site/search-data.js').read_text().removeprefix('window.GUIDE_SEARCH = ').strip().removesuffix(';'))
    expected = {p.relative_to(ROOT).as_posix() for p in active}
    urls = [entry['url'] for entry in search]
    if set(urls) != expected or len(urls) != len(expected):
        errors.append('Offline search coverage missing or duplicated.')
    for entry in search:
        source = (ROOT / entry['url']).read_text()
        article = re.search(r'<article id="main">(.*?)</article>', source, re.S)
        if not article or entry['text'] != plain_text(article[1]):
            errors.append(f'{entry["url"]}: stale search text')
    for name in ['BP_PlayerCharacter', 'BP_EnemyBase']:
        if assets[name]['parent'] != 'PaperZDCharacter → PaperCharacter → Character':
            errors.append(f'{name}: incorrect character base')
    if assets['BP_NPCBase']['parent'] != 'Actor':
        errors.append('Stationary NPC Actor base changed unnecessarily.')
    required = ['Paper2D = 2D assets', 'PaperZD = complex character', 'Gameplay systems = authoritative',
                'Windup/Active/Recovery', 'body/session identity', 'cannot depend on the notify',
                'never changes or seeks the body Sprite', 'does not execute a gameplay jump']
    animation = plain_text((ROOT / 'systems/animation.html').read_text())
    for phrase in required:
        if phrase not in animation:
            errors.append(f'Animation contract missing boundary: {phrase}')
    evidence = json.loads((ROOT / 'sources/cpp-engineering-evidence.json').read_text())
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in ['original-roadmap.html', 'sources/asset-manifest.json']}
    preserved = (hashes['original-roadmap.html'] == evidence['original_roadmap_sha256'] and
                 hashes['sources/asset-manifest.json'] == evidence['asset_manifest_sha256'])
    if not preserved:
        errors.append('Historical roadmap/manifest bytes changed.')
    report = dict(date='2026-10-05', check='Paper2D + PaperZD static documentation verification',
                  current_assets=len(manifest), asset_pages=len(actual), html_pages_checked=len(active),
                  search_entries=len(search), folders=len({a['folder'] for a in manifest}),
                  phase_counts=[len(orders[str(i)]) for i in range(12)],
                  type_counts=dict(sorted(Counter(a['type'] for a in manifest).items())),
                  historical_sources_preserved=preserved, preserved_sha256=hashes, errors=errors,
                  unreal_editor_run=False, game_build_run=False, blueprints_compiled=False,
                  runtime_tests_run=False, packaged_game_run=False, installed_paperzd_compatibility_verified=False)
    if args.write_report:
        (ROOT / 'sources/paperzd-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Passed: {len(manifest)} current assets, {len(active)} HTML pages, search/index coverage and animation boundaries; historical sources preserved.')


if __name__ == '__main__':
    main()
