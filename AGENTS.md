# Documentation workflow

This repository is an offline HTML game-development manual. The project’s C++
engineering standard starts at [engineering/index.html](engineering/index.html).
Read [engineering/architecture.html](engineering/architecture.html) before making
project architecture claims: documented planned assets are not verified game code.
Use [engineering/16-review-codex.html](engineering/16-review-codex.html) for native
implementation and review guidance when this standard is used with the game.

For engineering documentation changes:

- Edit `engineering/content/*.html` and `engineering/pages.json`.
- Generate assembled pages and offline search with
  `python3 tools/build_manual_indexes.py` then
  `python3 tools/build_cpp_standard.py`.
- Verify with `python3 tools/build_cpp_standard.py --check` and
  `python3 tools/check_cpp_standard.py`, plus
  `python3 tools/build_manual_indexes.py --check` and
  `python3 tools/check_paperzd_docs.py`; use `--write-report` on check scripts
  when updating committed static verification records.
- Keep gameplay policy and authoritative ownership intact unless the requested
  work changes them. Record scope, compatibility and evidence for architecture
  changes; do not invent unimplemented systems.
- Preserve the historical original roadmap and asset manifest during standards
  work. Current asset identities live in `sources/current-asset-manifest.json`;
  creation order lives in `sources/phase-creation-order.json`. Keep historical
  audits distinct from new verification records. The current animation contract
  is `systems/animation.html`, with compatibility in `animation-migration.html`.
- Report engine builds, Blueprint compilation and runtime tests only when run.

Code comments should exist only when they reduce cognitive load. Prefer clear
code; explain non-obvious intent, constraints, lifecycle or compatibility briefly.
Do not narrate obvious code or add comments merely because a file changed.
