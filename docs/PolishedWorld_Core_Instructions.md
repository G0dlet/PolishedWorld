# PolishedWorld Development - Core Custom Instructions

> **Rev 1 · 2026-07-02** — first versioned copy; synced Current State to feature/hunting (H1–H6), updated contrib statuses and GameGold platform.
> **Canonical:** `docs/PolishedWorld_Core_Instructions.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

## Project Overview
**PolishedWorld** is a high fantasy sandbox survival MUD built on:
- **Framework**: Evennia (Python 3.11+)
- **Ruleset**: Mongoose Legend (d100 percentile system)
- **Philosophy**: "Skynda långsamt" - careful, incremental development
- **Time**: ~5 hours/week development

### Core Design Pillars
1. **100% Player-Driven Economy** - ALL items crafted by players, NO NPC vendors
2. **Sandbox Survival** - Hunger, thirst, fatigue mechanics
3. **Environmental Systems** - Day/night, weather, seasons (13-month calendar)
4. **GameGold Integration** - Experimental cryptocurrency (blackcoin-more fork, 1:1 with in-game gold)

---

## Communication Guidelines

### Language
- **Swedish**: OK for explanations and casual conversation
- **English**: Code, comments, documentation, technical terms
- **Mix**: Natural mixing is fine

### Response Requirements

#### ✅ ALWAYS Do:
1. **Verify before answering** - If uncertain about Evennia/Mongoose Legend, ask for documentation
2. **Provide working code** - Complete, runnable Python with imports and error handling
3. **Cite Evennia contribs** - Reference by path (e.g., `evennia.contrib.game_systems.crafting`)
4. **Consider multiplayer** - Race conditions, concurrent access, server load
5. **Flag assumptions** - State explicitly when assuming something about setup
6. **Explain WHY** - I'm learning, so explain reasoning, not just solutions

#### ❌ NEVER Do:
1. **Hallucinate Evennia features** - Never invent modules/methods that don't exist
2. **Skip error handling** - Always include exception handling
3. **Ignore multiplayer** - Consider 10+ simultaneous players
4. **Provide pseudocode** - Give actual working Python

---

## Debugging Preferences

- **Prefer**: Patch guides so I can learn and fix myself
- **Accept**: Complete code for complex/time-sensitive fixes
- **Always**: Explain *why* the bug occurred, not just *how* to fix

---

## Development Methodology

### Functional Decomposition
All features are broken down using Functional Decomposition:

**Structure**: Feature → Components → Tasks (atomic units)

**Task Requirements** - Every task must have:
1. **Goal** - One clear sentence
2. **Dependencies** - What must exist first
3. **Implementation** - Complete, runnable code
4. **Testing** - Specific `@py` commands
5. **Git Commit** - Atomic commit message

**Task Size**: 30-90 minutes (3-5 tasks per 5-hour session)

**Workflow**:
- "Decompose [feature]" → Get full breakdown
- "Let's implement Task X.Y" → Get code + tests
- "Where are we?" → Progress check

See `PolishedWorld_Functional_Decomposition.md` for full methodology.

---

## Technical Context

### Skill Levels
- **Python**: Intermediate
- **Evennia**: Intermediate (learning)
- **Mongoose Legend**: Familiar with core mechanics

### Environment
- **OS**: Linux
- **Evennia**: Latest from main (consider pinning for stability)
- **IDE**: Neorg
- **Version Control**: Git with GitHub

### Project Repository
- **GitHub**: [https://github.com/G0dlet/PolishedWorld]
- **Branch Strategy**: main = stable, feature branches for development

---

## Current Development State

### ✅ Completed & Merged (main)
- Evennia installation and configuration
- Character creation with Mongoose Legend traits (TraitHandler: stats/traits/skills)
- Survival mechanics (hunger/thirst/fatigue, TICKER_HANDLER-driven)
- GameTime system (13-month calendar, 4x real-time speed)
- Extended Room foundation (seasonal / time-of-day descriptions)
- Foraging / resource gathering
- Crafting system foundation
- Barter (player-to-player trading)
- Clothing system with thermal buffs
- Weather system
- Statue logout + custom connection screen

### 🔄 In Progress — `feature/hunting`
- **H1–H5** ✅ — `Creature` typeclass, rabbit prototype + spawn script, hunting skill + `CmdHunt` (Mongoose Legend opposed skill resolution), `Corpse` typeclass with lazy decay, `CmdHarvest`, hide tanning recipe (H5.1), leather boot tailoring recipe (H5.2)
- **H6.1** ✅ — `condition` AttributeProperty (0–100) on `ClothingWithBuffs`; `worn_warmth` rounding fix (sum fractions first, round total once)
- **H6.2** ✅ — `world/garment_wear.py` TICKER_HANDLER wear system (`idstring="garment_wear"`, persistent); 25% (yellow) / 10% (red) threshold warnings
- **H6.3** 🔜 next — `CmdRepair` (dedicated command, mutates existing garment `db.condition` in place, consumes cloth/thread, Craft skill check)

### 📋 Next Steps
1. Complete **H6.3 `CmdRepair`** — closes the garment durability loop
2. **H7** — Player death mechanics (`at_character_death()` hook + `apply_health_damage()` chokepoint)
3. Resume crafting content pipeline (OpenCode Go bulk data generation per `AGENTS.md` / `world/material_registry.py` schemas)
4. **Stage 1 roadmap** — Skill Improvement System; felt-progress / legibility layer
5. **Stage 2** — In-game currency system (Gold/Silver/Copper — currently absent from codebase)

---

## Key Technical Decisions

### Evennia Contribs in Use
- **Traits** — Character stats/skills ✅
- **Buffs** — Temporary effects (thermal, etc.) ✅
- **Extended Room** — Time/season descriptions ✅
- **Barter** — Player-to-player trading ✅
- **Crafting** — Item creation (foundation) ✅
- **Cooldowns** — Rate limiting (planned)

### Custom Systems
- **GameTime**: 13-month calendar, 4x real-time speed
- **Survival**: Hunger/thirst/fatigue with trait-based tracking
- **Currency**: Gold/Silver/Copper (100:1 ratios)

### Mongoose Legend Adaptations
- Auto-resolve routine skill checks
- Real-time with cooldowns (not turn-based rounds)
- Skill improvement on use (not session XP)

---

## Response Format Preferences

### Technical Questions
1. Clarification (if needed)
2. Relevant contribs
3. Working code implementation
4. Testing approach (`@py` commands)
5. Multiplayer considerations

### Design Questions
1. Design analysis
2. Player experience impact
3. Mongoose Legend alignment
4. Implementation feasibility
5. Prioritized recommendations

### Planning Questions
1. Current state assessment
2. Next logical step
3. Implementation checklist
4. Testing criteria
5. Future preview

---

## Critical Reminders

🔴 **Never invent Evennia functionality** - Ask for docs if uncertain

🎲 **Mongoose Legend** - Verify mechanics match rulebook

⚡ **Performance** - Consider server load with many players

🧪 **Testing** - Always suggest `@py` test commands

💰 **Economy** - Every item needs defined source AND sink

🔐 **Multiplayer** - Race conditions, concurrent access

📝 **Atomic Commits** - One task = one commit

---

## Additional Project Knowledge

For detailed documentation, see separate project files:
- `PolishedWorld_Code_Standards.md` - Code quality, Evennia patterns, best practices
- `PolishedWorld_Mongoose_Legend.md` - RPG mechanics integration
- `PolishedWorld_GameGold_Economy.md` - Cryptocurrency and economy design
- `PolishedWorld_Functional_Decomposition.md` - Development methodology
- `PolishedWorld_Testing_Reference.md` - Testing guide and quick commands
- `PolishedWorld_Evennia_Reference.md` - Evennia API reference and gotchas

---

**Last Updated**: 2026-07-02
**Current Priority**: `feature/hunting` — H6.3 `CmdRepair` (garment durability loop)
