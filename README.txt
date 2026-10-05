BLUEPRINT RPG DEVELOPMENT GUIDE

Extract this whole directory and open index.html in a desktop browser.
No web server, internet connection, package installation or account is required.
Keep the site, assets, phases and systems directories together.

START: getting-started.html → phases/phase-00.html
FIND: asset-index.html or search.html
TRACK: checklist.html (export progress JSON for a portable backup)
SOURCE: original-roadmap.html is byte-for-byte unchanged.
AUDIT: audit.html distinguishes website checks from unexecuted Unreal tests.

149 canonical asset pages; 12 phases; 19 system chapters; 20 exact Content folders.
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
  python3 tools/build_cpp_standard.py
  python3 tools/build_cpp_standard.py --check
  python3 tools/check_cpp_standard.py
Generated pages and offline search stay in sync without third-party packages.
