# Project documentation and architecture audit

**Repository:** [evanmcpheron/game_docs](https://github.com/evanmcpheron/game_docs)  
**Audit date:** October 3, 2026  
**Default branch:** `main`  
**Initial read baseline:** `d797bf8e75655a483229db5d8d75d42a7c64755d`  
**Final reviewed baseline:** `a8549f5f295b410ee050dcd8558b54c5a064649d`  
**Requested implementation target:** Unreal Engine 5.8.3, Blueprints, Paper2D  
**Repository change made by this audit:** this report only.

> **Evidence boundary:** This is a repository-wide documentation-content and architecture audit, not a certification of a running Unreal project. The complete search-indexed guide corpus, the original roadmap, asset manifest, phase-order data, supporting files, and high-risk raw pages were reviewed. Not every raw HTML file was independently downloaded and parsed. A fresh exhaustive HTML link/anchor crawler, direct `file://` browser test, Blueprint compilation, Editor execution, save migration, and packaged build were **not** run. Existing repository validation results are identified as historical evidence, not claimed as tests performed during this audit. These limitations prevent an unconditional implementation or navigation sign-off.

## A. Executive Summary

### Overall assessment

The architecture is **fundamentally coherent and aligned with the intended game**. It does not need a wholesale redesign, a C++ rewrite, GAS, World Partition, a generic service layer, or an inventory manager per feature. Its separation of authored definitions, persistent character/world models, temporary runtime bodies, disk snapshots, and presentation is a sound foundation for this project.

However, the guide is **not yet safe to follow literally without correction or supervision**. The highest-risk problem is unusually concrete: several widget `RefreshView` recipes issue gameplay commands even though those functions are invoked automatically after binding and completed state changes. A literal implementation can buy a skill merely by opening its view. The save design also leaves the first New Game write into an existing alternating-generation bank insufficiently specified. Two phase/movement implementation ambiguities and the old flat content paths need correction before they become implementation habits.

### Finding totals

| Severity | Findings |
|---|---:|
| Blocker | 0 |
| High | 2 |
| Medium | 3 |
| Low | 1 |
| Possible Improvements, separate from defects | 2 |

These are **six distinct documentation findings**, not a count of every repeated occurrence. No running-game failure was reproduced. The save-bank finding is an implementation gap with a conditional failure example, not proof that a compiled implementation already loses data.

| ID | Severity | Finding | Primary section |
|---|---|---|---|
| AUD-01 | High | Widget redraw functions mix observation with commands | E |
| AUD-02 | High | New Game replacement of an existing save-generation bank is underspecified | F |
| AUD-03 | Medium | `TravelHandoff` simultaneously says Phase 3 and Phase 9 | I |
| AUD-04 | Medium | Current content placements preserve obsolete flat folders | H |
| AUD-05 | Medium | Essential post-movement observation hook is unnamed | G |
| AUD-06 | Low | Archive byte-preservation claims are stale after the mobile merge | J |
| PI-01 | Improvement | Make documentation regeneration and validation reproducible | K |
| PI-02 | Improvement | Label asset-level acceptance tests by implementation phase | K |

### What should remain unchanged

Keep the persistent `BP_PlayerProfile` and `BP_WorldState` Objects, GameInstance coordination, runtime component ownership, single jump execution policy, action tokens, stable world IDs, equipment Entry-ID references, full stat reconstruction, and the Phase 0–11 sequence. Preserve the explicit distinction between death recovery, ordinary travel, and loading a disk save. Do not turn development fixtures into final content.

### Concurrent repository change

During the audit, `main` advanced from `d797bf8` to `a8549f5` through PR #2, the mobile-responsiveness merge. The [reviewed comparison](https://github.com/evanmcpheron/game_docs/compare/d797bf8e75655a483229db5d8d75d42a7c64755d...a8549f5f295b410ee050dcd8558b54c5a064649d) changes only `original-roadmap.html`, `site/app.js`, and `site/style.css`. The CSS/JavaScript changes were inspected; they do not change the asset register or the five technical/content findings established at the initial baseline. They do invalidate a literal byte-for-byte archive claim, recorded as AUD-06. This report's branch starts from the newer baseline and does not revert that work.

## B. Repository Inventory

### Documentation inventory

The inventory reconciles to **219 HTML pages**:

| Group | Count | Location |
|---|---:|---|
| Individual planned-asset pages | 149 | `assets/<Feature>/<Asset>.html` |
| Feature/folder index pages | 20 | `assets/<Feature>/index.html` |
| System chapters | 19 | `systems/`, excluding its index |
| System index | 1 | `systems/index.html` |
| Phase pages | 12 | `phases/phase-00.html` through `phase-11.html` |
| Root-level HTML pages | 18 | Listed below |
| **Total** | **219** | Includes `original-roadmap.html` |

The identified supporting set contains `README.txt`, two JavaScript files, one CSS file, four JSON files, and one task-brief text file. That is nine supporting files and an inventoried total of 228 files before this report. These counts reconcile the tree/manifest/index and stored inventory; they are not presented as the output of a new local filesystem crawl.

Root HTML pages: `index.html`, `getting-started.html`, `game-overview.html`, `architecture.html`, `architecture-notes.html`, `ownership.html`, `communication.html`, `dependency-map.html`, `development-roadmap.html`, `first-vertical-slice.html`, `asset-index.html`, `search.html`, `checklist.html`, `troubleshooting.html`, `glossary.html`, `sources-verification.html`, `audit.html`, and `original-roadmap.html`.

Supporting files:

| File | Role and audit treatment |
|---|---|
| `README.txt` | Entry point and package description |
| `site/style.css` | Shared site presentation; latest mobile changes inspected |
| `site/app.js` | Local navigation, filtering, search rendering, and checklist behavior; latest mobile changes inspected |
| `site/search-data.js` | Generated search corpus; reviewed across the current guide, not treated as an independent architectural authority |
| `sources/asset-manifest.json` | Normalized identity source for comparison with the roadmap and repeated metadata |
| `sources/phase-creation-order.json` | Explicit creation sequence and staged dependencies |
| `sources/documentation-audit.json` | Previously recorded static validation; not re-executed here |
| `sources/browser-checks.json` | Previously recorded browser checks with explicit limitations |
| `sources/task-brief.txt` | Historical generation instructions; lower priority than the current audit prompt |

The observed repository is a static manual, not the Unreal project. No `.uproject`, compiled Blueprints, `.uasset`/`.umap` implementation, or packaged executable was available to validate. No checked-in generator or executable validation script was found in the identified tree. JSON/search metadata and highly uniform HTML indicate generated derivatives, but the generation implementation itself is not present.

### Authority and archival status

`Blueprint_RPG_Architecture_Roadmap.html` is **not present under that filename**. The repository instead supplies `original-roadmap.html`, and current asset pages explicitly cite its placement and phase registers as their source. This is not, by itself, a missing-asset defect.

For this audit, the current user's requirements outrank the historical generation brief and original folder assignments. The preserved roadmap remains architectural evidence for unchanged names, relationships, phases, and rules. Current expanded guidance is evaluated against those rules and verified engine behavior. Historical paths are not counted as independent defects merely because an archive contains them; **current identity tables and creation instructions that repeat those paths are**.

The site's links and notices identify an original source, but current authority references should expressly distinguish preserved architecture from superseded folder instructions. AUD-04 covers that precedence issue. AUD-06 separately covers exact-byte provenance after the new CSS insertion.

### What was actually checked

| Check class | Evidence obtained | Limitation |
|---|---|---|
| Repository structure | Default branch, pinned refs, root/subdirectory listings, asset register, phase data, final three-file diff | Some connector tree responses omitted entries; path-based reads and contents listings were used to resolve discrepancies rather than reporting phantom missing pages |
| Repository-wide prose | Complete search-indexed guide corpus and original roadmap | The index is a derivative; this does not prove every origin HTML byte matches it |
| High-risk instructions | Direct raw reads of framework, movement, combat, persistence/save material, Profile, key value pages, and widget recipes | Raw reads were deeper for risky systems, not a claim that all 219 origin pages received identical review |
| Normalized inventory | Local checks on a transcription of the remotely read register and phase data | Not a parser run against a downloaded copy of the original JSON/HTML |
| Engine verification | Official Epic documentation/API sources in D | Mechanism verification, not hotfix-specific runtime execution |
| Site integrity | Source inspection plus stored audit/browser evidence | No fresh exhaustive link/anchor crawl or direct offline-browser run |

Source HTML is often minified into very long lines. Findings therefore use **exact paths, section IDs, field/function names, and short claim excerpts**. Connector wrapper line numbers are not misrepresented as source-file line numbers.

## C. Project-Context Findings

No additional confirmed game-identity or gameplay-scope defect was found in the reviewed corpus. The guide consistently describes interconnected exploration, rooms and areas, persistent discoveries, one lasting RPG character, platforming, real-time combat, equipment, leveling, skills, abilities, and NPC dialogue. It does not require a seamless open world.

The scope review covered the following requested term families, including contextual uses rather than treating every mention as approval:

| Topic family | Assessment |
|---|---|
| Double jump, dash, wall jump/climbing/traversal, ledge grabbing/climbing, rolling, sliding, crouching, sprinting | Future animation capacity or explicitly uncommitted mechanics, not silently required gameplay in the reviewed progression |
| Crafting, merchants, formal economy, currency, randomized loot, rarity, durability | No confirmed promotion into committed implementation dependencies |
| Character classes, respec, multiple loadouts | Not assumed as established character systems |
| Fast travel, seamless travel, streaming, World Partition, procedural world generation | Not required to implement connected area-map travel |
| Formal quests, reputation, morality, persuasion, factions/faction reputation, procedural narrative | Not silently substituted for the intended conversation/world-flag model |
| Multiplayer, GAS migration, C++ rewrite, Behavior Trees, State Trees | Not mandatory architectural dependencies; optional alternatives are not defects merely because they are mentioned |
| Final biomes, lore, NPC cast, equipment sets, skill/ability/enemy catalogs, stat balance | Development examples are distinguished from final design |

`TestPulse`, `TestHelmet`, TestRoot/TestBranch variants, Slice A/B, test attacks/enemies, training dummy, and the architecture harness are development fixtures, not approved final lore or balance. The normalized inventory identifies 39 effective fixture/content entries: 29 currently under Tests, four placeholder art assets, and six test flipbooks. The remaining 110 entries are production architecture/configuration, not necessarily final authored content.

**Actual contextual mismatch:** the new selective folder organization is not reflected in current placements. See AUD-04. This requires a documentation placement update, not new assets, new gameplay, or a revised development sequence.

## D. Unreal Technical Findings

### Verification standard

The official pages retrieved identify the **Unreal Engine 5.8 documentation family**. They support the mechanisms below. They do not establish that a particular graph compiled or that 5.8.3 hotfix timing, asset-picker behavior, serialization, or cooking was tested. No material engine error is asserted simply because another architecture is possible.

AUD-05 is a beginner implementation gap around a real engine hook, not evidence that Launch Character or the one-jump design is invalid. The other findings primarily concern contradictory project instructions and completeness.

### Technical verification matrix

| Subject | Classification | Verified mechanism or remaining boundary |
|---|---|---|
| `APaperCharacter` | Verified mechanism, 5.8 | Inherits Character and uses a PaperFlipbook representation rather than the normal skeletal Mesh setup. The guide's inherited Sprite/CharacterMovement assumptions are appropriate. [E01] |
| `LaunchCharacter` | Verified mechanism, 5.8 | Schedules pending launch velocity for the next CharacterMovement update and changes to Falling; override flags control replacement versus addition. Do not expect immediate positive Z on the next Blueprint node. [E02] |
| `OnLanded` | Verified mechanism, 5.8 | Movement mode is still Falling during the event. Waiting for a confirmed movement-mode change before rearming a buffered jump is correct. [E03] |
| Post-movement observation | Verified hook; project wiring requires Editor validation | `On Character Movement Updated` provides an end-of-movement update hook. Name it in the recipe rather than leaving the reader to discover a timing point. [E04] |
| Add Movement Input | Verified mechanism, 5.8 | Character handles the submitted movement input through its movement implementation; a base Pawn does not automatically implement movement. Do not duplicate submission or multiply the input scale by Delta Seconds as an extra integration step. [E05] |
| X/Z plane constraint | Verified mechanism; configuration test required | Plane normal `(0,1,0)` constrains the Y-normal plane. Configure the plane origin/snapping policy and collision depth deliberately; normal alone does not author room collision or camera orientation. [E06] |
| Enhanced Input | Verified mechanism; mapping-dependent behavior | Boolean and Axis1D values, mapping contexts, Local Player subsystem, and trigger-state events are supported. Event behavior depends on configured triggers; Started/Completed are not universally interchangeable with raw key-down/up for every trigger configuration. [E07, E08] |
| GameInstance lifetime | Verified mechanism, 5.8 | GameInstance exists for the game instance, not a single level's Actor lifetime. Holding explicit model references there is appropriate. [E09] |
| GameMode/spawn/possession | Verified framework mechanism; project gates unexecuted | GameMode configuration and Controller possession support the chosen single-player setup. Ordinary Open Level is not evidence that the old Controller/Pawn survives; the project correctly reconstructs and rebinds. [E10, E11, E12] |
| Plain Object construction | Verified mechanism; project lifetime convention | Construct Object from Class accepts a Class and Outer. GI as Outer plus retained typed references and explicit initialization is a valid project choice. Outer is not a substitute for retaining reachable references. Plain Objects do not acquire Actor BeginPlay. [E13, E14] |
| SaveGame / async save | Verified mechanism, not transactions | Async Save Game to Slot exposes completion and success/failure for a slot. It does not supply the project's revision accounting, A/B selection, bank replacement, or cross-model transaction semantics. [E15, E16] |
| Blueprint PrimaryDataAsset schema | Verified base; exact instance workflow requires Editor validation | PrimaryDataAsset is Blueprintable and supplies primary-asset behavior. Epic distinguishes native Data Asset instances from data-only Blueprint inheritance. The exact Blueprint-schema/DA-instance picker workflow must be demonstrated in 5.8.3; do not call that already proven. No mandatory C++ rewrite follows. [E17, E18] |
| Hard/soft references and cooked content | Verified mechanism; package completeness unproven | Soft references permit deferred resolution; loading success still requires available cooked content and correct references. A string ID alone does not prove that a map or executor class is included. [E19, E20] |
| PaperFlipbook playback | Verified mechanism; synchronization unexecuted | Playback position can be set in time or frames; changing flipbook can reset play time. `OnFinishedPlaying` concerns non-looping playback. The guide correctly does not make damage, death, rewards, or jump permission depend on it. [E21] |
| Blueprint Interfaces | Verified mechanism | Interfaces declare shared contracts, not arbitrary Actor parents or owned state. Unrelated target types can implement the same request interface. [E22] |
| Event Dispatchers | Verified mechanism; semantics are project rules | Binding/unbinding and broadcasting are supported. The command-versus-completed-event convention is this project's responsibility, not an automatic transaction guarantee. [E23] |
| Blueprint structs and containers | Likely correct; not specifically Editor-tested | The documented scalar/enum/Guid/Name/array/map/set shapes are plausible. Explicit local-value edit and container writeback is safe guidance; not every node variant has identical reference semantics. Compile/save/import tests remain necessary. |
| Gameplay Tags | Architecture recommendation / unverified configuration | Extensible semantic labels are not substitutes for every closed enum or numeric field. No dependency requiring a new tag framework was established; tag setup was not verified in an Editor. |
| Content Browser moves/redirectors | Verified mechanism | Real assets should be moved/renamed with Unreal-aware tooling and references fixed up. `mkdir` can create folders; `touch` cannot create valid Unreal asset content. [E24] |

### Official technical sources

Links below were used for mechanism verification; project-specific recommendations are identified separately in the findings.

- **E01:** [APaperCharacter](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/Paper2D/APaperCharacter)
- **E02:** [ACharacter::LaunchCharacter](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/ACharacter/LaunchCharacter)
- **E03:** [ACharacter::OnLanded](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/ACharacter/OnLanded)
- **E04:** [On Character Movement Updated](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Character/OnCharacterMovementUpdated)
- **E05:** [Add Movement Input](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Pawn/Input/AddMovementInput)
- **E06:** [SetPlaneConstraintNormal](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UMovementComponent/SetPlaneConstraintNormal)
- **E07:** [Enhanced Input](https://dev.epicgames.com/documentation/en-us/unreal-engine/enhanced-input-in-unreal-engine)
- **E08:** [ETriggerEvent](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/EnhancedInput/ETriggerEvent)
- **E09:** [UGameInstance](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UGameInstance)
- **E10:** [Game Mode and Game State](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-mode-and-game-state-in-unreal-engine)
- **E11:** [Possess](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Pawn/Possess)
- **E12:** [Open Level by Object Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Game/OpenLevel_byObjectReference)
- **E13:** [Construct Object from Class](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Game/ConstructObjectfromClass)
- **E14:** [Unreal Object Handling](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-object-handling-in-unreal-engine)
- **E15:** [Async Save Game to Slot](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/SaveGame/AsyncSaveGametoSlot)
- **E16:** [Saving and Loading Your Game](https://dev.epicgames.com/documentation/en-us/unreal-engine/saving-and-loading-your-game-in-unreal-engine)
- **E17:** [UPrimaryDataAsset](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UPrimaryDataAsset)
- **E18:** [Data Assets](https://dev.epicgames.com/documentation/en-us/unreal-engine/data-assets-in-unreal-engine)
- **E19:** [Asynchronous Asset Loading](https://dev.epicgames.com/documentation/en-us/unreal-engine/asynchronous-asset-loading-in-unreal-engine)
- **E20:** [Packaging Unreal Engine Projects](https://dev.epicgames.com/documentation/en-us/unreal-engine/packaging-your-project)
- **E21:** [UPaperFlipbookComponent](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/Paper2D/UPaperFlipbookComponent)
- **E22:** [Blueprint Interface](https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-interface-in-unreal-engine)
- **E23:** [Event Dispatchers](https://dev.epicgames.com/documentation/en-us/unreal-engine/event-dispatchers-in-unreal-engine)
- **E24:** [Asset Redirectors](https://dev.epicgames.com/documentation/en-us/unreal-engine/asset-redirectors-in-unreal-engine)

## E. Architecture and Ownership Findings

### AUD-01 — Redraw functions contain gameplay command instructions

**Severity:** High  
**Category:** Architecture Contradiction; Internal Inconsistency; Ambiguous Beginner Guidance  
**Confidence:** High for the documentation contradiction; runtime consequences are conditional on following the conflicting recipe literally.  
**File:** `assets/UI/WBP_SkillNode.html`  
**Section / location:** `#fn-BindSources`, `#fn-RefreshView`, and `#events`.

**Current claim:** `BindSources` binds sources and immediately calls `RefreshView`. `RefreshView` is called by “BindSources and source change events” and allows only “Widget text, bars, buttons and selection” changes. Yet its body instructs: “Request Profile.TryPurchaseSkill(SkillId), display the returned reason and refresh from the model.” The same paragraph then says no gameplay mutation is required merely to redraw.

**Problem:** The API recipe places a purchase command in the automatically invoked observation path. This contradicts both its own allowed-change contract and the separate instruction that native button clicks request operations.

**Why it matters:** With sufficient points, creating/binding a skill node could purchase it without a click. Repeated model notifications can submit repeated commands. Validation may reject duplicates, but it does not restore the player's unrequested initial expenditure or branch choice. Similar instructions can consume items, change equipment, advance dialogue, or start menu operations during a refresh.

**Project source of truth:** Current audit requirements 20, 21, and 29; `communication.html`; `ownership.html`; `assets/Player/BP_PlayerProfile.html#events`; widget creation and event sections. Commands request changes; completed changes trigger read-only presentation updates.

**Technical verification:** This is a project-level control-flow contradiction, not a claim about a built-in Unreal `RefreshView` node. `RefreshView` is custom. Epic's dispatcher mechanism invokes bound handlers [E23]; it does not distinguish a harmless redraw from a command placed inside that handler.

**Recommended correction:** Keep `RefreshView` observation-only. Move each command to an explicitly named native-button handler or custom request function inside the existing widget. The handler submits one request; the model validates and commits; notifications refresh the view. No new widget assets, managers, or authoritative UI stores are needed. “Read-only” here describes behavior; it does not require marking every view function Blueprint Pure.

**Affected related pages, confirmed occurrences:**

| Exact file, all at `#fn-RefreshView` | Command incorrectly included in refresh description |
|---|---|
| `assets/UI/WBP_SkillNode.html` | `Profile.TryPurchaseSkill(SkillId)` |
| `assets/UI/WBP_Inventory.html` | Request item use through Controller/GI and equipment operations through Profile |
| `assets/UI/WBP_Equipment.html` | `Profile.TryEquip` or `TryUnequip` |
| `assets/UI/WBP_Dialogue.html` | `Controller.AdvanceDialogue` or `CloseModalScreen(false)` |
| `assets/UI/WBP_MainMenu.html` | New Game or Load request |
| `assets/UI/WBP_PauseMenu.html` | Resume, save, retry, or save-before-quit request |

Also regenerate affected `site/search-data.js` entries. In `assets/UI/WBP_SaveStatus.html`, explicitly separate the Retry button handler from the display recipe; its wording is less direct and is not counted as another independent defect. `WBP_Abilities` correctly describes displaying state rather than replenishing charges.

**Acceptance test:** Create, bind, rebind, and refresh each affected view repeatedly without input. Persistent revision, points, inventory, equipment, health, dialogue position, and session selection must not change. One deliberate click should issue one request. A notification caused by that request must not issue another request.

### Ownership review outside AUD-01

`BP_PlayerProfile` owns lasting character values; `BP_WorldState` owns unloaded-world-compatible value facts. Neither is instructed to mutate the other directly. GI coordinates cross-model changes while gameplay bodies/components own live movement, health, combat, effects, cooldowns, AI, and presentation.

The Profile page contains a `bPublishingCommit` guard and distinguishes standalone commit events from GI-deferred cross-model notifications. Therefore, a generic claim that the guide lacks all reentrancy protection would be inaccurate. Likewise, the Combat implementation uses an elapsed-time update path; it should not be criticized for an imaginary Blueprint closure/timer mechanism it does not require.

Direct typed references for known ownership, interfaces for unrelated targets, deliberate boundary casts, and completed-change dispatchers are appropriate. No concrete need was established for a global event bus, service locator, dependency container, or additional manager hierarchy.

## F. Persistence and Save/Load Findings

### AUD-02 — New Game does not fully specify replacement of an existing A/B save bank

**Severity:** High  
**Category:** Ambiguous Beginner Guidance; Persistence Implementation Gap  
**Confidence:** High that the documented initialization contract is incomplete; Moderate for the conditional data-selection failure below because no runtime implementation was executed.  
**File:** `assets/Core/BP_GameInstance.html`  
**Section / location:** `#fields`, especially `NextSaveSequence` and `LastGoodSlot`; `#fn-StartNewGame`; load/save contracts. Also `assets/Save/S_SaveHeader.html#fields` and `systems/save-load.html`.

**Current claim:** `NextSaveSequence` starts at 1, with guidance to seed above accepted generations on load. `S_SaveHeader.SaveSequence` is monotonically increasing physical-generation order, and loading selects the highest valid generation. `StartNewGame` says to settle outstanding I/O, protect existing generations until overwrite intent is explicit, construct clean models, and choose the NewGame destination. The first-write generation and old-bank eligibility policy after explicit New Game is not concretely specified.

**Problem:** New Game can be requested in a fresh process without first loading the existing character. The described load-only seeding rule does not specify how that path initializes the sequence or retires the previous playthrough's fallback generation. An overwrite-intent guard is necessary, but it is not a complete physical-generation replacement algorithm.

**Why it matters:** Consider a documented-default implementation with old valid generations A=50 and B=51. A fresh-process New Game initializes the next sequence to 1 and replaces only one generation. If the old sequence-51 generation remains eligible, the next Continue selects the old character rather than the newly saved character. This is a **conditional reasoning example**, not an observed engine test. Even when a developer correctly seeds the first new sequence above 51, the intended behavior of falling back to an old playthrough after the sole new-generation save is corrupted still needs an explicit policy.

**Project source of truth:** Requirements 11, 24, and 52; the repository's recovery-state save policy; explicit New Game versus Load separation; `S_SaveHeader`'s highest-valid-generation selection rule.

**Technical verification:** Epic provides single-slot save/load operations and completion results [E15, E16]. The logical bank, save sequence, previous-run eligibility, and safe overwrite behavior are project conventions. Unreal does not automatically reconcile them.

**Recommended correction:** Add an explicit New Game bank-initialization contract inside existing GI orchestration. Settle earlier I/O; obtain explicit overwrite intent; select and document one bank-replacement strategy; initialize sequence/slot/revision bookkeeping for that strategy before the first write; and define which old generations remain eligible at each failure point. For example, a deliberately acknowledged reset of both physical slots requires handling deletion/reset failures before sequence 1 is reused. A preserve-until-success approach requires seeding above retained generations and explicitly defining when prior-playthrough fallback becomes ineligible. Do not silently mix the two strategies or add speculative save managers.

Retain the existing `LastSavedRevision = -1` convention for an unsaved new session. This audit does **not** claim the guide initializes every revision to zero or lacks a dirty-new-session distinction.

**Affected related pages:** `assets/Save/S_SaveHeader.html`; `assets/Save/BP_SaveGame.html`; `systems/save-load.html`; `assets/UI/WBP_MainMenu.html`; `phases/phase-04.html`; `phases/phase-10.html`; `assets/Tests/BP_ArchitectureTestHarness.html`; `site/search-data.js`.

**Acceptance test:** From a fresh process with two existing valid saves, choose New Game without Load, save once, terminate, and Continue. Repeat with first-write failure, one stale old generation, one corrupted new generation, unsupported headers, and interruption during replacement. Expected character selection must follow the explicitly chosen policy and never depend on accidental default sequence values.

### Persistence rules that are represented correctly

The reviewed guide correctly separates **state persistence** from **Actor survival**. Durable world records do not require a loaded door or pickup. Authored stable IDs are validated before replay. Initialization applies stored records before becoming gameplay-ready, and `ApplyPersistentRecord` reconstructs presentation/collision without replaying rewards.

Runtime-generated inventory Entry IDs are not the same issue as regenerated world IDs: generating a new owned-entry Guid once on acquisition is appropriate; generating a placed pickup's persistent ID on every BeginPlay or Construction Script is not. The guide distinguishes these concepts.

Cross-model pickup/reward operations validate and stage changes, use synchronous non-latent mutation, publish after both models agree, increment one persistent revision, and only then request saving. This is an application convention, not an Unreal database transaction. Internal helper access and deferred notifications are already discussed in `architecture-notes.html`.

The save design correctly describes a fresh snapshot, one in-flight writer, pending/coalesced requests, immutable in-flight data, and success/failure handling. Advancing the durable revision to the snapshot's captured revision rather than whatever the live revision is at completion is the correct intended rule. Save failure must leave progress dirty and visible, not falsely announce durability.

Loading validates a candidate before importing and does not grant XP, inventory, skills, or encounter rewards while reconstructing. Schema/content versions are useful metadata, but the guide already warns that incompatible Blueprint struct changes can prevent deserialization before migration logic runs. That warning should remain.

### Recovery/travel distinction

| Operation | Persistent models | Runtime body state | Disk behavior |
|---|---|---|---|
| Normal death | Keep current in-memory Profile and WorldState | Reconstruct at active checkpoint/fallback; apply the defined recovery reset | Do not load an older disk snapshot |
| Ordinary area travel | Keep current models | Carry health and, when implemented, remaining effects/recharge values under handoff policy | Travel is not a recovery reset |
| Explicit disk load | Replace/import only a validated supported snapshot | Rebuild a recovery state, not the exact old simulation instant | Read and validate eligible generations |
| Explicit New Game | Construct clean models | Initialize a new body at the starting destination | Must resolve existing-bank overwrite policy; AUD-02 |

Persistent progression surviving death does not mean current runtime health must survive death unchanged. Conversely, restoring health for recovery does not authorize restoring full health on normal area travel. The principal documentation keeps this distinction; AUD-03 could mislead someone about when the handoff must be implemented.

## G. Movement Findings

### AUD-05 — The required observation point is not named for a beginner

**Severity:** Medium  
**Category:** Ambiguous Beginner Guidance  
**Confidence:** High for the missing concrete instruction; exact 5.8.3 ordering remains an Editor-validation requirement.  
**File:** `systems/movement.html`  
**Section / location:** `#observe-movement-do-not-invent-another-physics-simulation`; also `#variable-height-including-a-release-before-velocity-appears`.

**Current claim:** Centralize support/launch observation in one body update function and use “a known post-movement observation point in your installed Editor.” Check velocity/mode before clearing `bLaunchPending`; retain a pending jump cut until the initial launch has been observed.

**Problem:** This is essential timing infrastructure, not optional polish, but the recipe does not identify the native event/delegate to start from. A beginner is left to guess Actor Tick, component Tick, an arbitrary Delay, or an unrelated input callback.

**Why it matters:** Observing stale support/velocity can leave a jump pending, erase release intent, arm coyote incorrectly, or make buffering work at one frame rate but not another. The underlying architecture is plausible; the missing executable hook makes the first graph unnecessarily uncertain.

**Project source of truth:** Requirement 4's responsiveness and edge cases; `original-roadmap.html` Part J; `assets/Player/BP_PlayerCharacter.html` movement functions; Phase 1's movement-first completion criteria.

**Technical verification:** Epic documents `On Character Movement Updated` as an end-of-CharacterMovement update hook [E04]. Launch is deferred [E02], and OnLanded still reports Falling [E03]. Naming that hook is supported; claiming the complete proposed graph has been proven on 5.8.3 is not.

**Recommended correction:** Name the native `On Character Movement Updated` hook and the custom observation function it invokes. Specify which path updates genuine support, observes the pending launch, applies a single deferred cut, expires intent, and publishes animation facts. Keep Walking-transition rearming explicit and idempotent; do not let another Tick/input path reset the same flags. Document that a movement update is not an assumed once-per-render-frame event. Retain Editor logging and edge-case tests.

**Affected related pages:** `assets/Player/BP_PlayerCharacter.html`; `phases/phase-01.html`; `assets/Tests/L_MovementLab.html`; `architecture-notes.html#engine-evidence-boundary`; movement troubleshooting and search text.

**Acceptance test:** Log request generation, pending launch, movement mode, positive Z observation, cut application, and rejection reason. Test same-frame press/release, released buffered landing, ceiling impact, walk-off coyote, forced knockback, interruption, and immediate buffered re-jump at approximately 30/60/120 FPS. No old request should fire after a modal interruption.

### Movement decisions verified or strongly supported

The reviewed recipes correctly use X horizontal/Z vertical/Y depth, inherited CharacterMovement integration, an explicit facing sign affecting visual layers, and one location for Add Movement Input. They warn against moving the capsule every frame with Set Actor Location, changing collision with sprite frames, duplicate input submission, or scaling intent by Delta Seconds.

There is one initial jump execution policy: custom `ExecuteJump` calls Launch Character with XY preserved and Z overridden. Native Jump/JumpMaxHoldTime/StopJumping are discussed as a different approach, not a parallel fallback. A one-time positive-Z jump cut is not a second committed jump.

Coyote permission is limited to a genuine walk-off and is consumed once. Jump/knockback/death/teleport/transition close it. Pending-launch guards prevent stale ground state from manufacturing another budget. Air-spawned bodies do not invent a recent ground timestamp. Release intent is retained for a buffered short jump. Falling velocity is not cut upward. Landing animation is interruptible and does not gate valid movement.

Rise/apex/fall are derived from movement facts; the apex is presentation, not a third physics mode. Acceleration, braking, friction, air control, gravity, and jump constants are test parameters rather than final RPG balance. These are important invariants to preserve, not reasons to add a custom movement component solely for organization.

## H. Asset Register and Folder Findings

### Asset-count reconciliation

The source register, current asset identities, manifest, and phase-order data reconcile to **149 planned assets**, not 149 plus a second set of generated pages. Index pages, schema instances, and phase references must not be double-counted.

Local normalization checks on the remote-register transcription produced 149 unique asset names, 149 unique primary page paths, and exactly phases 0–11. Their per-phase counts are:

| Phase | First-created assets | Intended milestone |
|---|---:|---|
| 0 | 8 | Framework, input, player body |
| 1 | 14 | Movement quality and animation foundation |
| 2 | 21 | Health, stats, actions, attacks, hazards |
| 3 | 32 | Session models, interaction, areas, checkpoints |
| 4 | 9 | Disk saves and persistent pickups |
| 5 | 13 | Enemies, rewards, XP/leveling |
| 6 | 3 | Inventory |
| 7 | 6 | Equipment |
| 8 | 8 | Skill tree |
| 9 | 17 | Abilities and effects |
| 10 | 16 | NPC dialogue and complete menus |
| 11 | 2 | Validation and packaged proof |
| **Total** | **149** | No approved count change found |

Type totals: 29 Blueprint Classes, 9 Actor Components, 11 Blueprint data schemas, 11 enumerations, 4 interfaces, 23 structures, 23 Data Asset instances, 1 Data Table, 6 flipbooks, 1 function library, 10 Input Actions, 2 Input Mapping Contexts, 5 maps, 2 sprites, 2 textures, and 10 Widget Blueprints.

### Parent/base reconciliation

No concrete parent/base mismatch was established between the reviewed source register and current identity metadata. The following distinctions were checked rather than treating every asset as an Actor:

| Asset/family | Correct documented base or creation type |
|---|---|
| `BP_GameInstance` | GameInstance |
| `BP_GameMode`, `BP_MenuGameMode` | GameModeBase |
| `BP_PlayerController` | PlayerController |
| `BP_PlayerCharacter`, `BP_EnemyBase` | PaperCharacter → Character |
| `BP_PlayerProfile`, `BP_WorldState` | Object |
| `BP_SaveGame` | SaveGame |
| `BP_Enemy_MeleeBasic`, `BP_Enemy_RangedBasic` | BP_EnemyBase |
| `BP_EnemyAIController` | AIController |
| `BP_ProjectileBase`, `BP_AbilityBase`, `BP_NPCBase` | Actor |
| `BP_Ability_TestPulse` | BP_AbilityBase |
| `BP_InteractableBase` | Actor |
| `BP_Checkpoint`, `BP_Door`, `BP_Switch`, `BP_PickupBase` | BP_InteractableBase |
| `BP_SpawnPoint` | PlayerStart → Actor |
| Other registered world/test Actor classes | Actor as specified in the register |
| All 9 `BPC_` assets | ActorComponent |
| All 10 `WBP_` assets | UserWidget |
| All 11 `BPDA_` schemas | PrimaryDataAsset |
| `BFL_GameRules` | BlueprintFunctionLibrary |
| `DA_` entries | Instances/configuration of the appropriate BPDA schema, not arbitrary Actor Blueprints; exact creation workflow remains a validation item |
| `BPI_`, `S_`, `E_`, `IA_`, `IMC_` | Interface, Structure, Enumeration, Input Action, Input Mapping Context assets; no arbitrary Actor parent |
| `DT_LevelProgression` | Data Table using `S_LevelProgressionRow` |
| Maps/textures/sprites/flipbooks | Their respective native asset types; maps are World assets |

The normalized table used name, type, base, phase, physical Content folder, fixture status, and primary documentation page. Primary pages use `assets/<current feature>/<asset name>.html`. Metadata comparison is content-level; an exhaustive new machine comparison of every repeated origin-HTML row remains part of the unexecuted raw-site validation boundary.

### AUD-04 — Current content paths preserve the old flat arrangement

**Severity:** Medium  
**Category:** Stale Documentation; Context/Scope Error  
**Confidence:** High  
**File:** `sources/asset-manifest.json`, current asset identity/creation pages, and their repeated placement tables.  
**Section / location:** Asset pages `#identity` and `#create`; `asset-index.html`; feature indexes; `architecture-notes.html#preserved-architecture-explicit-issues`.

**Current claim:** Assets remain in their original folders. Current player art is in `Content/Game/Art/`, flipbooks in `Content/Game/Animation/`, the frontend map in `Content/Game/Maps/`, and development fixtures in `Content/Game/Tests/` without the approved selective subfolders. Architecture Notes explicitly says all original folder assignments are retained.

**Problem:** Those are no longer the current project's intended physical locations. The user's requirements expressly approve selective nesting for content collections while keeping feature architecture flat. A historical generation brief cannot override that newer requirement.

**Why it matters:** A beginner following exact creation instructions will rebuild the obsolete layout and later have to move real assets and repair references. Search, folder browsing, phase instructions, and the asset index reinforce the same stale placement rather than correcting it.

**Project source of truth:** Current audit requirements 31–34 and the approved tree. The 20 feature roots still exist; therefore the number “20” is not itself wrong. The missing selective descendants and obsolete exact placements are the defect.

**Technical verification:** This is a project organization requirement, not an Epic-mandated folder style. Later movement of real assets should use the Content Browser and redirector fixup [E24], not ordinary filesystem renames of `.uasset`/`.umap` files.

**Recommended correction:** Update physical paths, Content Browser paths, creation instructions, manifest/search data, indexes, phase/system placement tables, and current authority notices together. Keep the 149 names, types, parents, and first phases. Do not move feature components/interfaces/structs into generic asset-type folders. Do not rename documentation URLs merely because an Unreal Content path changes unless all site links are updated deliberately.

**Affected related pages:** The 40 asset pages identified below; `assets/Art/index.html`, `assets/Animation/index.html`, `assets/Maps/index.html`, `assets/Tests/index.html`; `asset-index.html`; relevant `phases/phase-00.html` through `phase-11.html`; system related-asset tables; `getting-started.html`; `architecture-notes.html`; `site/search-data.js`; `sources/asset-manifest.json`. Historical roadmap/task-brief placements need a clear supersession notice, not silent rewriting as though they were newly approved instructions.

#### Affected placement inventory: 40 entries

Each asset below identifies its exact documentation file by the stated prefix and `.html` suffix. This is a content-placement correction inventory, **not permission to change files during this audit**.

| Documentation prefix | Asset(s) | Current physical folder | Required/proposed target |
|---|---|---|---|
| `assets/Art/` | `T_TestPlayer`, `SPR_TestPlayer` | `Content/Game/Art/` | `Content/Game/Art/Characters/Player/` |
| `assets/Art/` | `T_TestHelmet`, `SPR_TestHelmet` | `Content/Game/Art/` | `Content/Game/Art/Equipment/` |
| `assets/Animation/` | `FB_Player_IdleTest`, `FB_Player_MoveTest`, `FB_Player_RiseTest`, `FB_Player_FallTest`, `FB_Player_LandTest` | `Content/Game/Animation/` | `Content/Game/Animation/Player/` |
| `assets/Animation/` | `FB_Helmet_Test` | `Content/Game/Animation/` | `Content/Game/Animation/Equipment/` |
| `assets/Maps/` | `L_Frontend` | `Content/Game/Maps/` | `Content/Game/Maps/Frontend/` |
| `assets/Tests/` | `L_MovementLab`, `DA_Anim_PlayerTest` | `Content/Game/Tests/` | `Content/Game/Tests/Movement/` |
| `assets/Tests/` | `BP_TrainingDummy`, `DA_Attack_PlayerAirTest`, `DA_Attack_PlayerGroundTest` | `Content/Game/Tests/` | `Content/Game/Tests/Combat/` |
| `assets/Tests/` | `DA_Area_SliceA`, `DA_Area_SliceB`, `L_Slice_A`, `L_Slice_B` | `Content/Game/Tests/` | `Content/Game/Tests/World/` |
| `assets/Tests/` | `DA_Item_TestReward` | `Content/Game/Tests/` | `Content/Game/Tests/Save/` |
| `assets/Tests/` | `DA_Attack_EnemyMeleeTest`, `DA_Attack_EnemyRangedTest`, `DA_Enemy_MeleeTest`, `DA_Enemy_RangedTest` | `Content/Game/Tests/` | `Content/Game/Tests/Enemies/` |
| `assets/Tests/` | `DA_Item_TestConsumable` | `Content/Game/Tests/` | `Content/Game/Tests/Inventory/` |
| `assets/Tests/` | `DA_Anim_TestHelmet`, `DA_Item_TestHelmet` | `Content/Game/Tests/` | `Content/Game/Tests/Equipment/` |
| `assets/Tests/` | `DA_Skill_TestRoot`, `DA_Skill_TestBranchA`, `DA_Skill_TestBranchB` | `Content/Game/Tests/` | `Content/Game/Tests/Skills/` |
| `assets/Tests/` | `BP_AbilityTestReceiver`, `BP_Ability_TestPulse`, `DA_Ability_TestPulse`, `DA_Effect_TestBuff`, `DA_Item_TestBuffConsumable`, `DA_Skill_TestActive` | `Content/Game/Tests/` | `Content/Game/Tests/Abilities/` |
| `assets/Tests/` | `DA_Dialogue_TestNPC` | `Content/Game/Tests/` | `Content/Game/Tests/NPCs/` |
| `assets/Tests/` | `BP_ArchitectureTestHarness`, `L_SystemTests` | `Content/Game/Tests/` | `Content/Game/Tests/System/` |

The first five rows directly implement the user's named content categories. The allocation of cross-feature test fixtures among the already-approved Tests subfolders is a **proposed classification**, not an invented canonical mapping. For example, assigning the reward fixture to Save reflects its first test purpose; an explicitly approved different system classification would also be valid. No new Tests/Effects or Tests/Animation folder is required.

`BPC_FlipbookAnimator`, `BPDA_AnimationSet`, `E_AnimState`, and `S_AnimationSnapshot` can remain at `Content/Game/Animation/`; the new player/equipment subfolders are for content collections, not a demand to nest every architecture asset. `Content/Game/Maps/Areas/` is reserved for future production maps; do not relabel Slice A/B as final production areas.

Also retain the correct mount-path distinction: physical `Content/Game/Player/` corresponds to a `/Game/Game/Player/` asset path. The repeated word `Game` there is not an erroneous extra physical directory.

## I. Cross-Document Inconsistencies

### AUD-03 — TravelHandoff timing contradicts the Phase 3 travel contract

**Severity:** Medium  
**Category:** Internal Inconsistency; Ambiguous Beginner Guidance  
**Confidence:** High  
**File:** `assets/Core/BP_GameInstance.html`  
**Section / location:** `#fields`, the `TravelHandoff` row.

**Current claim:** The row describes `S_RuntimeTravelState` as “Runtime only; Phase 3, extended Phase 9,” but the timing badge says “Add/use in Phase 9 or later.”

**Problem:** The same field is both needed for health-preserving ordinary travel in Phase 3 and apparently deferred until Phase 9. The type's own phase and the explicit staged-construction note disagree with the generated badge.

**Why it matters:** Following the badge can cause the beginner to omit the Phase 3 handoff, accidentally reset health on ordinary travel, or postpone connected-area acceptance tests until abilities exist.

**Project source of truth:** Phase 3 introduces connected areas and `S_RuntimeTravelState`; `architecture-notes.html#fields-that-arrive-after-a-class-is-first-created` explicitly says the structure starts with health in Phase 3 and gains effect/recharge fields in Phase 9. The user's requirements distinguish normal travel from recovery.

**Technical verification:** This is an internal project phase contradiction, not an engine limitation. A struct may be introduced with a smaller current-phase shape and extended when later types exist. The native travel mechanism does not automatically preserve current body health [E12].

**Recommended correction:** Mark the GI handoff container and health path as Phase 3. Mark only the later effect/recharge members and their integrations as Phase 9. Do not move the entire struct later, save runtime handoff on disk, or move current health into Profile.

**Affected related pages:** `assets/World/S_RuntimeTravelState.html`; `phases/phase-03.html`; `phases/phase-09.html`; `systems/save-load.html`; the connected-world chapter; `architecture-notes.html`; `site/search-data.js`. The type/phase register itself does not need reordering.

### Contradiction cross-reference

| Conflicting guidance | Expected resolution | Finding |
|---|---|---|
| Widget refresh allowed-change/caller contract versus command body | Observation-only refresh; command on deliberate input | AUD-01 |
| New Game clean-model initialization versus highest-valid-generation load policy and load-only sequence seeding | Explicit bank replacement/bootstrap protocol | AUD-02 |
| GI `TravelHandoff` Phase 9 badge versus Phase 3 type/health handoff | Phase 3 container, Phase 9 extension | AUD-03 |
| Current old-folder identity tables versus current approved selective nesting | Current prompt takes precedence over historical folder policy | AUD-04 |
| Unnamed post-movement observation instruction versus requirement for a buildable beginner graph | Name native hook and separate custom functions | AUD-05 |
| Exact-byte preservation notice versus actual original-roadmap CSS change | Correct provenance wording; keep an identifiable immutable baseline | AUD-06 |

Source aliases already acknowledged in `architecture-notes.html` are not counted as additional unresolved defects: MoveAxis/MoveIntent, LastJumpPressedTime/JumpPressedTime, TryConsumeBufferedJump/TryConsumeJumpRequest, EquippedEntries/EquippedEntryIdsBySlot, AwardXP/GrantXP, Recalculate/RebuildStats, Interrupt/InterruptCurrentAction, and TryAddItem/TryAddItems. The guide explicitly directs one underlying store/implementation rather than parallel authorities.

### Phase dependency review

| Phase | Dependency result and important staging condition |
|---|---|
| 0 | Small GI/Controller/Character shells; later Profile, WorldState, catalog, and SaveGame references are deferred. Automatic pawn spawn is a temporary phase configuration. |
| 1 | Action/animation enums and snapshot/schema support the movement presentation. Player test art/flipbooks are fixtures. No later combat or skill mechanics are required for a valid jump. |
| 2 | Stat/damage value types and interfaces precede component wiring. Combat/action state and health do not require checkpoint or inventory ownership. |
| 3 | Equipment-slot/inventory save value types are created early to define persistence shapes; this is not implementation of equipment UI early. Model/catalog shells and explicit initialization support areas/checkpoints. Automatic pawn spawning is replaced, not supplemented, by the controlled route. AUD-03 affects field guidance, not the intended phase sequence. |
| 4 | Item grant/reward/header types and SaveGame precede persistent pickup/save orchestration. Later full inventory UI is not needed merely to validate a saved reward entry. New Game bank policy needs AUD-02. |
| 5 | Enemy base precedes melee/ranged children; state/reward/progression types exist for their consumers. Native CharacterMovement can apply body intent while a small AI state machine makes decisions. No mandatory Behavior Tree is introduced. |
| 6 | Inventory UI operates on the existing Profile entries. Native focused UI controls can close the screen before the Phase 10 UI mapping context exists. |
| 7 | Equipment references existing owned Entry IDs; schema/stat/animation foundations exist. A second inventory is not needed. |
| 8 | Availability enum/schema precede test definitions and node/tree views. The final skill catalog is not invented. AUD-01 must be corrected before wiring node refresh. |
| 9 | Ability/effect runtime value types, schemas, components, and test executor are introduced here. Extend travel handoff now without moving its Phase 3 health implementation. |
| 10 | Dialogue conditions/lines/variants precede definitions and NPC/UI consumers. Menu GameMode avoids a gameplay pawn. UI contexts and pause/focus behavior must be tested. |
| 11 | Harness/map support validation; end-to-end area tests still use registered Slice A/B. No speculative test-area definitions are required. |

No impossible creation cycle was established once the documented shell-first and later-field staging rules were applied. Cross-references in an eventual API page are not automatically current-phase construction dependencies. Architecture Notes already explains the later use of the original movement lab and system-test map after manual spawning; that caveat should not be reported as an entirely missing solution.

## J. Broken Navigation / Static Site Problems

### Current integrity assessment

The site uses relative paths and local CSS/JavaScript. Search data is supplied locally rather than fetched from a remote service. The inspected app code does not require an internet connection for navigation/search. Checklist persistence handles unavailable local storage and offers export/import behavior. These are appropriate offline design choices.

**A new exhaustive broken-link/anchor result is not available.** No concrete unresolved broken target was confirmed in the directly inspected links, but this is not equivalent to validating every link. The historical audit reports successful static checks; those results were not rerun. Search metadata contains the stale content-path guidance in AUD-04 even where the document URL itself exists.

| Integrity check | Result of this audit |
|---|---|
| Phase 0–11 documents | Present in the reconciled inventory |
| 149 asset pages and feature indexes | Reconciled with manifest/indexed identities |
| Every HTML href and fragment | Not independently exhaustively revalidated |
| Previous/next, breadcrumb, folder-browser links | Inspected patterns and selected targets; no blanket pass asserted |
| Every search target exists and body matches origin HTML | Not independently exhaustively revalidated |
| Search/current path semantics | Stale placements confirmed, AUD-04 |
| Direct `file://` navigation/search | Not executed |
| Browser rendering and new mobile menu | Source inspected; no fresh browser execution |
| Duplicate `index.html` basenames | Expected feature indexes, not a conflict by themselves |

`sources/browser-checks.json` records 18 earlier checks using injected HTML/CSS/JavaScript in Chromium/Playwright. Its own notes distinguish that from direct filesystem or localhost navigation, and distinguish unavailable-storage handling from actual persisted localStorage. Those qualifications are good and should remain. They do not prove the later mobile changes or every navigation target.

### AUD-06 — Byte-for-byte archive statements no longer match the file

**Severity:** Low  
**Category:** Stale Documentation; Overstatement  
**Confidence:** High  
**File:** `architecture-notes.html`  
**Section / location:** `#preserved-architecture-explicit-issues`; related archive/source verification metadata.

**Current claim:** “The original roadmap is included byte-for-byte.” Stored verification material also identifies the earlier preserved-source baseline.

**Problem:** The reviewed mobile merge adds 11 lines to `original-roadmap.html`'s embedded CSS. The original file's Git blob changes from `94220b72b0a8a0deb97189c20ee512f68691c4cf` to `5248095e57fb9c3afaa5c51daa53eff20c600165`. Its architectural prose can remain preserved while the file is no longer byte-identical.

**Why it matters:** Exact-byte and hash claims are reproducibility evidence, not merely descriptive prose. A future auditor could mistake an old checksum or test record for validation of the current bytes. This does not imply the mobile styling damaged the architecture.

**Project source of truth:** Requirements 2, 42, and 62: distinguish archival content, current guidance, and what was actually verified.

**Technical verification:** Git's baseline-to-final comparison shows the source-file modification; this is not an Unreal claim. The new source-page CSS begins in the hunk around old line 17, before the closing style element.

**Recommended correction:** State that the architectural source content is preserved with presentation-only modifications, and identify the immutable original commit/blob separately. Alternatively preserve a genuinely byte-identical archival artifact in a later approved change. Refresh provenance/checksum claims only after recomputing them. Do not revert useful mobile styling merely to preserve an inaccurate sentence, and do not relabel old browser checks as freshly executed.

**Affected related pages:** `sources-verification.html`; `audit.html`; `sources/documentation-audit.json`; `README.txt` if it makes an exact-byte claim; relevant `site/search-data.js` text. Update only claims that actually assert exact preservation/current verification, not every historical reference.

### Reproducibility steps still required for a full site sign-off

On a complete checkout of the final reviewed commit, enumerate all HTML files; parse every `href`, `src`, `id`, and named anchor; resolve relative paths against the containing file; decode fragments; check file existence and fragment targets; check duplicate IDs; and compare search paths and identity rows against the manifest. Report every failure as `source path : target : reason` rather than accepting aggregate counts alone. Run the site's search/filter/checklist flow using actual local files and a browser with network access disabled. Then separately run the new mobile menu's open, close, Escape/focus, and breakpoint transitions. These are **unexecuted validation steps**, not a newly committed script or claimed pass.

## K. Beginner-Usability Problems

The asset-page structure is substantially better than a bare asset list. Identity, purpose, type/base, location, creation, fields, function contracts, events, dependencies, lifecycle, tests, mistakes, and completion criteria are generally present. The guide explicitly labels project-defined functions and distinguishes suggested signatures from source names. It also distinguishes runtime-only structures and authored value assets from executable Actor classes.

Nevertheless, a warning that a recipe is suggested does not neutralize contradictions inside that recipe. Fix AUD-01 and AUD-03 rather than asking a beginner to choose which sentence to follow. Name the movement hook in AUD-05 rather than leaving the crucial integration point implicit.

Functions such as `TryConsumeJumpRequest`, `ExecuteJump`, `TryStartAttack`, `PerformHitQuery`, `RefreshBuildFromProfile`, `TryEquip`, `TryPurchaseSkill`, `RefreshUnlocks`, `BuildSnapshot`, and `InitializeState` are project APIs. The reviewed custom-function notices are appropriate; no broad defect was found presenting all of them as native engine nodes. Continue explicitly distinguishing a native event, custom event, function, interface implementation, and dispatcher.

### PI-01 — Reproducible generation/validation provenance

**Category:** Possible Improvement, not a defect count.  
**Confidence:** High that the observed tree lacks the generator/checker implementation.  
**Files:** `sources/asset-manifest.json`, `sources/phase-creation-order.json`, `sources/documentation-audit.json`, `site/search-data.js`, generated HTML.

**Current situation:** Many derivative pages repeat identities, paths, timing badges, and function descriptions. Validation results are stored, but the process that regenerates all derivatives is not available in the identified tree.

**Why useful:** AUD-01 and AUD-03 are the kind of templating/metadata issues that can return if only one rendered page is patched. A small documented generation/check command would make future updates more reliable.

**Recommendation:** In a later authorized task, record which editable sources generate which outputs and provide a minimal reproducible validation command. Do not introduce a new documentation platform solely for this purpose. No script is committed by this audit.

### PI-02 — Phase-gate asset-level tests and completion criteria

**Category:** Possible Improvement, not an impossible-dependency finding.  
**Confidence:** High.  
**Files:** `assets/Core/BP_GameInstance.html#tests`, `assets/Player/BP_PlayerProfile.html#tests`, corresponding `#done` sections and phase pages.

**Current situation:** Assets introduced early have eventual acceptance tests involving much later systems. For example, Profile is first created in Phase 3, but its test list includes TestHelmet entries and skill branches. The overall guide does say to implement only current-phase features.

**Why useful:** A first-time reader may interpret the asset's full Definition of Done as a gate that must be satisfied before leaving its creation phase, despite the staging note.

**Recommendation:** Add the first applicable phase to each acceptance test or divide shell/current-phase tests from final-system tests. Preserve the existing phase order and test coverage; do not create future schemas prematurely merely to clear a checkbox.

## L. Overengineering / Scope Drift

No confirmed requirement to add an unnecessary manager framework, global event bus, service locator, dependency container, factory hierarchy, custom movement component solely for organization, speculative subsystem migration, C++ rewrite, GAS migration, or World Partition migration was established.

The existing small abstractions have concrete responsibilities: Health owns current health; Stats computes final runtime values; ActionState controls permissions/tokens; Combat owns attack execution; Interaction submits unrelated-target requests; PersistentState applies durable records to loaded actors; Profile and WorldState have different lasting-state responsibilities. Their existence is not overengineering merely because the project is a first game.

A real skill tree with prerequisites, explicit costs, purchased state, and exclusions is an approved requirement, not scope drift. Layered equipment presentation is also intentional. Do not simplify either away under the pretext of auditing a beginner project.

Two useful guardrails remain important: a valid specialization must not permanently block mandatory progression, and future animation targets must not silently approve traversal mechanics. The reviewed text maintains those distinctions. No final ability/skill catalog should be inferred from test fixtures.

## M. Claims Requiring Editor Validation

These are **open verification gates**, not additional confirmed defects and not claims that the mechanisms are impossible.

| Gate | Exact area to exercise | Evidence needed before calling it proven |
|---|---|---|
| M-01: Framework creation | `BP_PlayerCharacter`, `BP_EnemyBase`, menu/game modes, Controller | Confirm Paper2D enabled, correct inherited components, native parent selections, one pawn, successful possession, no unintended rotation |
| M-02: Object model lifetime | GI, Profile, WorldState | Construct with GI Outer, retain typed references, initialize explicitly, travel across maps, verify same model values and no stale world references |
| M-03: Enhanced Input | `IA_Move`, `IA_Jump`, gameplay/UI contexts | Confirm actual triggers/modifiers, Started/Triggered/Completed/Canceled routing, negative axis mapping, held-key context changes, pause behavior, release clearing |
| M-04: Movement ordering | PlayerCharacter, movement chapter | Trace pending launch, Walking transition, cut, coyote/buffer windows, ceiling impact, interruptions, and 30/60/120 FPS behavior using the named hook |
| M-05: Manual spawn handoff | Phase 3 area setup and frontend | Ensure Default Pawn auto route is disabled when manual route becomes active; destination readiness and spawn/possess happen once; frontend functions without a player body |
| M-06: Damage/action lifecycle | Combat, Health, projectiles, hazards | Test one accepted damage path, hurtbox dedup, hitches crossing Active, interruption, stale completion tokens, owner exclusion, death/reward once, grounded/air attacks |
| M-07: Persistent reconstruction | doors, switches, pickups, checkpoints, unique encounters | Duplicate/empty IDs rejected; unloaded-target records applied on return; repeated ApplyPersistentRecord grants nothing; collision/presentation ready before interaction |
| M-08: Save concurrency and replacement | GI, SaveGame, headers | Mutate while save in flight; force failures; verify captured revision, immutable snapshot, no overlapping unsafe I/O, A/B fallback, and AUD-02's New Game matrix |
| M-09: Schema compatibility | save structs and retained save fixtures | Load actual prior binary saves after schema/content changes; verify deserialization and migrations before import; no replayed rewards |
| M-10: Blueprint data schemas | each BPDA/DA family, catalogs | Demonstrate the exact 5.8.3 creation/selection workflow, editable fields, class-versus-instance reference type, stable IDs, read-only runtime use, and cooked resolution |
| M-11: Inventory/equipment/stats | Profile, inventory/equipment views, Stats/Health | Distinct same-definition Entry IDs, quantity-one equipment, replace/unequip loops, no cumulative modifiers, load reconstruction, explicit max-health change policy |
| M-12: Skills/abilities/effects | Profile, Abilities, StatusEffects, test executor | Validate prerequisites/cost/exclusion, failed purchase unchanged, no purchase on refresh, executor spawn validation, cancellation, charges/recharge, refresh/expiry, and travel handoff |
| M-13: UMG implementation | all widgets, especially dynamic inventory entries and skill nodes | Prove native row/button-to-EntryId binding without unlisted authoritative widgets; verify chosen creation-pin exposure in the actual Editor; focus/close while paused; unbind/rebind on pawn replacement |
| M-14: Flipbook/equipment layers | animator and animation sets | Matching pivots/frames/durations, common playback clock, visual-only facing, no collision changes, no gameplay dependence on non-looping completion |
| M-15: Cooked content | frontend, area maps, catalog, executor classes | Fresh-process packaged launch and load; maps/definitions/classes resolve; correct soft-reference loading; no editor-only assumptions or blanket exclusion of required test content |
| M-16: Offline documentation | all HTML, app.js, search data, CSS | Full raw href/anchor/search validation plus direct offline browser run; new mobile menu/focus and checklist export/import tested |

The production/test cook distinction is already acknowledged in `architecture-notes.html#development-cook-versus-production-cook`: the development catalog and character configuration reference fixtures. Excluding all Tests content now would break the slice. Include required fixtures for packaged proof; exclude development content only after approved production references replace it. This is not a reason to move fixture definitions into production folders.

## N. Verified Architecture Invariants

Here, **verified architecture invariant** means consistently represented in the reviewed documentation and compatible with the relevant verified mechanisms. It does not mean an Unreal graph has been executed.

| Invariant | Evidence locations | Assessment |
|---|---|---|
| Intended game identity and connected exploration | `game-overview.html`, `original-roadmap.html`, phase/world material | Consistent; no mandatory seamless-world architecture |
| Definitions describe authored possibilities, not player ownership | BPDA/DA pages, Profile, item/skill chapters | Preserve immutable definitions and stable definition lookup |
| Persistent character is not the current Pawn | `ownership.html`, `assets/Player/BP_PlayerProfile.html` | Profile owns XP, points, purchases, inventory, equipment |
| Persistent world can exist without loaded actors | `assets/World/BP_WorldState.html`, persistent-state chapters | Durable value records and stable IDs, not door references |
| GI coordinates rather than implements every gameplay feature | `assets/Core/BP_GameInstance.html`, `communication.html` | Cross-model/travel/save responsibilities are separated from live simulation |
| Runtime current health is separate from final max-health stats | `assets/Combat/BPC_Health.html`, `assets/Combat/BPC_Stats.html` | Rebuild sources rather than save/re-add final totals |
| Death recovery is not disk load | `systems/save-load.html`, GI, Profile/WorldState lifecycle sections | Current persistent session retained |
| Ordinary travel is not recovery | `assets/World/S_RuntimeTravelState.html`, save/travel material | Value handoff intended; correct AUD-03's timing badge |
| SaveGame is a snapshot | `assets/Save/BP_SaveGame.html`, `systems/save-load.html` | No live UI/components/attack frames/AI/projectiles as save authority |
| Persistent replay is idempotent and reward-free | `assets/World/BPC_PersistentState.html`, persistent actors, world records | Interaction/reward commands separate from reconstruction |
| Cross-model changes finish before notification/save request | GI, Profile, WorldState, `architecture-notes.html` | Synchronous staged application convention, not engine transaction magic |
| One jump policy and one-jump budget | `systems/movement.html`, PlayerCharacter, original Part J | No native Jump parallel path; cut is not a new jump |
| Animation is presentation | animator, animation snapshot, combat/movement chapters | Does not authorize jumps, damage, death, cooldowns, rewards |
| Combat uses action phases/tokens and accepted damage | Combat/ActionState/Health/damage interface pages | No required simultaneous custom-interface and Apply Damage pipeline |
| Equipment references inventory identity | Profile, `S_InventoryEntry`, equipment material | No second independent inventory; repeated replacements must rebuild |
| Skill purchase state belongs to Profile | skill schema, Profile, skill chapters | Explicit costs/prerequisites/exclusions; no mutable purchase flag on definitions |
| Ability/effect execution is runtime state | Abilities/StatusEffects/value pages | Cooldowns/effects not a second permanent skill purchase store |
| Ordinary versus unique encounter persistence | enemy base/children, reward/world chapters | Ordinary resets and designated permanent completion are distinguished |
| UI observes and requests; source remains authoritative | `ownership.html`, widget boundaries, Profile | General architecture correct; AUD-01's refresh recipes are the important exception |
| Phase staging is deliberate | `sources/phase-creation-order.json`, `dependency-map.html`, Architecture Notes | No unjustified wholesale phase reorder needed |
| Examples are not final game content | fixture notices, test asset pages, scope notes | Test names/tuning remain development-only |
| Packaged proof is distinct from PIE | `phases/phase-11.html`, verification and test material | Correctly called for; not claimed executed here |

Concrete anti-pattern search did not establish instructions to keep inventory only on a Pawn, load an old save on normal death, reward in BeginPlay/ApplyPersistentRecord, mutate Data Assets as player state, use cross-map Actor pointers for world facts, repeatedly accumulate final stats, or solve initialization with arbitrary Delay/Get All Actors of Class loops. The relevant guardrails are unusually explicit and should not be removed during correction.

## O. Recommended Correction Order

1. **AUD-01: Separate widget observation from commands.** This is the clearest literal-implementation hazard. Correct all six confirmed recipes together and regenerate their search text. Prove that opening/refreshing a view changes no gameplay state.
2. **AUD-02: Define save-bank replacement before implementing New Game persistence.** Choose one explicit strategy, document failure boundaries, and add fresh-process old-bank/new-character tests. Preserve the existing single-writer/revision/snapshot design.
3. **AUD-03 and AUD-05: Make early runtime integration unambiguous.** Put health handoff in Phase 3, later effect/recharge extensions in Phase 9, and name the native movement observation hook. Prove ordinary travel and jump edge cases before adding more game content.
4. **AUD-04: Update current folder metadata before creating many real assets.** Apply approved selective nesting without renaming assets or changing the count. Update manifest, identity/creation pages, indexes, phase/system tables, and search together. Use the Content Browser for any later real-asset moves.
5. **AUD-06: Repair provenance claims.** Distinguish preserved architectural text from modified file bytes; identify historical check results and the immutable baseline. Keep the mobile improvements unless they fail actual usability tests.
6. **Complete the outstanding validation gates.** Run the raw-site crawler/offline browser checks and the high-risk Editor/package matrix. A report should say which checks actually ran and retain failure details, not just a green summary.
7. **Consider PI-01 and PI-02 as maintenance improvements.** They can reduce recurrence and beginner confusion but are not prerequisites for changing the architecture.

No existing documentation, gameplay system, asset name, Content folder, or runtime implementation was changed by this audit. The correction descriptions above are recommendations for a later task.

## P. Final Verification Checklist

Checked boxes indicate a documentation-level pass within the stated coverage boundary, not an executed Unreal acceptance test. An unchecked item names either a confirmed defect or missing validation; it does not silently mean both.

- [x] Game identity consistent in the reviewed corpus.
- [x] No uncommitted systems found promoted to requirements.
- [ ] Phase 0–11 order consistent without contradictory field guidance — intended sequence reconciles, but AUD-03 remains.
- [x] Planned asset count reconciled to 149.
- [x] Parent/base classes reconciled at register/current-identity level; no concrete mismatch found.
- [ ] Content paths reconciled with current requirements — AUD-04.
- [ ] Ownership model consistently expressed in all implementation recipes — general model is sound, but AUD-01 violates command/observation separation.
- [ ] Movement architecture technically coherent and sufficiently concrete to follow without timing guesswork — core mechanism supported; AUD-05 and M-04 remain.
- [x] Death recovery distinct from disk load in the documented design.
- [x] Normal travel distinct from death recovery in the documented design; implementation timing caveat AUD-03.
- [x] Persistent world IDs are stable/authored by policy, not regenerated each load.
- [x] ApplyPersistentRecord does not replay rewards in the documented design.
- [x] SaveGame treated as a snapshot; New Game bank bootstrap still needs AUD-02.
- [ ] UI does not trigger gameplay rules from observation paths — authoritative stores are correctly placed, but AUD-01 remains.
- [x] Animation does not own gameplay rules.
- [x] Test fixtures clearly distinguished from final content in the reviewed corpus.
- [ ] Internal HTML links valid — fresh exhaustive raw link/anchor validation not executed.
- [ ] Search/index metadata valid — stale content-path semantics confirmed; full target/body parity not independently revalidated.
- [x] Packaged-build assumptions identified; actual cooked-build proof remains unexecuted.
- [x] Material Unreal claims reviewed here are verified at mechanism level or explicitly qualified; 5.8.3 graph/runtime behavior is not falsely certified.

**Final judgment:** Preserve the architecture. Correct the six documented issues, especially UI refresh commands and New Game save-bank initialization, then close the explicitly outstanding Editor and static-site validation gates. This is a useful first-game implementation foundation, but it is not yet a trustworthy literal, end-to-end build manual without those corrections and proofs.
