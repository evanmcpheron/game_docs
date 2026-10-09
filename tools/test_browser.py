#!/usr/bin/env python3
"""Smoke-test the offline HTML manual in Chromium through file://, not a server."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import traceback
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', default='/usr/bin/chromium', help='Installed Chromium executable')
    parser.add_argument('--write-report', action='store_true')
    parser.add_argument('--http', action='store_true', help='Test over localhost; this does NOT verify file:// behavior')
    parser.add_argument('--all-pages', action='store_true', help='Load every generated HTML page for script/structure smoke checks')
    parser.add_argument('--screenshots', type=Path, help='Optional diagnostic screenshot folder outside public art sources')
    arguments = parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('NOT RUN: Playwright is not installed. No browser result is claimed.')
        return 2
    server = None
    if arguments.http:
        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *values):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
        Thread(target=server.serve_forever, daemon=True).start()
    base_url = f'http://127.0.0.1:{server.server_port}/' if server else None
    tests = []
    errors = []
    requests = []
    def record(name, action):
        try:
            action()
            tests.append({'name':name,'status':'pass'})
            print('PASS: '+name,flush=True)
        except Exception as exception:
            tests.append({'name':name,'status':'fail','error':str(exception)})
            print('FAIL: '+name+': '+str(exception)[:300],flush=True)
    def require(condition, message):
        if not condition:raise AssertionError(message)
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(executable_path=arguments.browser, headless=True, args=['--no-sandbox'])
        except Exception as exception:
            print('NOT RUN: Chromium launch failed: '+str(exception))
            return 2
        context = browser.new_context(viewport={'width':1440,'height':1000}, accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(5000)
        page.set_default_navigation_timeout(10000)
        page.on('pageerror', lambda exception:errors.append(str(exception)))
        page.on('request', lambda request:requests.append(request.url) if request.url.startswith(('http:','https:')) and not (base_url and request.url.startswith(base_url)) else None)
        def visit(relative):
            page.goto(base_url+relative if base_url else (ROOT/relative).as_uri(),wait_until='load')
        def home():
            visit('index.html')
            require(page.locator('h1').count()==1,'home h1 count')
            require(page.locator('nav[aria-label="Main navigation"] a').count()>=10,'navigation missing')
            page.keyboard.press('Tab')
            require(page.evaluate('document.activeElement.classList.contains("skip")'),'skip link not first focus stop')
        record('home navigation and keyboard skip link ('+('localhost' if base_url else 'file://')+')',home)
        def theme():
            page.locator('#theme-toggle').click()
            require(page.locator('html').get_attribute('data-theme')=='dark','dark theme not applied')
            page.reload(wait_until='load')
            require(page.locator('html').get_attribute('data-theme')=='dark','theme did not persist')
            if arguments.screenshots:
                arguments.screenshots.mkdir(parents=True,exist_ok=True)
                page.screenshot(path=str(arguments.screenshots/'home-dark.png'),full_page=True)
            page.locator('#theme-toggle').click()
        record('light/dark toggle and reload',theme)
        def assets():
            visit('asset-index.html')
            expected=len(json.loads((ROOT/'sources/current-asset-manifest.json').read_text())['assets'])
            require(page.locator('#asset-table tbody tr').count()==expected,'asset row count')
            page.locator('#asset-filter').fill('IronHatchet')
            require(0<page.locator('#asset-table tbody tr:visible').count()<expected,'asset filter ineffective')
            page.locator('#asset-filter').fill('')
            page.locator('#asset-category').select_option('Fishing')
            require(page.locator('#asset-table tbody tr:visible').count()>0,'category filter missing rows')
            page.locator('#asset-category').select_option('')
            page.locator('[data-sort="phase"]').click()
            values=page.locator('#asset-table tbody tr').evaluate_all('(rows)=>rows.map(row=>Number(row.dataset.phase))')
            require(values==sorted(values,reverse=True),'phase descending numeric sort failed')
        record('asset filter, category and numeric sorting',assets)
        def search():
            visit('search.html')
            page.locator('#search-query').fill('fishing')
            require(page.locator('#search-results article').count()>0,'offline search empty')
            first=page.locator('#search-results article a').first
            require('fish' in first.inner_text().lower(),'title relevance failed')
            first.click()
            require(page.url.startswith(base_url or 'file:'),'search link not local')
            visit('search.html')
            page.locator('#search-query').fill('<img src=x onerror=alert(1)>')
            require(page.locator('#search-results img').count()==0,'search injected HTML')
        record('local full-text search, result links and inert input',search)
        def progress():
            visit('checklist.html')
            first=page.locator('[data-progress-id="phase-00-read"]')
            first.check()
            page.reload(wait_until='load')
            require(first.is_checked(),'checkbox did not persist')
            with page.expect_download() as download_info:
                page.locator('#progress-export').click()
            download=download_info.value
            exported=json.loads(Path(download.path()).read_text())
            require(exported['schemaVersion']==1 and exported['progress']['phase-00-read'] is True,'export schema/value incorrect')
            first.uncheck()
            page.locator('#progress-import').set_input_files({'name':'progress.json','mimeType':'application/json','buffer':json.dumps(exported).encode()})
            page.wait_for_function('document.querySelector("[data-progress-id=phase-00-read]").checked')
            bad={'schemaVersion':1,'progress':{'invented-id':True}}
            page.locator('#progress-import').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':json.dumps(bad).encode()})
            page.wait_for_function('document.querySelector("#progress-status").textContent.includes("Import rejected")')
            require(first.is_checked(),'rejected import corrupted existing progress')
        record('progress persistence, real download, import and invalid-import rejection',progress)
        def responsive():
            page.set_viewport_size({'width':390,'height':844})
            for relative in ['index.html','phases/phase-12.html','assets/Gathering/URPGGatheringComponent.html','asset-index.html']:
                visit(relative)
                width=page.evaluate('({document:document.documentElement.scrollWidth,viewport:innerWidth})')
                require(width['document']<=width['viewport']+1,f'page-wide horizontal overflow: {relative}: {width}')
            if arguments.screenshots:
                visit('phases/phase-12.html')
                page.screenshot(path=str(arguments.screenshots/'phase-mobile.png'))
            page.set_viewport_size({'width':1440,'height':1000})
            visit('index.html')
            if arguments.screenshots:
                page.screenshot(path=str(arguments.screenshots/'home-desktop.png'),full_page=True)
                visit('assets/Fishing/URPGFishingComponent.html')
                page.screenshot(path=str(arguments.screenshots/'fishing-contract.png'))
        record('390px responsive reading and table containment',responsive)
        loaded=0
        def all_pages():
            nonlocal loaded
            for item in json.loads((ROOT/'sources/generated-page-index.json').read_text()):
                visit(item['path'])
                require(page.locator('h1').count()==1,'bad heading: '+item['path'])
                require(page.locator('#main').count()==1,'bad main: '+item['path'])
                loaded+=1
        if arguments.all_pages:record('all generated pages load ('+('localhost' if base_url else 'file://')+')',all_pages)
        record('no browser script errors',lambda:require(not errors,str(errors)))
        record('no remote resource requests',lambda:require(not requests,str(requests)))
        version=browser.version
        browser.close()
    failures=[test for test in tests if test['status']=='fail']
    report={'status':('partial_file_protocol_not_verified' if arguments.http else 'pass') if not failures else 'fail','summary':f'{len(tests)-len(failures)} of {len(tests)} browser smoke groups passed; {loaded} generated pages loaded. No Unreal gameplay tested.','generated_at':datetime.now(timezone.utc).isoformat(),'command':'python tools/test_browser.py --browser '+arguments.browser+(' --all-pages' if arguments.all_pages else '')+(' --write-report' if arguments.write_report else '')+(' --http' if arguments.http else ''),'browser':version,'protocol':'localhost_http' if arguments.http else 'file://','pages_loaded':loaded,'tests':tests,'script_errors':errors,'remote_requests':requests,'limitations':['Chromium file:// navigation was attempted but blocked by environment policy (ERR_BLOCKED_BY_ADMINISTRATOR); localhost tests do not prove file:// behavior.' if arguments.http else 'Chromium on this Linux environment only; other browsers/OS file-storage policies not tested.','No assistive-technology audit or Unreal UI/game tests performed.','Screenshots are diagnostic captures of generated documentation, not game/art previews.']}
    if arguments.write_report:(ROOT/'reports/browser-validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if server:
        server.shutdown()
        server.server_close()
    print(report['status'].upper()+': '+report['summary'])
    for failure in failures:print(failure)
    return 1 if failures else 0
if __name__=='__main__':raise SystemExit(main())
