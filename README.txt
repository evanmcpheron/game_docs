BLUEPRINT RPG DEVELOPMENT GUIDE

Extract this whole directory and open index.html in a desktop browser.
No web server, internet connection, package installation or account is required.
Keep the site, assets, phases and systems directories together.

START: getting-started.html → phases/phase-00.html
FIND: asset-index.html or search.html
TRACK: checklist.html (export progress JSON for a portable backup)
SOURCE: original-roadmap.html is byte-for-byte unchanged.
AUDIT: audit.html is historical; animation-migration.html and sources/paperzd-verification.json record current documentation checks.

163 current asset pages (149 in the preserved historical manifest); 12 phases; 19 system chapters; 20 exact Content folders.
This is documentation, not a playable Unreal project or generated .uasset files.
The target is the requested Unreal Engine 5.8.3. Official mechanism pages were
consulted in the 5.8 documentation family; no Unreal Editor graphs were compiled
or game build executed while creating the manual. Test values are provisional.

Local checklist storage depends on your browser. Export progress before moving
or replacing the guide; importing progress changes only documentation checkmarks.

C++ ENGINEERING STANDARD (05 October 2026)
Open engineering/index.html for the project-specific native engineering rules.
The Blueprint roadmap retains domain ownership; new/modified C++ follows this
standard. engineering/architecture.html records the inspected repository gap:
RPG main contains only .gitignore, so planned assets are not verified game code.
The local engine reports 5.8.3; game compilation/runtime were not performed.
Edit engineering/content/*.html and engineering/pages.json, then run:
  python3 tools/build_manual_indexes.py
  python3 tools/build_cpp_standard.py
  python3 tools/build_manual_indexes.py --check
  python3 tools/build_cpp_standard.py --check
  python3 tools/check_cpp_standard.py
  python3 tools/check_paperzd_docs.py
Generated pages and offline search stay in sync without third-party packages.

ANIMATION STANDARD
Paper2D: sprites, flipbooks, TileSets/TileMaps and simple prop loops.
PaperZD: complex character sources/sequences/AnimBPs, state machines and notifies.
Gameplay: authoritative movement, actions, damage, abilities and persistence.
Start at systems/animation.html; see animation-migration.html for compatibility.
The installed PaperZD release and game build/runtime remain unverified.

INCREMENTAL INTEGRATION WORKFLOW (07 October 2026)
Open development-test-environments.html for map roles and the Phase 2→3 bootstrap transition.
Every phase now names existing consumers to reopen, assignments, world edits,
run-now success/rejection cases and selected regression gates. Asset references
share those same contracts; deliberately staged definitions identify activation.
Edit sources/phase-integration.json; the existing manual generator invokes
 tools/phase_integration.py to render the marked blocks and test-environment page.
After the existing generation/check sequence, run:
  python3 tools/check_phase_integration.py --write-report
The current report preserves the original roadmap, historical audit/manifest,
phase order and all 163 registered identities/folders. This is still documentation,
not compiled Blueprints or a tested Unreal game. The related RPG repository was
not accessible through the GitHub connection during this audit; October 5 game
repository/engine findings above remain historical evidence only.
