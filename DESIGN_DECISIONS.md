# Design decisions

## D01 Authority

Use dedicated zone servers for live rules and one authenticated backend for durable state. Client input is a request.

## D02 Native and Blueprint boundary

C++ owns rule validation, GAS, movement extensions and adapters. Blueprints edit definitions and compose visuals/UI.

## D03 Engine baseline

Target Unreal Engine 5.8.3; public release verified, local installation/build not verified.

## D04 Sprite presentation

ACharacter-based native bodies with Paper2D visual components and a single PaperZD presentation adapter.

## D05 Camera and movement

Fixed azimuth, elevated restrained perspective, zoom only; true X/Y locomotion with Z height.

## D06 Art coverage

Four-direction fallback and common body until archive inspection; eight directions and missing actions are production tasks.

## D07 Replication

Begin with generic actor/property/RPC replication.

## D08 Abilities

Choose GAS; player ASC on PlayerState, enemy ASC on enemy Character.

## D09 Persistence stack

One ASP.NET Core service on .NET 10 plus PostgreSQL 18, authenticated UE HTTP adapter.

## D10 Transactions

One DB transaction for each economic command, command receipt, affected rows and durable source claim; fence every server write.

## D11 Zone handoff

ClientTravel connects only the transferring player to an independently hosted destination. Backend ticket redemption changes the fencing epoch.

## D12 Early dependencies

Introduce identity/item records, reward receipt and session lock in Phase 05; minimal party/credit contract in Phase 08.

## D13 Resource competition

Exclusive transient action reservation, followed by atomic durable depleted-generation claim and reward.

## D14 Fishing

Server-owned attempt, bite window and terminal receipt; deterministic client visuals from accepted times.

## D15 Crafting

Deterministic output at first; all material, currency, item and profession changes commit together.

## D16 Loot and group credit

Initially party-shared kill credit with equal XP split among eligible nearby members, and personal loot allocations.

## D17 Equipment

15 logical positions: Head, Chest, Legs, Hands, Feet, Waist, Shoulders, Cloak, MainHand, OffHand, Neck, Ring1/2, Trinket1/2.

## D18 Death

Retain inventory, XP and quests; safe shrine respawn, remove short harmful effects, reinitialize resources under one recovery policy.

## D19 Scope stages

24 phases, three slices, six zone-family designs; only two graybox zones required for Slice A.

## D20 Naming and identity

Stable definition IDs, UUIDs for owned nonstackables/characters, integers for quantities and base currency.

## D21 Narrative

Original world of the Talarin Reach, with river, forest, marsh, highland, mountain and coast regions.

## D22 Daily/escort policy

No daily resets or escort production in initial core; define extension gates rather than silently enable.

## D23 Publication

Replace main only after validated documentation generation; retain existing history and a backup reference.

## D24 Evidence status

Delivered documentation is an evidence-labeled draft, not an acceptance-complete manual while the archive and installed APIs remain unavailable.

