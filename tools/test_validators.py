#!/usr/bin/env python3
"""Mutation-test documentation validators and synthetic ZIP audit boundaries."""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile
import zipfile
from audit_asset_archive import audit
from check_phase_integration import check
from validate_docs import validate
ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-report', action='store_true')
    arguments = parser.parse_args()
    results = []
    with tempfile.TemporaryDirectory(prefix='rpg-doc-validation-') as temporary:
        root = Path(temporary) / 'manual'
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('__pycache__'))
        def test_mutation(name, filename, transform, validator, expected_code):
            target = root / filename
            previous = target.read_text(encoding='utf-8')
            try:
                target.write_text(transform(previous), encoding='utf-8')
                report = validator(root)
                found = any(error['code'] == expected_code for error in report['errors'])
                results.append({'name': name, 'status': 'pass' if found else 'fail', 'expected_detection': expected_code})
            finally:
                target.write_text(previous, encoding='utf-8')
        def json_change(text, mutation):
            value = json.loads(text)
            mutation(value)
            return json.dumps(value)
        test_mutation('broken relative link','index.html',lambda text:text.replace('</main>','<a href="missing-fixture.html">Broken fixture</a></main>'),validate,'BROKEN_LINK')
        test_mutation('duplicate anchor','index.html',lambda text:text.replace('</main>','<div id="main"></div></main>'),validate,'DUPLICATE_ANCHOR')
        test_mutation('duplicate asset identity','sources/current-asset-manifest.json',lambda text:json_change(text,lambda value:value['assets'].append(value['assets'][0].copy())),validate,'DUPLICATE_ASSET')
        test_mutation('invalid planned folder','sources/current-asset-manifest.json',lambda text:json_change(text,lambda value:value['assets'][0].update(path='../escape.h')),validate,'ASSET_PATH')
        test_mutation('missing ownership field','sources/ownership-records.json',lambda text:json_change(text,lambda value:value[0].update(authoritative_owner='')),validate,'MISSING_OWNERSHIP')
        test_mutation('future creation dependency','sources/current-asset-manifest.json',lambda text:json_change(text,lambda value:value['assets'][0]['dependencies'].append(next(asset['id'] for asset in value['assets'] if asset['first_phase']==23))),check,'CREATION_ORDER')
        test_mutation('undeclared phase consumer','sources/phase-integration.json',lambda text:json_change(text,lambda value:value['phases'][0]['reopen'].append({'consumer':'ARPGPlayerCharacter','asset':'URPGGameInstance','change':'Unregistered fixture'})),check,'UNDECLARED_CONSUMER')
        test_mutation('broken UI coverage link','sources/feature-coverage.json',lambda text:json_change(text,lambda value:value['features'][0].update(ui='assets/UI/Missing.html')),validate,'FEATURE_LINK')
        test_mutation('fabricated archive count','sources/verification.json',lambda text:json_change(text,lambda value:value['archive'].update(actual_png_count=2596)),validate,'FABRICATED_ARCHIVE_COUNT')
        test_mutation('unsupported runtime pass','sources/verification.json',lambda text:json_change(text,lambda value:value.update(multiplayer_runtime='passed')),validate,'UNSUPPORTED_RUNTIME_CLAIM')
        test_mutation('missing world return path','sources/world-catalog.json',lambda text:json_change(text,lambda value:value['zones'][0]['routes'][0].__setitem__(2,'gate.invalid')),check,'ZONE_RETURN_PATH')
        fixture = Path(temporary)/'synthetic.zip'
        png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aXZsAAAAASUVORK5CYII=')
        with zipfile.ZipFile(fixture,'w') as archive:
            archive.writestr('fixture/p1_0bas.png',png)
            archive.writestr('fixture/p1_1out.png',png)
            archive.writestr('__MACOSX/fixture/._p1_0bas.png',b'not image data')
            archive.writestr('fixture/readme.txt','Synthetic metadata test; no license grant inferred.')
        report=audit(fixture,Path(temporary)/'audit')
        success=report['actual_png_count']==2 and report['metadata_files_excluded']==1 and report['distinct_png_hashes']==1 and not report['animation_frames_verified'] and not report['license_verified']
        results.append({'name':'synthetic PNG counts/AppleDouble/duplicate hashes/unknown frames','status':'pass' if success else 'fail','scope':'Synthetic fixture only; requested archive unavailable'})
        for name,member,content in [('ZIP traversal rejection','../outside.png',png),('invalid PNG header rejection','fixture/bad.png',b'not PNG')]:
            with zipfile.ZipFile(fixture,'w') as archive:archive.writestr(member,content)
            try:
                audit(fixture,Path(temporary)/'rejected-audit')
                success=False
            except ValueError:success=True
            results.append({'name':name,'status':'pass' if success else 'fail'})
    failures=[result for result in results if result['status']!='pass']
    report={'status':'pass' if not failures else 'fail','summary':f'{len(results)-len(failures)} of {len(results)} documentation/audit self-tests passed; no game tests run.','generated_at':datetime.now(timezone.utc).isoformat(),'command':'python tools/test_validators.py'+(' --write-report' if arguments.write_report else ''),'tests':results}
    if arguments.write_report:(ROOT/'reports/validation-selftest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['status'].upper()+': '+report['summary'])
    for failure in failures:print(failure)
    return 1 if failures else 0
if __name__=='__main__':raise SystemExit(main())
