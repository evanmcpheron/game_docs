#!/usr/bin/env python3
"""Render the offline manual from its authoritative JSON sources."""
from __future__ import annotations
import argparse
import html
import json
import os
from pathlib import Path
import re
import sys
from registry import derive_sources

ROOT=Path(__file__).resolve().parents[1]
EDITION='2026-10-09-draft-1'
DERIVED = {}
def read(name: str):
    if name in DERIVED:
        return DERIVED[name]
    return json.loads((ROOT/'sources'/name).read_text(encoding='utf-8'))
def escape(value) -> str:
    return html.escape(str(value),quote=True)
def slug(value: str) -> str:
    return re.sub(r'[^a-z0-9]+','-',value.lower()).strip('-')
def relative(target: str,current: str) -> str:
    path,separator,fragment=target.partition('#')
    return os.path.relpath(path or current,Path(current).parent).replace(os.sep,'/')+(separator+fragment if separator else '')

class ManualBuilder:
    def __init__(self):
        self.assets=read('current-asset-manifest.json')['assets']
        self.asset_by_id={a['id']:a for a in self.assets}
        self.features=read('feature-specifications.json')
        self.feature_by_id={f['id']:f for f in self.features}
        self.phases=read('phases.json')
        self.integrations=read('phase-integration.json')['phases']
        self.references={r['id']:r for r in read('references.json')}
        self.fixtures=read('test-world-fixtures.json')
        self.pages={}
        self.outputs={'sources/'+name:json.dumps(value,indent=2,ensure_ascii=False)+'\n' for name,value in DERIVED.items()}
        self.catalog_paths=set()
        self.asset_token=re.compile(r'\b(?:'+ '|'.join(re.escape(i) for i in sorted(self.asset_by_id,key=len,reverse=True))+r')\b')
    def link(self,target: str,label: str,current: str) -> str:
        return f'<a href="{escape(relative(target,current))}">{escape(label)}</a>'
    def text(self,value,current):
        text=str(value)
        pattern=re.compile(self.asset_token.pattern+r'|\b(?:[a-zA-Z0-9_-]+/)*[a-zA-Z0-9_-]+\.html\b')
        pieces=[];last=0
        for match in pattern.finditer(text):
            pieces.append(escape(text[last:match.start()]));token=match.group()
            target=self.asset_by_id[token]['page'] if token in self.asset_by_id else token
            pieces.append(self.link(target,token,current) if token in self.asset_by_id or target in self.catalog_paths else escape(token))
            last=match.end()
        pieces.append(escape(text[last:]));return ''.join(pieces)
    def paragraph(self,text,current):return '<p>'+self.text(text,current)+'</p>'
    def ordered(self,rows,current):return '<ol>'+''.join('<li>'+self.text(row,current)+'</li>' for row in rows)+'</ol>'
    def table(self,headers,rows,current,raw=False,attributes=''):
        output=f'<div class="table-wrap" tabindex="0" role="region" aria-label="Scrollable data table"><table {attributes}><thead><tr>'
        output+=''.join('<th scope="col">'+escape(h)+'</th>' for h in headers)+'</tr></thead><tbody>'
        for row in rows:
            output+='<tr>'+''.join('<td>'+(str(cell) if raw else self.text(cell,current))+'</td>' for cell in row)+'</tr>'
        return output+'</tbody></table></div>'
    def section(self,title,body):return '<section><h2 id="'+slug(title)+'">'+escape(title)+'</h2>'+body+'</section>'
    def add(self,path,title,lead,body,group='Guide',refs=None):
        if path in self.pages:raise ValueError('Duplicate page '+path)
        self.pages[path]=dict(title=title,lead=lead,body=body,group=group,refs=refs or [])
    def asset_link(self,identity,current):return self.link(self.asset_by_id[identity]['page'],identity,current)
    def reference_html(self,identities):
        if not identities:return ''
        parts=[]
        for identity in dict.fromkeys(identities):
            if identity not in self.references:raise ValueError('Unknown source reference '+identity)
            r=self.references[identity]
            parts.append('<li><a href="'+escape(r['url'])+'" rel="noopener noreferrer">'+escape(r['title'])+'</a> — '+escape(r['evidence'])+'</li>')
        return self.section('Evidence and external references','<p>External links need internet; the manual itself remains offline. Public documentation does not prove installed compatibility.</p><ul>'+''.join(parts)+'</ul>')
    def feature_refs(self,f):
        if f['id'] in ['presentation','camera','audio-vfx']:return ['EPIC-PAPER2D','PAPERZD-FAB']
        if f['id'] in ['locomotion','swimming']:return ['EPIC-MOVEMENT']
        if f['id'] in ['combat-gas','targeting','attacks','effects']:return ['EPIC-GAS','EPIC-ASC']
        if f['id'] in ['zone-travel','fast-travel','dungeons-bosses']:return ['EPIC-TRAVEL']
        if f['id'] in ['deployment','network-performance','dedicated-server']:return ['EPIC-SERVER','EPIC-NET','EPIC-IRIS']
        if f['phase']>=4 and f['id'] not in ['optional-expansions','input-ui']:return ['PG-ISOLATION']
        return ['EPIC-NET','EPIC-REFLECTION']
    def editorial(self):
        for record in read('page-content.json'):
            path=record['path'];body=''
            for s in record['sections']:
                part=''.join(self.paragraph(p,path) for p in s['paragraphs'])
                if 'steps' in s:part+=self.ordered(s['steps'],path)
                if 'table' in s:part+=self.table(s['table']['headers'],s['table']['rows'],path)
                body+=self.section(s['title'],part)
            self.add(path,record['title'],record['lead'],body,path.split('/')[0].title() if '/' in path else 'Guide',record['references'])
    def feature_pages(self):
        for f in self.features:
            path=f['page'];body=''
            body+=self.section('Scope and player interaction',self.paragraph(f['purpose'],path)+self.table(['Stage','Meaning'],[[f"First integration: Phase{f['phase']:02d}",f['scope']+'; full feature contract may include explicitly staged later extensions'],['Evidence','Authored implementation specification; no native/Blueprint/backend runtime verified']],path))
            body+=self.section('UI state machine',self.paragraph(' → '.join(f['ui_states']),path)+self.paragraph(f"{f['widget']} observes results from {f['owner']}. Pending is not Accepted. Close/cancel clears local focus and stale callbacks, but cannot undo an already committed backend command.",path))
            body+=self.section('Definitions, fields and units',self.paragraph(f"Canonical definition: {f['definition']}. Stable IDs, quantities, seconds and centimeters are validated by the owner, not inferred from translated labels or sprites.",path)+self.table(['Field / rule'],[[x] for x in f['fields']],path))
            body+=self.section('C++ / Blueprint / backend ownership',self.table(['Layer','Responsibility'],[[f['owner'],'Implement the native validated request/state lifecycle described below; native runtime state is not editable by UMG.'],['Blueprint/Data Assets','Tune the declared defaults and visual/asset assignments. Keep definition references EditDefaultsOnly/BlueprintReadOnly; cosmetic hooks cannot grant rewards.'],['Zone server','Validate live actor ownership, range/LOS, alive/action state, cooldown/tool/target rules and current session epoch where relevant.'],['Backend','For durable changes, revalidate trusted catalog/revision/ownership and commit records/source claims/receipt atomically. Read-only/cosmetic features have no durable mutation.'],[f['widget'],'Local observer/requester. Create only for local player; bind once, refresh immediately, unbind on teardown.']],path))
            body+=self.section('Custom command contracts',self.paragraph('These names are project custom APIs or backend proposals, not existing Unreal/PaperZD nodes. Economic/backend requests are asynchronous; Pending resolves through the same command ID. Pure local queries are synchronous unless noted.',path)+self.table(['Command / result'],[[x] for x in f['commands']],path))
            body+=self.section('End-to-end command and observation flow',self.ordered(f['flow'],path))
            body+=self.section('Editor configuration and real consumers',self.ordered(f['editor_steps'],path)+self.paragraph(f"Reopen Phase{f['phase']:02d} integration entries after creating the assets. Test fixture: {f['fixture']}. No later-phase runtime dependency should be activated before its recorded integration phase.",path))
            body+=self.section('Failure, contention and recovery acceptance',self.table(['Test stimulus and expected result'],[[x] for x in f['failures']],path)+self.paragraph('Repeat the success route with two clients when networking exists, then disconnect immediately before/after a committed result. Query the same command and compare authoritative snapshot/receipt with UI. Restart the relevant zone, reject stale epochs, and rerun the previous phase route. Pure visual/input features instead verify cleanup and unchanged server facts. These are future test recipes, not reported passes.',path))
            body+=self.section('Tuning, accessibility and observability',self.paragraph(f['tuning'],path)+self.paragraph(f['observability'],path))
            body+=self.section('Art gaps, production and do-not-build-yet',self.paragraph('The asset ZIP and installed PaperZD APIs remain unverified. Required new art/unsupported layer combinations are tracked in art/animation-matrix.html and art/equipment-visual-matrix.html. A legal debug visual can prove authority but is not finished content. Production features listed as later/optional remain disabled until their phase/gate passes.',path))
            ids=f['asset_ids']
            body+=self.section('Registered implementation assets',self.table(['Asset','Type','Create phase'],[[self.asset_link(i,path),escape(self.asset_by_id[i]['type']),str(self.asset_by_id[i]['first_phase'])] for i in ids],path,raw=True))
            body+=self.section('Integration and related records',self.paragraph(f"phases/phase-{f['phase']:02d}.html · ownership.html · architecture/state-transactions.html · engineering/naming-and-content.html",path))
            self.add(path,f['title'],f['purpose'],body,'System',self.feature_refs(f))
    def asset_pages(self):
        for a in self.assets:
            path=a['page'];f=next((self.feature_by_id[i] for i in a['features'] if i in self.feature_by_id),None)
            body=self.section('Identity and evidence',self.table(['Property','Contract'],[[key,value] for key,value in [('Name',a['id']),('Type / parent',a['type']+' / '+a['parent']),('Planned physical path',a['path']),('Planned object path',a['object_path'] or 'Not a Content Browser object'),('Creation / last consumer phase',f"{a['first_phase']:02d} / {a['last_phase']:02d}"),('Owner',a['owner']),('Lifetime',a['lifespan']),('Production status',a['production_status']),('Maturity',a['maturity']),('Evidence','Planned documentation contract. No engine asset, native file or backend model is implemented by this HTML page.')]],path))
            body+=self.section('Purpose and exclusions',self.paragraph(a['purpose'],path)+self.paragraph(a['exclusions'],path))
            config=a['configuration'] or self.default_creation(a)
            body+=self.section('Creation and configuration',self.ordered(config,path)+self.paragraph('Required sequence: create native prerequisites -> actual build -> child/data creation -> configure -> assign to listed consumer -> save -> run named fixture. A compiled shell without its consumer assignment is not feature completion.',path))
            fields=a['fields'] or (f['fields'] if f else ['Stable identity and revision: required for persistent/definition records; unknown or duplicate IDs rejected.','Typed owner/dependency references injected during readiness; never discover authoritative owners through an unbounded world scan.'])
            body+=self.section('Components, fields, identifiers and permissions',self.table(['Property / proposed value','Access and validation'],[[x,self.field_access(a)] for x in fields],path))
            if a['type'] in ['Data Asset','Native schema','Native structure','Native enumeration','Gameplay Tag set','Paper2D Flipbook','PaperZD Animation Sequence','Material','Texture','Static Mesh','Paper2D Sprite','Data Table','Blackboard','Behavior Tree','Input Action','Input Mapping Context']:
                commands=['Read/resolve this authored definition through its registered consumer; no direct persistent mutation function belongs on the asset.','Editor validation checks required fields, allowed values, dependency presence and version; failed content validation blocks feature readiness.']
            else:commands=a.get('commands',f['commands'] if f else [self.default_command(a)])
            body+=self.section('Functions, commands and event bindings',self.paragraph('Project custom contracts are not engine/plugin nodes. A read-only asset participates through its consumer; it does not inherit that consumer’s mutation methods. Backend endpoint pages label transport proposals explicitly.',path)+self.table(['Contract','Execution / effect'],[[x,self.command_execution(a)] for x in commands],path))
            if 'endpoint' in a:
                endpoint=a['endpoint'];body+=self.section('Backend endpoint schema',self.table(['Field','Proposal'],[[k,v] for k,v in endpoint.items() if k not in ['id','feature']],path))
            if 'database_model' in a:
                model=a['database_model'];body+=self.section('Database constraints and migration',self.table(['Key','Specification'],[[k,v] for k,v in model.items() if k not in ['id','columns','checks']],path))
            body+=self.section('Ownership, replication and persistence',self.table(['Concern','Policy'],[['Authority',a['owner']],['Replication',a['replication_role']],['Durability',a['persistence_role']],['Client observation','Local UI reads safe accepted projections. No tokens/private economy data broadcast to other players.'],['Failure','Reject invalid definitions before mutation. On uncertain durable result query same command receipt; stale session epochs cannot commit.']],path))
            dependencies=[[self.asset_link(d,path),'Creation prerequisite',f"{self.asset_by_id[d]['first_phase']:02d}",'Create and verify before this asset'] for d in a['dependencies']]
            dependencies += [[self.asset_link(r['asset'],path),'Later assignment',f"{r['phase']:02d}",escape(r['assignment'])] for r in a['references']]
            body+=self.section('Dependencies and required assignments',self.table(['Asset','Relationship','Phase','Action'],dependencies,path,raw=True) if dependencies else self.paragraph('No project-asset prerequisite beyond the listed native/Editor parent and environment. This does not remove its integration/test requirement.',path))
            body+=self.section('Reverse consumers: reopen these assets',self.table(['Consumer','Phase','Relationship'],[[self.asset_link(u['asset'],path),f"{u['phase']:02d}",escape(u['kind'])] for u in a['users']],path,raw=True) if a['users'] else self.paragraph('This asset is a phase/catalog entry point or isolated acceptance fixture. Its feature/phase integration below is the explicit consumer; do not assume an unused leaf runs automatically.',path))
            lifecycle=self.lifecycle(a)
            body+=self.section('Lifecycle and cleanup',self.ordered(lifecycle,path))
            if f:
                body+=self.section('Concrete player-to-authority flow',self.paragraph('Participation in '+f['title']+'. Rule owner: '+f['owner']+'. This asset’s role is '+a['purpose'],path)+self.ordered(f['flow'],path))
                fixture=f['fixture'];tests=f['failures'][:4]
            else:
                fixture=self.phases[a['first_phase']]['map']+' / TEST_Phase'+f"{a['first_phase']:02d}"
                tests=[f"Remove {a['id']} from its required assignment: ready-state validation reports the missing asset/contract instead of silently proceeding.",f"Restore {a['id']} and restart the fixture: one owner/spawn/binding remains; no duplicate persistent mutation.",'After networking is active, a second client sees only approved public state; private records remain private.']
                body+=self.section('Concrete integration flow',self.ordered(self.asset_flow(a),path))
            body+=self.section('Named fixture and acceptance',self.paragraph('Fixture: '+fixture+'. Configure this asset at its first phase and run the linked phase recipe. Actual result: not run in Unreal/backend during documentation generation.',path)+self.table(['Stimulus / expected result'],[[x] for x in tests],path)+self.paragraph('Record expected/observed separately. Reopen the concrete map consumer; inspect authoritative state, stable IDs/revisions and UI. Static link checks cannot satisfy this gameplay test.',path))
            if a['type']=='Map' and a['id'] in self.fixtures:
                record=self.fixtures[a['id']];body+=self.section('Exact graybox fixture edits',self.paragraph(record['description'],path)+self.table(['Actor label / identity','Class or role','Proposed placement / assignment'],record['actors'],path))
            body+=self.section('Common mistakes and staged limits',self.paragraph(self.mistake(a),path)+self.paragraph('Do not build later references as empty shells in an earlier phase. Source-derived art rows remain blocked by the missing ZIP; plugin API bindings remain blocked by installed-source verification. Placeholder visuals and proposed tuning are explicitly not production proof.',path))
            body+=self.section('Phase and system navigation',self.paragraph(f"phases/phase-{a['first_phase']:02d}.html · asset-index.html · dependency-map.html · engineering/naming-and-content.html",path)+''.join(self.paragraph(self.feature_by_id[i]['page'],path) for i in a['features'] if i in self.feature_by_id))
            refs=['EPIC-REFLECTION'] if a['type'].startswith('Native') else (['PG-ISOLATION'] if a['type'] in ['Database model','API contract','Backend service'] else [])
            self.add(path,a['id'],a['purpose'],body,'Asset · '+a['category'],refs)
    def default_creation(self,a):
        if a['type'].startswith('Native'):
            return ['Create the native '+a['parent']+'-derived role in the registered RPG module path. For Actor classes use Tools > New C++ Class with the actual base; for structs/interfaces/components use the appropriate native declaration rather than an invented asset factory.','Implement only the current-phase contract, expose intended Blueprint tuning/queries, then build the real Development Editor target. No native implementation is included in this repository.','If a registered Blueprint child exists, create it from the successfully compiled native parent; assign the fields below and reopen its declared consumers.']
        return ['Create '+a['id']+' with the listed actual asset/service type at the planned path, after its prerequisites are ready.','Populate the listed required fields and validate identities/references before assigning the asset into the named phase consumer.','Run its concrete fixture and reject missing/incompatible configuration; a named file alone has no gameplay effect.']
    def default_command(self,a):
        name=a['id']
        if name=='ARPGZoneGameMode':return 'AdmitCharacter(ValidatedTicket, Snapshot, Epoch) -> Ready|Rejected; server only, asynchronous durability/readiness before one spawn'
        if name=='ARPGPlayerController':return 'SubmitOwnedIntent(ActionId, TargetId, CommandId) -> Pending|Rejected; local request routed through owned server channel, never an arbitrary world Actor RPC'
        if name=='ARPGPlayerCharacter':return 'InitializeBody(PlayerState, Definition, Epoch) -> Ready|MissingDependency; native idempotent lifecycle; ClearBodyBindings() on unpossession'
        if name=='ARPGPlayerState':return 'ApplyCommittedSnapshot(Snapshot, Epoch) -> Applied|Stale; server/current-session projection, owner-only private replication'
        if name=='ARPGZoneGameState':return 'ApplyZonePublicState(ZoneId, ClockRevision) -> Applied|Stale; server mutation, clients observe'
        return 'InitializeCurrentPhase(ValidatedDependencies, Identity) -> Ready|MissingDependency; custom native/service lifecycle. Observe accepted changes and release timers/delegates/handles on teardown.'
    def field_access(self,a):
        if a['type'] in ['Data Asset','Native schema','Gameplay Tag set','Data Table']:return 'Authored default; EditDefaultsOnly/BlueprintReadOnly when reflected. Validate range/ID/reference; immutable at runtime.'
        if a['type']=='Widget Blueprint':return 'Local view state/read-only model projection; no server rule or durable setter. Text uses FText/localization.'
        if a['type']=='Database model':return 'Backend-only SQL record; constraints/locks/version validation; no direct client mutation.'
        if a['type'] in ['Paper2D Flipbook','PaperZD Animation Sequence','Texture','Material','Static Mesh','Paper2D Sprite']:return 'Cosmetic authoring; provenance and compatible page/frame/pivot required. Not replicated gameplay truth.'
        return 'Typed native state; expose reads/default tuning deliberately. Runtime mutation remains the declared owner, on the game thread where UObject state is involved.'
    def command_execution(self,a):
        if a['type']=='Widget Blueprint':return 'Local only; request asynchronous owner command, observe matching result, clear stale callbacks; never save or grant.'
        if a['type'] in ['API contract','Backend service','Database model']:return 'Authenticated backend transaction/read; asynchronous to zone/client. Commit before success; same-key retry and epoch fencing.'
        if a['type'] in ['Data Asset','Native schema','Native structure','Native enumeration','Input Action','Input Mapping Context','Paper2D Flipbook','PaperZD Animation Sequence','Material','Texture','Static Mesh','Data Table','Gameplay Tag set','Blackboard','Behavior Tree']:return 'Read-only authoring or local intent. The native feature consumer owns rules; no direct durable side effect.'
        return 'Native current owner; local request versus server validation as the command states. Backend work is asynchronous, cosmetics observe only after accepted state.'
    def lifecycle(self,a):
        if a['type'] in ['Data Asset','Native schema','Data Table','Gameplay Tag set','Paper2D Flipbook','PaperZD Animation Sequence','Texture','Material','Static Mesh','Paper2D Sprite','Native enumeration','Native structure']:
            return ['Author and validate stable definition/frame/field identity before use; load through declared references at readiness.','Consumers may cache read-only references for their world/session lifetime; do not mutate the shared definition or place player quantities on it.','On reimport/version change validate compatibility and migrate persistent IDs deliberately. Missing required rules fail closed; missing cosmetic layers use documented fallback.','World/pawn teardown releases runtime references; persistent records retain IDs and versions only. Reconnect resolves the same definition without replaying grants.']
        return ['Construct with only safe defaults; no service calls or world scans from construction scripts.','Inject current owner/definition/session and subscribe once after readiness. Possession and replicated state may arrive in either order; guard initialization.','Accept only permitted commands under current identity/epoch; keep local UI/cosmetic prediction separate from committed state.','After server/backend result apply only matching request generation and nonstale revision; late reply to old body does not mutate new body.','On death, transfer, disconnect, restart or teardown cancel transient work, clear input/timers, unbind delegates and release weak observers. Durable receipts remain authoritative.','On reconnect create fresh runtime objects from current committed snapshot; never deserialize old Actor/widget pointers or rerun initial grants.']
    def asset_flow(self,a):
        if a['type']=='Map':return ['Player selects the zone/admission fixture. Effective GameMode checks readiness and creates one authorized body at a safe spawn.','The body uses this map’s 3D collision/navmesh while local sprites/camera render independently.','Current-phase interactions route to server validators and durable service where needed; map Actor labels are not persistent identities.','Accepted projections update the local HUD and remote players; leaving/reloading the map does not replay source rewards.']
        if a['type']=='Database model':return ['Player action enters the owned request path with a command ID; zone verifies live eligibility.','Backend validates identity/epoch and locks this relation plus required related rows.','Apply the all-or-nothing mutation/receipt or return a rejection without partial effects.','Zone applies committed projection; reconnect reads the same record, while UI only observes.']
        return ['Current phase creates and configures '+a['id']+' with the listed type/parent and required fields.','The declared consumer resolves/injects it at readiness; a missing assignment produces an explicit validation error before the player action.','The player input/world action follows the native feature owner; this asset contributes only its declared role and cannot bypass authority.','Observe the accepted server/backend projection in the named fixture and UI; teardown/restart must not duplicate bindings, Actors or grants.']
    def mistake(self,a):
        if 'PaperZD' in a['type']:return 'Do not invent installed PaperZD factory/property names, reuse an incompatible action page, or make notifies release authoritative gameplay locks.'
        if a['type']=='Widget Blueprint':return 'Do not bind every frame, subscribe twice after possession, show Accepted before commit, trust client displayed currency or keep an old pawn reference after travel.'
        if a['type']=='Data Asset':return 'Do not put mutable stock, current health, inventory quantities or player quest progress on a shared Data Asset. A soft reference still needs validation and readiness.'
        if a['type'] in ['Database model','API contract']:return 'Do not trust client prices/rolls/identity, reuse a command ID with changed payload, hold DB locks during cast timers, or split source claim from reward commit.'
        if a['type']=='Map':return 'Do not preserve the old X/Z plane constraint, duplicate auto-possessed pawns, confuse streaming with server migration, or put an invisible blocking floor over deep water.'
        return 'Do not duplicate a native rule in Blueprint, assume a planned type is compiled, or keep callbacks/owners valid after world or session replacement.'
    def phase_pages(self):
        for p,integration in zip(self.phases,self.integrations):
            n=p['number'];path=f'phases/phase-{n:02d}.html';body=''
            body+=self.section('Purpose, prerequisites and stage',self.paragraph(p['purpose'],path)+self.paragraph('Prerequisites: '+(', '.join(f'phases/phase-{x:02d}.html' for x in p['prerequisites']) or 'None; inspect inputs and tools first.')+' All earlier accepted invariants remain required. Runtime status: not run in this documentation environment.',path))
            body+=self.section('Creation order and physical paths',self.table(['Order','Asset','Type / native parent','Planned path'],[[str(i+1),self.asset_link(identity,path),escape(self.asset_by_id[identity]['type']+' / '+self.asset_by_id[identity]['parent']),escape(self.asset_by_id[identity]['path'])] for i,identity in enumerate(integration['new_assets'])],path,raw=True))
            body+=self.section('Configure current feature',self.ordered(integration['configure'] or self.fixtures[p['map']].get('setup',['Open the current map and confirm effective GameMode/controller/pawn assignments.','Create only the listed native/asset prerequisites, configure their individual contracts and verify one normal spawn before adding later gameplay.']),path))
            body+=self.section('Reopen existing consumers and assign',self.table(['Consumer','New reference','Required change'],[[self.asset_link(r['consumer'],path),self.asset_link(r['asset'],path),escape(r['change'])] for r in integration['reopen']],path,raw=True) if integration['reopen'] else self.paragraph('This phase introduces no later asset-reference rewiring. Its map/test fixture and native configuration still require the steps above.',path))
            fixture=self.fixtures[p['map']]
            body+=self.section('Exact test-world edits',self.paragraph(p['map']+': '+fixture['description'],path)+self.table(['Actor / fixture','Class / role','Proposed location and configuration'],fixture['actors'],path)+self.paragraph('Only place actors whose systems are active in this phase; later rows are staged expansion instructions, not a requirement to build all map content now. Keep placeholders labeled and preserve earlier test sections.',path))
            recipe=integration['run_now']
            run=self.ordered(recipe['steps'],path)+self.table(['Expected success'],[[text] for text in recipe['success']],path)
            body+=self.section('Run now: current-phase integrated scenarios',run)
            body+=self.section('Explicitly not active yet',self.ordered(recipe['deferred'],path))
            body+=self.section('Expected rejection and concurrency results',self.table(['System','Stimulus -> expected outcome'],[[r['feature'],r['expected']] for r in integration['rejections']],path) if integration['rejections'] else self.paragraph('Remove a required reference or use an invalid ID; readiness fails clearly, with no duplicate spawn or partial mutation. Restore it and rerun.',path))
            body+=self.section('Regression, disconnect and restart',self.ordered(integration['regression']+(['From phase03 onward run two separate clients; disconnect A while B remains, then reconnect with the correct identity.','From phase05 onward query committed receipt/revision after timeout/restart. From06 onward reject old source epoch after transfer.'] if n>=3 else ['Before networking, verify local cleanup but do not label it a multiplayer test.']),path))
            body+=self.section('Stop condition and deferred work',self.paragraph(p['stop_condition'],path)+self.paragraph('Stop on a failed required assertion, missing required rule definition, duplicate authority or unverified dependency that this phase relies on. Legal debug art may support physics tests but cannot close the archive/PaperZD art gate. Do not activate future-phase systems merely because their full-game chapter exists.',path)+self.link('checklist.html#phase-'+f'{n:02d}','Record phase progress',path))
            body+=self.section('Feature chapters',''.join(self.paragraph(self.feature_by_id[i]['page'],path) for i in integration['features']) or self.paragraph('engineering/index.html · sources-verification.html',path))
            self.add(path,f'Phase {n:02d} · '+p['title'],p['purpose'],body,'Build phase')
    def indices(self):
        path='index.html'
        body='<div class="status-banner"><strong>Evidence-labeled draft.</strong> Source repository inspected; art archive and installed engine/plugin unavailable. No Unreal or backend runtime tests are claimed.</div>'
        body+='<div class="cards">'+''.join('<a class="card" href="'+escape(target)+'"><strong>'+escape(title)+'</strong><span>'+escape(text)+'</span></a>' for target,title,text in [('getting-started.html','Start building','Environment, vocabulary and first actionable steps'),('development-roadmap.html','24 sequential phases','Creation order, assignments, fixtures and stop conditions'),('asset-index.html',f'{len(self.assets)} planned assets','Individual contracts, paths, dependencies and consumers'),('systems/index.html',f'{len(self.features)} system chapters','Gameplay, authority, data, UI and rejection cases'),('first-vertical-slice.html','Three acceptance slices','Foundation, RPG loop and online-ready proof'),('sources-verification.html','Evidence and limitations','Actual documentation checks versus tests not run')])+'</div>'
        body+=self.section('Build the online foundation before expanding content',self.paragraph('This manual describes RPG, an original 2.5D online action RPG with 3D terrain and layered sprite characters. Dedicated-server authority and durable backend transactions are early dependencies. Rich world content follows working ownership, not the reverse.',path)+self.paragraph('The first art/terrain lab is small. By Slice A two clients connect, move, transfer individually between zone servers, fight and receive XP. Slice B adds the complete village/economy/profession/quest loop. Later phases add classes, biomes, dungeons, social systems and measured operations.',path))
        body+=self.section('Source of truth',self.paragraph('Edit the human/machine source records under sources/ and run the standard-library Python generator/checks in tools/. Do not hand-edit generated HTML/index tables. Every gameplay asset here is a planned specification, not a compiled Unreal artifact.',path))
        self.add(path,'RPG MMO Development Guide','Offline implementation manual · UE 5.8.3 target · C++ authority, Blueprint authoring · October 2026',body)
        path='development-roadmap.html'
        body=self.paragraph('The order refines the suggested roadmap: minimal item/reward schemas precede08 rewards, and minimal party credit contracts precede18 dungeon content even though full party UX arrives19. Definition identities are early; complete UI/content is staged.',path)
        body+=self.table(['Phase','Purpose','Test world','Stop condition'],[[self.link(f"phases/phase-{p['number']:02d}.html",f"{p['number']:02d} · {p['title']}",path),escape(p['purpose']),self.asset_link(p['map'],path),escape(p['stop_condition'])] for p in self.phases],path,raw=True)
        self.add(path,'Development roadmap','Create → build → configure → integrate → edit world → run → reject/regress → continue.',body)
        path='asset-index.html'
        body='<div class="controls"><label for="asset-filter">Filter assets</label><input id="asset-filter" type="search" placeholder="Name, type, category, path or phase"><label for="asset-category">Category</label><select id="asset-category"><option value="">All categories</option>'+''.join('<option>'+escape(c)+'</option>' for c in sorted({a['category'] for a in self.assets}))+'</select><p id="asset-count" role="status"></p></div>'
        body+='<div class="table-wrap" tabindex="0" role="region" aria-label="Sortable asset registry"><table id="asset-table"><thead><tr>'+''.join(f'<th scope="col"><button type="button" data-sort="{key}">{label}</button></th>' for key,label in [('id','Asset'),('type','Type'),('category','Category'),('phase','Phase')])+'<th scope="col">Planned path</th></tr></thead><tbody>'
        for a in self.assets:
            body+=f'<tr data-id="{escape(a["id"])}" data-type="{escape(a["type"])}" data-category="{escape(a["category"])}" data-phase="{a["first_phase"]}"><td>'+self.asset_link(a['id'],path)+'</td><td>'+escape(a['type'])+'</td><td>'+escape(a['category'])+f'</td><td>{a["first_phase"]:02d}</td><td><code>'+escape(a['path'])+'</code></td></tr>'
        body+='</tbody></table></div>'+self.paragraph('Counts describe registered planned assets only. Final source-sheet sprites cannot be enumerated without the missing archive. Sorting/filtering is local; all rows remain readable without JavaScript.',path)
        self.add(path,'Asset registry',f'{len(self.assets)} unique planned assets; each has one individual technical page.',body)
        path='systems/index.html'
        body=self.table(['System','First phase','Scope','Owner'],[[self.link(f['page'],f['title'],path),f"{f['phase']:02d}",escape(f['scope']),self.asset_link(f['owner'],path)] for f in self.features],path,raw=True)
        self.add(path,'System chapters','Player interaction, definitions, native/Blueprint responsibility, commands, integration and expected failures.',body,'Systems')
        path='feature-coverage.html'
        body=self.paragraph(read('feature-coverage.json')['coverage_claim'],path)+self.table(['Feature','Stage','Chapter / UI','Acceptance cases','Status'],[[escape(f['title']),f"{f['first_phase']:02d} / {escape(f['scope'])}",self.link(f['chapter'],'System chapter',path)+' · '+self.link(f['ui'],'UI contract',path),str(f['acceptance_cases']),escape(f['status'])] for f in read('feature-coverage.json')['features']],path,raw=True)
        self.add(path,'Feature coverage','Authored coverage is not runtime completion; source-art enumeration and installed compatibility are explicitly blocked.',body)
        path='dependency-map.html'
        body=self.paragraph('Creation prerequisites are a directed acyclic graph. Integration references are phase-stamped assignments and may legitimately connect collaborators in both directions. Each asset page lists direct prerequisites and reverse consumers. No runtime assignment silently creates a future-phase prerequisite.',path)
        edges=read('dependency-edges.json')['edges']
        body+=self.table(['Consumer / source','Required asset / target','Kind','Phase'],[[self.asset_link(e['source'],path),self.asset_link(e['target'],path),escape(e['kind']),f"{e['phase']:02d}"] for e in edges],path,raw=True)
        self.add(path,'Dependency graph and reverse navigation',f'{len(edges)} explicit creation/assignment edges generated from the manifest.',body)
        path='ownership.html';body=''
        for r in read('ownership-records.json'):
            body+=self.section(r['fact'],self.table(['Concern','Owner / rule'],[[k.replace('_',' ').title(),v] for k,v in r.items() if k not in ['id','fact']],path))
        self.add(path,'Persistent fact ownership','Authority, cache, replication, store, identity, change path, revision, recovery and observer for every registered durable fact.',body)
        path='checklist.html'
        body=self.paragraph('These checkboxes record your local progress, not verified game results from this documentation run. Export regularly: browser file:// storage behavior can vary, and another browser or folder may not share it.',path)
        body+='<div class="controls"><button id="progress-export" type="button">Export progress JSON</button><label for="progress-import">Import progress JSON</label><input id="progress-import" type="file" accept="application/json,.json"><button id="progress-reset" type="button">Reset local progress</button><p id="progress-status" role="status" aria-live="polite"></p></div>'
        for p in self.phases:
            n=p['number'];body+=f'<section><h2 id="phase-{n:02d}">Phase {n:02d} · '+escape(p['title'])+'</h2>'
            for key,label in [('read','Read contracts and evidence gates'),('create','Create/build/configure current assets'),('integrate','Assign consumers and edit named test world'),('success','Run success case and retain actual evidence'),('rejection','Run rejection/concurrency/recovery cases'),('regression','Run previous-phase regression and review stop condition')]:
                identity=f'phase-{n:02d}-{key}';body+=f'<label class="check-row"><input type="checkbox" data-progress-id="{identity}"><span>{escape(label)}</span></label>'
            body+=self.link(f'phases/phase-{n:02d}.html','Open phase recipe',path)+'</section>'
        self.add(path,'Progress checklist','Local completion tracking with explicit JSON export/import; no server or account needed for the manual.',body)
        path='search.html'
        body='<form id="search-form"><label for="search-query">Search all manual text</label><div class="search-bar"><input id="search-query" name="q" type="search" autocomplete="off" placeholder="Try: fishing, session epoch, IronHatchet"><button type="submit">Search</button></div></form><p id="search-status" role="status" aria-live="polite">Enter a term. All search data is local.</p><div id="search-results"></div><noscript><p>JavaScript is disabled. Use the asset registry and system index to browse all pages.</p></noscript>'
        self.add(path,'Search the offline manual','Search descriptions, fields, commands, phase steps and tests without network requests.',body)
        path='network/index.html'
        body=self.table(['Guide','Purpose'],[[self.link('network/'+name+'.html',title,path),escape(desc)] for name,title,desc in [('server-setup','Server setup','Dedicated process and two-client proof'),('character-service','Character service','Authenticated asynchronous durability adapter'),('zone-transfer','Zone transfer','Individual travel and fencing tests'),('security','Security','Ownership, replay, abuse and secrets'),('testing','Network testing','Latency/loss/concurrency/crash cases'),('deployment','Deployment','Readiness, drain, restore and measured capacity')]],path,raw=True)
        self.add(path,'Network and backend guides','Build and operate a small measured online game before adopting scale optimizations.',body,'Network')
    def design_world(self):
        path='design/decisions.html';decisions=read('design-decisions.json')
        rows=decisions.get('decisions',[]) if isinstance(decisions,dict) else decisions
        body=''
        for r in rows:
            body+=self.section(r.get('id','Decision')+' · '+r.get('topic',''),self.table(['Field','Decision'],[[k,v] for k,v in r.items() if k not in ['id','topic']],path))
        self.add(path,'Design-decision register','Source commitments, adopted defaults, proof gates and consequences.',body,'Design')
        path='design/classes.html';body=self.paragraph('Four common-body archetypes. Values below are initial authored examples, not tested balance or a complete level50 content library. Six ability and six talent-node examples per class define production patterns; expansion must preserve DAG/exclusivity/respec validation. Additional points may remain unspent until more content is authored.',path)
        for c in read('class-catalog.json'):
            body+=self.section(c['name']+' · '+c['role'],self.paragraph(c['growth']+' '+c['weapons']+' '+c['art_status'],path)+self.table(['Ability','Type','Cost / cooldown','Timing / effect','Rule'],[[a['asset'],a['kind'],a['cost']+' / '+a['cooldown'],a['timing']+'; '+a['formula'],a['rule']] for a in c['abilities']],path)+self.table(['Node','Cost','Prerequisite','Exclusive group','Effect'],[[t['id'],t['cost'],', '.join(t['requires']) or 'None',t['exclusive_group'] or 'None',t['effect']] for t in c['talents']],path))
        self.add(path,'Classes, abilities and skill-tree examples','Vanguard, Ranger, Arcanist and Warden: authored definitions on one compatible body.',body,'Design')
        world=read('world-catalog.json')
        for path in ['design/world-and-biomes.html','world/index.html']:
            body=self.paragraph('The Talarin Reach is an original connected region whose water-regulation ruins create a regional conflict between frontier services, wardens, survey crews and coastal communities. The first implementation is Hearthford/Rillmere and a small Thornweald receiving courtyard, not six finished environments.',path)
            body+=self.table(['Zone family','Levels (proposal)','First map phase','Guide'],[[escape(z['name']),escape(str(z['levels'])),f"{z['phase']:02d}",self.link('world/'+z['id'].split('.')[1]+'.html','Production brief',path)] for z in world['zones']],path,raw=True)
            body+=self.section('Adjacency diagram: reversible gate pairs',self.table(['Source','Destination','Outgoing gate','Return gate'],[[z['name'],next(t['name'] for t in world['zones'] if t['id']==r[0]),r[1],r[2]] for z in world['zones'] for r in z['routes']],path))
            body+=self.section('Hub and cooperative dungeon',self.paragraph('world/hearthford.html · world/sluice-vault.html · world/biome-authoring.html',path))
            self.add(path,'World and biome catalog',world['world']+' · six design biomes, one initial hub and a staged dungeon.',body,'World')
        for z in world['zones']:
            path='world/'+z['id'].split('.')[1]+'.html';body=self.table(['Identity','Specification'],[['ZoneId',z['id']],['Definition',z['asset']],['Map',z['map']],['Initial map phase',z['phase']],['Level range proposal',z['levels']]],path)
            for title,key in [('Climate, lighting and weather','climate'),('Factions','factions'),('Settlement and service placement','services'),('Travel-time tests','travel'),('Environmental hazards','hazards'),('Quest arc and consequences','arc'),('Landmarks and discovery','landmarks'),('Enemy families','enemies'),('Ore distribution','ore'),('Tree distribution','trees'),('Fish species pools','fish'),('Music and ambience','music'),('3D art production requirements','art'),('Optimization and streaming','optimization')]:
                value=z[key];body+=self.section(title,self.paragraph('; '.join(value) if isinstance(value,list) else value,path))
            body+=self.section('Gate authoring',self.table(['Destination','Outgoing GateId','Receiving/return GateId'],z['routes'],path)+self.paragraph('Author dry clear arrival spawns outside trigger bounds. Validate compatible build/capacity/eligibility before issuing a ticket. Gate labels are not stable identity; use the listed IDs. The reciprocal pair is checked by the documentation validator.',path))
            body+=self.section('Concrete production and test steps',self.ordered(['Create the map/definition according to the asset pages; only activate the first-phase portion now.','Graybox services/roads/water with legal primitives and validate capsule/navigation before art replacement.','Register stable site/gate/encounter/NPC/objective IDs through the existing schemas.','Assign current-phase references in zone runtime and run two-client admission/travel tests.']+z['tests'],path))
            self.add(path,z['name'],z['arc'],body,'World design')
        path='world/hearthford.html';hub=world['hub'];body=self.paragraph(hub['layout'],path)+self.table(['Fixture','Class / role','Placement / integration'],self.fixtures['L_Rillmere']['actors'],path)
        body+=self.section('Playable village chain',self.ordered(['Create/select A, enter shrine, talk to Mara for First Steps and learn interaction without receiving repeated starter grants.','Accept Road Supplies, move onto WestRoad, defeat Mossfang, claim personal loot and record kill/loot objective events.','Mine ore, cut ash, fish from dry pier and craft IronHatchet at forge; use server-approved events to progress objectives.','Buy/sell/buyback a draught, equip sword/shield/cloak under visual compatibility rules, then finish the quest for one XP/currency receipt.','Die/recover and transfer north/reconnect. Verify all IDs/quantities/objectives/appearance remain consistent.'],path))
        self.add(path,'Hearthford first playable village','A compact service and quest loop inside Rillmere, not a separate unnecessary world server.',body,'World')
        path='world/sluice-vault.html';dungeon=world['dungeon'];body=self.table(['Field','Design'],[[k,v] for k,v in dungeon.items()],path)+self.table(['Actor','Role','Configuration'],self.fixtures['L_SluiceVault']['actors'],path)
        body+=self.section('Recovery test','<p>Wipe before boss resolution, disconnect a member after resolution, reload corpse state and expire instance. Verify no extra boss loot/XP, safe return spawns, preserved party identity and one valid member session per epoch. A fresh intended encounter generation must be distinguished from reloading the same completed generation.</p>')
        self.add(path,'Sluice Vault cooperative instance','Bounded four-player dungeon and boss patterns after basic party/zone authority is proven.',body,'World')
        path='world/biome-authoring.html';body=self.paragraph('Use design/content-pipeline.html as the factory specification. This checklist is the per-zone acceptance document for a new authored biome.',path)+self.ordered(['Define ZoneId/map/version/level targets and register reciprocal gate pairs before landscape expansion.','Author a contiguous main route and safe services; measure walking/jump/swim requirements with the actual capsule.','Create candidate resource rows with terrain projection, slope/clearance/path/density tests; persist selected cycles, not invalid random scatter.','Add fishing water regions and dry shoreline access, NPC roles/dialogue/quests and bounded encounters using existing schemas.','Define discovery regions/minimap bounds and time/weather/music presets. Reference IDs, never Actor display labels.','Acquire or author legally usable 3D/2D assets, retain provenance and replace debug art without breaking collision/foot alignment.','Run two-client contention/quest/travel/reconnect, packaged cook, streaming unload/reload and measured performance.','Register all new assets/consumers/phase/test records, regenerate docs and add release/content version.'],path)
        self.add(path,'Author one new biome','Repeatable data/Blueprint content production without routine C++ changes.',body,'World')
    def slices(self):
        path='first-vertical-slice.html';body=''
        slices=[('A','Real multiplayer foundation',8,['Create terrain/art labs and dedicated server; prepare two identities and minimal durable character/item/reward schemas.','Start Zone_A Rillmere and Zone_B Thornweald, connect A+B to A with distinct CharacterIds.','Walk/jump/sprint/dodge/swim on actual 3D terrain; inspect four-direction/debug sprites and remote state.','A uses north gate to Zone_B while B stays in A. Validate ticket/epoch/same durable state; return A.','A+B defeat one server Mossfang under legitimate contribution/party fixture; each gets rules-based XP once.','Disconnect/reconnect and reject old ticket/old source writes.'],'Two remote clients, one character writer each, individual two-zone handoff and once-only legitimate XP; no client SaveGame authority.'),('B','Complete RPG loop',15,['Create/select common-body class appearance and reconnect to verify remote consistency.','Accept village quest, travel to wilderness, defeat creature and claim personal loot.','Cut tree, mine ore and catch fish; two-client resource races grant once and deplete generation.','Craft IronHatchet, disconnect immediately after confirmation, reconnect in another zone and receive exactly one result.','Buy/sell/buyback/repair at merchant, move bank item, equip visible/explicitly stats-only gear and level up.','Complete quest once, die/recover without inventory wipe, cross zones and recheck all persistent records.'],'One integrated village quest/economy/profession loop; all durable commands idempotent and correct under two clients.'),('C','Online-ready measured slice',23,['Provision multiple parties and compatible zone/instance servers; record actual population/build/hardware.','Use talents/respec, party chat/friends/block and secure trade; include guild flow at its committed stage.','Enter/complete SluiceVault with boss telegraphs and personal group loot; recover after wipe/disconnect.','Inject source/destination/backend failures at commit/redeem/ack boundaries; restore staging backup and verify ledger/IDs.','Run latency/jitter/loss and representative actor-load steps; compare generic replication to only one justified alternative if needed.','Build packaged client+dedicated server, run accessibility/localization/version/secret checks and review release blockers.'],'Only the measured tested population is approved; no claim of mass concurrency or completed art from documentation alone.')]
        for label,title,phase,steps,acceptance in slices:
            body+=self.section('Slice '+label+' · '+title,self.paragraph(f'After required phases through{phase:02d}. Status: NOT RUN. '+acceptance,path)+self.ordered(steps,path)+self.table(['Evidence required','Expected'],[['Identity/session','Account/Character IDs, current epoch, one body/lease'],['State durability','Before/after currency/item/quest/profession rows and command/source receipt IDs'],['Multiplayer','Server plus separate client captures and actual network settings'],['Recovery','Crash/replay/reconnect outcomes; no missing acknowledged grant'],['Visual/UI','Appearance/page fallback, owner-only HUD, clear Pending/Rejected/Accepted'],['Scope','Art/API blockers and tuning proposals remain explicitly listed']],path))
        self.add(path,'Three vertical-slice acceptance gates','A reproducible route from two-client authority to the full RPG loop and online-ready operations.',body)
    def verification(self):
        path='sources-verification.html';v=read('verification.json')
        body=self.section('Evidence status',self.table(['Category','Recorded status'],[[k,vv] for k,vv in v.items() if k not in ['archive','publication','acceptance_blockers']],path))
        body+=self.section('Missing dependencies and remaining verification',self.table(['Archive field','Status'],[[k,vv] for k,vv in v['archive'].items()],path)+self.ordered(v['acceptance_blockers'],path))
        report_rows=[]
        for name in ['static-validation.json','phase-integration-validation.json','validation-selftest.json','browser-validation.json','dom-render-validation.json','content-depth-review.json','github-generation.json']:
            report_path=ROOT/'reports'/name
            report=json.loads(report_path.read_text()) if report_path.exists() else {'status':'not_run'}
            report_rows.append([self.link('reports/'+name,name,path),escape(report.get('status','unknown')),escape(report.get('summary','Read report for exact scope; not an Unreal runtime test.'))])
        body+=self.section('Actual documentation validation reports',self.table(['Report','Status','Scope'],report_rows,path,raw=True))
        body+=self.section('Publication status',self.table(['Field','Recorded result'],[[k,vv] for k,vv in v['publication'].items()],path)+'<p>'+self.link('sources/publication-receipt.json','Read the separate publication receipt',path)+'. ZIP generation alone is not a GitHub publication result.</p>')
        body+=self.section('Checked references',self.table(['Reference','Evidence','Checked'],[['<a href="'+escape(r['url'])+'" rel="noopener noreferrer">'+escape(r['title'])+'</a>',escape(r['evidence']),escape(r['checked_date'])] for r in self.references.values()],path,raw=True))
        body+=self.section('No false completion','<p>All planned assets and test recipes are documentation. No Unreal project, compiled Blueprint, engine build, packaged game, live PostgreSQL service, multiplayer benchmark or paid source-art audit was produced here. Passing static/browser documentation checks does not satisfy those implementation gates.</p>')
        self.add(path,'Sources, verification and limitations','Trace checked public documentation, inspected repository records and actual local documentation tests separately.',body)
    def sitemap(self):
        path='all-pages.html';body=''
        groups={}
        for target,record in sorted(self.pages.items()):
            groups.setdefault(record['group'],[]).append((target,record))
        for group,entries in groups.items():
            body+=self.section(group,self.table(['Page','Purpose'],[[self.link(target,record['title'],path),escape(record['lead'])] for target,record in entries],path,raw=True))
        self.add(path,'All chapters and asset contracts','Complete generated directory; each page is also indexed by local search.',body)
    def wrap(self,path,record):
        navigation=[('index.html','Guide home'),('getting-started.html','Start here'),('development-roadmap.html','Phases 00–23'),('first-vertical-slice.html','Acceptance slices'),('systems/index.html','System chapters'),('asset-index.html','Asset registry'),('dependency-map.html','Dependencies'),('ownership.html','Ownership'),('world/index.html','World production'),('engineering/index.html','Engineering'),('network/index.html','Networking'),('art/asset-audit.html','Art audit'),('all-pages.html','All chapters'),('search.html','Offline search'),('checklist.html','Progress'),('sources-verification.html','Verification')]
        nav=''.join('<a'+(' aria-current="page"' if target==path else '')+' href="'+escape(relative(target,path))+'">'+escape(label)+'</a>' for target,label in navigation)
        headings=re.findall(r'<h2 id="([^"]+)">([^<]+)</h2>',record['body'])
        toc='<details class="toc"><summary>On this page</summary><nav aria-label="Page contents">'+''.join('<a href="#'+escape(identity)+'">'+text+'</a>' for identity,text in headings)+'</nav></details>' if headings else ''
        searchscript='<script defer src="'+escape(relative('site/search-data.js',path))+'"></script>' if path=='search.html' else ''
        return '<!doctype html>\n<!-- Generated by tools/build_manual_indexes.py; edit sources, not this file. -->\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="'+escape(record['lead'])+'"><title>'+escape(record['title'])+' · RPG MMO Development Guide</title><link rel="stylesheet" href="'+escape(relative('site/style.css',path))+'">'+searchscript+'<script defer src="'+escape(relative('site/app.js',path))+'"></script></head><body data-edition="'+EDITION+'"><a class="skip" href="#main">Skip to content</a><aside class="sidebar"><a class="brand" href="'+escape(relative('index.html',path))+'"><span>RPG / DEVELOPMENT</span><strong>MMO Guide</strong></a><p class="edition">Offline edition · UE5.8.3 target<br>Planned implementation, not a game build</p><nav aria-label="Main navigation">'+nav+'</nav><button id="theme-toggle" type="button" aria-pressed="false">Dark theme</button></aside><div class="layout"><header class="topline"><span>'+escape(record['group'])+'</span><span>Evidence-labeled draft · 09 Oct2026</span></header><main id="main" tabindex="-1"><header class="page-header"><p class="eyebrow">'+escape(record['group'])+'</p><h1>'+escape(record['title'])+'</h1><p class="lead">'+escape(record['lead'])+'</p></header>'+toc+record['body']+self.reference_html(record['refs'])+'<footer><p>Planned game assets are not compiled assets. Values are proposals unless explicitly evidenced. <a href="'+escape(relative('sources-verification.html',path))+'">Verification and limitations</a>.</p></footer></main></div></body></html>\n'
    def build(self):
        self.catalog_paths={r['path'] for r in read('page-content.json')}|{a['page'] for a in self.assets}|{f['page'] for f in self.features}|{f'phases/phase-{n:02d}.html' for n in range(24)}|{'index.html','development-roadmap.html','asset-index.html','systems/index.html','feature-coverage.html','dependency-map.html','ownership.html','checklist.html','search.html','network/index.html','design/decisions.html','design/classes.html','design/world-and-biomes.html','world/index.html','world/hearthford.html','world/sluice-vault.html','world/biome-authoring.html','first-vertical-slice.html','sources-verification.html'}|{'world/'+z['id'].split('.')[1]+'.html' for z in read('world-catalog.json')['zones']}
        self.editorial();self.feature_pages();self.asset_pages();self.phase_pages();self.indices();self.design_world();self.slices();self.verification();self.sitemap()
        for path,record in self.pages.items():self.outputs[path]=self.wrap(path,record)
        search=[]
        for path,record in self.pages.items():
            text=html.unescape(re.sub('<[^>]+>',' ',record['body']))
            text=re.sub(r'\s+',' ',text).strip()
            search.append(dict(path=path,title=record['title'],group=record['group'],text=text))
        self.outputs['site/search-data.js']='window.RPG_SEARCH_DATA = '+json.dumps(search,ensure_ascii=False,separators=(',',':'))+';\n'
        self.outputs['sources/generated-page-index.json']=json.dumps([dict(path=p,title=r['title'],group=r['group']) for p,r in self.pages.items()],indent=2,ensure_ascii=False)+'\n'
        self.outputs['DESIGN_DECISIONS.md']='# Design decisions\n\n'+''.join('## '+r.get('id','')+' '+r.get('topic','')+'\n\n'+r.get('decision','')+'\n\n' for r in (read('design-decisions.json').get('decisions',[]) if isinstance(read('design-decisions.json'),dict) else read('design-decisions.json')))
        self.outputs['FEATURE_COVERAGE.md']='# Feature coverage\n\nStatus: authored draft, not runtime verified. Source-art enumeration remains blocked.\n\n'+''.join(f"- Phase{f['phase']:02d}: {f['title']} — {f['page']} ({f['scope']})\n" for f in self.features)
        self.outputs['ASSET_AUDIT.md']='# Asset audit\n\nRequested archive: 2d_game_assets.zip. Status: unavailable. Actual PNG count: unknown. Prompt estimate: approximately2596, NOT VERIFIED. No source PNGs, paid thumbnails or 3D assets are distributed. The CSV has headers only; run tools/audit_asset_archive.py against your private licensed ZIP and review guides/license before merging metadata.\n'
        return self.outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    DERIVED.update(derive_sources(ROOT))
    outputs=ManualBuilder().build();stale=[]
    for name,content in outputs.items():
        path=ROOT/name
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8')!=content:stale.append(name)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf-8')
    if stale:
        print('Generated files stale/missing: '+', '.join(stale),file=sys.stderr);return 1
    print(('CHECK PASS' if args.check else 'BUILT')+f': {len(outputs)} generated files; {sum(p.endswith(".html") for p in outputs)} HTML pages')
    return 0
if __name__=='__main__':raise SystemExit(main())
