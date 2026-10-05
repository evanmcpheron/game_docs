#!/usr/bin/env python3
"""Rebuild current asset tables, dependency lists, phase orders and displayed counts."""
import argparse
from collections import Counter
from html import escape
import json
import posixpath
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def href(source, target):
    return posixpath.relpath(target, str(Path(source).parent))


def asset_link(asset, source):
    return f'<a href="{href(source, asset["doc"])}"><code>{escape(asset["name"])}</code></a>'


def asset_table(items, source, filtered=False):
    rows = []
    for asset in items:
        attrs = ''
        if filtered:
            attrs = (f' data-asset="{asset["name"]}" data-type="{escape(asset["type"], quote=True)}"'
                     f' data-phase="{asset["phase"]}" data-folder="{asset["folder"]}"')
        rows.append(f'<tr{attrs}><td>{asset_link(asset, source)}</td><td>{escape(asset["type"])}</td>'
                    f'<td><code>{escape(asset["parent"])}</code></td>'
                    f'<td><a href="{href(source, f"phases/phase-{asset['phase']:02}.html")}">{asset["phase"]}</a></td>'
                    f'<td><code>{asset["folder"]}</code></td><td>{escape(asset["purpose"])}</td></tr>')
    return ''.join(rows)


def replace_table(source, header, rows):
    pattern = r'(<table[^>]*><thead><tr><th[^>]*>' + re.escape(header) + r'</th>.*?</thead><tbody>).*?(</tbody>)'
    return re.sub(pattern, lambda m: m[1] + rows + m[2], source, flags=re.S)


def build_outputs():
    manifest = json.loads((ROOT / 'sources/current-asset-manifest.json').read_text())
    assets = {a['name']: a for a in manifest}
    orders = json.loads((ROOT / 'sources/phase-creation-order.json').read_text())
    count = len(manifest)
    types = Counter(a['type'] for a in manifest)
    folders = Counter(a['folder'] for a in manifest)
    phase_counts = Counter(a['phase'] for a in manifest)
    outputs = {}
    for path in sorted(ROOT.rglob('*.html')):
        rel = path.relative_to(ROOT).as_posix()
        if path.name in ['original-roadmap.html', 'audit.html'] or rel.startswith('engineering/'):
            continue
        source = path.read_text()
        source = re.sub(r'All \d+ assets', f'All {count} assets', source)
        source = re.sub(r'all \d+ assets', f'all {count} assets', source)
        items = None
        if rel == 'asset-index.html':
            items = sorted(manifest, key=lambda a: a['name'])
            source = re.sub(r'(<select id="type-filter">).*?(</select>)',
                            lambda m: m[1] + '<option value="">All types</option>' + ''.join(
                                f'<option value="{escape(t, quote=True)}">{escape(t)}</option>' for t in sorted(types)) + m[2], source, flags=re.S)
            source = re.sub(r'\d+ of \d+ assets shown', f'{count} of {count} assets shown', source)
        elif rel.startswith('assets/') and path.name == 'index.html':
            folder = f'Content/Game/{path.parent.name}/'
            items = sorted((a for a in manifest if a['folder'] == folder), key=lambda a: a['name'])
            source = re.sub(r'\d+ registered asset\(s\)', f'{len(items)} registered asset(s)', source)
        elif rel.startswith('phases/'):
            phase = int(path.stem[-2:])
            items = [assets[name] for name in orders[str(phase)]]
            source = re.sub(r'\d+ new assets', f'{len(items)} new assets', source)
            steps = []
            for asset in items:
                instruction = 'Create/configure and save before assigning references.'
                if asset['type'] == 'PaperZD Animation Source':
                    instruction = 'Create the native Flipbook Animation Source; save before authoring sequences.'
                elif asset['type'] == 'PaperZD Animation Sequence':
                    instruction = 'Create through its Animation Source editor; assign its documented flipbook and save.'
                elif asset['type'] == 'PaperZD Animation Blueprint':
                    instruction = 'Select its Animation Source, build current-phase states, compile and assign AnimInstanceClass.'
                elif asset['type'] == 'Data Asset instance':
                    instruction = 'Choose its compiled schema; fill references after the required content exists.'
                elif asset['type'].startswith('Blueprint'):
                    instruction = 'Create the exact parent/type and save/compile the shell before adding dependent fields.'
                steps.append(f'<li>{asset_link(asset, rel)} — {instruction}</li>')
            source = re.sub(r'(<h3>Save/compile checkpoints</h3><ol>).*?(</ol>)',
                            lambda m: m[1] + ''.join(steps) + m[2], source, flags=re.S)
        if items is not None:
            source = replace_table(source, 'Asset name', asset_table(items, rel, rel == 'asset-index.html'))
        if rel == 'dependency-map.html':
            def names(values):
                return ', '.join(asset_link(assets[n], rel) for n in values) or 'Native plugin/engine types or local request only'
            rows = ''.join(f'<tr><td>{asset_link(a, rel)}</td><td>{names(a["deps"])}</td><td>{names(a["users"])}</td></tr>'
                           for a in sorted(manifest, key=lambda a: a['name']))
            source = replace_table(source, 'Asset', rows)
        if rel in ['index.html', 'asset-index.html']:
            for folder, number in folders.items():
                name = folder.split('/')[-2]
                source = re.sub(r'(<section class="card"><span class="num">)\d+( assets</span><h3><a href="assets/' + name + r'/index.html">)',
                                lambda m: m[1] + str(number) + m[2], source)
            if rel == 'index.html':
                source = re.sub(r'\d+ documented assets', f'{count} documented assets', source)
                start = source.find('<h2 id="browse-by-asset-type">')
                end = source.find('<h2 ', start + 5)
                if start >= 0:
                    cards = '<div class="cards">' + ''.join(f'<section class="card"><span class="num">{number} assets</span><h3><a href="asset-index.html?type={escape(t, quote=True)}">{escape(t)}</a></h3><p>Filter the current index by asset type.</p></section>' for t, number in sorted(types.items())) + '</div>'
                    source = source[:start] + '<h2 id="browse-by-asset-type">Browse by asset type</h2>' + cards + source[end:]
        if rel == 'development-roadmap.html':
            for phase, number in phase_counts.items():
                source = re.sub(r'(PHASE ' + f'{phase:02}' + r' · )\d+( ASSETS)', lambda m: m[1] + str(number) + m[2], source)
        if rel.startswith('assets/') and path.stem in assets:
            asset = assets[path.stem]
            dependency_rows = ''.join(f'<tr><td>{asset_link(assets[n], rel)}</td><td>{escape(assets[n]["type"])}</td><td>{assets[n]["phase"]}</td><td>{"Later-phase extension" if assets[n]["phase"] > asset["phase"] else "Compile/load prerequisite"}; use only when that phase arrives.</td></tr>' for n in asset['deps'])
            source = replace_table(source, 'Required type/configuration', dependency_rows)
            source = replace_table(source, 'Dependency', dependency_rows)
            source = replace_table(source, 'Depends on / type or configuration reference', dependency_rows)
            source = re.sub(r'(<h3>Used by / direct known consumers</h3><p>).*?(</p>)',
                            lambda m: m[1] + (', '.join(asset_link(assets[n], rel) for n in asset['users']) or 'Phase recipe / local request') + '.' + m[2], source, flags=re.S)
            source = re.sub(r'(<p><strong>Known direct consumers:</strong>).*?(</p>)',
                            lambda m: m[1] + ', '.join(asset_link(assets[n], rel) for n in asset['users']) + '.' + m[2], source, flags=re.S)
        if source != path.read_text():
            outputs[path] = source
    app = ROOT / 'site/app.js'
    source = app.read_text()
    source = re.sub(r"count\+' of \d+ assets shown'", f"count+' of {count} assets shown'", source)
    if source != app.read_text():
        outputs[app] = source
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = build_outputs()
    if args.check and outputs:
        raise SystemExit('Stale manual indexes: ' + ', '.join(str(p.relative_to(ROOT)) for p in outputs))
    for path, source in outputs.items():
        path.write_text(source)
    print(f'Manual indexes current; {len(outputs)} files updated.')


if __name__ == '__main__':
    main()
