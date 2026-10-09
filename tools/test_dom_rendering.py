#!/usr/bin/env python3
"""Render provided HTML/CSS in memory. Does not test file:// navigation or persistence."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser',default='/usr/bin/chromium')
    parser.add_argument('--screenshots',type=Path,required=True)
    parser.add_argument('--write-report',action='store_true')
    arguments=parser.parse_args()
    arguments.screenshots.mkdir(parents=True,exist_ok=True)
    results=[]
    script_errors=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path=arguments.browser,headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.set_default_timeout(5000)
        page.on('pageerror',lambda error:script_errors.append(str(error)))
        def render(name):
            text=(ROOT/name).read_text(encoding='utf-8')
            text=re.sub(r'<script\b[^>]*>.*?</script>','',text,flags=re.S)
            text=re.sub(r'<link\b[^>]*rel="stylesheet"[^>]*>','',text)
            text=text.replace('</head>','<style>'+(ROOT/'site/style.css').read_text()+'</style></head>')
            page.set_content(text,wait_until='domcontentloaded')
            if name=='search.html':page.add_script_tag(content=(ROOT/'site/search-data.js').read_text())
            page.add_script_tag(content=(ROOT/'site/app.js').read_text())
        def test(name,function):
            try:
                function();results.append({'name':name,'status':'pass'})
            except Exception as error:
                results.append({'name':name,'status':'fail','error':str(error)})
        def require(condition,message):
            if not condition:raise AssertionError(message)
        def layout():
            render('index.html')
            page.screenshot(path=str(arguments.screenshots/'home-desktop.png'),full_page=True)
            page.locator('#theme-toggle').click()
            require(page.locator('html').get_attribute('data-theme')=='dark','theme toggle')
            page.screenshot(path=str(arguments.screenshots/'home-dark.png'),full_page=True)
            render('assets/Fishing/URPGFishingComponent.html')
            page.screenshot(path=str(arguments.screenshots/'fishing-contract.png'))
            page.set_viewport_size({'width':390,'height':844})
            for name in ['index.html','phases/phase-12.html','asset-index.html','assets/Fishing/URPGFishingComponent.html']:
                render(name)
                require(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'horizontal document overflow: '+name)
            render('phases/phase-12.html')
            page.screenshot(path=str(arguments.screenshots/'phase-mobile.png'))
            page.set_viewport_size({'width':1440,'height':1000})
        test('provided HTML/CSS desktop/dark/mobile rendering',layout)
        def registry():
            render('asset-index.html')
            page.locator('#asset-filter').fill('IronHatchet')
            require(page.locator('#asset-table tbody tr:visible').count()>0,'filter empty')
            page.locator('#asset-filter').fill('')
            page.locator('#asset-category').select_option('Fishing')
            require(page.locator('#asset-table tbody tr:visible').count()>0,'category empty')
            page.locator('#asset-category').select_option('')
            page.locator('[data-sort="phase"]').click()
            phases=page.locator('#asset-table tbody tr').evaluate_all('(rows)=>rows.map(row=>Number(row.dataset.phase))')
            require(phases==sorted(phases,reverse=True),'numeric sort')
        test('in-memory asset filter/category/sort DOM',registry)
        def search():
            render('search.html')
            page.locator('#search-query').fill('fishing')
            require(page.locator('#search-results article').count()>0,'no search matches')
            require('fish' in page.locator('#search-results a').first.inner_text().lower(),'relevance')
            page.locator('#search-query').fill('<img src=x onerror=alert(1)>')
            require(page.locator('#search-results img').count()==0,'HTML injection')
        test('in-memory search result construction and inert input',search)
        def progress():
            render('checklist.html')
            first=page.locator('[data-progress-id="phase-00-read"]')
            first.check()
            require(first.is_checked(),'checkbox state')
            valid={'schemaVersion':1,'progress':{'phase-00-read':True,'phase-01-read':True}}
            page.locator('#progress-import').set_input_files({'name':'progress.json','mimeType':'application/json','buffer':json.dumps(valid).encode()})
            page.wait_for_function('document.querySelector("[data-progress-id=phase-01-read]").checked')
            invalid={'schemaVersion':1,'progress':{'invented':True}}
            page.locator('#progress-import').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':json.dumps(invalid).encode()})
            page.wait_for_function('document.querySelector("#progress-status").textContent.includes("Import rejected")')
            require(first.is_checked(),'rejected import mutated progress')
        test('in-memory checkbox and import schema handling',progress)
        test('no script errors in provided DOM',lambda:require(not script_errors,str(script_errors)))
        version=browser.version
        browser.close()
    failures=[result for result in results if result['status']=='fail']
    report={'status':'pass' if not failures else 'fail','summary':f'{len(results)-len(failures)} of {len(results)} in-memory DOM/render groups passed; file/HTTP navigation and persistent storage NOT verified.','generated_at':datetime.now(timezone.utc).isoformat(),'command':'python tools/test_dom_rendering.py --screenshots <diagnostic-folder> --write-report','browser':version,'method':'Playwright set_content plus provided CSS and JavaScript; no URL navigation or changed browser policies','tests':results,'script_errors':script_errors,'not_verified':['file:// loading/navigation','localhost HTTP loading/navigation','localStorage persistence across real pages/reloads','actual export download','assistive technology and other browsers','Unreal/game UI']}
    if arguments.write_report:(ROOT/'reports/dom-render-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'].upper()+': '+report['summary'])
    for failure in failures:print(failure)
    return 1 if failures else 0
if __name__=='__main__':raise SystemExit(main())
