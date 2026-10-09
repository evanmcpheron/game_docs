# RPG MMO Development Guide

An offline-first HTML implementation manual for **RPG**, an original online 2.5D action RPG targeting Unreal Engine 5.8.3. It describes native C++ authority, Blueprint/data-driven authoring, Paper2D/PaperZD presentation, dedicated zone servers and a small authenticated PostgreSQL-backed service.

## Open the manual

Extract the entire repository/ZIP and open **`index.html`** directly in a browser. Keep the directory structure intact. No local web server, CDN, external font or JavaScript package installation is required for reading, local search, asset filtering, or checklist export/import.

Begin with `getting-started.html`, `sources-verification.html`, `architecture/source-migration.html`, then `development-roadmap.html`. `all-pages.html` is the complete directory; every planned asset has an individual page under `assets/`. `first-vertical-slice.html` defines three implementation acceptance routes.

## Status: evidence-labeled partial draft

This is **documentation, not an Unreal project or completed game**. The registered features and phases have authored specifications and test recipes, but the complete acceptance contract has not been met. The requested `2d_game_assets.zip` and optional companion inputs were not accessible. Actual PNG count, dimensions, frame timing, layer compatibility and redistribution permission are therefore unknown. Approximately 2,596 PNGs is an unverified observation from the request, not an audit result.

No Unreal installation, PaperZD source, C++/Blueprint build, database service, packaged client/server, multiplayer run or load benchmark was available to test. Public documentation checks do not establish installed compatibility. Shared individual-asset contract templates and example content catalogs still need specialist implementation/Editor review. Read `UNVERIFIED.md` and `reports/content-depth-review.json` before adopting the manual as an implementation specification.

No `.uasset`, `.umap`, `.uproject`, Unreal gameplay source, paid sprite image, fabricated mesh, game executable or fictional runtime log is included. Planned Content/Source paths are strings in the documentation.

## Build and verify documentation

Use Python 3.10 or later. The build, structural checks, phase checks and audit metadata tool use the standard library.

```sh
python tools/build_manual_indexes.py
python tools/validate_docs.py --write-report
python tools/check_phase_integration.py --write-report
python tools/test_validators.py --write-report
python tools/build_manual_indexes.py
python tools/build_manual_indexes.py --check
```

In this generation environment, Chromium blocked both direct `file://` and localhost navigation with `ERR_BLOCKED_BY_ADMINISTRATOR`. Five in-memory DOM/render groups passed, but direct offline navigation, cross-page storage and actual export downloading remain unverified. See `reports/browser-validation.json` and `reports/dom-render-validation.json`. The site is designed for direct disk reading; this environment could not certify that route.

The browser smoke test additionally uses Playwright and an installed Chromium executable; see `tools/test_browser.py --help`. It checks the HTML manual, not the game. A missing browser dependency must be reported as not run, never as passed.

## Private source-art audit

```sh
python tools/audit_asset_archive.py /private/path/2d_game_assets.zip --output /private/path/audit-output
```

The tool reads ZIP metadata, hashes and PNG headers without extracting or redistributing artwork. It excludes AppleDouble/macOS metadata from PNG counts, distinguishes inferred filename tokens from reviewed frame mappings, and records provenance. Manually review the actual guides, decoded images and license before adopting any art capability or derived asset row. This command was **not** run against the missing requested archive; only synthetic audit fixtures were tested.

## Source records

`current-asset-manifest.json` defines identities and creation/assignment dependencies. The generator derives reverse users, phase counts/order, dependency edges, coverage lists, HTML and search data. `phase-run-recipes.json` supplies the bounded run-now steps; full-game feature chapters must not introduce later systems into early phases. `ownership-records.json`, `database-models.json`, `api-contracts.json`, `world-catalog.json` and `design-decisions.json` define their separate contracts. See `AGENTS.md` for editing rules.

## Repository replacement and provenance

The reference was inspected at commit `6633ca27f7b2fcfc80fc95a1567e97c0eb5a6a25` in `evanmcpheron/game_docs`. The historical manual's local-save/platformer ownership is not the new online specification. The original revision was preserved on `backup/pre-mmo-guide-2026-10-09`. Publication is separate from ZIP generation: **read `sources/publication-receipt.json` for the actual result**. Never infer a successful GitHub overwrite from this README or from the presence of a downloadable ZIP.

Third-party artwork remains subject to its original license. This repository grants no redistribution permission for missing/private art or any linked product. All world/content names here are newly authored proposals, not completed third-party assets.
