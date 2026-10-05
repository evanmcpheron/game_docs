#!/usr/bin/env python3
"""Check engineering structure, offline references, search coverage and source preservation."""
import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.references = []
        self.heading_count = 0
        self.main_count = 0
        self.title_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'h1':
            self.heading_count += 1
        if tag == 'title':
            self.title_count += 1
        if tag == 'article' and attrs.get('id') == 'main':
            self.main_count += 1
        for key in ('href', 'src'):
            if key in attrs:
                self.references.append(attrs[key])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-report', action='store_true')
    args = parser.parse_args()
    files = sorted(p for p in ROOT.rglob('*.html') if 'content' not in p.relative_to(ROOT).parts)
    parsed = {}
    for path in files:
        page = PageParser()
        page.feed(path.read_text())
        parsed[path.resolve()] = page
    errors = []
    reference_count = 0
    engineering_files = [p for p in files if p.parent.name == 'engineering']
    for path, page in parsed.items():
        if path.parent.name == 'engineering':
            if len(page.ids) != len(set(page.ids)):
                errors.append(f'{path.name}: duplicate IDs')
            if (page.heading_count, page.main_count, page.title_count) != (1, 1, 1):
                errors.append(f'{path.name}: invalid page landmarks')
        for reference in page.references:
            url = urlsplit(reference)
            if url.scheme or url.netloc:
                continue
            reference_count += 1
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not target.exists():
                errors.append(f'{path.relative_to(ROOT)}: missing {reference}')
            elif url.fragment and target.suffix == '.html':
                target_page = parsed.get(target)
                if target_page is None or unquote(url.fragment) not in target_page.ids:
                    errors.append(f'{path.relative_to(ROOT)}: missing anchor {reference}')
    search = json.loads((ROOT / 'site/search-data.js').read_text().removeprefix('window.GUIDE_SEARCH = ').strip().removesuffix(';'))
    urls = [entry['url'] for entry in search if entry['url'].startswith('engineering/')]
    expected = {str(p.relative_to(ROOT)) for p in engineering_files}
    if set(urls) != expected or len(urls) != len(expected):
        errors.append('Engineering search coverage missing or duplicated.')
    for entry in search:
        if entry['url'].startswith('engineering/') and len(entry['text']) < 100:
            errors.append(f'{entry["url"]}: empty search text')
    evidence = json.loads((ROOT / 'sources/cpp-engineering-evidence.json').read_text())
    preserved = {}
    for filename, key in [('original-roadmap.html', 'original_roadmap_sha256'),
                          ('sources/asset-manifest.json', 'asset_manifest_sha256')]:
        preserved[filename] = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() == evidence[key]
        if not preserved[filename]:
            errors.append(f'{filename}: preserved baseline changed')
    report = dict(date='2026-10-05', check='static documentation validation',
                  html_pages_checked=len(files), engineering_pages=len(engineering_files),
                  local_references_checked=reference_count, engineering_search_entries=len(urls),
                  original_roadmap_preserved=preserved['original-roadmap.html'],
                  asset_manifest_preserved=preserved['sources/asset-manifest.json'],
                  errors=errors, cpp_examples_compiled=False, game_build_run=False,
                  blueprints_compiled=False, packaged_game_run=False)
    if args.write_report:
        (ROOT / 'sources/cpp-engineering-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Passed: {len(engineering_files)} engineering pages, {reference_count} local references, search coverage and preserved source hashes.')


if __name__ == '__main__':
    main()
