"""Render incremental integration guidance from the shared authored contracts."""
from html import escape
import json
from pathlib import Path
import posixpath
import re

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- BEGIN GENERATED PHASE INTEGRATION -->'
END = '<!-- END GENERATED PHASE INTEGRATION -->'
TOC_START = '<!-- BEGIN INTEGRATION TOC -->'
TOC_END = '<!-- END INTEGRATION TOC -->'
ENVIRONMENT_PAGE = 'development-test-environments.html'


def load_integration():
    return json.loads((ROOT / 'sources/phase-integration.json').read_text())


def relative_link(source, target, label):
    path, separator, fragment = target.partition('#')
    relative = posixpath.relpath(path, str(Path(source).parent)) if path else ''
    destination = relative + (separator + fragment if separator else '')
    return f'<a href="{escape(destination, quote=True)}">{escape(label)}</a>'


def linked_text(text, source, assets):
    """Link exact registered names while escaping all authored prose."""
    pattern = r'(?<![A-Za-z0-9_])(' + '|'.join(re.escape(name) for name in sorted(assets, key=len, reverse=True)) + r')(?![A-Za-z0-9_])'
    parts = []
    previous = 0
    for match in re.finditer(pattern, text):
        parts.append(escape(text[previous:match.start()]))
        name = match[0]
        parts.append('<code>' + relative_link(source, assets[name]['doc'], name) + '</code>')
        previous = match.end()
    parts.append(escape(text[previous:]))
    return ''.join(parts)


def paragraphs(values, source, assets):
    return '\n'.join('<p>' + linked_text(value, source, assets) + '</p>' for value in values)


def ordered(values, source, assets):
    return '<ol>\n' + '\n'.join('<li>' + linked_text(value, source, assets) + '</li>' for value in values) + '\n</ol>'


def table(headers, rows, label):
    return ('<div class="table-wrap" role="region" tabindex="0" aria-label="' + escape(label, quote=True) + '"><table><thead><tr>'
            + ''.join('<th scope="col">' + escape(header) + '</th>' for header in headers)
            + '</tr></thead><tbody>\n'
            + '\n'.join('<tr>' + ''.join('<td>' + cell + '</td>' for cell in row) + '</tr>' for row in rows)
            + '\n</tbody></table></div>')


def phase_link(source, phase, section='integrate-hook-up', label=None):
    return relative_link(source, f'phases/phase-{phase:02}.html#{section}', label or f'Phase {phase}')


def contract_rows(bindings, source, assets, compact=False):
    rows = []
    for binding in bindings:
        assignment = linked_text(binding['asset'] + ' → ' + ', '.join(binding['owners']), source, assets)
        assignment += '<br><strong>' + escape(binding['slot']) + '</strong>'
        if compact:
            rows.append([assignment,
                         linked_text(binding['editor'], source, assets),
                         linked_text(binding['missing'], source, assets)])
        else:
            rows.append([phase_link(source, binding['phase']) + '<br>' + assignment,
                         '<p>' + linked_text(binding['editor'], source, assets) + '</p><p>' + linked_text(binding['runtime'], source, assets) + '</p>',
                         '<p>' + linked_text(binding['missing'], source, assets) + '</p><p><strong>Expected verification:</strong> ' + linked_text(binding['test'], source, assets) + '</p>'])
    return rows


def render_phase(phase, source, data, assets):
    number = phase['phase']
    sections = ['<h2 id="integrate-existing">Existing assets to modify in this phase</h2>']
    sections.append('<p>Follow this operational sequence with the detailed implementation notes below. '
                    'The creation table is the new-asset list, not permission to leave runtime assets disconnected. '
                    + relative_link(source, ENVIRONMENT_PAGE, 'Development test environments and fixture rules') + '.</p>')
    if phase['existing']:
        sections.append(table(['Existing asset', 'Change now and purpose'], [
            [linked_text(row['asset'], source, assets), linked_text(row['change'], source, assets)]
            for row in phase['existing']], f'Phase {number} existing consumers to reopen'))
    else:
        sections.append('<p>No earlier-phase assets exist. Configure the new shells together now; future session functionality remains explicitly staged.</p>')
    sections.append('<h2 id="integrate-configure">Configure the new assets and required references</h2>')
    sections.append(ordered(phase['configure'], source, assets))
    definitions = [binding for binding in data['bindings'] if binding['phase'] == number and binding['kind'] == 'definition']
    if definitions:
        sections.append('<h3>Assign these data instances to real consumers</h3>')
        sections.append(table(['Definition → consumer / slot', 'Where to assign in the Editor', 'Required, optional, or unset behavior'],
                              contract_rows(definitions, source, assets, compact=True), f'Phase {number} data assignments'))
    sections.append('<h2 id="integrate-hook-up">Hook the feature into the existing game</h2>')
    sections.append(ordered(phase['connect'], source, assets))
    sections.append('<p><strong>Connections established:</strong> the edits above must reach the current ready owner, not just a compiled shell. '
                    'Use each linked asset’s integration reference for the same component, interface, input and widget contract. '
                    'Names newly proposed by this audit are labeled <strong>Suggested implementation detail</strong>; existing suggested field/function names retain that status. '
                    'Editor/plugin behavior still requires validation in the installed project.</p>')
    for key, identifier, title, use_list in [
        ('world', 'integrate-world', 'Update the test world', True),
        ('run', 'integrate-run', 'Run the feature now', True),
        ('failure', 'integrate-failure', 'Failure and rejection tests', True),
        ('regression', 'integrate-regression', 'Regression gates', True),
        ('deferred', 'integrate-deferred', 'Intentionally staged or not connected yet', False),
    ]:
        sections.append(f'<h2 id="{identifier}">{title}</h2>')
        sections.append((ordered if use_list else paragraphs)(phase[key], source, assets))
    sections.append('<h2 id="integrate-complete">Integrated completion gate</h2>')
    checks = [
        'Every current-phase runtime asset is connected to its actual consumer; intentionally staged definitions have an explicit activation phase.',
        'Existing owners were reopened, required references and input paths assigned, and modified Blueprints compiled in the installed project.',
        'The specified development world is saved with valid spawn/bootstrap, fixture data, collision and authored identities where required.',
        'The run-now success path, rejection cases and selected regression gates were actually exercised and expected/observed values recorded.',
        'UI/animation absence cannot suppress authoritative behavior; later-phase or unapproved systems were not added.',
    ]
    sections.append('<div class="checks">' + ''.join(
        f'<label><input type="checkbox" data-check="integrated-phase-{number:02}-{index}"><span>{escape(text)}</span></label>'
        for index, text in enumerate(checks)) + '</div>')
    sections.append('<p><strong>Stop:</strong> do not advance if one required connection or integrated gate fails, even when all new assets compile. '
                    'These are expected results to run, not a claim that this documentation audit executed Unreal. '
                    + relative_link(source, 'systems/validation.html', 'Full validation suite') + ' · '
                    + relative_link(source, 'checklist.html', 'Project checklists') + '.</p>')
    return '\n'.join(sections)


def render_asset(asset, source, data, assets):
    name = asset['name']
    sections = ['<h2 id="phase-integration">When and where to connect this asset</h2>']
    note = data['asset_notes'].get(name)
    if note:
        sections.append('<p><strong>' + escape(note['role']) + '.</strong> ' + linked_text(note['text'], source, assets) + '</p>')
        if note['first_active'] > asset['phase']:
            sections.append('<p><strong>Created in Phase ' + str(asset['phase']) + '; the staged functionality becomes active in '
                            + phase_link(source, note['first_active']) + '.</strong> Do not infer an early runtime consumer.</p>')
    sections.append('<p>Creation phase: ' + phase_link(source, asset['phase']) + '. '
                    + phase_link(source, asset['phase'], 'integrate-world', 'World setup') + ' · '
                    + phase_link(source, asset['phase'], 'integrate-run', 'Run-now proof') + ' · '
                    + relative_link(source, ENVIRONMENT_PAGE, 'Which test map to use') + '.</p>')
    relevant = [binding for binding in data['bindings'] if binding['asset'] == name or name in binding['owners']]
    if relevant:
        sections.append(table(['Activation / asset → owner', 'Editor operation and runtime connection', 'Requirement, failure and test'],
                              contract_rows(relevant, source, assets), f'{name} incremental integration contracts'))
    modifications = [(phase['phase'], row['change']) for phase in data['phases'] for row in phase['existing'] if row['asset'] == name]
    if modifications:
        sections.append('<h3>Reopen this existing asset at these phase boundaries</h3>')
        sections.append(table(['Phase', 'Change to this existing consumer'], [
            [phase_link(source, number), linked_text(change, source, assets)] for number, change in modifications], f'{name} later edits'))
    sections.append('<p>Only the current phase’s connections are active. The full reference/dependency list can include later schema extensions; '
                    'it is not an instruction to add them early. Suggested properties/graph calls are implementation guidance, not verified existing game fields. '
                    'Compile/configure the real consumer, save its world fixture, and record the linked scenario’s observed result before marking this asset done.</p>')
    return '\n'.join(sections)


def render_cross_links(source, data):
    sections = ['<h2 id="incremental-integration">Incremental integration and test-world workflow</h2>',
                '<p><strong>' + escape(data['workflow']) + '</strong>. '
                'A phase is complete only after its new runtime feature reaches the real consumer and passes a playable or controlled system scenario. '
                'Use ' + relative_link(source, ENVIRONMENT_PAGE, 'development test environments') + ' for map roles, stable fixture identity and bootstrap boundaries.</p>']
    if source == 'troubleshooting.html':
        sections.append('<p><strong>New asset compiles but does nothing:</strong> check the owning Blueprint’s component/interface, actual data assignment, '
                        'installed input mapping and receiver, current ready-body reference, world fixture collision and effective GameMode. '
                        'Follow the phase request path to the authoritative result; do not add a second manager, input handler or damage path.</p>')
    if source == 'architecture-notes.html':
        sections.append('<p><strong>Current integration clarification:</strong> Phase 2 explicitly attaches Stats/Health/Combat and routes RequestAttack; '
                        'Phase 3 replaces early automatic spawning with registered readiness and explicit single-player spawning. '
                        'Unregistered L_MovementLab is not an end-to-end current gameplay area after that transition. '
                        'The generated assignment contracts label proposed property names and keep every later extension phase-gated.</p>')
    if source == 'dependency-map.html':
        sections.append('<p>Dependency edges include assigned component classes, interfaces, data instances, input actions and created widgets. '
                        'The per-phase activation/assignment tables distinguish compile/type dependencies from runtime use. '
                        'A later-phase dependency in a complete asset reference does not require adding it while compiling an earlier shell.</p>')
    system_phases = {
        'input': [0, 1, 2, 3, 6, 8, 9, 10], 'movement': [0, 1, 2, 11],
        'animation': [1, 2, 5, 7, 9, 11], 'combat': [1, 2, 5, 9],
        'stats': [2, 5, 7, 8, 9], 'interaction': [3, 4, 10],
        'world': [3, 11], 'persistence': [3, 4, 11], 'save-load': [3, 4, 10, 11],
        'enemies': [5, 11], 'progression': [5, 8], 'inventory': [4, 6, 7, 9],
        'equipment': [7, 11], 'skills': [8, 9, 11], 'abilities': [9, 11],
        'effects': [6, 9, 11], 'npcs-dialogue': [10, 11],
        'ui': [2, 4, 6, 7, 8, 9, 10], 'validation': list(range(12)),
    }
    relevant_phases = system_phases.get(Path(source).stem, list(range(12))) if source.startswith('systems/') else list(range(12))
    sections.append(table(['Phase', 'Sequential integration', 'World and proof'], [
        [str(phase['phase']), phase_link(source, phase['phase'], 'integrate-existing', 'Existing assets to modify and connect'),
         phase_link(source, phase['phase'], 'integrate-world', 'World edits') + ' · ' + phase_link(source, phase['phase'], 'integrate-run', 'Run now')]
        for phase in data['phases'] if phase['phase'] in relevant_phases], 'Phase integration entry points'))
    if source == 'checklist.html':
        sections.append('<p>Keep existing checkmarks, but recheck the new integrated gates in each phase before considering an old asset-only completion sufficient. '
                        'A documentation checkbox is not runtime evidence; record actual expected/observed results, build and fixture IDs.</p>')
    return '\n'.join(sections)


def replace_block(source, block, before=None):
    wrapped = START + '\n' + block + '\n' + END
    if START in source:
        return re.sub(re.escape(START) + r'.*?' + re.escape(END), lambda match: wrapped, source, count=1, flags=re.S)
    if before and before in source:
        return source.replace(before, wrapped + '\n' + before, 1)
    match = re.search(r'<nav[^>]*class="page-nav"', source)
    if match:
        return source[:match.start()] + wrapped + '\n' + source[match.start():]
    return source.replace('</article>', wrapped + '\n</article>', 1)


def sync_toc(source, block):
    source = re.sub(re.escape(TOC_START) + r'.*?' + re.escape(TOC_END), '', source, flags=re.S)
    match = re.search(r'(<details class="toc">.*?<ul>)(.*?)(</ul></details>)', source, re.S)
    if not match:
        return source
    links = ''.join(f'<li><a href="#{identifier}">{title}</a></li>'
                    for identifier, title in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', block))
    replacement = match[1] + match[2] + TOC_START + links + TOC_END + match[3]
    return source[:match.start()] + replacement + source[match.end():]


def update_page(source, relative, data, assets):
    if relative.startswith('phases/'):
        phase = data['phases'][int(Path(relative).stem[-2:])]
        block = render_phase(phase, relative, data, assets)
        return sync_toc(replace_block(source, block, '<h2 id="implementation-sequence">'), block)
    asset = assets.get(Path(relative).stem) if relative.startswith('assets/') else None
    if asset:
        block = render_asset(asset, relative, data, assets)
        # Place operational reference before detailed fields/dependencies rather than after the done checklist.
        anchor = next((heading for heading in ['<h2 id="fields">', '<h2 id="components">', '<h2 id="dependencies">'] if heading in source), None)
        return sync_toc(replace_block(source, block, anchor), block)
    cross_pages = {'index.html', 'getting-started.html', 'development-roadmap.html', 'architecture.html',
                   'architecture-notes.html', 'ownership.html', 'dependency-map.html', 'communication.html',
                   'checklist.html', 'troubleshooting.html', 'first-vertical-slice.html', 'sources-verification.html'}
    if relative in cross_pages or (relative.startswith('systems/') and relative != 'systems/index.html'):
        block = render_cross_links(relative, data)
        return sync_toc(replace_block(source, block), block)
    return source


def render_environments(home, data, assets):
    source = ENVIRONMENT_PAGE
    sections = [
        '<h2 id="workflow">Build a continuously playable project</h2>',
        '<p><strong>' + escape(data['workflow']) + '</strong>. '
        'Create and compile types first, but connect each current-phase runtime feature to its real owner before continuing. '
        'A data-only/staged contract must say when its runtime consumer becomes active. '
        'Phase pages provide the sequential Editor operations; asset pages provide matching detailed contracts.</p>',
        '<h2 id="map-roles">Development test environments</h2>',
        table(['Environment', 'Primary period and purpose', 'Bootstrap and boundary'], [
            [linked_text('L_MovementLab', source, assets), 'Phases 0–2: movement/player, then dummy/hazard combat integration.',
             'Early BP_GameMode default-player spawn, native PlayerStart, one possessed player. Preserve the obstacle course and separate combat section. After Phase 3 retain as an early-phase reference or reproduce its course inside a registered slice; never bypass current readiness.'],
            [linked_text('L_Slice_A / L_Slice_B (SliceA / SliceB)', source, assets), 'Phase 3 onward: full player/world/travel/recovery and cumulative feature integration.',
             'Matching catalog/AreaRoot definition, registered safe spawns and rooms, reverse connections, persistent projection and one explicit initialized player. BP_GameMode Default Pawn=None; no placed auto-possessed duplicate.'],
            [linked_text('L_SystemTests', source, assets), 'Phase 11: controlled architecture/system harness and deterministic public-API assertions.',
             'BP_ArchitectureTestHarness with actual definitions and explicit initial values. Native GameModeBase is an optional no-player harness setup, not an alternate valid gameplay-area bootstrap. End-to-end physics/player/travel stays in registered slices.'],
            [linked_text('L_Frontend', source, assets), 'Phase 10 onward: real New Game/Load/menu/quit entry and later packaged launch.',
             'BP_MenuGameMode, BP_PlayerController and no default pawn or AreaRoot requirement. Accepted commands enter the registered gameplay slices through the session coordinator.'],
        ], 'Development map roles'),
        '<h2 id="transition">The Phase 2 → 3 map and initialization transition</h2>',
        ordered([
            'Before Phase 3, finish movement and combat in L_MovementLab using its early automatic player spawn. Preserve that map/course and the early-phase source revision for isolated old-lab checks.',
            'At Phase 3, compile the session/world/bootstrap types, assign DA_GameCatalog and both area definitions, and configure exactly one root plus registered safe spawns/rooms/reverse transitions in each slice.',
            'Reopen BP_GameMode and change Default Pawn Class to None. Remove any placed auto-possessed player in the slices. Wait for session/area/controller/spawn readiness, apply persistent actors, explicitly spawn/initialize/possess one body, then bind UI and allow input.',
            'Reuse the same player and its existing movement/combat setup. Replace the early unconditional BeginPlay setup with the explicit ready-body initialization path; do not keep a late second Health initialization that refills a travel handoff.',
            'Reproduce movement obstacles, BP_TrainingDummy and BP_Hazard in a development section of registered SliceA. Validate current gameplay there. The old unregistered lab is not made a production area by changing its name or skipping missing prerequisites.',
        ], source, assets),
        '<h2 id="evolution">Evolve fixtures at the phase they are usable</h2>',
    ]
    fixture_summaries = [
        'Native floor/ledges/ceiling and safe PlayerStart; no future session types.',
        'Short/held jumps, buffer/coyote/ceiling/landing course and spare combat space.',
        'TrainingDummy grounded/airborne targets plus separated Hazard; no AI or checkpoint yet.',
        'Registered roots/spawns/rooms/reverse transitions, checkpoint, switch/door and reproduced movement/combat course.',
        'Persistent TestReward pickup and isolated save/load/retry route; retain shortcut/checkpoint.',
        'Ordinary/unique melee fixtures, then ranged/projectile obstruction lane; prove first architecture slice.',
        'Consumable pickups with distinct IDs and stack quantities; use existing hazard for Health benefit.',
        'Two TestHelmet pickups producing separate EntryIds; retain movement/action visual checks.',
        'No new world Actor: use current rewards/points and validate both legal specializations can progress.',
        'AbilityTestReceiver and buff pickup; supported query collision, matching capability and stable IDs.',
        'Reachable stationary NPC plus no-pawn frontend; retain revisit/reload and modal input tests.',
        'Controlled harness map plus combined all-map manifest and packaged frontend/slice acceptance.',
    ]
    sections.append(table(['Phase', 'Environment and retained arrangement', 'Edit and run'], [
        [str(number), ('L_MovementLab' if number < 3 else 'Registered SliceA/B' if number < 10 else 'Frontend + registered slices' if number == 10 else 'System harness + frontend/registered slices') + ': ' + escape(summary),
         phase_link(source, number, 'integrate-world', 'World-edit steps') + ' · ' + phase_link(source, number, 'integrate-run', 'Run-now scenario')]
        for number, summary in enumerate(fixture_summaries)], 'Fixture evolution by phase'))
    sections.extend([
        '<h2 id="editor-check">Before pressing Play</h2>',
        ordered([
            'Open the specified existing map and check its effective GameMode, Game Instance assignment and spawn policy. Save All after configuring Blueprint defaults and placed-instance overrides; a saved data asset alone is not an assigned reference.',
            'Use native blocking collision for floor/obstacles, query-only shapes for interaction/ability/hazard detection, and the documented target response for combat. Keep X/Z plane, Y depth and camera/facing consistent. A noncolliding visual does not replace an actor’s Hurtbox/Trigger/Blocker.',
            'Place fixtures in reachable relationships rather than invented final coordinates: safe spawn outside hazards/transitions, open floor for attacks, a reachable platform for airborne tests, a switch connected by exact ID to its blocker, and arrival outside reverse travel volumes.',
            'For every persistent placement author one stable PersistentId; for spawn/room/area/NPC definitions use the documented identity scope. Duplicating an Actor copies its ID: deliberately assign a distinct ID before testing. Never regenerate IDs in BeginPlay/Construction Script to reset progress.',
            'Record which definitions and instance Details are assigned, expected initial Profile/WorldState values, and whether the case requires a fresh test Profile or revisit. Use isolated test slots/user data for corrupt-save cases, not valuable player saves.',
            'PIE uses normal registered/PlayerStart spawning, not a convenient Play From Here position that skips the intended arrival route. For persistence proof, observe actual save completion and use a fresh Standalone/packaged process; a restarted PIE session alone is not complete packaged proof.',
        ], source, assets),
        '<h2 id="fixture-record">Fixture status and evidence record</h2>',
        '<p>Dummy targets, test attacks, consumables, helmet, test enemies, TestPulse/receiver and NPC lines are development/slice fixtures. '
        'Reusable production systems are being proved with them; no final equipment catalog, ability catalog, lore or production level layout is approved by placing them. '
        'Retain useful regression fixtures as later phases extend the same slices. Remove/replace only with an explicit regression replacement and updated references.</p>',
        table(['Record', 'What to write'], [
            ['Identity/context', 'Phase, map/AreaId/RoomId, fixture class and PersistentId where required; build/schema/content version and test date.'],
            ['Configuration', 'Assigned definitions, component/interface setup, instance overrides, collision/query arrangement and safe spawn relationship.'],
            ['Initial state/action', 'XP/points/entry IDs/quantities/equipment/world records/Health/charges/effect values; exact public request or mapped player action.'],
            ['Expected/observed', 'Accepted or rejected result, changed owner values, callbacks/token count, UI/visual observation and meaningful previous-feature regression.'],
            ['Cleanup/retention', 'Restore intentionally broken test data, retain useful slice fixtures, keep stable IDs, clear old body/widget subscriptions and distinguish normal travel from clean recovery.'],
        ], 'Development fixture test record'),
        '<h2 id="completion">A phase completion is an integrated result</h2>',
        '<p>Compile new and modified assets, assign references, wire the public request to its owner, save the test-world fixture, run success/rejection cases and the selected regressions, '
        'then record observed results. UI and PaperZD can be absent without suppressing damage, action legality, persistence or required cleanup. '
        'Use ' + relative_link(source, 'checklist.html', 'the project checklists') + ' and ' + relative_link(source, 'systems/validation.html', 'the full validation suite') + '; do not repeat every historical test manually on every page.</p>',
        '<h2 id="audit">Incremental integration audit · 07 October 2026</h2>',
        '<p>Inspected documentation baseline <code>383ac235010c3c7d8ab357eb21b7eebd2b87c19f</code>. '
        'A GitHub Pages build artifact was recovered and its source-only Git tree verified byte-for-byte against '
        '<code>3a518e71f0a71d9a5ee7e7636d0c08e19b739685</code> before editing. '
        'The related RPG repository returned 404 through the available GitHub connection; no actual game Blueprints, project settings or installed Editor were available to validate here. '
        'Historical engine/repository evidence remains historical, not a new runtime verification.</p>',
        '<p>The baseline already documented ownership and many implementation rules. The audit found that generated creation checkpoints deferred assignment, '
        'phase pages lacked an explicit existing-consumer/world-edit sequence, and multiple test Data Asset instances had no direct consumers recorded. '
        'This update adds all twelve operational workflows, shared attachment/interface/input/view/data assignments, staged-asset dispositions, reverse consumer edits and explicit map transition rules. '
        'The initial two-point curve also cannot fund TestRoot plus a specialization and TestActive; Phase 9 explicitly extends the development point budget through real progression rather than refunds or import-time awards. '
        'No registered asset identity, phase, Content folder, original roadmap or historical audit is changed.</p>',
        '<p>Current static results: ' + relative_link(source, 'sources/phase-integration-verification.json', 'integration verification record') + ' · '
        + relative_link(source, 'sources/phase-integration-browser-checks.json', 'browser checks') + '. '
        'Existing historical measurements: ' + relative_link(source, 'audit.html', '02 October package audit') + '. '
        '<strong>Static HTML/link/search/generation validation is not Blueprint compilation, PIE, Standalone or packaged gameplay validation.</strong></p>',
        '<h2 id="maintenance">Keep phase and asset instructions synchronized</h2>',
        '<p>Edit ' + relative_link(source, 'sources/phase-integration.json', 'sources/phase-integration.json') + ' for phase recipes, shared contracts and staged dispositions. '
        'Edit the current asset manifest only for genuine dependency changes; keep identities/folders/phases and creation order unchanged. '
        'Generated integration blocks are maintained by <code>tools/phase_integration.py</code> through the existing manual generator; do not hand-edit their copies.</p>',
        '<pre><code>python3 tools/build_manual_indexes.py\npython3 tools/build_cpp_standard.py\npython3 tools/build_manual_indexes.py --check\npython3 tools/build_cpp_standard.py --check\npython3 tools/check_cpp_standard.py\npython3 tools/check_paperzd_docs.py\npython3 tools/check_phase_integration.py --write-report</code></pre>',
    ])
    body = '\n'.join(sections)
    toc = '<details class="toc"><summary>On this page</summary><ul>' + ''.join(
        f'<li><a href="#{identifier}">{title}</a></li>' for identifier, title in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)) + '</ul></details>'
    sidebar = re.search(r'<aside class="sidebar">.*?</aside>', home, re.S)[0]
    sidebar = sidebar.replace('aria-current="page"', '')
    return ('<!doctype html>\n<!-- Generated by tools/phase_integration.py through tools/build_manual_indexes.py. -->\n'
            '<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Development test environments · Blueprint RPG Development Guide</title>'
            '<meta name="description" content="Connect each phase to the existing game, evolve development fixtures and verify the integrated path.">'
            '<link rel="stylesheet" href="site/style.css"><script defer src="site/app.js"></script></head><body>'
            '<a class="skip" href="#main">Skip to content</a>' + sidebar + '<div class="layout">'
            '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="index.html">Guide home</a><span>/</span><a href="development-roadmap.html">Phases 0–11</a><span>/</span><span>Development test environments</span></nav>'
            '<article id="main"><header><div class="eyebrow">Incremental implementation workflow</div><h1>Development test environments</h1>'
            '<p class="lead">Connect the current feature, evolve the correct test world, and verify the complete path before continuing.</p></header>'
            + toc + body + '<nav class="page-nav" aria-label="Previous and next"><a href="development-roadmap.html">← Phases 0–11</a><a href="phases/phase-00.html">Start Phase 0 →</a></nav></article>'
            '<footer class="page-footer">Integration audit · 07 October 2026. Expected Editor scenarios are not executed gameplay results.</footer></div></body></html>\n')
