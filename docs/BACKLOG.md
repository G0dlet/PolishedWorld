# PolishedWorld — Consolidated Backlog

> **Rev 47 · 2026-10-20** — one entry **closed**, one **annotated**, both from `feature/harvest-guard`, merged to `main` in `1c57f0a` (PR #17; fix `08d6c44`, tree `cfb6075`). *⚠️ `harvest` treats a player's body as a rabbit* goes **OPEN → DONE**: a refusal of its own in `CmdHarvest`, placed after the expiry check so an expired body still crumbles. Its *Status* records why neither (A) nor (B) as filed was taken — (A) would have removed one of `crumble()`'s three triggers, and the dev DB showed (B) would have fixed no existing corpse — and that the stored `creature_type` values are deliberately left. **Annotated:** *⚠️ Decay time can run backwards when the weather turns* gains a sighting from this branch's protocol: an untouched corpse read expired one evening and not expired the next morning. It is recorded as a sighting, not a receipt.
> **Rev 46 · 2026-10-19** — one entry **closed**, one **annotated**, two **added**, all from `feature/death-contract`, merged to `main` in `123ac53` (PR #16; feat `dd5f69e`, fix `2d87533`, tree `18a3d83`). *Death contract surfaces* goes **OPEN → DONE**: an owner-first loot grace on an unscaled clock, a death line and a `help death` topic built from the same live constants. Its *Status* records nine prose sites, not eight, the dev-DB corpses deliberately left unmigrated, and the one thing the in-game protocol found that the suite did not (the death line arrived after *Death's Chill* announced the comeback). **Annotated:** *⚠️ `CoinPile` vs the corpse's atomic content delete* gains two prose sites the Stage 5 task must change. **Added** (*Death & Corpses*): **⚠️ `harvest` treats a player's body as a rabbit**, OPEN, and **⚠️ Decay time can run backwards when the weather turns**, OPEN (latent), both found in this branch's anchor check and both outside its scope.
> **Rev 45 · 2026-10-19** — one entry **closed**, one **added**, both from `feature/sweeper`, merged to `main` in `1517235` (PR #15; refactor `726390e`, feat `0110922`, fix `66827a0`, tree `9bc9af7`). *Ambient sweeper NPC* goes **OPEN → DONE**: `Room.sweep_expired_corpses()` is the one home of the sweep loop, and the room hook and a `Sweeper` NPC both call it. Its *Status* records the departure from the entry's text rather than smoothing it over: the NPC runs on a **Script, not `TICKER_HANDLER`**, because the in-game protocol found that this project's startup code wipes every persistent ticker it does not itself re-add. **Added** (*Tooling & Process*): **⚠️ `at_server_start` ticker re-adds wipe every other persistent ticker**, OPEN and latent — nothing on `main` subscribes a ticker outside `at_server_start` today; the sweeper was the first and was moved off it.
> **Rev 44 · 2026-10-18** — one entry **closed**, one **unblocked**, three **annotated**, all from `feature/janitor`, merged to `main` in `cea296d` (fix `c95eb85`, test `73249d6`, tree `b3f56c3`). *⚠️ Corpse expiry fires only on direct interaction* goes **OPEN → DONE**: `Corpse.crumble()` is the single expiry writer, and look, harvest and a new `Room.at_object_receive` sweep call it and nothing else. Two places where the delivery departs from the entry's text are recorded in its *Status* rather than smoothed over: the sweep fires on **puppeted arrivals only**, not on anything entering, and the entry's *20 expired* receipt overcounted. *Ambient sweeper NPC* goes **BLOCKED → OPEN** and gains the consequence of that scope: the room hook does not fire for it. *`CoinPile` vs the corpse's atomic content delete*, *Death contract surfaces* and *Per-item corpse decay* are re-read against the merged code; the death contract's prose-site count rises from seven to eight.
> **Rev 43 · 2026-10-18** — two entries **added**, two **annotated**, all from the cozy-NPC design discussion. **Added** (*Death & Corpses*): **⚠️ Corpse expiry fires only on direct interaction — and its two writers disagree**, OPEN as an alpha prerequisite: room `look` never triggers the lazy sink, and `harvest` on an expired `PlayerCorpse` *moves* its loot to `home` via Evennia's `clear_contents()` instead of destroying it; the fix is one `Corpse.crumble()` writer plus a tickerless `Room.at_object_receive` sweep. **Added** (*World & Rooms*): **Ambient sweeper NPC**, BLOCKED on that writer — ambience only, it never decides a deletion. **Annotated:** *`CoinPile` vs the corpse's atomic content delete* (the Treasury sweep lands in `crumble()`) and *Death contract surfaces* (the crumble prose site moves there).
> **Rev 42 · 2026-10-18** — one entry **annotated**, one status pointer **moved**: *Alpha content epic* — task AC1.1 shipped on `main` (`cb60434`), and the entry now points at the decomposition's Rev 2, which records it. Nothing else changes.
> **Rev 41 · 2026-10-18** — one entry **added**, six **annotated**, three statuses **changed**. **Added** (*Containers*): **Weight and encumbrance (Legend ENC) — decompose before code**, OPEN as an alpha prerequisite (roadmap Rev 28 (E)): the data starts in the alpha content epic (AD8), the mechanic gets its own decomposition because the rule does not translate directly, and *Full container support* is folded into it, its trigger (craftable bags) being met by batch AC4.2. *Persistent alpha instance* is annotated with the seventh prerequisite, and *Fatigue-exhaustion consequence* with the weight mechanic's dependency on it and its chosen direction — Legend's Fatigue levels read as penalty bands on the gauge, with an Athletics test at the bottom whose failure forces a short rest (B), the forced rest being the last step rather than the first consequence. The weight entry records the intended direction — overload drains fatigue faster, so a loaded character rests more often, and costs in combat — and how Legend reaches the same place through harder Fatigue tests rather than a faster rate. And the alpha content epic is decomposed in `docs/PolishedWorld_Alpha_Content_Decomposition.md` (Rev 1). *Alpha content epic* goes **OPEN (due) → SCHEDULED**; its annotation records the two choices it left to the decomposition — a stone axe with a tool check in `forage` (AD1), because Flint and Tinder, flint's only consumer among the 44, is blocked on a steel striker; generic `wood` for the alpha with DECISION #10's revisit moved to Stage 5 (AD2), because a bow has no mechanic before combat — and three of its own figures the decomposition corrects: about 29 reachable items is **24** by name, the bow does not need `sinew`, and the registry drift is six entries plus `stick`, including `feather` and `tusk` marked EXISTS with no source since the registry's first commit. *Public test server*'s seeding part becomes component AC3 and *⛔ The recipe catalogue does not span the skill scale*'s E.1 becomes AC5; E.2 and the wiped box keep their statuses. The epic's "registry, ledger and AoL sweep in one commit" is kept for the registry and moved to the docs close-out for the two docs, because `main` does not describe branch code as shipped (decomposition AD6).
> **Rev 40 · 2026-10-17** — four entries **added**, four **annotated**, one status **changed**, all from the track-order decision (roadmap Rev 27). **Added:** *Alpha content epic — decompose before code* (Crafting & Tools, OPEN and due next session) — the FAS 1 cut, the registry corrections, seeding, the catalogue batches and E.1 as one decomposition, because costing showed them to be one epic; *Tanning upgrade — bark and water as `LeatherRecipe` inputs* (OPEN), the System Backlog §4 sketch kept as an upgrade now that tanning is ratified as shipped; *Persistent alpha instance* (Tooling & Process, BLOCKED on the alpha prerequisites), the owner Rev 38 recorded as missing, wiped at alpha close-out; and *Four docs under `docs/crafting/` and `docs/reference/` carry no Rev header*, found while giving the System Backlog its first. **Annotated:** the catalogue entry (a narrower FAS 1, tanning already delivered, catalogue authoring named as a step before E.1); *Public test server* — (a) moves onto the alpha track as the node-placement path, (b) is unchanged, and the entry's claim that world data already exists in `world/testworld_data.py` is corrected, since no such file is on `origin`; *System Backlog altitude* — its trigger is effectively met, and the rev header it cited did not exist until today; *Parchment* — **BLOCKED → OPEN**, because its trigger was tanning landing and tanning landed eighteen days before the entry was written. ⚠️ **One root cause under three of these:** `LeatherRecipe` shipped on 2026-06-30 and `world/material_registry.py` was not updated, so every document that asked the registry whether tanning existed was told no — the parchment entry, the alpha decision's (B) and the System Backlog. Correcting the registry is code and lands with the materials in the alpha content epic; this Rev records how far the drift reached.
> **Rev 39 · 2026-10-17** — one entry **decided**, one **annotated**, two **added**, all from the death-consequence policy (roadmap Rev 26). *`CoinPile` vs the corpse's atomic content delete* goes **SCHEDULED → DECIDED**, two stages early: its trigger was Stage 5 kickoff, but what it asked was a policy question — does any cleanup path get to destroy currency — and the policy session answered it with a rule rather than a `CoinPile` detail: **never; an abandoned pile is transferred to the Treasury with a ledger entry**. The entry's three candidates are all retired, and the text says why: two of them (exempt the pile, drop it on the floor) leave a `CoinPile` in a room that Stage 6 may recycle, which is the same unlogged burn moved to another file, and the third amends the principle that makes the economy auditable. The trigger for the *code* is unchanged. *Bank / post office* gains the owner-first grace in the sentence that already described the corpse, so it does not promise a risk the policy softened. **Added**, both under *Death & Corpses*: **death contract surfaces** — the owner-first `get_from` lock, the death message that carries the contract, and `help death`, with the seven prose sites in four files that the policy falsifies listed in the entry so they are changed in the same commit and not found afterwards; and **`at_character_death()` restore block vs persistent wound tiers**, BLOCKED on Stage 5, which is the die-to-heal hazard the roadmap entry names — filed now, before the wound model is coded, so the epic that adds locational HP reads it before touching the restore block rather than after.
> **Rev 38 · 2026-10-17** — two entries **annotated**, none added, both from the alpha milestone decision (roadmap Rev 25). *⛔ The recipe catalogue does not span the skill scale* gains the census the roadmap's open question asked for: its 110/152 figures — written here on 2026-08-12 and copied upward — are tag occurrences, not items; at item level the AoL decomposition holds 44 `[DATA]` finished items against 43 `[BLOCKED]`, with the same depth distribution on both sides, and neither the decomposition nor *Arms of Legend* carries a per-item difficulty. The Trigger is unchanged; what changes is *when* E.1 may run — after FAS 1 and tanning, per the roadmap decision — and the entry now says so, because an entry whose trigger can be met by assignment alone would otherwise invite exactly the guessing its own Trigger forbids. *Public test server with nightly reset* gains a conflict note rather than a change: its hosting half is sequenced *after Stage 5*, and its own text says the wiped box cannot test the economy pillar, while the alpha now defined excludes combat and exists to test pillar 1. Status is left as it is — the conflict is sequencing, which is roadmap altitude, and it is settled there with the track order; the annotation is here so the trigger is not read as current by someone who reads only this file.
> **Rev 37 · 2026-10-17** — **Epic A merged to `main` (`34b2ee4`)**, and the three entries that waited on it move. *Crafting resolves instantly* and *Timed player actions have a pattern but no shared home* go **SCHEDULED → DONE**: they asked to be done in one pass, and they were — on `feature/timed-actions`, merged together. Their *What* and *Why deferred* text is unchanged: it is the design as settled, including "`craft_duration` replaces `craft_cooldown`", which is what shipped. Both are kept for traceability and pruned at the next sweep, per the legend. *Two-stage healing* loses half of its blocker: Trigger (2), Epic A's timed-action module merged, is met, so the entry is now **BLOCKED (Stage 5 wound tiers)** alone. Its design text — surgery belongs on Epic A's slot rather than a hand-rolled branch — is unchanged, and now describes something that exists.
> **Rev 36 · 2026-10-17** — two entries **added**, two **annotated**, all found while Epic A's TA2.3 and TA3 were open and none of them Epic A's. They are filed on `main` before the epic merges because each describes behaviour `main` already has. *Tooling & Process* gains **the recipe visibility gate has no test**: `CmdRecipes` writes one rule out twice — the list hides unlearned advanced recipes, the detail view refuses them — and no test would notice the two copies drifting apart. *UX & Item Identity* gains **`look <scroll>` collapses the recipe block's column padding**, confirmed by running Evennia's own `compress_whitespace` on the block's rows rather than by reading its regex. The annotations: *Prototype keys leak into player-facing recipe names* gains a third surface, the craft-outcome line in `MongooseCraftRecipe.post_craft`, which names the product without an article. That is the object's own name, so not a key leak, but it is the article half of the same entry, and the entry's Trigger already says that a fix which leaves one surface behind has only moved the inconsistency. *`_format_wait()` truncates* gains the short end of its arithmetic: the last two minutes of every cooldown read `1 minute`, the rounding the entry proposes still errs by up to thirty seconds there, and one second reads `1 seconds`.
> **Rev 35 · 2026-10-09** — three entries **added**, one **annotated**, all found during Epic A TA1.3's in-game protocol and none of them Epic A's. *UX & Item Identity* gains two: **`descs` tables are read as upper bounds but shaped like lower bounds**, and **health `descs` use a 0–100 scale against a max of `CON × 2`** — the second is wrong under *either* reading of the first, which is why it is its own entry, and it is the one a player sees: a character at full health is told they are *critically wounded*. *Tooling & Process* gains **`Idmapper flush called more than once`**, the watch item the TA1.3 handoff asked to be filed if it recurred; it recurred, and reading Evennia's source turns it from "check memory usage" into a probable timing artifact with a stated way to confirm it. The annotation is on *Skill `descs` stop at 95*, whose band arithmetic reads the table as lower bounds while `world/improvement.py::tier_for()` reads it — deliberately, by its own docstring — as upper bounds. The two documents cannot both describe intent; the new entry says which decision has to come first, and the annotation stops the skill entry being picked up without it. Rev 35 corrects one claim made in the chat that found these: that the tables *were written* as lower bounds. Their shape suggests it; nothing records it, and `tier_for()`'s author recorded the opposite.
> **Rev 34 · 2026-10-08** — one entry **added** (*Tooling & Process*): **two treasury tests assume the developer's settings match the shipped ones.** Both test the *unset* state by applying no override at all, so on any working tree with a configured Treasury — which is every tree someone actually plays on — they fail on every local run. Filed rather than fixed because neither file belongs to Epic A, whose branch was open when this was found. Filed rather than tolerated because "expected failures" are the slow form of the Testing Reference's §11 trap: once two reds are normal, a third looks the same. The entry carries one verified detail that makes the obvious fix wrong — `override_settings(TREASURY_DBREF="")`, the pattern `tests/test_work_command.py` already uses, satisfies `resolve_treasury()` but fails `test_unset_is_a_supported_state`'s `assertIsNone(get_configured_dbref())`. The hermetic value there is `None`.
> **Rev 33 · 2026-09-09** — the two **timed-action** entries move **OPEN → SCHEDULED (Epic A)**. Nothing about either has changed; what changed is that the pass they both name now exists as a document instead of as a chat log. *Crafting resolves instantly* and *Timed player actions have a pattern but no shared home* have been cross-referenced since Rev 24 with the instruction to do both in one pass, and that pass is now decomposed in `docs/PolishedWorld_Timed_Actions_Decomposition.md` (Rev 1), which locks seven decisions (D1–D7) settled in chat and otherwise unrecorded — one slot rather than a flag per action, `rest` migrating rather than staying, explicit mutual exclusion rather than silent interruption, and `craft_duration` fully replacing `craft_cooldown`. They move to SCHEDULED rather than closing because nothing is built: it is the status Rev 23 used for `CmdScribe` in the same situation. The epic is defined at roadmap altitude (Rev 23), which is also where "Epic A" acquires a definition at all — the name was cited by this file's *two-stage healing* entry, Trigger and Status both, before anything defined it.
> **Rev 32 · 2026-09-09** — one entry **added** (*GameGold*): **cold staking (PIVX-style P2CS)**. The entry exists because the decision was to *defer*, and a deferral with a good reason behind it is exactly the thing that gets silently reversed later by whoever no longer remembers the reason. The reason: it feels like a genesis-only choice and is not — Bitcoin script reserves `OP_NOP` opcodes for redefinition at a fixed activation height, and on a chain with no listings, no third-party wallets and a handful of operators, later costs about what genesis costs. What genesis *does* cost is a consensus patch carried against upstream from day one, which spends the same budget as `GameGold_Design.md` Rev 3's exit trigger — the option to leave blackcoin-more stays cheap only while the patch set stays small. Filed rather than dropped because the payoff is a real pillar-1 mechanic: the temple as delegate staking node lets players stake without running infrastructure or holding keys.
> **Rev 31 · 2026-09-09** — new section **Environment & Weather**, three entries from a forward-looking design discussion (no code written; `world/weather.py` and `world/gametime_utils.py` read live from `main` first). The section exists because the three sit on one axis and would otherwise scatter into *Survival* and *World & Rooms*, where nobody looking for "what do we do about weather" would find them together. Two are cheap and want no new state: **weather inertia** (`roll_weather(season, current=None)` already carries `current` as an unused extension point, so a Markov table per season is a body swap) and **season-dependent day length**, encapsulated because `get_time_of_day()` is already the single reader. The third, **regional weather**, is filed **BLOCKED** rather than OPEN and cross-referenced to *biome fragment library* (Rev 26) and Stage 6 — per-region weather needs a region concept, and building one on today's global broadcast would author the same migration debt the biome entry exists to prevent. What the section deliberately does **not** hold is the temperature/exposure gauge: that is a survival mechanic with its own trait, its own clothing coupling and its own death mode — stage-sized, so it lands in `roadmap.md` (Rev 22) under this file's own scope rule.
> **Rev 30 · 2026-09-09** — one entry **added** (*Tooling & Process*): **public test server with nightly reset**. Filed as one entry rather than two because the halves are sequenced, not independent — deterministic seeding from an empty database is the *prerequisite* for the hosted box, and it is the half worth building now: it yields a reproducible fresh-DB environment locally and lets other people run the code without anyone operating a server. The hosting half is **BLOCKED on Stage 5**, and the reason is the opposite of the obvious one — the constraint is not effort but *content*. Multiplayer exposure is the entire point of hosting, and until two accounts have a reason to occupy one room, a public server buys uptime obligations toward strangers in exchange for a smoke test the maintainer could run alone. The entry also closes a hypothesis rather than leaving it to re-form later: the Evennia Game Index was assumed to require a live server, and source verification shows it does not — three required listing fields, none of them a hostname — so the index is **not** an argument for hosting, and a nightly-wiped instance would in fact publish a total-account count that resets to zero every day.
> **Rev 29 · 2026-09-09** — new section **Health & Injury**, one entry: **two-stage healing (stabilise vs. repair)**. It is the surviving half of a proposal the roadmap declined in the same session (Rev 21, `[RESOLVED]` organ-level damage model) — the organ *data model* was rejected, the triage/surgery *split* was not, and separating the two is the whole point of filing it here rather than losing it inside the rejection. Its own section rather than a sub-bullet of *Death & Corpses*, for the reason Rev 26 gave the biome library one: wound state is a domain Stage 5 is about to create, this is the first entry in it and will not be the last (armour AP mapping and prosthetics both land here), and an entry parked under a neighbouring heading is an entry nobody finds at stage-planning time. Filed **BLOCKED** on two named prerequisites rather than OPEN, because both are dated — there is nothing to treat until Stage 5's wound tiers exist, and surgery is a timed action by construction, so building it before Epic A's shared home lands would produce exactly the fourth hand-written `at_pre_move` branch Rev 24 wrote the trigger to prevent.
> **Rev 28 · 2026-08-24** — one entry **added** (*UX & Item Identity*): **skill `descs` stop at 95, so nothing reads above `master`** — surfaced by Stage 4.5 D.2 lifting the 100% cap, which made 140% reachable and `master` the label for everything from 95 upward. Deferred rather than fixed in D.2 because `descs` are stored **per trait on every existing character**, so new bands carry the same migration surface the cap removal did, for a purely cosmetic gain. One entry **re-homed**: **⛔ the recipe catalogue does not span the skill scale** was the blocker behind Stage 4.5's Component E, and with 4.5 closed and E moved out of the epic, this file is now E's only home — the trigger is armed here or nowhere.
> **Rev 27 · 2026-08-15** — one entry **widened, not added** (Crafting & Tools): **`recipes <name>` output name is a prettified prototype key** now covers the mirror defect found during Stage 4.5 D.1's in-game protocol — `CmdCraftGated`'s failure message renders the raw key (`Could not craft bone_needle without bone`) where the recipe is named `bone needle`. Same root cause, opposite direction: one surface prettifies the key and one forgets to, so a player sees two different names for the same recipe within a single session. Filed under the existing entry rather than as a new one, per the *one item, one home* rule — a fix that resolves prototype display names correctly closes both, and splitting them invites fixing one and calling it done. The entry's title and Trigger are updated to say so; its Status stays OPEN.
> **Rev 26 · 2026-08-13** — new section **World & Rooms**, two entries added from a builder-ergonomics design discussion (no code written; `typeclasses/rooms.py` read live from `main` first). The small one, **builder QoL for dynamic rooms**, bundles three cheap fixes — a state-combination preview, a `roommsg` command to replace the three-line `@py` echo setup, and a written authoring convention (base desc + overlay fragments; full `@desc/<time>/<season>` matrix variants are the exception, not the model). The load-bearing one, **biome fragment library**, is deliberately its own entry so it cannot vanish as a sub-bullet of the QoL list: per-room authoring of a 7-time × 4-season × weather state space does not scale past the test world, and every room built before the library exists becomes migration debt — which is also what makes the entry's trigger self-arming. It is filed as a design session, not a drop-in, because its open questions (fragment format, composition with ExtendedRoom's priority chain, zone overrides, procgen alignment) are exactly the kind that go wrong when settled implicitly in code.

> **Rev 25 · 2026-08-12** — one entry **added** (Tooling & Process) and one **annotated, not changed** (Crafting & Tools). Added: **`PolishedWorld_System_Backlog.md` sits at the wrong altitude for its location** — a strategic 14-system build-order list inside a tactical crafting subfolder. Logged rather than fixed, because moving a file breaks its rev header's canonical path and every reference to it; that is its own small task, not something to fold into a documentation sweep. Annotated: the **recipe catalogue** entry, whose Trigger described the work as though the catalogue had to be authored from nothing. It does not — `docs/crafting/` has held a complete *Arms of Legend* dependency decomposition throughout, and the entry's own author did not know it, which is precisely what an unindexed subdirectory does (see `docs/README.md` Rev 8). **The blocker does not lift:** `min_skill` appears zero times in that decomposition, so the axis Component E reads is the one thing the existing material lacks. What changes is the size and shape of the remaining work, and that is worth recording before someone scopes it as authorship.

> **Rev 24 · 2026-08-11** — one entry **added** (Crafting & Tools): **crafting resolves instantly**, with the design settled ahead of any code — timing belongs in the command, not the recipe, because `CraftingRecipeBase.craft()` is synchronous by construction; the shape is to delay `super().func()` in `CmdCraftGated` so ingredient re-resolution lands at completion and the collect→roll→consume sequence stays atomic in one tick. The entry matters less for itself than for what it fires: **it is the third timed action**, so the *Timed player actions have a pattern but no shared home* trigger is now **met**, and the two entries are cross-referenced from both sides. That entry named gathering and Stage 6 combat as the likely third; crafting arrived first, which is exactly why it is written down rather than left to become a fourth hand-written `at_pre_move` branch. The *`CmdCraftGated` recipe-resolver duplication* entry is **annotated, not changed**: a future discipline resolver and recipe-mastery handler both want to read the private registry, and both go inside `world/knowledge.py` to hold the consumer count at four modules — the move F.3 already made for `render_recipe_detail_by_name`.

> **Rev 23 · 2026-08-05** — the **`CmdScribe`** entry is **answered and moves OPEN → SCHEDULED**: Stage 4.5's sub-decision close-out settled it in favour of training, and it ships as C.1's sixth call-site. The entry stays rather than closing, because it is not done until C.1 does it. The deciding argument was not the balance one the entry itself had already ruled out — it was that a rule of the form *"some Craft rolls teach and some do not, and you are not told which"* is not learnable by a player, and P-5 makes generosity the safe side to err on. One entry **added** (Crafting & Tools): **the recipe catalogue does not span the skill scale** — eight recipes, one `min_skill`, highest 30 — which is what blocks Stage 4.5's Component E and would strand every crafter above 61 if the gate shipped against it. Filed as BLOCKED with a content trigger, not as tuning.
> **Rev 22 · 2026-08-05** — one entry added from the Stage 4.5 Component B close-out (Crafting & Tools): **`SkillXPHandler.add()` does not raise on an unknown skill key.** Recorded because it is the one place Component B knowingly departs from D7, not because it is a defect — it follows `improve_skill_on_use`, which made the same call in the opposite direction and wrote down why. Filed as SCHEDULED rather than OPEN: C.1 reviews every improvement call-site anyway, which is the only moment the answer can change without being a guess.
> **Rev 21 · 2026-08-03** — one entry added (Crafting & Tools): **`CmdScribe` rolls Craft but grants no improvement.** Surfaced while counting `skill_check` call-sites for the roadmap Rev 13 correction — five of six roll-sites train the skill, one does not, and nothing in the code or the decomposition says whether that is a decision or an omission. Recorded as an open question rather than a defect, because either answer is defensible and neither is written down.
> **Rev 20 · 2026-08-03** — one entry added from the Core Instructions Rev 3 sweep (Tooling & Process): **three cited documents live outside the repo**, and they are also the only three in the project with no Rev header, no date and no canonical path. Rev 3 marks them per §9 rather than importing them blind.
> **Rev 19 · 2026-08-03** — the seam-checker entry (Tooling & Process) gains a second job: **parse the Mermaid blocks too.** System Map Rev 2 shipped a diagram that did not render, and the failure was invisible to every check performed on it — balanced brackets, balanced pipes, careful reading. Only the actual Mermaid parser found it. A checker that verifies the seam *table* while the *diagram* above it is silently broken is checking the cheaper half.
> **Rev 18 · 2026-08-03** — one entry added from the System Map Rev 2 sweep: **a runnable seam checker** (Tooling & Process). Not a defect and not a nice-to-have — the map's §*How to keep it honest* prescribes a `grep` that produced two of the three false rows Rev 2 had to fix, and the obvious replacement (AST) silently misses `getattr`-string dispatch. Rev 2 fixed the rows and documented both failure modes in prose; a convention that has now failed once is worth making runnable. Trigger is concrete rather than aspirational: the Damage-chokepoint row already reads `(future: combat)`, so Stage 5 will edit that table.
> **Rev 17 · 2026-08-03** — Stage 4 Component E close-out. One entry **narrowed**, two added, neither a defect. The **`copper` name collision** (Currency) shrank rather than closed: `offer` was the one verb where both readings were plausible, and E.1's digit-first rule settles it without renaming anything, because Evennia's disambiguation syntax is a *suffix* (`copper-2`) and so no valid object name begins with a digit. What is still deferred is only `caller.search()` facing two `copper`s in a room, which needs `CoinPile` to exist. **Upstream `finish()` is not safe to call twice** (Currency) is recorded rather than scheduled: it is unreachable in play, but it is *currently* what prevents a double currency settlement — by accident, in someone else's code — and anyone reading our one-shot flag should know the belt is doing work the braces also do. **Trade item moves bypass move hooks and `get` locks** (Crafting & Items) is not new debt but newly *homed*: it lived only in `world/README_barter.md`, and it pairs with the future no-trade flag, since the flag without enforcement is decorative and enforcement without the flag has nothing to enforce.

> **Rev 16 · 2026-08-02** — Stage 4 Component D close-out. Three new entries, none of them defects. **Faucet task-table tuning** (Currency) is the entry the decomposition asked for by name: `TEMPLE_TASKS` is the anchor, and its numbers cannot be judged until crafted goods have prices players actually charge, because the faucet's whole job is to read as obviously a supplement against a market that does not exist yet. **Timed player actions have a pattern but no shared home** (Tooling & Process) records a duplication rather than a bug: `rest` and `work` implement interruptible timed actions independently, and `at_pre_move` in `characters.py` now carries two hand-written branches that will grow one per future action — the *third* is the signal to extract a helper, not the second. **`_format_wait()` truncates** (Currency) is cosmetic: a fresh one-hour cooldown renders as `59 minutes`, which reads as though the clock started early; noted with the reason the naive ceiling fix is wrong in the other direction.

> **Rev 15 · 2026-08-02** — Stage 4 Component C close-out. Four new entries, all small and all found by running the shipped command rather than by reading it. **Ledger `actor` field** (Currency) is the only one with teeth: the entry shape records who *received* a mint but not who *ordered* it, so the ledger alone cannot answer "which admin minted this" — `@economy` writes the actor to the rotating server log as a stopgap, and the trail exists today, but it is in the wrong place. **Audit holder-count vs wallet-sum inconsistency** (Currency) — the count includes the Treasury while the sum excludes it, so a freshly minted economy reads `Wallets: nothing (1 holder)` where the one holder is the Treasury reported on the next line. **`@economy` log-line direction** (Currency) — burns log `-> treasury #N`, which reads as money going in. **Player → Treasury has no command** (Currency): `pay` refuses the Treasury by design and `donate` was deliberately not claimed, so the Stage 4 exchange-back is admin-mediated; Stage 8's `exchange` owns the direction, recorded so nobody fills the gap speculatively.

> **Rev 14 · 2026-07-30** — Stage 4 Component B close-out. Three new entries. **Bank / post office** (Currency) is the deliberate counterpart to a locked *rejection*: `pay` is same-room permanently, because coin is carried on the body and stays with the corpse, so remote payment would cancel the risk that makes carrying a decision — the sanctioned answer to "I don't want to carry this" is a *place* you have to reach. The rejection itself lives in the Currency decomposition, not here; this entry is the feature that replaces it. **`PAY_CONFIRM_THRESHOLD`** (Currency) carries the reasoning for shipping `pay` with no confirmation prompt, and the constraint that any future confirmation must not be a `yield`. ⚠️ **`CoinPile` vs the corpse's atomic delete** (Death & Corpses) is a doc-vs-code conflict found while reading corpse behaviour for B: `PlayerCorpse` destroys all contents at expiry, while Economic Philosophy Rev 2 states currency never weathers and Gold has exactly one permanent exit. Harmless today (no coin objects exist), a silent second burn point the moment `CoinPile` lands.

> **Rev 13 · 2026-07-27** — Stage 4 Component A close-out. Three new entries: **compact amount input** (`50c`, `2g30s` — one feature, one entry), the **`copper` name collision** between the material registry and the currency denomination (harmless in Stage 4, detonates when `CoinPile` materialises), and **`MINT_SOURCES` / `BURN_REASONS` tuning**. The unit-test coverage initiative is marked **DONE** — its "neither is in the repo" note was written honestly and is now simply out of date: `tests/__init__.py` and `tests/test_knowledge.py` are on `main`, `AGENTS.md` Rev 2 carries §0A, and `tests/test_currency.py` is the second suite built to the template.

> **Rev 12 · 2026-07-26** — Stage 3 close-out. **Component I (thin world-loot scroll
> seed) deferred here in full** rather than built — the decomp named it a defer-candidate
> if world-content plumbing wasn't ready, and it isn't (`world/batch_cmds.ev` is untouched
> Evennia boilerplate). The entry carries the profession-coverage analysis, the sharpened
> trigger (risk is highest at LOW player counts, so the trigger is *before the first real
> player cohort*, not "when the world is big"), and the design decisions that would
> otherwise be lost. Also added the *unit-test coverage initiative* under a new
> **Tooling & Process** section: `tests/test_knowledge.py` was drafted in an earlier
> session but is not in the repo on either branch, and `AGENTS.md` §0 never gained the
> `tests/` scope entry — logged honestly rather than left in working memory.
> **Rev 11 · 2026-07-26** — Stage 3 Component H close-out (teaching — synkron
> transfer med samtycke, H.1). Added two *Crafting & Tools* entries: *teach-channel
> tuning* (`TEACH_TIMEOUT` / `TEACH_COOLDOWN` — one axis, and the entry carries the
> `TEACH_COOLDOWN >= TEACH_TIMEOUT` invariant that makes "one student at a time"
> structural), and *Teaching skill as an amplifier* — moved into its canonical home
> here, having lived only as a decomp §15 anchor since Rev 1. The two entries are
> deliberately cross-referenced: any future "more simultaneous students" amplifier
> must be read against the invariant, since raising it silently is what would break
> the one-offer guarantee.
> **Rev 10 · 2026-07-25** — Stage 3 Component G close-out (book — perishable bulk
> transfer, G.1–G.3). Added three *Crafting & Tools* deferrals: *book-channel tuning
> constants* (`SCRIBE_MIN_CRAFT` / `SCRIBE_COOLDOWN` / `SCRIBE_CONDITION_BY_TIER` /
> `BOOK_WEAR_PER_STUDY` — one balance axis, since start-condition ÷ wear IS
> readers-per-book), *scribe's band→condition bypasses `quality_band`* (a deliberate
> consistency divergence, logged rather than refactored), and *book repair
> ("rebind")* — moved into its canonical home here, having lived only as a decomp
> §15 anchor. Extended the existing *parchment* entry with G.2's book-cover case
> instead of duplicating it (same tanning-chain blocker, same design axis).
> **Rev 9 · 2026-07-18** — Stage 3 Component G.1 (perishable `Book` typeclass).
> Added one *UX & Item Identity* deferral: *per-recipe `min_skill`/detail on
> book & scroll `look`/`evaluate`* — the "show buyers craftability, not just
> contents" refinement; MVP Alpha ships names + condition only. No new Crafting
> deferral from G.1 itself; the barter `evaluate`→`get_display_desc` fix that
> surfaced alongside it is a completed hardening (shipped on
> `feature/recipe-knowledge`), not a backlog item.
> **Rev 8 · 2026-07-18** — Stage 3 Component F close-out (scroll — the first *written*
> knowledge channel, F.1–F.4). Added three Crafting & Tools deferrals: *`INSCRIBE_COOLDOWN`
> tuning* (conservative 60s, no playtest data), *parchment writing material* (the
> hide-derived surface deferred from F.1a, BLOCKED on the tanning chain), and *blank
> scroll as a craftable intermediate* (F.4 follow-up, same design axis as parchment).
> Extended *`CmdCraftGated` recipe-resolver duplication* to its full four call sites —
> `_can_transmit` (F.1) and `CmdLearn` (F.2) both read `_RECIPE_CLASSES`, and
> `render_recipe_detail_by_name` (F.3) deliberately keeps that read inside
> `world/knowledge.py` so the `Scroll` typeclass never becomes a fifth consumer.
> Extended the *`recipes <name>` prettify* entry: the renderer is now shared
> (`render_recipe_detail`) by `recipes <name>` and `look <scroll>`, so one fix lands both.
> **Rev 7 · 2026-07-13** — Stage 3 Component E close-out. Added *`DISASSEMBLE_COOLDOWN`
> tuning* under Crafting & Tools (the conservative 300s constant, no playtest data
> yet). Extended *`CmdCraftGated` recipe-resolver duplication*: `CmdDisassemble`
> (E.2) is a second consumer of the contrib's private `_RECIPE_CLASSES` — an exact
> `.get(name)` this time, not the fuzzy matcher — so both live under one entry.
> Noted the E.1 `obj.db.recipe` stamp now provides the recipe half of the
> maker's-mark identity.
> **Rev 6 · 2026-07-12** — Added a new *Professions & Chargen* section two
> Stage 3 Component D deferrals from the Legend profession analysis: *Profession
> Common-Skill bonuses (Legend's other half)* and *Cultural-Background gating of
> professions*. Both BLOCKED on a real chargen / Cultural Background system;
> Component D ships knowledge-only, free-choice professions.
> **Rev 5 · 2026-07-11** — Added *`recipes <name>` output name is a prettified
> prototype key* (polish) under Crafting & Tools — the C.2 detail view (Recipe
> Knowledge decomp §8) shows `output_prototypes` keys with underscores swapped
> for spaces; resolving the prototype's real key/desc and correct
> article/pluralisation ("a pair of leather boots") is deferred.
> **Rev 4 · 2026-07-11** — Added *`CmdCraftGated` recipe-resolver duplication*
> (tech-debt) under Crafting & Tools — a UX-layer duplicate of the crafting
> contrib's private recipe matcher, backstopped by pre_craft (Recipe Knowledge
> decomp §7 / Task B.2).
> **Rev 3 · 2026-07-11** — Added *Duplicate `MongooseCraftRecipe` import in
> recipes.py* (tech-debt) under Crafting & Tools, flagged during Stage 3
> Component A source-verification.
> **Rev 2 · 2026-07-11** — Origin-trim pass. Added the hunt-independent needle
> primitive (a Stage 2 §13 item missed in the Rev 1 seed). Removed *Search /
> disambiguation UX* — it is already richly homed in the always-read `roadmap.md`
> §backlog, so listing it here would only duplicate it (see scope note below).
> Corrected two origins (`look`-injection and GameGold explorer originate from
> working memory, not a written doc line). Migrated items trimmed to pointers in
> their origin decomps (crafting §13 Rev 9, hunting Rev 2, Evennia Ref §8.8 Rev 12).
> **Rev 1 · 2026-07-11** — Initial consolidated backlog. Seeded from the Stage 2
> crafting decomposition §13, the hunting/H7 decomposition backlog, the Evennia
> Reference §8.8 note, and the Component G "not in scope" deferrals.
>
> Canonical: docs/BACKLOG.md

## Purpose & scope

Tactical deferrals **smaller than a stage** — refinements, tech-debt, and
cross-cutting or orphaned tasks that would otherwise die inside a feature
decomposition's §Backlog once that decomposition closes and stops being read.

**This is not the roadmap.** Strategic epics and future stages live in
`roadmap.md` (its backlog + decision log). This file is for the small stuff that
has no stage of its own. **Items already safely homed in the always-read
`roadmap.md` are intentionally excluded** — duplicating them here would recreate
the very drift this file exists to prevent. Only items that would otherwise be
*orphaned* (buried in a closing decomp, or living only in working memory) belong
here.

**One item, one home.** When an item lands here it is trimmed from its origin
doc to a one-line pointer (`→ see BACKLOG.md`). A feature-internal deferral that
already has a *scheduled* home ("fixed in Component X") stays in its decomp; only
the homeless items migrate here.

**Workflow hook:** whenever a task is deferred, log it here in the same pass —
so this document doesn't become the next thing that's forgotten.

## Status legend

- **OPEN** — actionable whenever picked up; no blocker.
- **BLOCKED** — waiting on a named prerequisite (stated in *Trigger*).
- **SCHEDULED** — has a concrete future home (stage/component named).
- **DONE** — completed; kept briefly for traceability, then pruned.

Each entry: **What · Why deferred · Trigger · Origin · Status**

---

## Crafting & Tools

### Metal tools + craft-station / forge
- **What:** Metal-tier tools (metal knife/needle already exist as spawn-only
  prototypes) made craftable via a forge/craft-station.
- **Why deferred:** Out of Stage 2 scope; needs a station concept + metallurgy
  materials that don't exist yet.
- **Trigger:** A future crafting/metallurgy epic.
- **Origin:** Crafting Progression decomp §13.
- **Status:** OPEN

### Superior-tool longevity / condition bonus
- **What:** Let a *superior* crafted tool (quality > 100) start with better
  condition or wear slower, on top of the +10 craft bonus it already grants.
- **Why deferred:** Would collide with the prototype-driven start-condition
  (40/30, D.5) that `_apply_tool_quality` deliberately does **not** touch.
- **Trigger:** Metal tools + forge (when start-condition becomes tier-driven
  rather than a flat prototype value).
- **Origin:** Component G design (Rev 8), deferred by decision.
- **Status:** BLOCKED (metal tools + forge)

### `tool_wear_on_fumble` tuning
- **What:** Extra wear on a fumbled craft, tunable via a `tool_wear_on_fumble`
  knob.
- **Why deferred:** Balance-tuning, not a mechanic gap; no data to tune against
  yet.
- **Trigger:** Live playtest data on wear pacing.
- **Origin:** Crafting Progression decomp §13.
- **Status:** OPEN

### `DISASSEMBLE_COOLDOWN` tuning
- **What:** Real-time seconds between reverse-engineering attempts, the named
  constant `commands/crafting_commands.py::DISASSEMBLE_COOLDOWN` (currently 300).
- **Why deferred:** Balance-tuning, not a mechanic gap. The disassemble roll is
  already destructive (the item is consumed win or lose), so the cooldown only
  paces *attempts*; 300s is a conservative dev value chosen to keep the item
  channel from undercutting the paid scroll/teach channels, with no playtest data
  to tune against yet.
- - **Trigger:** Live playtest data on how fast players grind bought goods for
  recipes.
- **Origin:** Recipe Knowledge decomp §10, Task E.2.
- **Status:** OPEN

### `INSCRIBE_COOLDOWN` tuning
- **What:** Real-time seconds between `inscribe` attempts, the named constant
  `commands/crafting_commands.py::INSCRIBE_COOLDOWN` (currently 60).
- **Why deferred:** Balance-tuning, not a mechanic gap. `inscribe` already costs a
  bolt of cloth per scroll, so the material is the real economic throttle and the
  cooldown only stops scroll-spam; 60s is a conservative dev value (lighter than
  disassemble's 300, since inscribe is the *intended* paid channel), no playtest
  data yet.
- **Trigger:** Live playtest data on scroll production/trade cadence.
- **Origin:** Recipe Knowledge decomp §11, Task F.1.
- **Status:** OPEN

### Parchment writing material (hide-derived writing surface)
- **What:** A dedicated `parchment` primitive as the scroll's writing surface,
  tanned/derived from hide (tying the hunting economy into the knowledge economy),
  instead of F.1's MVP reuse of `cloth`. G.2 extends the same question to the
  *book*: the decomposition's first shape was `parchment×N` pages plus a `leather`
  cover bound with `twine`, shipped instead as `SCRIBE_MATERIAL_TAGS = cloth×2 +
  twine`. Both carriers should adopt the hide-derived surface together.
- **Why deferred:** Parchment-from-hide needs a tanning chain that does not exist:
  `leather` is DECISION-status (unbuilt) and `raw_hide` is an orphan until tanning
  lands, so building parchment now drags in half an unbuilt economy chain. F.1
  reuses `cloth` (EXISTS, a plausible woven writing surface) so the scroll channel
  ships without blocking on tanning.
- **Trigger:** The tanning chain landing (leather / DECISION #2 resolved), decided
  *together with* the blank-scroll entry below — both answer the same question
  ("what is the physical writing surface, and is it a crafted good?").
- **Annotation (2026-10-17, roadmap Rev 27 (D2)):** the trigger is met, and the
  premise under *Why deferred* was false when it was written. `LeatherRecipe`
  (`raw_hide`×2 → `leather`) shipped on 2026-06-30 (`896ce33`), eighteen days
  before this entry. The entry read the material registry, where `leather` still
  said DECISION and `raw_hide` had no sink — the registry was not updated when the
  recipe shipped. DECISION #2 is ratified as shipped in roadmap Rev 27. Still
  decided *together with* the blank-scroll entry below, and not part of the alpha
  scope.
- **Origin:** Recipe Knowledge decomp §11, Task F.1 (choice (a), locked to cloth);
  §12, Task G.2 (choice (b), book bound from cloth×2 + twine).
- **Status:** OPEN (trigger met 2026-10-17 — previously BLOCKED on the tanning chain)

### Blank scroll as a craftable intermediate
- **What:** Make the writing surface its own craftable good:
  `cloth → blank scroll (craft) → inscribe → scroll of <recipe>`. `inscribe` would
  then simply `stamp()` a held blank scroll (F.4 already provides `stamp()`) — no
  prototype spawn, no material search inside the command.
- **Why deferred:** An economy-depth refinement, not a correctness gap: the scroll
  loop works today (inscribe spawns + consumes cloth directly). Adding a tradeable
  intermediate before players want to *trade* blank scrolls builds depth ahead of
  demand. Low-risk to defer — inserting a craft step later needs no migration of
  existing "scroll of <recipe>" items.
- **Trigger:** Player demand to trade blank writing surfaces, or the parchment
  decision above — same design axis, decide the two together.
- **Origin:** Working memory — Component F.4 follow-up (deferred by decision).
- **Status:** OPEN

### Material / maker's-mark aliases beyond "superior"
- **What:** Individuating aliases from material and maker ("a steel dagger of
  <smith>") on top of the quality alias.
- **Why deferred:** Pairs with recipe knowledge (who knows/made what). The data
  primitives are now in place: `crafted_by` (the maker) plus the `obj.db.recipe`
  stamp from E.1 (the recipe) — this entry is the display/alias layer on top.
- **Trigger:** Stage 3 (Recipe Knowledge & Discovery).
- **Origin:** Crafting Progression decomp §13; also feeds the disambiguation fix.
- **Status:** SCHEDULED (Stage 3)

### Waterskin `durability` → `condition` migration
- **What:** Migrate the waterskin's refill-count `durability` onto the shared
  `condition` axis used by everything else.
- **Why deferred:** D3 standardised on `condition` but left the waterskin as a
  known divergent; migrating it is a self-contained refactor.
- **Trigger:** None hard; do when touching waterskin next.
- **Origin:** Crafting Progression decomp §3 (name-fork note) + §13.
- **Status:** OPEN

### Hunt-independent needle primitive
- **What:** A gatherable needle primitive (e.g. a `thorn`/`stick` needle) so the
  needle bootstrap doesn't require a hunt (bone needle → bone → a kill).
- **Why deferred:** The bone needle covers the bootstrap today; a forage-only
  path is a convenience/robustness refinement, not a gap.
- **Trigger:** None hard; do if the hunt-gated needle proves a friction point for
  new players.
- **Origin:** Crafting Progression decomp §13.
- **Status:** OPEN

### Duplicate `MongooseCraftRecipe` import in `recipes.py`
- **What:** `world/recipes.py` imports `MongooseCraftRecipe` twice on adjacent
  lines at the top of the file. Remove the redundant second import.
- **Why deferred:** Pure hygiene; harmless (a re-import is a no-op) and outside
  the scope of the Stage 3 Component A commits it was spotted during.
- **Trigger:** None hard; fold into the next `recipes.py` touch, or a standalone
  `chore(recipes): remove duplicate import`.
- **Origin:** Stage 3 Component A source-verification (2026-07-11).
- **Status:** OPEN

### `CmdCraftGated` recipe-resolver duplication
- - **What:** `commands/crafting_commands.py::_resolve_recipe` re-implements the
  contrib's fuzzy match (exact → `startswith` → `in`, unique) and reads the
  private `_RECIPE_CLASSES` / `_load_recipes` from the crafting contrib. There are
  now four call sites reading that private registry: `_resolve_recipe` (B.2, fuzzy)
  and `CmdDisassemble` (E.2, exact `.get` on the E.1 stamp) in
  `crafting_commands.py`, plus `_can_transmit` (F.1) and `CmdLearn` (F.2, exact
  `.get` on a scroll stamp) in `world/knowledge.py` / `crafting_commands.py`. F.3's
  `render_recipe_detail_by_name` deliberately keeps its resolve *inside*
  `world/knowledge.py` (already a consumer via `_can_transmit`) so the `Scroll`
  typeclass renders `look` detail without touching the registry — the count stays at
  these four modules, not five.
- **Why deferred:** The contrib exposes no public recipe-resolver API; `pre_craft`
  (B.1) is the authoritative backstop if this duplicate drifts, so the ~5 lines
  are an accepted UX-only convenience, not a correctness dependency. E.2's
  exact-get degrades gracefully (a removed recipe → None → unlearnable, no
  destroy), so it too tolerates the private matcher changing under us.
- **Trigger:** The crafting contrib stabilising a public resolver API (or its
  private matcher changing under us).
- **Constraint until then (Rev 24):** any *new* reader of the private registry
  goes inside an existing consumer module, not a fifth. The recipe-mastery epic
  wants two — a `discipline` resolver for `recipes <discipline>` and the mastery
  handler's recipe lookup — and both belong in `world/knowledge.py`, which is
  already a consumer via `_can_transmit`. This is the move F.3 made for
  `render_recipe_detail_by_name`, for the same reason.
- **Origin:** Recipe Knowledge decomp §7 (Task B.2); §10 (Task E.2).
- **Status:** OPEN

### Prototype keys leak into player-facing recipe names (both directions)
- **What:** Two surfaces disagree about how a prototype key becomes a name the
  player reads.

  *Prettified but not resolved:* `world/knowledge.py::render_recipe_detail`
  renders each `output_prototypes` entry by swapping `_`→space (e.g.
  `leather_boots` → "leather boots"). It does not resolve the prototype's real
  `key`/`desc`, nor apply a correct article/pluralisation ("a pair of leather
  boots"). As of F.3 this renderer is shared by `recipes <name>` (C.2) and
  `look <scroll>` (the `Scroll` typeclass), so one fix corrects both surfaces.

  *Not prettified at all:* `CmdCraftGated`'s missing-material message emits the
  raw key — `Could not craft bone_needle without bone.` — for a recipe whose own
  name is `bone needle`. Found in the Stage 4.5 D.1 in-game protocol. The player
  sees two different names for one recipe inside a single session, and the
  underscore reads as a leaked identifier rather than a typo, which is what it
  is.
- **Why deferred:** Resolving prototypes is a separate verification surface
  (`evennia.prototypes`) and article/plural rules are per-item; the prettified
  key is legible and correct enough for discovery. Cosmetic only.
- **Trigger:** Any pass that adds prototype display-name resolution, or the first
  recipe whose prototype key reads badly when prettified. Whichever pass takes it
  must fix **both** surfaces — a resolver that leaves the error path emitting raw
  keys has moved the inconsistency rather than closed it.
- **Origin:** Recipe Knowledge decomp §8, Task C.2; error-path half found in
  Stage 4.5 Component D.1's in-game protocol (2026-08-15).
- ⚠️ **Rev 36 — a third surface: the craft-outcome line.**
  `world/crafting_base.py::MongooseCraftRecipe.post_craft` fills the
  `{outputs}` slot of `tier_messages` with each product's `get_display_name()`.
  That is the spawned object's own key, so the name is right, but it has no
  article: *"The work fights you; length of twine comes out poorly made."*
  (seen in play 2026-10-17). All four tier templates have the slot. This is not
  a prototype-key leak; it is the article half of the first surface above,
  reached from the other end. Whichever pass takes this entry fixes **all
  three** surfaces, by the Trigger's own reasoning.
- **Status:** OPEN

### Book-channel tuning (`SCRIBE_*` + `BOOK_WEAR_PER_STUDY`)
- **What:** The four named constants in `commands/crafting_commands.py` governing how
  fast books spread knowledge: `SCRIBE_MIN_CRAFT` (50), `SCRIBE_COOLDOWN` (120),
  `SCRIBE_CONDITION_BY_TIER` (`{critical: 100 + crit_score, success: 80, failure: 50,
  fumble: 25}`) and `BOOK_WEAR_PER_STUDY` (20).
- **Why deferred:** Balance-tuning, not a mechanic gap, and deliberately ONE entry:
  start-condition ÷ wear IS readers-per-book (currently 2 / 3 / 4 / 5+ by binding
  quality), so tuning any one constant in isolation moves the same emergent number.
  All four are conservative dev values — the material cost (cloth×2 + twine) is the
  real economic throttle, and no playtest data exists on how widely a single book
  should seed a recipe.
- **Trigger:** Live data on book production/trade cadence, or recipes spreading
  visibly faster/slower than the scroll and teach channels.
- **Origin:** Recipe Knowledge decomp §12, Tasks G.2 & G.3.
- **Status:** OPEN

### `CmdScribe` rolls Craft but grants no skill improvement

- **What:** Decide whether binding a book should train Craft, then make the code
  and the docs agree. `commands/crafting_commands.py:663` calls
  `skill_check(skill_value)` to set the book's start-condition, but never calls
  `attempt_skill_improvement`. Five of the six production roll-sites do
  (craft, repair, hunt-attack, hunt-harvest, disassemble); scribe is the one that
  does not.
- **Why deferred:** It is not obviously a bug. Stage 3 G may have decided that
  binding is not craft *practice* — the roll measures the author's existing skill
  rather than exercising it — which is a coherent position. It may equally be an
  oversight: Component E remembered to wire disassemble and G did not.
- **Why it matters, stated plainly:** the asymmetry is undocumented in both
  directions. `PolishedWorld_Skill_Improvement_Decomposition.md` describes
  improvement-on-use as riding on the check surface, so a reader reasonably infers
  every roll trains; the code quietly disagrees at one site. Whichever way it is
  settled, one of the two has to say so out loud — a per-skill cooldown already
  prevents the "scribe-spam to grind Craft" failure mode, so the balance argument
  does not decide it either.
- **ANSWERED 2026-08-05 — it trains.** Settled by Stage 4.5's sub-decision
  close-out (Skill Progression decomp Rev 4, §2). Neither of the two readings in
  *Why deferred* above turned out to be decisive; what decided it is that the
  resulting rule has to be inferable by a player, and "some Craft rolls teach and
  some do not, and you are not told which" is not. P-5 makes generosity the safe
  side to err on, and the per-skill cooldown plus Component E's future difficulty
  gate are the anti-grind controls — not a per-command exclusion list, which
  grows and gets forgotten.
- **Trigger:** Task C.1, which folds scribe in as the sixth call-site
  (`imp = caller.attempt_skill_improvement("craft", outcome)` + the standard
  `_improvement_feedback` routing). P-6 already reads six.
- **Origin:** Found while verifying the `skill_check` call-site count for roadmap
  Rev 13 / System Map Rev 2 (2026-08-03). Answered 2026-08-05.
- **Status:** SCHEDULED — not DONE until C.1 ships it.

### ⛔ The recipe catalogue does not span the skill scale
- **What:** `world/recipes.py` holds **eight** recipes, of which exactly **one**
  sets `min_skill` (`LeatherBootsRecipe`, 30); the rest default to 0. There is no
  ladder of increasingly demanding work for a crafter to climb.
- **Why deferred:** It is content, not engineering — and it was invisible until
  something needed to read difficulty. Stage 4.5's **Component E** does: its
  trivial-work gate stops a recipe teaching once your skill exceeds its
  `min_skill` by more than the band. With the highest `min_skill` at 30 and a
  30-point band, **nothing in the game teaches Craft above 61**, and a crafter
  who gets there can never improve again. A smaller band only moves the wall
  (50 → wall at 81); a dead end is strictly worse than the grind the gate
  removes, so E is BLOCKED on this rather than scheduled behind it.
- **Trigger:** `min_skill` values form a ladder with no gap wider than
  `SKILL_TRIVIAL_BAND` from 0 to the intended ceiling — in practice recipes at
  roughly 0 / 20 / 40 / 60 / 80, not eight clustered at the bottom. Belongs to
  whichever stage grows the crafting catalogue. Assigning the values once the
  catalogue exists is Task E.1 and is inside OpenCode's permitted scope
  (`world/recipes.py`); assigning them *now* would be guessing.
- **Annotation (2026-08-12):** the decomposition work is **already done and was
  not visible from here.** `docs/crafting/` holds a complete *Arms of Legend*
  dependency decomposition — every item tree, with shared material nodes and
  per-node status. It carries **no difficulty axis**: `min_skill` appears zero
  times in it. So the remaining work is not authoring a catalogue but laddering
  `min_skill` across the subset that is buildable today — **152** nodes are
  `[BLOCKED]` on unbuilt systems against **110** `[DATA]`, and the 14 systems
  those blocks resolve to are enumerated in build order in
  `docs/crafting/PolishedWorld_System_Backlog.md`. **One question to settle
  first, by judgement and not by grep:** whether the `[DATA]` subset spans enough
  of the scale to ladder at all. If it tops out below the intended ceiling, the
  gate reproduces this exact dead end one rung higher — a wall at 80 instead of
  61 is still a wall.
- **Annotation (2026-10-17, alpha decision — roadmap Rev 25):** the figures
  above are **tag occurrences, not items**. At item level (bold headers with a
  status tag, categories A–I) the decomposition holds **44 `[DATA]`** finished
  items against **43 `[BLOCKED]`** — 17 adventuring gear, 1 riding & animal,
  11 clothing, 4 armour, 8 wooden weapons/ammunition, 3 basic transport (one
  tagged `[DATA for basic]`), and **none** in *Tools & Utility* —
  and the two sets have the same tree-depth distribution (depths 1/2/3: 4/34/6
  vs 6/35/2). What is blocked is blocked on systems (33 of 43 name smithing),
  not on complexity, and neither this decomposition nor *Arms of Legend* carries
  a per-item difficulty. So the "spans the scale" question has no answer in
  the content: `min_skill` is assigned, not read, and the two-jobs hazard in
  Skill Progression decomp Rev 5 is what E.2 resolves. Of the 44, **10** stand
  on `[EXISTS]` alone, **22** need a `[NEW MATERIAL]` gathering node and **10**
  cite leather (`[DECISION #2]`), five with no cloth alternative.
  **Decided (roadmap Rev 25, B):** E.1 runs after
  `docs/crafting/PolishedWorld_System_Backlog.md` FAS 1 (Systems 1–3) and
  System 4 (tanning) are delivered — the subset is laddered as data, not as a
  promise — and smithing (FAS 3) is outside the alpha. The Trigger below is
  unchanged.
- **Annotation (2026-10-17, track order — roadmap Rev 27 (D2)):** the ordering
  above stands, with a narrower FAS 1 and a System 4 that needs no work. FAS 1 for
  the alpha is the sink-bearing cut — wood, flint, clay (stone exists). Of the 22
  items that cite a `[NEW MATERIAL]`, only **9** need one the cut provides and
  **13** need materials FAS 1 does not provide at all. The 10 that cite leather
  were never gated: tanning shipped on 2026-06-30 (`896ce33`) and is ratified as
  shipped. **The catalogue is not yet recipes** — `world/recipes.py` holds eight,
  two of them among the 44 — so E.1 runs after the FAS 1 cut *and* the catalogue
  batches; both are components of *Alpha content epic* directly below. The
  Trigger is unchanged.
- **⚠️ Re-homed (2026-08-24, Stage 4.5 close-out):** Component E has **left the
  epic**. Stage 4.5 closed with A–D delivered, and E was moved out rather than
  holding the stage open — a stage blocked on a content trigger that belongs to
  no scheduled stage blocks the *next* stage (Combat) without anyone having
  decided to. **This entry is now E's only armed home.** The design still lives
  in Skill Progression decomp §7, which is marked as moved-out and will stop
  being read once that decomp is closed; if the trigger below is ever met, start
  here. E's own tasks (E.1 `min_skill` laddering, E.2 the trivial-work gate) are
  specified there in full.
- **Annotation (2026-10-18, alpha content decomposition):** E.1 is task **AC5.1** of
  `docs/PolishedWorld_Alpha_Content_Decomposition.md`, after three catalogue batches over the **24**
  reachable items listed in its §4. The list carries a use-in-alpha column:
  six are garments that wear, three are containers that matter once *Weight and
  encumbrance* ships, thirteen are goods nothing in the alpha uses — ladder
  rungs, or not, is decided before the first batch (its Q1). E.2 and the
  two-jobs hazard stay here.
- **Origin:** Skill Progression decomp Rev 4 §7, measured 2026-08-05 while
  decomposing Component E; re-homed at Rev 8 close-out.
- **Status:** BLOCKED

### Alpha content epic — decompose before code (FAS 1 cut → seeding → catalogue → E.1)
- **What:** The work between the alpha decision and E.1, costed in roadmap Rev 27
  (alpha entry, (D)) and too large to start from a list. Five components in one
  decomposition. **(1) The FAS 1 cut** — `wood`, `flint` and `clay` materials and
  their nodes in the existing `ResourceNode` shape (`stone` exists since
  `3caaefc`). Two choices are made in the decomposition: the felling model —
  deadfall with no tool, like `stick_deadfall`, or a stone/flint axe and a tool
  check that `CmdForage` does not have today, which is typeclass and command code
  and outside OpenCode's scope — and DECISION #10, confirmed or split, since its
  own revisit condition (bows needing ash or yew) is inside the alpha. `sinew` as
  a harvest part, for the bow. **(2) Registry corrections**, in the same commit as
  the materials they touch: `stone` DATA → EXISTS (prototype live since
  `3caaefc`), `stick` registered, `leather` DECISION → EXISTS and `raw_hide` given
  its sink (`LeatherRecipe`, `896ce33`), with
  `docs/PolishedWorld_SourceSink_Ledger.md` regenerated from `render_ledger()` and
  the AoL decomposition's `[DECISION #2]` tags swept in the same pass. The registry
  is what every generator reads, and its drift is how the tanning claim survived
  four months. **(3) Seeding** — *Public test server* part (a), as the only
  versioned path for placing nodes (roadmap, Stage 6 entry's interim placement
  rule). **(4) Catalogue batches** — the roughly 29 reachable `[DATA]` items (the
  22 that cite no new material, less the two that exist, plus the 9 the FAS 1 cut
  reaches) as OpenCode batches against
  `docs/crafting/deer_batch_gold_standard.md`. **(5) E.1** — `min_skill`
  laddering, as specified in Skill Progression decomp §7.
- **Why deferred:** Methodology — a feature this size gets Feature → Components →
  Tasks before code, and the decomposition is where (1)'s two choices are made.
- **Trigger:** The next PolishedWorld session — the alpha track is coded first
  (roadmap Rev 27 (D1)). *Death contract surfaces* does not wait on it.
- **Annotation (2026-10-18, decomposed — `docs/PolishedWorld_Alpha_Content_Decomposition.md` Rev 1):** five components and a
  close-out, AC1–AC6, 12 tasks, 7.5–10 sessions. The two choices are made:
  **felling** is a stone axe and a hard tool check in `forage`, with wear (AD1) —
  the only option that gives `flint` a consumer, since Flint and Tinder needs a
  steel striker that is `[BLOCKED: smithing]`; **DECISION #10** is generic `wood`
  for the alpha, its revisit re-anchored to Stage 5 (AD2) — the condition is
  *mechanical* need, and a bow has no mechanic before combat, so it cannot fire
  inside the alpha as this entry says. **Corrections to the text above:** the
  reachable catalogue is **24** items, listed by name in the decomposition's §4,
  not about 29 — five trees do not resolve as written; `sinew` is **not** needed
  for the bow, whose fiber string is its own `[DATA]` branch (AD4), so
  `world/harvest_templates.py` is untouched; and the registry corrections are
  wider than (2) lists — a loop over the whole registry finds `bone` and
  `needle` live but DATA, and `feather` and `tusk` EXISTS with no prototype or
  source since `0e0d224` (AD3). (2)'s *same commit* holds for the registry,
  which is code on the branch; the ledger and the AoL sweep are docs and move
  to the close-out on `main` (AD6). Every item prototype carries Legend `enc`
  from AC2.2 on, read by nothing until *Weight and encumbrance* (AD8).
- **Annotation (2026-10-18, AC1.1 shipped — decomposition Rev 2):** task AC1.1 is on
  `main` as `cb60434`. The registry matches shipped content — `stone`, `bone`,
  `leather` and the `needle` tool EXISTS, `stick` registered, `feather` and `tusk`
  back to DATA, `raw_hide` sourced from the rabbit and sunk into `LeatherRecipe`,
  DECISIONs #2 and #5 resolved — and `tests/test_material_registry.py` keeps it
  there (eight tests; suite 519 OK). (2)'s *same commit as the materials they
  touch* did not hold for this first task: it shipped alone, and on `main` rather
  than the branch, so `docs/PolishedWorld_SourceSink_Ledger.md` on `main` lags the
  registry on `main` until the close-out (decomposition AD6, Rev 2 note). Four
  findings from the task are homed in the decomposition (§3 finding 6, Q7–Q8).
- **Origin:** FAS 1 costing session (2026-10-17).
- **Status:** SCHEDULED (`docs/PolishedWorld_Alpha_Content_Decomposition.md` Rev 2; AC1.1 shipped `cb60434`)

### Tanning upgrade — bark and water as `LeatherRecipe` inputs
- **What:** `LeatherRecipe` tans `raw_hide`×2 with an optional knife. The System
  Backlog §4 sketch and the AoL decomposition's leather tree add `oak_bark`
  (tannin) and water. Two questions to settle when it is picked up: where bark
  comes from — the registry's source is *oak tree + knife*, but `oak_wood` is a
  forbidden variant of the generic `wood` (DECISION #10), so bark is either its
  own node yield or `wood` + knife — and DECISION #6 (water as a consumed
  material or a nearby-source requirement), which sets the pattern for every
  water-using recipe after it.
- **Why deferred:** The alpha ratifies tanning as shipped (roadmap Rev 27 (D2)):
  the leather branch needs no new input to be laddered, and adding bark now would
  put a second consumer on `wood` before the felling model is decided. Changing
  what a recipe consumes before launch de-levels no one.
- **Trigger:** DECISION #6 being taken for any recipe, or the alpha close-out
  balance pass, whichever comes first.
- **Origin:** FAS 1 costing session (2026-10-17) — the System Backlog §4 sketch.
- **Status:** OPEN

### `SkillXPHandler.add()` does not raise on an unknown skill key
- **What:** `world/skill_xp.py::SkillXPHandler.add()` accepts any `skill_key`,
  including one the character has no trait for, and stores XP under it. D7's
  convention would raise, since a key nobody has is a caller bug and not a
  condition a player can be in.
- **Why deferred:** The codebase already decided this case, in the opposite
  direction, deliberately. `Character.improve_skill_on_use` returns None for an
  unknown skill "rather than raising, so a shared call site that passes a key
  this character lacks stays safe" — and after C.1 it is the *only* caller that
  reaches `add()`. A second guard here could only fire for a caller that had
  already bypassed the first one, and its sole observable effect would be to
  abort a live craft. Compensating control shipped instead: `all()` unions the
  stored keys with the character's real skills, so an orphaned entry is
  findable rather than silent.
- **Trigger:** Task C.1, which reviews all five improvement call-sites (P-6). If
  any of them can reach `add()` without passing through
  `improve_skill_on_use`'s existing guard, the argument above stops holding and
  the raise goes in.
- **Origin:** Skill Progression decomp §4, Delivered 2026-08-05, deviation 3.
- **Status:** SCHEDULED

### Scribe's band→condition bypasses `quality_band`
- **What:** `SCRIBE_CONDITION_BY_TIER` maps a `skill_check` result tier straight to a
  start-condition, where the house pattern routes tier → `QUALITY_BY_TIER` →
  `crafting_quality.quality_band()` → a band→condition table (E.3's
  `_apply_garment_quality` / `GARMENT_CONDITION_BY_BAND`).
- **Why deferred:** Deliberate, not an oversight. `scribe` is a standalone Command,
  not a `MongooseCraftRecipe`: it never computes a `quality` number and stamps no
  `db.quality`, so routing through `quality_band()` would mean synthesising a quality
  purely to classify it back into a condition. The four values are tuned directly
  against `DurableObject`'s colour bands instead. Cost of the divergence: if the
  quality bands are ever retuned, scribe will not follow, and books cannot gain a
  "superior" alias the way tools and waterskins do.
- **Trigger:** Retuning the quality bands, or wanting a `superior book of <recipes>`
  alias — either makes unification worth its indirection.
- **Origin:** Recipe Knowledge decomp §12, Task G.2 (locked band→condition choice).
- **Status:** OPEN

### Book repair ("rebind")
- **What:** Let a worn book be repaired/rebound rather than crumbling away, the way
  `CmdRepair` restores tools and garments.
- **Why deferred:** Excluded from Component G *on purpose*, to keep the sink clean.
  A book is the bulk knowledge-carrier; if it can be rebound indefinitely, one
  well-scribed book seeds a recipe to the whole server and the channel stops costing
  anything. Complete-then-crumble (G.3) makes the book a genuine consumable. Repair
  would also need its own material + skill story (rebinding ≠ patching leather).
- **Trigger:** Playtest showing books crumble faster than the economy can replace
  them, or a deliberate decision to soften the knowledge sink.
- **Origin:** Recipe Knowledge decomp §12, Task G.3 (and §15 anchor).
- **Status:** OPEN

### Teach-channel tuning (`TEACH_TIMEOUT` / `TEACH_COOLDOWN`)
- **What:** The two named constants in `commands/crafting_commands.py` pacing the live
  knowledge channel: `TEACH_TIMEOUT` (60s, how long a pending offer stays answerable)
  and `TEACH_COOLDOWN` (120s, between teaching *offers*).
- **Why deferred:** Conservative dev values, and deliberately ONE entry because the
  two are not independent. **Invariant: `TEACH_COOLDOWN >= TEACH_TIMEOUT`.** That
  relationship is what makes the MVP "one student at a time" rule structural rather
  than bookkeeping — an old offer has always lapsed before a teacher may send a new
  one, so there is never more than one live offer per teacher and no second copy of
  the state to keep in sync. Tuning either constant in isolation can silently break
  that guarantee. Teaching is otherwise entirely free (no material, no roll), so the
  cooldown is the whole economic and social throttle, and it is spent at OFFER time
  because the unsolicited message is the only thing `teach` can push at an unwilling
  player.
- **Trigger:** Playtest data on how fast recipes should spread person-to-person
  relative to the scroll and book channels, or offer-spam complaints.
- **Origin:** Recipe Knowledge decomp §13, Task H.1.
- **Status:** OPEN

### Teaching skill as an amplifier (never a gate)
- **What:** Use Legend's Teaching skill (INT+CHA) as a *bonus* on the knowledge
  channels — shorter `teach` cooldown, more simultaneous students, or lower book
  wear per study. Never as a permission gate.
- **Why deferred:** Locked at decomp §2 (d): the transmission gate is *know it +
  meet `min_skill`* only. Legend (p.72–73) treats Teaching as something that makes
  instruction better, not something that makes it possible — a competent smith with
  no Teaching skill can still show an apprentice how it is done. Adding it as a gate
  would also mean a second skill to raise before a player can participate in the
  knowledge economy at all, which cuts against the cold-start story professions and
  the world-loot seed exist to solve.
- **Trigger:** A chargen/skill pass that makes Teaching a real, raisable skill, plus
  a reason to differentiate teachers beyond "knows it well enough".
- **Note:** A "more simultaneous students" amplifier interacts directly with the
  *Teach-channel tuning* entry above — one live offer per teacher is currently
  guaranteed by `TEACH_COOLDOWN >= TEACH_TIMEOUT`, not by an explicit check, so
  multi-student teaching needs real per-teacher offer state rather than just a
  shortened cooldown.
- **Origin:** Recipe Knowledge decomp §2 (d) + §15 anchor; Legend p.72–73.
- **Status:** BLOCKED (on a real chargen/skill system — see *Professions & Chargen*)

### World-loot scroll seed (Stage 3 Component I — the knowledge safety valve)

- **What:** A small, deterministic supply of stamped recipe scrolls placed in the world,
  so an advanced recipe cannot become permanently unreachable when no online player holds
  the profession that grants it. Decomp §2 (c) named it the safety valve for the
  profession-grant bootstrap; §14 specified it as Task I.1. **Deferred in full at Stage 3
  close-out — Stage 3 shipped Components A–H, not A–I.**
- **Why deferred:** Three reasons, in order of weight.
  1. **The failure mode requires players, and there are none.** Profession-grant is the
     only bootstrap source (reverse-engineering needs a crafted item, and scroll/book/teach
     all need a sender who already knows the recipe), so a coverage gap is real — but it
     cannot occur with an empty server.
  2. **The valve is already operable manually.** An admin can place a correctly stamped
     scroll in one line
     (`@py ... spawn("scroll")[0] ... .stamp("linen shirt") ... .move_to(...)`, see
     Testing Reference §7). I.1 would add *automation and determinism*, not capability, so
     deferring costs almost nothing today.
  3. **There is no world to seed into.** `world/batch_cmds.ev` is untouched Evennia
     boilerplate — zero build commands. Choosing a seed location, cadence and respawn
     policy against a world that doesn't exist is guesswork that would need redoing.
- **Trigger:** ⚠️ **Before the first cohort of real players logs in** — *not* "when the
  world is large". The risk runs the other way: with few players the profession bundles
  are unlikely to be fully covered, so exposure is **highest** at low player counts and
  falls as the population grows. Treat this as a launch-blocker checklist item, not a
  someday-item.
- **Exposure at time of writing (recompute before implementing):** coverage is uneven
  across the four advanced recipes —

  | Recipe | Granted by | Exposure |
  |---|---|---|
  | `cloth` | weaver, generalist | 2 — robust |
  | `leather` | tanner, generalist | 2 — robust |
  | `linen shirt` | **weaver only** | **1 — exposed** |
  | `leather boots` | **cobbler only** | **1 — exposed** |

  So a seed needs to cover `linen shirt` and `leather boots`, not all four. `leather boots`
  is doubly exposed: single grantor, plus `min_skill = 30`, plus a dependency on
  tanner/generalist leather. ⚠️ **This table is an artefact of the current 4-recipe /
  4-profession vertical slice.** When the recipe catalogue grows the coverage maths changes
  completely — recompute against `world/professions.py` and `world/recipes.py` at
  implementation time rather than trusting this snapshot.
- **Design decisions to preserve (so the future build is short):**
  - Go through `Scroll.stamp(recipe_name)` — it owns identity and sets both `db.recipe` and
    a real stored `key` (barter matches on `obj.key`). Never hand-set `db.recipe`.
  - Only `requires_knowledge = True` recipes can be seeded; `learn` refuses common ones.
  - **Idempotency is required** — re-running the seed must not double the scrolls. Tag the
    seeded objects, or flag the room.
  - **Decide one-shot vs respawn explicitly.** A seeded scroll is *consumed* by `learn`, so
    without replenishment the valve fires exactly once, ever. That has to be a decision, not
    an accident.
  - No loot-table infrastructure — the goal is the valve, not a drop system.
- **Origin:** Recipe Knowledge decomp §14 (Task I.1) + §2 (c).
- **Status:** BLOCKED (on world content existing, and on a real player base)

### Crafting resolves instantly
- **What:** `craft` produces its output in the same tick it is typed. The crafting
  contrib has no timing support by construction — `CraftingRecipeBase.craft()` runs
  `pre_craft → do_craft → post_craft` synchronously — so duration belongs in the
  command, not the recipe. Settled shape: split `CmdCraftGated.func()` into
  start/complete and delay `super().func()` itself, so ingredient re-resolution,
  the three gates, the roll and the consume all land at completion in a single
  tick; stale-reference consumption (an ingredient bartered away mid-craft) then
  cannot happen. A new `craft_duration` on `MongooseCraftRecipe` replaces
  `craft_cooldown` as the time sink. `utils.delay` with `persistent=False`, not
  `yield` — `yield` needs session-backed context and is unreliable under
  `execute_cmd` / `.call()`, which is how the test protocol drives commands.
- **Why deferred:** Not a defect; instant crafting is playable. It is also the
  **third timed action**, so building it means extracting the shared helper the
  entry below asks for rather than writing a fourth `at_pre_move` branch — which
  makes it a pass, not a drop-in. Skill-scaled duration is deliberately excluded
  from v1: it interacts with the Stage 4.5 C/D practice-line balance. v1 abort is
  movement only, via the existing `at_pre_move` precedent set by `rest` / `work`.
- **Trigger:** After Stage 4.5 Component D. Pairs with *Timed player actions have
  a pattern but no shared home* — do both in one pass.
- **Origin:** Session 2026-08-11 (design settled against live source, no code written).
- **Status:** **DONE** (2026-10-17). Delivered by Epic A Component TA2 and merged to
  `main` in `34b2ee4`: `craft` waits its recipe's `craft_duration` on the shared
  timed-action slot and resolves at completion, no recipe defines `craft_cooldown`
  any more, and `recipes <name>` shows the wait. Decisions T14–T29 in
  `PolishedWorld_Timed_Actions_Decomposition.md`. Keep for traceability, prune at
  the next backlog sweep.

---

## Professions & Chargen

### Profession Common-Skill bonuses (Legend's other half)
- **What:** A Legend profession grants two things -- access to Advanced Skills
  (modelled today as recipe knowledge, Component D) *and* Common-Skill bonuses
  (e.g. Blacksmith: Brawn +15%, Hammer +10%). Only the knowledge half is built;
  the skill-bonus half is deferred.
- **Why deferred:** Stat territory, which Component D deliberately excludes
  ("knowledge only, no stat bonuses"). Also meaningless while every character
  has placeholder characteristics -- the bonuses need a real chargen (rolled or
  allocated characteristics) to sit on.
- **Trigger:** A real chargen with per-character characteristics.
- **Origin:** Stage 3 Component D -- Legend profession analysis (Legend.pdf
  Professions section, verified 2026-07-12).
- **Status:** BLOCKED (real chargen / characteristic variation)

### Cultural-Background gating of professions
- **What:** In Legend RAW the only gate on which profession a character may take
  is Cultural Background (e.g. Alchemist = Civilised only), NOT a characteristic
  minimum. Component D ships free choice (any character, any profession); a
  culture-based availability gate is the Legend-authentic future refinement.
- **Why deferred:** No Cultural Background / chargen system exists yet to gate
  against, and free choice is both Legend-faithful and the only meaningful option
  while characteristics are identical placeholders. Explicitly NOT a
  characteristic-minimum gate -- that would diverge from Legend RAW.
- **Trigger:** A Cultural Background / chargen system.
- **Origin:** Stage 3 Component D.2 -- Legend profession analysis (verified
  2026-07-12).
- **Status:** BLOCKED (Cultural Background / chargen system)

---

## Death & Corpses

### Per-item corpse decay
- **What:** Independent decay timers per loot item, so loot lingers after the
  corpse rots (leather before steel) instead of the current atomic delete.
- **Why deferred:** Current `PlayerCorpse` deletes all loot at expiry; the
  single expiry writer, `Corpse.crumble()` (Rev 44), makes per-item decay a
  clean later addition: it would land there, once.
- **Trigger:** None hard; a refinement on the closed H7 loop.
- **Origin:** Hunting / H7 decomposition backlog.
- **Status:** OPEN

### ⚠️ `CoinPile` vs the corpse's atomic content delete
- **What:** Decide what happens to coin left on an unlooted corpse that expires.
  `typeclasses/corpse.py::PlayerCorpse.return_appearance` deletes **every** item
  inside the body when it passes its recovery window (288 game hours), then
  deletes the body. Once `CoinPile` materialises in Stage 5 and drops on death,
  that path destroys currency.
- **Decision (2026-10-17, roadmap Rev 26 — death-consequence policy, (ii)):**
  **currency is never deleted by any cleanup path.** When an expired
  `PlayerCorpse` crumbles, a `CoinPile` inside it is **transferred to the
  Treasury with a ledger entry** (a transfer, so `@economy audit` sees it and
  the invariant balances) before the body and the rest of its contents are
  deleted. The same rule binds every other cleanup that would otherwise remove a
  `CoinPile` — wilderness room recycling in Stage 6 above all — and it is
  written as a rule rather than a corpse fix for exactly that reason. The
  transfer goes through `world/currency.py` like every other wallet write
  (S4-R2). The three candidates this entry carried are retired: *exempt the
  pile from the delete* and *move it to the room* both leave a `CoinPile` on a
  floor that Stage 6 may reset, which is the same unlogged burn in another
  file; *accept it as a sink* amends the principle that makes the economy
  auditable. Gear is **not** covered by the rule: it has a crafting source, so
  the atomic delete of everything else at expiry stands as the loot sink.
- **Why deferred:** The *decision* is made; the *object* is not built. Stage 4
  keeps the wallet on death (S4-3) and no coin objects exist, so nothing
  currency-shaped can be inside a corpse today.
- **Why it mattered, stated plainly:** this was a **doc-vs-code conflict**, not a
  refinement. `PolishedWorld_Economic_Philosophy.md` Rev 2 states that currency
  never weathers and that Gold has exactly **one** permanent exit (exchange back
  to GameGold). An expiring corpse would have been a second, unintended and
  **unlogged** exit — invisible to `@economy audit`, because a deleted
  `CoinPile` simply stops appearing in `get_by_attribute("wallet")`, leaving the
  invariant reporting a discrepancy it cannot explain. The decision keeps the
  principle and changes the code's future, not the document's (§5 Rev 4 records
  the rule).
- **Trigger:** **Stage 5 kickoff**, with `CoinPile` — unchanged. The Treasury
  sweep lands in the same task that makes the pile droppable, so the rule is
  never false on `main` for a single commit. *(Rev 43:)* it lands in `Corpse.crumble()`,
  the single expiry writer from the entry below, so the room hook and the
  sweeper NPC inherit it for free. *(Rev 44:)* re-read against `cea296d`:
  `crumble()` exists, and its contents loop is now the only content delete at
  expiry, so the transfer goes before that loop. The *What*'s address
  (`PlayerCorpse.return_appearance`) is historical. *(Rev 46:)* the same task
  owns two more prose sites, written true for Stage 4 on purpose:
  `help death`'s *"Coin in your purse stays with you."* (`world/death_contract.py`,
  `help_text()`) and the *"Today the wallet is an Attribute…"* sentence in
  `commands/currency_commands.py`'s module docstring. `crumble()`'s docstring
  already names the change its *lost with it* clause needs.
- **Origin:** Found in Stage 4 B.2 while reading corpse behaviour for the
  same-room payment rationale (2026-07-30). Decided in the death-consequence
  policy session (2026-10-17).
- **Status:** DECIDED (roadmap Rev 26) · code SCHEDULED (Stage 5, with `CoinPile`)

### ⚠️ Corpse expiry fires only on direct interaction — and its two writers disagree
- **What:** Expired corpses are removed only when a player interacts with the
  body itself, so a corpse nobody looks at lingers forever. Two call sites
  delete today, and they do **not** do the same thing:
  `PlayerCorpse.return_appearance` (on `look <corpse>`) deletes every item
  inside, then the body; `CmdHarvest` step 4 (`commands/hunting_commands.py`)
  calls `corpse.delete()` on *any* `Corpse`, `PlayerCorpse` included
  (`_find_corpse` matches `exact=False`). Evennia's `DefaultObject.delete()`
  runs `clear_contents()`, which **moves** contents to each object's `home`
  (or `DEFAULT_HOME`) instead of destroying them — so harvesting an expired
  player corpse teleports its loot out of the sink. Creature corpses have no
  `look`-path delete at all; only `harvest` removes them. Room `look` never
  calls any of these.
  **Fix (decided 2026-10-18, A1 + B3):** extract one method on `Corpse` —
  call it `crumble()` — that is the **single writer** (P-2) for expiry: it
  messages the room, deletes the contents, then the body. `return_appearance`,
  `CmdHarvest` and a new lazy hook, `Room.at_object_receive`, all call it and
  nothing else. The hook sweeps the room's expired corpses when anything enters
  it: no ticker, and every room a player visits is covered. The hook only acts
  on what `is_expired` already says is expired — it decides nothing new.
- **Why it matters, stated plainly:** gear left in an unvisited corpse is a
  leak, not a sink — the death contract (roadmap Rev 26) says unrecovered gear
  is destroyed with the body, and today that is only true for bodies someone
  happens to look at. The harvest path is worse than a leak: it relocates loot
  to each item's `home`, wherever that happens to be. And the `CoinPile` rule
  (entry above) binds *every* cleanup path; with three writers the Treasury sweep
  would have to land three times. One `crumble()` means it lands once.
- **Receipt (2026-10-18, local test DB):** 20 expired `PlayerCorpse`s in Limbo
  survived repeated room `look`s unchanged; `look corpse-1` crumbled one at a
  time (20 → 19 → 18). Harvest-path relocation is read from source
  (`evennia/objects/objects.py::clear_contents`) and **not yet observed
  in-game** — the implementation's protocol must show it before the fix.
- **Why deferred:** Found during a design discussion; it is code, and code goes
  on a feature branch.
- **Trigger:** The alpha track, on its own `feature/janitor` branch (no file
  overlap with `feature/alpha-content` as of `d70a115`); **must be on `main`
  before the first test cohort**, since it is part of the death contract
  holding. Best before `feature/death-contract`, which rewrites the crumble line
  — after extraction that line lives in one place.
- **Origin:** Cozy-NPC design discussion (2026-10-18).
- **Status:** **DONE** (2026-10-18). Merged to `main` in `cea296d`
  (`feature/janitor`: fix `c95eb85`, test `73249d6`). `Corpse.crumble()` deletes
  the contents, then the body, and prints one room line whose *lost with it*
  clause appears only when something was held; harvest's own two lines are
  retired. A pk guard makes a repeat call on a stale reference a no-op: Evennia's
  second `delete()` on the same instance raises `ObjectDoesNotExist`
  (`evennia/typeclasses/models.py`), so the guard is load-bearing, not tidy.
  **Two departures from the text above, recorded rather than smoothed over.**
  (1) The sweep fires on **puppeted arrivals only** (`moved_obj.has_account`),
  not when anything enters: `clear_contents()` teleports a deleted container's
  contents home with `move_type="teleport"`, so sweeping on item arrivals would
  re-enter a sweep from inside a `crumble()`. (2) The *Receipt* above
  overcounted: after the fix, walking into Limbo crumbled 14 of the 18 corpses
  left, and the other 4 measured 64–271 h against a 288 h window — never
  expired. The harvest relocation **was** observed in-game before the fix
  (*"janitorring arrives to Limbo from janitorcorpse"*) and is gone after it.
  `tests/test_corpse_expiry.py`: 14 tests, the first 13 red on `c49b19f`;
  mutation run 11 of 14 killed, the 3 survivors equivalent (test commit
  message). Keep for traceability, prune at the next backlog sweep.

### Death contract surfaces — owner-first loot grace, death message, `help death`
- **What:** The player-facing half of the death-consequence policy (roadmap Rev
  26), three changes that ship together. **(1)** `PlayerCorpse`'s `get_from`
  lock becomes owner-only for a grace window and `true()` after it — a
  time-conditioned lock on `death_time` and the corpse's `owner` attribute,
  which `at_character_death()` already stamps; the grace length is a module
  constant next to `_PLAYER_EXPIRY_HOURS`, a calibration knob, not a contract
  term. **(2)** The death line carries the contract: where the body lies, that
  it keeps the belongings for days, that Death's Chill passes — replacing the
  bare `|RYou have died.|n`. **(3)** A `help death` topic saying the same in
  full. **Prose sites the policy falsifies, counted before writing (Testing
  Reference §11c) — seven in four files, to be changed in the same commit:**
  `typeclasses/characters.py` — the death line (`msg("|RYou have died.|n")`)
  and the `at_character_death()` docstring (*NOT permadeath* becomes a decision
  citation, not an assertion); `typeclasses/corpse.py` — the crumble line
  (*"what it held is lost with it"* is false once coin is swept, not lost) and
  the `PlayerCorpse` docstrings (*"time to run back"*, *"gear not recovered in
  time is destroyed with the body"* — true of gear, must say so);
  `commands/currency_commands.py` — the module docstring (*"stays with the
  corpse to be looted"* gains the owner-first grace); `commands/crafting_commands.py`
  — T17's `interrupt_msg` is listed because it was the trigger for the question
  and **stays unchanged**: it is true of the craft.
- **Why deferred:** It is code, and this policy was delivered as a docs patch on
  `main` (Core Instructions, *Delivery contract*). The grace lock is also the
  first lock in the project with a time term in it, and it wants its own
  in-game protocol (two accounts, one death, a clock) rather than a line in an
  unrelated epic.
- **Trigger:** The next code session on the alpha track, on its own
  `feature/death-contract` branch; **must be on `main` before the first test
  cohort** — the policy is an alpha prerequisite, and a contract the cohort
  cannot read is not settled. Does not wait on Stage 5: none of the three touch
  the wound model. *(Rev 43:)* if *Corpse expiry fires only on direct
  interaction* lands first, the crumble line in the prose-site count lives in
  `Corpse.crumble()` — still one site, new address. *(Rev 44:)* it did land
  first (`cea296d`). Recounted against that tree: every quoted phrase is still
  present, and there is **one new site** — `crumble()`'s docstring describes the
  *lost with it* clause, which is now printed only when the corpse held
  something. **Eight sites in four files.**
- **Origin:** Death-consequence policy session (2026-10-17), point (v); the
  grace from point (iii).
- **Status:** **DONE** (2026-10-19). Merged to `main` in `123ac53` (PR #16,
  `feature/death-contract`: feat `dd5f69e`, fix `2d87533`, tree `18a3d83`).
  **(1)** `PlayerCorpse` locks with `get_from:corpse_grace()`. The lockfunc
  (`server/conf/lockfuncs.py`, the project's first) passes the owner at any
  time — the character id read from `db.owner` at check time, so the id lives in
  one place and a deleted owner simply never matches — and anyone once
  `_PLAYER_GRACE_HOURS = 72` **unscaled** game-hours have passed. The clock is
  the new `_raw_elapsed_game_hours()`, which `_elapsed_game_hours()` now builds
  on; the grace therefore never re-locks when the weather turns, which a test
  pins. Evennia's `LockHandler.check()` calls lockfuncs without a `try`, so the
  lockfunc catches, logs and **fails closed**; the owner test runs first and needs
  no clock. The bound *grace < fastest possible expiry* (288 / 3.0 = 96) is a
  test that derives 3.0 from the modifier tables. The refusal is the corpse's
  static `get_from_err_msg`, printed by the command — one writer; an
  `at_pre_get_from` hook was rejected because the command adds its own *"You
  can't get that."* after it, and because it runs only once the lock has already
  passed. `look` shows how long the claim has left. **(2)** and **(3)** are built
  in `world/death_contract.py` from the live constants and read by both
  `at_character_death()` and `world/help_entries.py` (`help death`, alias
  `dying`, category Survival); every span floors, because each one is a promise.
  **Prose sites: nine, not eight.** The comment at `characters.py` l.1102 (on
  `c940c8b`) quotes the death line, and is counted; it stays unchanged and true,
  because `You have died.` is still the first line the death sends. T17 stays
  unchanged as planned. `currency_commands.py`'s docstring had been false since
  Stage 4 (the wallet is an Attribute and stays with the character through
  death) and now says so. **Not migrated, by decision:** the dev DB's earlier
  corpses (73/78/79/102/103/104) keep `get_from:true()`. Lock strings are stored
  per object, no cohort exists, and the in-game protocol's last step lists them
  as the receipt. **What the in-game protocol found and the suite did not:**
  `DeathWeakness.at_apply` messages at once, so *"You claw back from the edge of
  death"* arrived before *"You have died."*; the fix commit sends the death line
  first and tests the order. **`harvest`** reads a `PlayerCorpse` but moves
  nothing out of it, so it is no route around the grace; what it does do is filed
  below as its own entry. Receipts: 28 new tests (`tests/test_death_contract.py`);
  16 mutants, 16 killed (one first "killed" by an `IndentationError` and rerun —
  Testing Reference §11b); an in-game protocol with a non-superuser looter
  (§11j), a `reload` in the middle of the grace and the same corpse observed
  opening; the full suite on the branch tip, 578 tests, the two expected treasury
  failures checked by name.

### ⚠️ `harvest` treats a player's body as a rabbit
- **What:** `CmdHarvest._find_corpse` (`commands/hunting_commands.py`) accepts
  any `Corpse` subclass (`is_typeclass("typeclasses.corpse.Corpse",
  exact=False)`), and `PlayerCorpse` inherits `creature_type = "rabbit"`. So
  `harvest corpse of <player>` reads the rabbit template: it lists the rabbit's
  parts and, on a successful skill check, spawns them. The `PlayerCorpse` class
  docstring's *"harmless: no player-corpse code path reads them"* is false. It
  moves nothing out of the body's contents, which is why *Death contract
  surfaces* left it out of scope (its decision 7).
- **Verified:** by reading `main` at `c940c8b`, **not by running it**. The first
  step of whichever session takes this is the in-game receipt:
  `harvest corpse of TestChar` in the dev DB.
- **Options (undecided):** (A) `_find_corpse` skips corpses with
  `is_player_corpse`, with a refusal line of its own; (B) `PlayerCorpse` clears
  `creature_type`, so the template lookups find nothing (both the named-part
  path and the parts listing need checking against `None`);
  (C) a remains template of its own — a design question (what may be done to a
  player's body, and whether it is a sink), not a bug fix. The false docstring
  is corrected in the same commit, whichever option is chosen.
- **Why deferred:** A different question from the loot contract, and it touches
  the hunting commands.
- **Trigger:** Before the first test cohort. In an alpha without combat, a
  starved player's body is the corpse players will meet most often.
- **Origin:** Anchor check for *Death contract surfaces* (2026-10-19), decision 7.
- **Status:** **DONE** (2026-10-20). Merged to `main` in `1c57f0a` (PR #17,
  `feature/harvest-guard`: fix `08d6c44`, tree `cfb6075`). A variant of (A),
  put where (A) as filed could not go. `CmdHarvest` step **4b** refuses on
  `corpse.db.is_player_corpse` **after** step 4, so an expired player body still
  crumbles on `harvest` (one of `crumble()`'s three triggers, which a skip in
  `_find_corpse` would have removed, breaking `TestHarvestDestroysPlayerLoot`),
  and **before** both template lookups. The refusal is a free bailout (no roll,
  no cooldown) and names the loot path: *"That is no quarry, but what remains of
  someone. To take something back: get <item> from <corpse>."*
  `is_player_corpse` gets its first reader. (B) was rejected on the receipt:
  every player corpse in the dev DB had `creature_type = "rabbit"` **stored**
  (autocreate), so a changed default would have fixed none of them. They are
  left unmigrated, because the guard does not read the value; the in-game
  protocol refused with the data still present. **Prose:** three sites, all in
  the fix commit: the `PlayerCorpse` docstring's false sentence, the
  `is_player_corpse` comment (it named "search/loot rules" readers that did not
  exist), and `CmdHarvest`'s help text. The step is numbered 4b, not 5, because
  "`CmdHarvest` step 4" is cited elsewhere. **Receipts:** the bug reproduced as
  TestChar before any code (the rabbit's parts listed on a player corpse, and a
  named part reached `get_part`). After the fix, as TestChar: two player
  corpses refused, a named part with `bone` available refused without a roll,
  an expired player corpse crumbled, and a fresh creature corpse still listed
  its parts. `tests/test_harvest_guard.py`: 5 tests in 3 classes; 3 of 3 mutants
  killed by the intended classes (guard above step 4, guard keyed on the
  `Corpse` typeclass, refusal without `return`). Full suite: 583 tests, the two
  known treasury failures by name. (C), a remains template, was not taken up:
  it is a design question and is not filed.

### ⚠️ Decay time can run backwards when the weather turns
- **What:** `Corpse._elapsed_game_hours()` multiplies the **whole** raw span
  since death by the decay modifier as it is **now**. A change of weather or
  season therefore rescales the body's entire history: 100 raw hours read as 300
  in summer rain (×3.0) and as 200 once the rain stops. `decay_stage` can step
  backwards (*skeletal* → *rotting*), and `is_expired` can go True → False for a
  body nobody has touched since. Verified by arithmetic against
  `typeclasses/corpse.py`, not observed in-game.
- **Not affected:** the owner-first loot grace. It reads the unscaled
  `_raw_elapsed_game_hours()` (merge `123ac53`), and a test holds it monotone.
- **Impact today:** latent. Expiry acts only through `crumble()`, which deletes on
  the first trigger that sees True, so an un-expiry only postpones a crumble. The
  visible symptom is a body that looks fresher after the rain stops.
- **Options (undecided):** (A) integrate — accumulate effective hours whenever
  the modifier changes, which needs a hook on weather and season changes and
  state per corpse (or one global log of modifier history); (B) ratchet — store
  the largest effective age seen and never report less, monotone but dependent
  on who looked when; (C) accept it and document it.
- **Trigger:** The next session that touches corpse decay, or a player report of
  a body that "un-rots".
- **Origin:** A theory carried into the 2026-10-19 handoff; confirmed by
  arithmetic in the *Death contract surfaces* anchor check.
- **Sighting (2026-10-20, `feature/harvest-guard` protocol):** player corpse 73
  in the dev DB read `is_expired` **True** at 19:16 on 2026-10-19 and **False**
  at 05:57 the next morning, with weather changes logged in between. No protocol
  step wrote to it, and it was not crumbled, so no trigger saw it while it was
  True. This fits the entry, but `death_time` and the modifier were not printed
  at either moment, so it is a sighting, not a receipt. The session that takes
  this entry starts by printing both for a corpse across one weather change.
- **Status:** OPEN (latent)

### `at_character_death()` restore block vs persistent wound tiers
- **What:** When Stage 5 ships locational Hit Points and the three wound tiers
  (roadmap Rev 20), the restore block in `at_character_death()` — today
  `health.current = health.max` plus hunger/thirst reset — must restore location
  HP (which clears the *disabled* tier, temporary by RAW) and **must not clear
  the *maimed* or *severed* tiers**. Wound state persists through respawn.
- **Why deferred:** There is no wound state to preserve until Stage 5 writes it.
  Filed now so the epic that adds locational HP reads this before it touches
  the restore block — the hazard is silent: a respawn that resets everything is
  the obvious edit, and it is the wrong one.
- **Why it matters, stated plainly:** Rev 20 made *maimed* curable only by another
  player's Healing/surgery, which is the service pillar 1 wants crafters to
  sell. If death cleared it, starving to death would be the cheapest surgeon in
  the world — a free NPC healer in a game that forbids NPC vendors. The
  death-consequence policy (roadmap Rev 26, (iv)) settles it: `DeathWeakness`
  stays a timed respawn debuff, wounds are state, and the two coexist.
- **Trigger:** Stage 5's wound-tier task — the same task that writes the tiers,
  so that no commit on `main` has persistent wounds and a respawn that erases
  them.
- **Origin:** Death-consequence policy session (2026-10-17), answering the
  hit-location entry's sub-question (a).
- **Status:** BLOCKED (Stage 5 wound tiers)

### `DeathWeakness` debuff → `fatigue_rate`
- **What:** Point the death-weakness debuff at `fatigue_rate` (its intended
  target) instead of the current `hunger_rate`/`thirst_rate` stand-in (+25%).
- **Why deferred:** Fatigue-exhaustion has no real consequence yet, so a
  fatigue-rate debuff would be toothless.
- **Trigger:** Fatigue-exhaustion consequence (below).
- **Origin:** Hunting / H7 decomposition backlog.
- **Status:** BLOCKED (fatigue-exhaustion consequence)

---

## Health & Injury

### Two-stage healing — field stabilisation vs. repair
- **What:** Split wound treatment into two distinct actions rather than one
  heal. **Stabilise** (First Aid): stops the `CON+POW` bleed-out clock on a
  Major Wound, buys the victim time, restores **no** location Hit Points, and
  can be performed under field conditions by a modestly skilled player.
  **Repair** (Healing / surgery): restores the location to positive HP and
  clears the *maimed* tier; requires a higher skill, a meaningful duration, and
  crafted consumables (bandage, splint, sutures, splint-boards). Roadmap Rev 20
  already names Healing/First Aid as a service another player sells; this is the
  mechanic that makes the two saleable separately, at different prices, to
  different specialists.
- **Why deferred:** There is nothing to treat until Stage 5 ships wound state —
  the tiers, the bleed-out clock and the location HP that repair writes back to
  are all Stage 5 deliverables, and a treatment system built against a wound
  model that does not exist yet is designed against a guess. Second, surgery is
  a timed, interruptible action by construction, so it belongs on Epic A's
  `world/timed_actions.py` slot rather than as its own hand-rolled branch —
  building it first inverts that dependency.
- **Trigger:** Both, in order — (1) Stage 5's wound tiers shipped and
  in-game-verified, (2) Epic A's shared timed-action module merged (**met** —
  `34b2ee4`, 2026-10-17). Design
  session, not a drop-in: consumable list, skill thresholds, whether stabilise
  is self-applicable, and what a *failed* surgery does are all open, and the
  last one is a player contract that touches **[OPEN] death-consequence policy**.
- **Origin:** 2026-09-09 organ-damage-model evaluation; the surviving half of the
  proposal rejected in `docs/roadmap.md` Rev 21 (`[RESOLVED]` organ-level damage
  model). Original idea from another Evennia developer's RimWorld-derived system.
- **Status:** BLOCKED (Stage 5 wound tiers)

---

## Survival

### Fatigue-exhaustion consequence
- **What:** A real consequence for hitting fatigue exhaustion (unconsciousness,
  skill penalties, etc.), so fatigue matters like hunger/thirst do.
- **Why deferred:** Not yet needed for the core loop; unblocks `DeathWeakness`.
- **Trigger:** None hard; also the prerequisite for the death-weakness re-point.
- **Annotation (2026-10-18) — direction chosen (B), Legend-faithful:** the
  gauge is read in bands matching Legend's Fatigue levels (core pp. 89–90) —
  Winded, Tired, Wearied, Exhausted, Debilitated — each a penalty on skill checks
  through the resolver, −10 % to −50 %. At the bottom, an Athletics test each
  survival tick (Legend's skill for activity Fatigue tests; the project has no
  Persistence), and a failure collapses the character into a short **forced
  rest**. Legend's own end state is a failed Persistence test and
  unconsciousness; this is that, with a rest the player recovers from. The ramp
  comes first so a player feels the edge coming; the forced rest is the last
  step, not the first consequence. *Rejected:* **A**, a hard forced rest at zero
  — a cliff with no warning; **C**, refusing physical actions at zero — it never
  forces the rest. *Why it matters now:* *Weight and encumbrance* (*Containers*)
  intends overload to drain fatigue faster, which does nothing until this
  ships; that entry's decomposition decides whether this one is inside it, a
  dependency of it, or follows. **Open, for this entry's own decomposition:**
  the forced rest's length — Legend's 1D3×2 hours is 30–90 real minutes at
  `TIME_FACTOR = 4`, far too long; whether eating and drinking are allowed
  during it, since the ticker keeps draining hunger and thirst; the band
  thresholds, and whether the tick test grows harder with depth (Legend's
  *Debilitated* test is Difficult); that the forced rest **refuses** movement,
  unlike every timed action today (`at_pre_move` interrupts and allows the move,
  Epic A D1); and Stage 5 — a collapsed character is defenceless, which is
  designed with combat, not here. Once this ships, the `DeathWeakness` re-point
  in *Why deferred* is unblocked.
- **Origin:** Survival mechanics (core loop).
- **Status:** OPEN

---

## Containers

### Weight and encumbrance (Legend ENC) — decompose before code
- **What:** Legend's encumbrance rule (core p. 86): every item has an ENC score,
  and about 20 items too light to score count as 1 ENC when carried in a sack or
  backpack; a character carries up to STR+SIZ without penalty and is
  *Overloaded* above it — −20 % to physical tests, Movement halved, −20 % to
  Fatigue tests; a mount carries its own ENC and never more than double it. Plus
  storage containers — `CmdPut` and a container whose capacity is ENC, not item
  count — so *Full container support* below is folded into this entry. The data
  is not this entry's: from the alpha content epic on, every item prototype
  carries `enc` (`docs/PolishedWorld_Alpha_Content_Decomposition.md` AD8), and a test keeps it complete.
- **Why deferred:** The rule does not translate directly, and the translation is
  design work: a room-based world has no Movement rate to halve (a move cooldown?
  fatigue per room?); the project's fatigue is a survival counter, not Legend's
  Fatigue test (see *Fatigue-exhaustion consequence*); coin lives in a wallet
  attribute, not in objects; STR and SIZ are `static`, base 10, on every
  character until character creation; and `ContainerCmdSet` cannot be installed
  whole — it replaces the seasonal `look` — while `ContribContainer.capacity`
  counts items, with `at_pre_put_in` as the documented override point (Evennia
  `v6.1.0`, `evennia/contrib/game_systems/containers/containers.py`).
- **Why it is an alpha prerequisite (roadmap Rev 28, alpha entry (E)):** pillar 1
  measures emergent prices, and without weight distance costs nothing — one
  character carries any quantity anywhere, haulage is no service, and a price
  cannot differ between where a thing is gathered and where it is used. Weight
  gives the economy a geography, and the alpha's three craftable containers a use.
- **Trigger:** A decomposition session of its own, any time after the alpha
  content decomposition; **must be on `main` before *Persistent alpha instance*
  opens** — objects spawned there before a reader exists would need migrating,
  while every database before it is wiped by the seed.
- **Direction (2026-10-18), and how Legend maps it:** overload should drain
  fatigue faster, so a loaded character must rest more often, and it should cost
  in combat. Legend reaches the same place through tests rather than a rate:
  *Overloaded* is −20 % to Fatigue tests (core p. 86), each failed Fatigue test
  drops one level, and the levels carry −10 % to −50 % on all tests, Strike Rank
  and Combat Action penalties, and unconsciousness tests from *Exhausted*
  (pp. 89–90). In the project's gauge model a harder test becomes a faster rate:
  an `Overloaded` buff with a `fatigue_rate` mult mod, recomputed each tick as
  `ColdStress` and `HeatStress` already are (`world/survival_buffs.py`). Combat
  takes Legend's direct −20 % on weapon tests in Stage 5, through the skill-check
  modifier. The weight mechanic exposes **one** overloaded state that both the
  survival ticker and the resolver read (P-2), so combat never sums weight
  itself. Armour's Strike Rank penalty is a separate Legend rule (AP ÷ 5), not
  ENC.
- **Open question for the decomposition:** fatigue at zero has no consequence
  today — `world/survival_ticker.py` defers it to the skill-check resolver, and
  *Fatigue-exhaustion consequence* (*Survival*) is OPEN — so a faster drain
  changes nothing on its own. The decomposition decides whether that
  consequence is inside it, a dependency of it (which would make it an alpha
  prerequisite in practice), or whether the direct −20 % on physical tests
  carries the alpha alone.
- **Origin:** Alpha content decomposition session (2026-10-18), AD8.
- **Status:** OPEN (alpha prerequisite — decompose before code)

### Full container support
- **What:** Generic `CmdPut` + a reusable `ContribContainer` typeclass (bags,
  chests). Possibly a `CmdContainerLook` (likely skipped — contents shown via
  `return_appearance`).
- **Why deferred:** H7.3b added only `CmdContainerGet` for corpse looting, and
  deliberately excluded `ContainerCmdSet` to avoid a `look` collision with
  `ExtendedRoomCmdSet`. Full support needs bags/chests to exist first.
- **Trigger:** Bags/chests as craftable items.
- **Annotation (2026-10-18):** folded into *Weight and encumbrance* above, which owns
  `CmdPut` and a container with ENC capacity. This entry's trigger is met inside
  the alpha content epic — backpack, sack and saddlebag become craftable in batch
  AC4.2 — so it moves with that entry rather than firing on its own.
- **Origin:** Hunting / H7.3b decomposition backlog.
- **Status:** SCHEDULED (with *Weight and encumbrance*)

---

## Environment & Weather

### Weather inertia, and Legend's four independent axes

- **What:** Two changes to `world/weather.py`, in either order. **(1) Inertia:**
  `roll_weather(season, current=None)` already takes the current state and
  ignores it — the parameter is a stated extension point. Replace the uniform
  draw over `SEASON_ALLOWED_WEATHER` with a per-season Markov table, so rain
  follows cloud rather than sunshine. No new state, no migration, no schema.
  **(2) Legend's own tables:** the rulebook treats weather as four *independent*
  axes — wind strength, cloud cover, temperature, precipitation — with seasonal
  modifiers on cloud cover and a wind table that yields concrete Perception
  penalties. Splitting today's four-value enum into a small struct is RAW-faithful
  and is what makes weather *mechanical* rather than decorative.
- **Why deferred:** Neither is blocked; both were raised as future work in a
  discussion explicitly framed as backlog material, and neither competes well
  with the alpha-milestone session or Stage 5. (2) is also the larger of the two
  — an enum → struct change touches every reader of `room_state`, so it wants a
  moment when the weather readers are already open, not a standalone pass.
- **Why it matters:** weather without consequence is scenery. Today seasons gate
  weather and weather gates descs, and nothing else reads either. The Perception
  penalties in (2) are the cheapest available bridge from flavour to mechanic,
  and they arrive already balanced by someone else.
- **Trigger:** (1) any light week — it is a self-contained function body.
  (2) whenever a system first needs to *read* weather mechanically (Stage 5
  visibility, foraging yield, or the exposure gauge in `roadmap.md`), so the
  struct is designed against a real consumer rather than a guessed one.
- **Origin:** Session 2026-09-04 (weather/season expansion discussion).
- **Status:** OPEN

---

### Season-dependent day length

- **What:** Make the seven time-of-day period boundaries a function of season, so
  winter days are genuinely short and summer days genuinely long, instead of the
  same seven fixed slices year-round.
- **Why deferred:** Not blocked, just not urgent. It is a contained change
  precisely because `gametime_utils.get_time_of_day()` is already the single
  reader — nothing else derives period boundaries — so the cost does not grow
  while it waits.
- **Why it matters:** the 13-month calendar with its four-month summer is the
  most distinctive thing about the world model and currently has almost no
  mechanical surface. A winter day that is actually short sells that calendar
  harder than any room description does, and it feeds the exposure gauge and
  light/Perception coupling when those land.
- **Trigger:** Any light week; pairs naturally with weather inertia above (same
  file neighbourhood, same session).
- **Origin:** Session 2026-09-04 (weather/season expansion discussion).
- **Status:** OPEN

---

### ⛔ Regional weather (per-area rather than global)

- **What:** Weather that differs by place — rain over the valley while the ridge
  stays clear — instead of today's single global roll broadcast to every room
  with an `is_indoor` guard.
- **Why deferred — and why BLOCKED, not OPEN:** there is no region concept to
  hang it on. Rooms have no coordinates and no biome key, so "regional" would
  have to be invented here as an ad-hoc grouping, and every room built under that
  grouping becomes migration debt the moment the real one arrives. That is
  exactly the failure the *biome fragment library* entry (World & Rooms, Rev 26)
  is written to prevent, and the same one Stage 6's grid/wilderness split
  resolves. Building it early does not bring the payoff forward; it just moves
  the cost into a migration.
- **Also noted:** the broadcast architecture is a second, smaller concern.
  Today's global change walks tagged rooms; per-region weather multiplies that
  walk, and it wants designing against ten simultaneous players rather than
  discovered afterwards.
- **Trigger:** **After** the biome layer exists (*biome fragment library*) **and**
  Stage 6's coordinate model is decided — both, not either.
- **Origin:** Session 2026-09-04 (weather/season expansion discussion).
- **Status:** BLOCKED (biome layer + Stage 6 world architecture)

---

## World & Rooms

### Ambient sweeper NPC
- **What:** A cozy wandering NPC — an old sweeper with a broom — that walks
  between rooms on `TICKER_HANDLER` (pattern: `evennia.contrib.tutorials.
  tutorial_world.mob`, which patrols on a ticker) and "sweeps" by calling the
  same `crumble()` path as the room hook. **It never makes a deletion decision
  of its own**: it acts only on what `is_expired` already reports, so it
  cannot touch anything the death contract protects. Pure ambience; one ticker
  for one object at ~60 s is negligible load. Not a vendor and not an economic
  actor, so it does not conflict with pillar 1.
- **Rejected scope (2026-10-18):** a sweeper that removes *any* floor item
  (dropped loot, leftovers) would be a new, undesigned economic sink and would
  break the death contract's grace window and the `CoinPile` rule. Test-server
  clutter is not this entry's job — it belongs to *Public test server with
  nightly reset* (one item, one home); until then, `@destroy` with a dbref
  range (`#X-#Y`) clears a dev DB.
- **Why deferred:** It adds nothing until the single-writer `crumble()` exists.
- **Trigger:** *Corpse expiry fires only on direct interaction* merged to
  `main`. Create the NPC object in the DB only **after** its typeclass is on
  `main`: on a branch without it, Evennia falls back to a default typeclass and
  logs an error on every load. *(Rev 44:)* met — merged in `cea296d`.
- **Room-hook scope (Rev 44):** the merged sweep runs only for puppeted
  arrivals, so an NPC walking in triggers nothing; the sweeper must run the
  sweep itself. When the NPC is built, lift the loop out of
  `Room.at_object_receive` into a `Room` method and have both call it — one
  home for the loop, as `crumble()` is one home for the deletion — rather than
  copying the loop into the NPC.
- **Origin:** Cozy-NPC design discussion (2026-10-18), option B3.
- **Status:** **DONE** (2026-10-19). Merged to `main` in `1517235` (PR #15,
  `feature/sweeper`: refactor `726390e`, feat `0110922`, fix `66827a0`). The loop
  now lives in `Room.sweep_expired_corpses() -> int`, which returns how many
  corpses crumbled; the hook keeps its `has_account` gate and calls it, and the
  pre-existing `TestRoomSweep` passed unchanged as the refactor's receipt. The
  NPC is `typeclasses.npcs.Sweeper` (`DefaultObject`, no account, no cmdset):
  each tick he takes one quiet step (`move_to(..., quiet=True)`) to a room tagged
  `sweeper_beat` (category `npc_route`) through an exit he may traverse, stays
  put if there is none, and then calls the sweep where he stands. He adds no
  line of his own — `crumble()`'s room line is the only one, and an empty sweep
  says nothing. **One departure from the text above, recorded rather than
  smoothed over:** the timer is a persistent `SweeperScript` (interval 60 s),
  **not `TICKER_HANDLER`**. The ticker version passed every unit test and
  vanished on the first `reload` in-game — see *⚠️ `at_server_start` ticker
  re-adds wipe every other persistent ticker* (*Tooling & Process*). The Script
  is created once in `at_object_creation` behind a key guard (`scripts.add()`
  never deduplicates) and is deleted with the object by `DefaultObject.delete()`.
  In-game receipts (2026-10-19): the Script survived two reloads with the same
  id and kept moving him afterwards; an expired corpse placed in the room he was
  stepping into crumbled with exactly one line; deleting him removed the object
  and the Script, and nothing remained after a further reload. The NPC object is
  not left in the dev DB: create one on `main` with
  `create_object("typeclasses.npcs.Sweeper", key=..., location=...)` and tag the
  rooms of his beat.

### Builder QoL for dynamic rooms (preview · `roommsg` · authoring convention)
- **What:** Three small ergonomic fixes to the Extended Room builder surface.
  (1) **State preview** — `@rdesc/preview winter night snowing` renders the room
  under an arbitrary state combination by overriding `room_states` for a single
  render, so a builder sees the winter-night-snow version without touching game
  time or pinning states via `roomstate`; a companion `/coverage` view lists
  which desc slots the room actually fills and where each unfilled combination
  falls back in the 7-level priority chain — today the builder has to *deduce*
  that "night+winter → falls to desc_winter", the view should just say it.
  (2) **`roommsg` command** — `roommsg add <text>` / `roommsg rate <seconds>` /
  `roommsg list|del`, replacing the current three-line `@py` setup for
  atmospheric echoes (`db.room_messages` + `room_message_rate` +
  `start_repeat_broadcast_messages()`), which is builder-hostile.
  (3) **One written convention** — the canonical authoring model is *one base
  desc + short overlay fragments*; full `@desc/<time>/<season>` matrix variants
  are reserved for landmark rooms. Docs change only. Full variants and `$state`
  fragments are two knobs expressing the same overlay, and the convention picks
  one so the mental model halves without removing capability.
- **Why deferred:** None is a defect — rooms are fully authorable today, just
  expensively. And Stage 4.5 is mid-flight; no new feature work until it closes.
- **Trigger:** Before the next deliberate building pass. (1) and (2) are
  standard 30–90-minute tasks; (3) is documentation.
- **Origin:** Session 2026-08-13 (builder-ergonomics discussion; no code).
- **Status:** OPEN

---

### Biome fragment library for dynamic room descriptions
- **What:** Rooms gain a `biome` attribute (`forest`, `meadow`, `mountain`,
  `swamp`, …); a central `world/room_fragments.py` owns default overlay
  fragments per biome × state (weather, time-of-day, season). Lookup chain:
  room's own fragment → biome fragment → nothing. A builder then writes one
  base desc plus a biome value and gets rain, snow, night and season flavour
  for free; hand-written text remains only where a room is genuinely unique.
  Single-writer by construction — one module owns the fragment vocabulary, the
  same shape `world/material_registry.py` gives crafting. It is also the
  natural procgen seam: a generated room carries only a biome key and the
  library does the rest, which is the only authoring model that survives the
  Daggerfall-scale ambition.
- **Why deferred:** This is the load-bearing piece, but it is a design session,
  not a drop-in. Open questions that must be settled before code: fragment
  storage format; how library fragments compose with ExtendedRoom's priority
  chain and `$state()` parsing (inject? append? replace?); whether a zone level
  belongs between room and biome; and how far the biome key doubles as an input
  to future procgen and resource spawning. Building it speculatively
  mid-Stage-4.5 would break both the no-speculation rule and session focus.
- **Trigger:** Own decomposition session, scheduled **before any building pass
  larger than the test world** — every room authored under the per-room model
  before the library exists becomes migration debt, so the cost of delay grows
  with every room built. That makes the trigger self-arming rather than
  aspirational.
- **Origin:** Session 2026-08-13 (builder-ergonomics discussion; explicitly
  flagged as must-not-lose).
- **Status:** OPEN (requires its own design session)

---

## UX & Item Identity

### Skill `descs` stop at 95 — nothing reads above `master`
- **What:** Every skill trait's `descs` map tops out at `95: "master"`, so
  `tier_for()` returns `master` for 95 and for 250 alike. Stage 4.5 D.2 removed
  the 100% cap, so scores above 100 are now reachable and the top tier covers an
  open-ended band instead of the last five points.
- **Why deferred:** The gain is cosmetic and the cost is a migration. `descs` are
  stored **per trait on every existing character**, so new bands must be written
  in `Character.at_object_creation`, in
  `world/character_migrations.py::HUNTING_SKILL_DEFAULTS`, *and* onto every
  character created before the change — the same surface D.2's `max` removal had
  to solve with a write-time repair, incurred a second time for labels. D.2
  locked "leave `descs` alone" precisely so the migration commit had one job.
- **⚠️ Constraint if picked up:** **P-8** (no second progression number shown to
  the player) is *not* violated by a label — a tier name is not a figure — but the
  labels must stay honest about the curve. A point costs ~6 144 XP at skill 200
  (~44 h of pure cooldown), so a tier called `grandmaster` at 150 would name an
  altitude almost nobody reaches, and the band 95–140 would keep the single label
  it has now. Decide what the *reachable* range actually is before naming bands
  in it.
- **Trigger:** Either a player is observed above ~110, or another change is
  already migrating stored trait data and can carry this for free.
- **Origin:** Skill Progression decomp Rev 8 §6, D.2 locked decision 2.
- ⚠️ **Rev 35 — the band arithmetic above reads the table as lower bounds.**
  The code does not: `Trait.desc()` and `tier_for()` both read
  `{upper_bound_inclusive: label}`, so `80: "skilled", 95: "master"` puts
  **81** and everything above it in `master`, not "the last five points", and
  "the band 95–140" is 81–140. The entry's premise (one label for 95 and 250
  alike) still holds. Do not pick this up before *`descs` tables are read as
  upper bounds but shaped like lower bounds* (below) is decided — it changes
  what every number in this entry means.
- **Status:** OPEN

### `descs` tables are read as upper bounds but shaped like lower bounds
- **What:** Evennia's `Trait.desc()` reads every `descs` key as an **upper
  bound, inclusive**: the first key with `value <= key` wins, and a value above
  the top key gets the top label (`evennia/contrib/rpg/traits/traits.py`,
  pinned `v6.1.0` — its docstring says `{upper_bound_inclusive: text}`). Eight
  of the nine tables in `Character.at_object_creation` — the three survival
  gauges and all five skill tables — have the *shape* of a lower-bound table
  instead: the worst label at key `0`, the best at key `95`, the steps between
  at 20/40/60/80. (Health's is keyed differently; see the next entry.) Under
  the upper-bound reading that shape has two visible effects:
  - **The key-`0` label covers one value.** `starving`, `dying of thirst`,
    `exhausted`, and every skill table's bottom label (`unskilled`,
    `helpless`, `clumsy`, `feeble`, `oblivious`) apply at exactly 0 and nowhere
    else.
  - **The top key's number does nothing.** `80: "satisfied", 95: "full"` labels
    81–100 `full`: 81–95 match 95 as a bound and 96–100 fall above it.

  Net effect: a value strictly *between* two keys (21–39, 81–94, …) reads one
  band better than a lower-bound reading of the same table; a value on a key,
  or above 95, reads the same either way. Seen in play 2026-10-09: fatigue 50
  shows `weary` (lower-bound reading: `tired`), fatigue 70 shows `rested`. The
  same sheet's skills confirm the reading: Perception 25 → `attentive`
  (≤ 40), Stealth 20 → `obvious` (≤ 20).
- ⚠️ **The repository disagrees with itself about which reading is meant.**
  `world/improvement.py::tier_for()` mirrors the upper-bound rule on purpose and
  its docstring calls the maps "declared ascending, so order is meaningful and
  correct". The entry above (*Skill `descs` stop at 95*) reasons in lower
  bounds. Each is accurate about what it states; they cannot both describe
  intent, and nothing else in the repository records which was meant.
- **Three readers, one rule.** `Trait.desc()` (eight call sites:
  `commands/character_commands.py` ×7, `world/survival_ticker.py:127`),
  `tier_for()` (the skill tier-up message, `typeclasses/characters.py`), and
  `world/survival_ticker.py::_bucket_index()` (the "You feel …" message when a
  gauge drops a band). Any change to the reading changes all three together, or
  the sheet, the tier-up line and the ticker's warnings disagree about the band
  a character is in.
- **Decide the reading first; it decides the cost.**
  - *Upper bounds are the design:* the tables are rewritten so their numbers
    say what they do. `descs` are stored per trait on every character, so this
    is the data migration *Skill `descs` stop at 95* describes, for every gauge
    and every skill.
  - *Lower bounds are the design:* the stored tables are already right and the
    three readers change instead — no data migration, but every tier boundary
    moves by one band, so a tier-up message fires at a different score than it
    does today.
- **Why deferred:** Cosmetic. No mechanic branches on a label; the visible
  effects are the sheet, the tier-up line and the ticker's warnings. Not Epic
  A's, and found while Epic A's branch was open.
- **Trigger:** Before the next change to any `descs` table — including the
  entry above and the health entry below, either of which would otherwise bake
  a reading in by accident.
- **Origin:** Epic A TA1.3 in-game protocol, 2026-10-09 (the sheet's fatigue
  labels). Reading verified against `traits.py`, `improvement.py` and
  `survival_ticker.py`.
- **Status:** OPEN

### Health `descs` use a 0–100 scale against a max of `CON × 2`
- **What:** Health's `descs` are keyed 0/10/25/50/75/90/100, and `desc()`
  compares them against the trait's **absolute** value. But health's base is
  `self.stats.con.value * 2` — 20 at CON 10. A character at full health
  therefore reads `critically wounded` (20 ≤ 25), and `healthy` (91–100 under
  key 100) needs a max of at least 91 — CON 45.5 or more. Seen in play 2026-10-09:
  `Health 20.0/20.0 (100.0%) - critically wounded`.
- **Wrong under either reading** of the entry above, which is why this is its
  own entry: under lower bounds, 20/20 would read `near death`. The scale is the
  bug, not the bound. A fixed absolute table cannot be right for every character
  while the max moves with CON, so the label has to follow the gauge's
  `percent()` rather than its value. That is a reader change (or a table
  re-keyed per character whenever CON changes, which is worse).
- **Why deferred:** Cosmetic — no mechanic reads the label — but it is the most
  misleading of the `descs` problems: the one sentence about health a player
  sees contradicts the number printed next to it. Of the three `descs` entries,
  this is the one to do first.
- **Trigger:** Together with the decision in the entry above (the health reader
  is one of the three), or the next change to `sheet`/vitals output — whichever
  comes first.
- **Origin:** Epic A TA1.3 in-game protocol, 2026-10-09.
- **Status:** OPEN

### `look`-injected condition for non-admin players
- **What:** Surface the condition line in `look` output for regular players
  (who lack `examine`).
- **Why deferred:** D.3 shows condition on `look` for tools/garments via
  `return_appearance`, but a general `look`-injection for arbitrary items was
  scoped out.
- **Trigger:** None hard.
- **Origin:** Working memory (Component D.3 era) — never had a written doc entry;
  this is now its first written home.
- **Status:** OPEN

### Suppress "is wearing nothing" on a bare garment
- **What:** Stop `look`ing at a garment from emitting "X is wearing nothing."
- **Why deferred:** Pre-existing `ContribClothing.get_display_desc` quirk (a
  garment "wears" nothing); cosmetic, low priority.
- **Trigger:** None hard.
- **Origin:** Evennia Reference §8.8.
- **Status:** OPEN

### Per-recipe `min_skill` / detail on book & scroll `look`/`evaluate`
- **What:** Show each held recipe's `min_skill` (and optionally its full detail
  block) when a knowledge carrier is inspected, so a buyer can judge whether they
  could ever craft what a book/scroll teaches — not just its name and condition.
- **Why deferred:** MVP Alpha already gives buyers the two decisive signals —
  *which* recipes (stamped key + `status` list + names in `get_display_desc`) and
  *how worn* the item is (condition) — and craftability stays discoverable by
  attempting to `learn`/craft. Adding skill/detail now would couple the `Book`
  typeclass to recipe internals for a refinement, not a blocker.
- **Trigger:** Playtest signal that buyers misjudge books (pay for recipes above
  their skill), or books routinely carrying recipes far beyond a typical buyer.
- **Origin:** Component G.1 (Rev 9) — the "val C-half" surfaced while deciding
  what `look`/`evaluate` should reveal; deferred by decision.
- **Status:** OPEN — when built, route the lookup through a `world/knowledge.py`
  helper (a names→summary renderer), NOT direct `_RECIPE_CLASSES` access, so
  `Book`/`Scroll` never become registry consumers (mirrors
  `render_recipe_detail_by_name`, keeping the coupling in one module).

### `look <scroll>` collapses the recipe block's column padding
- **What:** `world/knowledge.py::render_recipe_detail` pads its labels so every
  value starts in the same column: `Needs:`, `Tool:`, `Skill:` and `Output:`
  are followed by 3, 4, 3 and 2 spaces. `recipes <name>` sends the block as
  written. `look` at a stamped scroll does not:
  `DefaultObject.format_appearance` returns
  `compress_whitespace(appearance).strip()`, and `compress_whitespace` cuts
  every run of two or more spaces that follows a non-space character down to
  two (`max_spacing=2`) — `evennia/objects/objects.py` and
  `evennia/utils/utils.py`, pinned `v6.1.0`. Each padding run follows the `|n`
  that closes its label, so each becomes two spaces. Running Evennia's own
  function on the block's rows puts the values at columns 11/11/11/11 for
  `recipes` and 10/9/10/11 for `look`. The two-space indent that opens each
  row survives, because it follows a newline rather than a character.
- **Why deferred:** Cosmetic, and present since Recipe Knowledge F.3 put the
  shared renderer behind `Scroll.get_display_desc`. That is the only step of
  the appearance chain `Scroll` overrides, so its whole description goes
  through the compression.
- **One possible route, not a decision:** Evennia's `|_` markup renders as a
  space but is not a space character (`evennia/utils/ansi.py`, `ANSI_SPACE`),
  so the compression leaves it alone — checked: `|_|_|_|_` comes through
  `compress_whitespace` intact and renders as four spaces. Padding written that
  way would hold the column in both views. Whether a renderer in `world/`
  should know about a display quirk of one of its consumers is the question to
  settle first.
- **Trigger:** The next change to `render_recipe_detail` or to the scroll's
  description, whichever comes first.
- **Origin:** Seen on a stamped cloth scroll during the Epic A TA2.3 in-game
  protocol; verified against Evennia's source 2026-10-17.
- **Status:** OPEN

> **Not listed here:** *Search / disambiguation UX + item identity* — already a
> written, cross-cutting entry in `roadmap.md` §backlog (rides on Stage 2/3 alias
> work). It has a safe home in an always-read doc, so per the scope note it is not
> duplicated here.

---

## Tooling & Process

### `PolishedWorld_System_Backlog.md` lives at the wrong altitude for its location

- **What:** `docs/crafting/PolishedWorld_System_Backlog.md` is a **strategic**
  document — 14 systems in dependency order, each one gating a branch of the
  crafting tree — filed inside a **tactical** subfolder, while `docs/BACKLOG.md`
  is declared the canonical home for deferrals and `roadmap.md` for anything
  stage-sized. Its content is neither: it is a build-order list for work that has
  no stage yet.
- **Why deferred:** Moving it is not free. Its own rev header names its canonical
  path, `docs/README.md` now indexes it there, and any cross-reference in the
  crafting decompositions points at the current location — so a move is a small
  coordinated task, not a line in a sweep. It was also invisible until
  `docs/README.md` Rev 8 widened the catalog check to `docs/**/*.md`; a document
  nobody could find is not a document anyone had an altitude opinion about.
- **Trigger:** whichever stage picks up the crafting catalogue — the same content
  trigger as *⛔ The recipe catalogue does not span the skill scale*, since that
  is the work which will actually read this file. Decide then between three
  homes: leave it and accept the location, promote its list into `roadmap.md`'s
  parallel backlog, or move it to `docs/` proper.
- **Annotation (2026-10-17, roadmap Rev 27):** the trigger is effectively met —
  the alpha track picks up the crafting catalogue next, through *Alpha content
  epic* (*Crafting & Tools*), and that session decides the home. One correction:
  *Why deferred* says the file's "own rev header names its canonical path". It
  had no rev header until 2026-10-17, when the roadmap Rev 27 session gave it
  Rev 1; the sentence was written from the convention, not from the file.
- **Origin:** roadmap Rev 17 session, 2026-08-12, while fetching `docs/crafting/`
  to check what the catalogue blocker actually needs.
- **Status:** OPEN

### Four docs under `docs/crafting/` and `docs/reference/` carry no Rev header

- **What:** `AGENTS.md` §9 requires a Rev header on every doc, and
  `docs/PolishedWorld_Core_Instructions.md` states it twice — *Critical Reminders*
  says all `docs/` files carry one, and the project-knowledge note calls its three
  docs the only ones in the project without one. Neither is true against the
  tree: `docs/crafting/PolishedWorld_Crafting_Decomposition.md`,
  `docs/crafting/PolishedWorld_Crafting_Decomposition_AoL_Complete.md`,
  `docs/crafting/deer_batch_gold_standard.md` and `docs/reference/arms_of_legend.md`
  have none. A fifth, `docs/crafting/PolishedWorld_System_Backlog.md`, got Rev 1
  on 2026-10-17 because that session edited it. The worked-example decomposition
  is also stale in content: it still shows tanning pending DECISION #2 and the
  boots recipe as dormant.
- **Why deferred:** A header is cheap, but each file's first Rev is a content
  decision — what does Rev 1 say about a doc edited for months without one? — and
  `arms_of_legend.md` is OGL rulebook text that may want a *reference* convention
  rather than a Rev at all.
- **Trigger:** Each file gets Rev 1 in the next commit that edits it, as the System
  Backlog did. Core Instructions' two sentences are corrected at its next
  revision.
- **Origin:** FAS 1 costing session (2026-10-17), while deciding whether the
  System Backlog should get a header.
- **Status:** OPEN

### Unit-test coverage initiative (`tests/` + OpenCode replication)

- **What:** A committed `tests/` package running under
  `evennia test --settings settings.py .`, seeded by a heavily-commented reference suite for
  `world/knowledge.py` intended as a golden template OpenCode replicates across the other
  modules, plus an `AGENTS.md` §0 scope entry permitting OpenCode to write under `tests/`
  **only**, gated on a green run before commit.
- **Why deferred:** Honest status, not a plan: a 21-test reference suite and a
  `tests/__init__.py` marker were drafted in an earlier session, but **neither is in the
  repo** — both return 404 on `main` and on `feature/recipe-knowledge` — and `AGENTS.md` §0
  still scopes OpenCode to `world/prototypes.py`, `world/recipes.py` and
  `world/harvest_templates.py` with no `tests/` entry. The work exists only in a closed
  chat. Logging it here beats leaving it in working memory, which is exactly how the
  original draft got lost.
- **Trigger:** Any of — a regression that in-game `@py` testing would not have caught;
  onboarding a second contributor; or the crafting-catalogue expansion, where bulk
  OpenCode-generated data makes a green-test guard genuinely load-bearing.
- **Note:** The `AGENTS.md` scope entry is a **prerequisite**, not a follow-up — without it
  OpenCode has no permission to write the files it is meant to replicate.
- **Origin:** Unit-test coverage session (pre-Component G); rediscovered at Stage 3 close-out.
- **Status:** **DONE** (2026-07-27). The "neither is in the repo" note above was
  accurate when written and is now stale: `tests/__init__.py` and
  `tests/test_knowledge.py` are on `main`, `AGENTS.md` Rev 2 adds §0A and the
  `tests/` write-scope, and `tests/test_currency.py` (82 tests at Stage 4
  Component A close) is the second suite built to the golden template. The
  OpenCode *replication* half has not been exercised yet — that is a task, not a
  deferral, and lives in the stage plans rather than here. Keep for traceability,
  prune at the next backlog sweep.

### Runnable seam checker for the System Map

- **What:** A small dev tool (`tools/check_seams.py` or equivalent) that takes the
  symbol list from `docs/PolishedWorld_System_Map.md`'s seam table and reports the
  real consumers of each: AST call-site and subclass detection, **plus** a sweep
  for the symbol as a string literal inside `getattr(...)`. Output compared to the
  "Consumers" column by eye; the tool reports, it does not gate. **It should also
  parse the file's Mermaid block** — `mermaid.parse()` under jsdom is enough, no
  renderer needed. Rev 2 shipped a diagram that did not render at all, and no
  amount of bracket-balancing or re-reading caught it; only the real parser did.
- **Why deferred:** System Map Rev 2 was scoped as a documentation commit, and the
  rows are correct as of `23f6f6e`. Shipping the checker in the same sweep would
  have mixed a tooling decision into a doc fix.
- **Why it matters, stated plainly:** the map's own honesty method is what let it
  rot. Plain `grep -rn` **over-reports** — `typeclasses/books.py` was credited as a
  `_RECIPE_CLASSES` consumer because two comments say it deliberately is *not* one,
  the same trap the Stage 4 D guard hit — and the natural fix **under-reports**,
  because `world/crafting_base.py:314` dispatches `attempt_skill_improvement`
  through a `getattr` string that no AST walk can see. Neither method is sound
  alone, so the cross-check is currently a paragraph of prose asking a human to be
  careful. That is exactly the kind of promise that gets skipped at 5 h/week.
- **Explicitly rejected:** making it a unit test that parses the markdown table.
  The Consumers column is free prose, so the table would have to be reformatted to
  machine-readable shape first — a larger change than the rot it prevents — and the
  test would fail on cosmetic edits. A red build caused by formatting is a build
  people learn to ignore.
- **Trigger:** **Stage 5 kickoff.** Combat becomes the second consumer of
  `apply_health_damage`, whose seam row already says `(future: combat)` — so that
  table is *going* to be edited, and that is the cheapest moment to make editing it
  verifiable.
- **Origin:** System Map Rev 2 verification sweep (2026-08-03).
- **Status:** SCHEDULED (Stage 5 kickoff)

### Import the three project-knowledge-only docs

- **What:** Bring `PolishedWorld_Functional_Decomposition.md` (244 lines),
  `PolishedWorld_Code_Standards.md` (282) and `PolishedWorld_Mongoose_Legend.md`
  (236) into `docs/`, each reviewed against the shipped code and given a Rev
  header per §9 — or retired if what they say has been superseded.
- **Why deferred:** They must be *read* before they are imported. All three
  predate the Rev-header convention (added 2026-07-01), none has been reviewed
  against the code as it stands after five stages, and at least one — Code
  Standards — is old enough to predate every Evennia gotcha now recorded in
  `PolishedWorld_Evennia_Reference.md`. Importing them unread would put three
  unreviewed authority documents on `main`, which is worse than leaving them
  outside it and saying so.
- **Why it matters, stated plainly:** `PolishedWorld_Core_Instructions.md` cites
  all three as authority. They have no version, no date, no canonical path and no
  git history, so there is no way to tell whether a project-knowledge copy is the
  latest — the exact failure the §9 convention exists to prevent. Rev 3 marks them
  as *project-knowledge only*, which makes the gap visible; it does not close it.
- **Trigger:** **The next time one of them is actually cited in a design
  discussion.** It gets read then anyway, so the review is nearly free at that
  moment and expensive as a standalone task.
- **Origin:** Core Instructions Rev 3 verification sweep (2026-08-03).
- **Status:** SCHEDULED (on next citation)

---

### Public test server with nightly reset

- **What:** A hosted instance that pulls `main`, wipes its database on a fixed
  cadence (~24 h) and re-seeds a playable world unattended, so other people can
  try the codebase as it stands. Two parts, and only one of them is hosting.
  **(a) Deterministic seeding from an empty DB** — `server/conf/at_initial_setup.py`
  as the once-per-fresh-database hook, sourcing the world data that already
  exists in `world/testworld_data.py`, plus a reset script (stop → drop
  `evennia.db3` → `evennia migrate` → non-interactive superuser → start).
  **(b) The box it runs on**, plus a documented one-command start in the README.
- **Why deferred:** Only (b) is deferred. (a) is useful immediately and
  independent of hosting: it gives a reproducible fresh-DB environment locally
  and lets anyone else run the code without anyone operating a server. (b) buys
  **multiplayer exposure that solo development cannot produce** — concurrent
  crafting against one `TimedAction` slot, barter between two real accounts, two
  harvesters on one node — and that value does not exist until two players have
  a reason to be in the same room.
- **The nightly wipe is the right shape and also the ceiling:** it matches the
  no-backfill philosophy — schema changes cost nothing and no migration debt
  accrues on a database that is thrown away — but it also means the economy
  pillar cannot be tested there. Emergent prices need persistence across weeks;
  a wiped server measures whether commands work, not whether the market does.
  Plan it as a smoke test, not as an economy trial.
- **The Evennia Game Index is not a reason to host** (verified against live
  source 2026-09-09: `evennia/settings_default.py`,
  `evennia/server/game_index_client/{service,client}.py`). Listing is decoupled
  from having a public server. Only `game_status`, `short_description` and
  `listing_contact` are required — they are read with `[]` and raise `KeyError`
  — while `telnet_hostname`, `telnet_port`, `web_client_url` and `game_website`
  all default to empty via `.get()`, and the settings comment states outright
  that a game in closed pre-alpha development may list. The client is a
  30-minute `LoopingCall` heartbeat from a *running* server (first check-in 10 s
  after start) reporting `connected_account_count` and `total_account_count`, so
  a nightly-wiped instance would publish a total that resets to zero daily —
  which argues for reporting from a persistent instance and **against** coupling
  the listing to the wipe box. A malformed listing returns HTTP 400 and the
  service then **shuts itself down for that run**, logging only an infomsg.
- **Two constraints for when (b) does happen:** no GameGold wallet or chain node
  on that machine, and not a home IP.
- **Trigger:** (a) **OPEN** — any light week; doing it first costs nothing twice,
  since (b) needs it anyway. (b) **after Stage 5**, when two accounts in one room
  is a scenario rather than a hypothetical.
- **Annotation (2026-10-17, alpha decision — roadmap Rev 25):** the alpha
  milestone is now defined and **excludes combat**, while (b) is sequenced
  *after Stage 5* — and this entry's own text says the wiped box measures
  commands, not the market, while the alpha exists to test pillar 1. So a
  first cohort needs a *persistent* instance that no entry owns. Not resolved
  here: it is sequencing, settled on the roadmap with the alpha-vs-Stage-5
  track order. Status unchanged until then; read (b)'s trigger as *contested*,
  not current.
- **Annotation (2026-10-17, track order — roadmap Rev 27 (D3)):** the contested
  trigger is resolved by separating what the alpha needs from what this entry
  describes. **(a) moves onto the alpha track:** it is the only versioned path for
  placing the alpha's resource nodes (roadmap, Stage 6 entry's interim placement
  rule) and the seed the persistent instance starts from — it is a component of
  *Alpha content epic* (*Crafting & Tools*). **(b) is unchanged** — a wiped
  smoke-test box after Stage 5 — and the persistent instance the alpha needs has
  its own entry, *Persistent alpha instance*, directly below. **Correction:** (a)
  above says the world data "already exists in `world/testworld_data.py`". It is
  not on `origin` in any commit, and `server/conf/at_initial_setup.py` is the
  unmodified template. Part (a) therefore authors the world data as well as the
  hook — the first versioned record of where anything in the world stands.
- **Annotation (2026-10-18, alpha content decomposition):** part (a) is component
  **AC3** of `docs/PolishedWorld_Alpha_Content_Decomposition.md`. Two things the decomposition verified against Evennia
  `v6.1.0` change its shape. The setup hook's `ImportError` at module import is
  swallowed and the step still recorded as done — a world that never seeds and
  never retries — while an exception from the hook function stops startup and
  re-runs it, so the seeder is imported inside the function and is idempotent.
  And the seed does not create the Treasury: `typeclasses/treasury.py` forbids a
  fresh database acquiring a money-holding object nobody placed, so it is a
  runbook step. The reset script stays (a)'s, built only if the runbook wants it.
- **Origin:** Session 2026-09-09 (test-server discussion; option B chosen —
  build seeding and reset now, host later).
- **Status:** SCHEDULED (seeding — alpha content decomposition, AC3) / BLOCKED on Stage 5 (wiped-box hosting)

### Persistent alpha instance

- **What:** A hosted instance for the closed-alpha cohort that is **not** wiped on
  a cadence: seeded once from an empty database by *Public test server* part (a),
  then left running for the length of the alpha so that prices can emerge — the
  one thing the nightly-wiped box cannot measure. **Wiped at alpha close-out**, and
  the cohort contract says so up front: a closed alpha's world ends with the
  alpha, which keeps no-backfill free afterwards and means Stage 5's
  character-state changes (locational Hit Points, wound tiers) never migrate a
  cohort character. During the alpha the trade-off is real: a schema change on
  the alpha track is either a migration or an announced wipe, and the contract
  should say which the cohort can expect. Inherits the wipe box's two
  constraints — no GameGold wallet or chain node on the machine, not a home IP —
  and is the natural instance to report to the Evennia Game Index from, for the
  reason *Public test server* already gives: a wiped box reports a total that
  resets daily.
- **Why deferred:** A cohort has nothing to do until the alpha prerequisites exist.
- **Trigger:** Alpha prerequisites 1–5 (roadmap, alpha entry (A)) on `main`, and
  *Death contract surfaces* on `main` — the contract must be readable before the
  first death. The sixth prerequisite, the launch minimum, is decided together
  with this instance, since moderation tooling only means something on a box
  players can reach.
- **Annotation (2026-10-18, roadmap Rev 28 (E)):** the trigger gains a seventh
  prerequisite, *Weight and encumbrance* on `main`. Like *Death contract
  surfaces* it sits outside (A)'s chain. It must precede this instance rather
  than follow it because objects spawned here before `enc` has a reader would
  need a migration — the cost the close-out wipe exists to avoid.
- **Origin:** FAS 1 costing session (2026-10-17), roadmap Rev 27 (D3) — the gap
  Rev 38 recorded: no entry owned a persistent alpha instance.
- **Status:** BLOCKED (alpha prerequisites)

### Two treasury tests assume the developer's settings match the shipped ones

- **What:** `tests/test_treasury.py::TestResolveTreasury::test_unset_is_a_supported_state`
  and `tests/test_economy_command.py::TestEconomyOverview::test_unconfigured_treasury_names_the_setting_and_the_fix`
  test the **unset** state by applying no override at all. Both rely on
  `TREASURY_DBREF` being absent from `server/conf/settings.py` — and
  `tests/test_treasury.py`'s module docstring says so in as many words
  (*SETTINGS OVERRIDE PATTERN*). That holds for the committed file and for a
  fresh clone. It does not hold on a working tree, where the local settings carry
  an uncommitted `TREASURY_DBREF` pointing at the live Treasury; the test
  database has no object at that dbref, so both tests fail on every local run
  (`'not_found' != 'unset'`, and an overview that reports a dangling dbref
  instead of naming the setting). Fix: make both hermetic with
  `override_settings`, and update the docstring section to say the unset state
  is *forced*, not assumed.
- ⚠️ **The hermetic value is `None`, not `""`.** `tests/test_work_command.py`
  uses `override_settings(TREASURY_DBREF="")`, and that is correct *there*:
  `resolve_treasury()` tests `if not dbref`, so `""` reads as unset. But
  `test_unset_is_a_supported_state` also asserts
  `assertIsNone(get_configured_dbref())`, and `get_configured_dbref()` returns
  the raw setting via `getattr` — `""` would fail it. Copying the work-test
  pattern verbatim swaps one red for another.
- **Why deferred:** Not Epic A's to fix. Neither file is touched by the epic,
  and fixing them on `feature/timed-actions` would put an unrelated change into a
  branch whose review is about one mechanism. The cost of waiting is not zero,
  which is why this is filed rather than remembered: two failures every run
  "expects" teach the reader to skim the failure list. Until fixed, verify them
  **by name** on every local run.
- **Trigger:** The next change to either test file, or any light week —
  whichever comes first. One small commit.
- **Origin:** Epic A TA1.2, 2026-10-08. Local run: 453 tests, 2 failures, both
  traced to the local `TREASURY_DBREF`. The sandbox clone, which has no local
  settings, ran 453 green.
- **Status:** OPEN

### `Idmapper flush called more than once` — probably a timing artifact, not memory
- **What:** `[WW] Warning: Idmapper flush called more than once in 5.0 min
  interval. Check memory usage.` in the server log — once on 2026-10-08, and on
  2026-10-09 at 17:21:12, **exactly nine minutes** after a reload logged at
  17:12:12. Read against Evennia's source (`evennia/server/service.py`,
  `evennia/utils/idmapper/models.py`, pinned `v6.1.0`), nine minutes is the one
  moment the warning can fire with no memory pressure at all:
  - `server_maintenance()` runs every 60 s (`LoopingCall`, `now=True`), and
    calls `conditional_flush()` on every fifth run — ~4 min and ~9 min after a
    start, then every 5 min.
  - The **first** call only records `LAST_FLUSH = now` and returns.
  - The **second** compares `now - LAST_FLUSH < 300.0` — and nominally exactly
    300 s have passed. If the first call ran a little later than its slot (the
    reactor is busiest just after a start), the difference is just under 300 and
    the warning fires.
  - It fires **before** the memory check is reached, so it says nothing about
    memory. `LAST_FLUSH` moves only on a real flush, so the third call sees
    ~600 s and the warning cannot repeat until the next start — **or** until a
    real flush resets `LAST_FLUSH`, after which the call five minutes later is
    in the same race. A real flush needs real pressure, so that case still
    points at memory.
- ⚠️ **This is a hypothesis with one data point.** It predicts that *every*
  occurrence sits at ≈ +9:00 after a start or reload. The 2026-10-08 occurrence
  has not been checked against the log. Confirm by listing the warning's
  timestamps next to the preceding `Server successfully reloaded` / start
  lines. All at ≈ +9 min → benign and upstream (a candidate Evennia report, no
  PolishedWorld action). Any occurrence at another offset → real cache pressure:
  check the idmapper cache with `@server`. The committed settings do not
  override `IDMAPPER_CACHE_MAXSIZE`, so unless the local settings do, the cap
  is Evennia's default of 400 MB.
- **Why deferred:** Not Epic A's, and the evidence so far says it is noise —
  but "it is noise" is exactly the conclusion that must be checked rather than
  assumed, which is why it is filed.
- **Trigger:** The next occurrence, or the next time the server log is read for
  anything else.
- **Origin:** Watch item carried by the Epic A TA1.3 handoff (first seen
  2026-10-08); recurred during the TA1.3 in-game protocol, 2026-10-09.
- **Status:** OPEN

### The recipe visibility gate has no test
- **What:** `commands/crafting_commands.py::CmdRecipes` keeps unlearned
  advanced recipes out of sight twice. The bare list (`_show_list`) counts them
  as hidden instead of listing them and, when any exist, ends with *"Whispers
  speak of crafts beyond your knowing."*; `recipes <name>` (`_show_detail`)
  refuses them — *"You don't know the recipe for '…'. Seek someone who
  does."* — before any ingredient is shown. Both apply one rule, *common, or
  learned by this caller*, written out separately in each method; the detail
  view's comment asks for exactly that (*"mirror the list exactly"*). No test
  exercises either half: not the hiding, not the refusal, not the hint line.
- **Why it matters:** The gate protects what the learn / buy / teach economy
  trades in, an advanced recipe's ingredients. A change that makes the two
  copies disagree (the list hiding a recipe whose detail opens, or the
  reverse) passes the suite in silence.
- **Why deferred:** Existing behaviour since Recipe Knowledge Component C that
  Epic A does not touch. TA2.3 kept it out of its own commit for that reason
  (Timed Actions decomp T29).
- **Trigger:** The next change to `CmdRecipes`, to `requires_knowledge`, or to
  how a character comes to know a recipe — or the recipe catalogue expansion,
  whose advanced recipes are what the gate exists for.
- **Shape when picked up:** one advanced recipe and two characters, one who
  has learned it and one who has not, each asking both views: hidden and
  refused for the one, listed and shown for the other. A test of either view
  alone cannot see the two drift apart.
- **Origin:** Epic A TA2.3 (T29), 2026-10-15.
- **Status:** OPEN

### ⚠️ `at_server_start` ticker re-adds wipe every other persistent ticker
- **What:** `server/conf/at_server_startstop.py` calls `TICKER_HANDLER.add(...)`
  in `at_server_start` for the survival and garment-wear tickers, on every
  start. In Evennia v6.1.0, `at_server_start` runs during server startup
  (`evennia/server/service.py` l.488), but `TICKER_HANDLER.restore()` runs later,
  in `at_post_portal_sync` (l.656). Each `add` calls `save()`
  (`evennia/scripts/tickerhandler.py` l.535), and `save()` (l.400) writes the
  handler's whole in-memory storage over the stored copy — which, in a fresh
  process, holds only what was just added. `restore()` then reads back those two
  tickers and nothing else. **Every persistent ticker subscribed anywhere else is
  lost on every reload and every cold start.** The survival and garment tickers
  survive only because they are the ones re-added.
- **Evidence (2026-10-19, `feature/sweeper` in-game protocol):** E1 — after a
  sweeper object re-registered its ticker, `TICKER_HANDLER.all_display()` held
  3 entries including it, and it fired (the NPC moved on its own between two
  polls). E3 — after one `reload`, the same expression returned the 2 global
  tickers and no sweeper. No traceback was logged. The unit tests were green
  throughout: a test process never restarts the server.
- **Impact today:** latent. Nothing on `main` subscribes a ticker outside
  `at_server_start`; the sweeper was the first and moved to a Script. The trap
  is the next per-object ticker, which will pass its unit tests and stop after
  the first reload. The comment at `at_server_startstop.py` l.44–46 ("re-adding
  ... is idempotent ... so running this on every start is safe") is true for the
  re-added ticker itself and false for everything else — a prose site to correct
  with the fix.
- **Fix candidates (undecided):** (1) move the survival and garment-wear timers
  to `GLOBAL_SCRIPTS` in `settings.py`, as `WeatherScript` and
  `CreatureSpawnScript` already are, so nothing touches ticker storage at
  startup; (2) keep the tickers but register them once (initial setup) and stop
  re-adding them on start. Either touches survival, which is alpha-critical, so
  it gets its own branch and its own receipts.
- **Receipt when fixed:** in-game only — subscribe a throwaway persistent
  ticker, `reload`, and show it still listed by `TICKER_HANDLER.all_display()`;
  plus a cold restart. Testing Reference §11h.
- **Origin:** `feature/sweeper` in-game protocol, 2026-10-19.
- **Status:** OPEN (latent)

---

## Currency

### `_format_wait()` truncates, so a fresh cooldown reads one unit short
- **What:** `commands/work_commands.py::_format_wait()` floors on division, so a
  cooldown set to 3600s renders as `59 minutes` from the first second onwards.
  Correct arithmetic, wrong impression: it reads as though the clock was already
  running before the chore finished.
- **Why deferred:** Purely cosmetic, and the naive fix (ceiling) is wrong in the
  other direction — it would render a fresh 3600s cooldown as `1 hour` for a
  whole minute and then jump. The right answer is probably to round to the
  nearest unit and accept a one-unit fuzz at both ends, which is a five-minute
  change nobody should make while a component is open.
- **Trigger:** Next time anyone touches faucet output, or the first player who
  mentions it.
- **Origin:** Stage 4 D.1, found in the in-game walkthrough.
- ⚠️ **Rev 36 — the short end of the same arithmetic.** The floor bites hardest
  in the last two minutes of *every* cooldown, whatever its length: 60–119 s
  remaining all render as `1 minute`, so at 119 s both callers — the cooldown
  reply in `CmdWork.func` and the board in `CmdWork._show_board` — understate
  the wait by 59 s, half of it. Rounding to the nearest minute, as proposed
  above, still errs by up to 30 s there (89 s → `1 minute`, 90 s →
  `2 minutes`). Below a minute the function already prints seconds, and one
  case of that is wrong too: 1 s renders as `1 seconds`. Keeping seconds below
  two minutes would remove the tail error; the rounding decision above should
  be taken with that option on the table. Noted while settling Timed Actions
  decomp T25, 2026-10-15.
- **Status:** OPEN

---

### Faucet task-table tuning (`TEMPLE_TASKS`)
- **What:** Rewards, cooldowns and now `duration` for the five temple chores, in
  `commands/work_commands.py::TEMPLE_TASKS`. The named constant is the anchor,
  per the decomposition; the numbers themselves are first-pass.
- **Why deferred:** They cannot be tuned against anything real until crafted
  goods have prices players actually charge each other. The faucet's job is to
  read as *obviously* a supplement — 170 Copper for the full chain, against a
  crafted item's eventual worth — and that ratio is unknowable before a market
  exists.
- **Trigger:** First playtest with real player-to-player pricing, or Stage 8
  when Gold acquires an external exchange rate.
- **Origin:** Stage 4 D.1 (decomposition §6/D asks for the constant explicitly).
- **Status:** OPEN

---

### Timed player actions have a pattern but no shared home
- **What:** `rest` (Stage 2) and `work` (Stage 4) both implement "this takes
  time and can be interrupted" independently: an `ndb` flag, a `delay`, an
  `at_pre_move` interrupt, a `has_account` guard in the callback. `at_pre_move`
  in `typeclasses/characters.py` now has two hand-written branches and will grow
  one per future timed action.
- **Why deferred:** Two instances is not yet a pattern worth extracting, and the
  third will teach more about the right shape than guessing now would. But the
  duplication is real and `at_pre_move` is where it will become visible first —
  a third branch is the signal to build a small `TimedAction` helper rather than
  a fourth.
- **Trigger:** **Met (Rev 24).** The third timed action is craft duration — see
  *Crafting resolves instantly* — not the gathering or Stage 6 combat this entry
  guessed at. Build the small `TimedAction` helper in that same pass; a fourth
  hand-written `at_pre_move` branch is the outcome this entry exists to prevent.
- **Origin:** Stage 4 D.1 (Evennia Reference §11.27 documents the mechanism).
- **Status:** **DONE** (2026-10-17). Delivered by Epic A Component TA1 and merged to
  `main` in `34b2ee4`: `world/timed_actions.py` holds one slot per character,
  `ndb.timed_action`; `rest`, `work` and `craft` all run on it; `at_pre_move`
  makes one `interrupt()` call for every timed action; and `at_character_death()`
  interrupts the slot itself, because death relocates without move hooks.
  Decisions D1–D7 and T1–T13 in `PolishedWorld_Timed_Actions_Decomposition.md`.
  Keep for traceability, prune at the next backlog sweep.

---

### Ledger `actor` field — record who ordered a mint, not only who received it
- **What:** Add an `actor_key` / `actor_dbref` pair to the ledger entry shape in
  `world/economy_log.py::append()`, populated by `@economy mint` / `burn`.
- **Why deferred:** Changing the entry shape is a Component A change, and it was
  found mid-Component-C; making it then would have edited the storage primitive
  after three components had been built and tested against it. The trail is not
  missing in the meantime — every mint and burn writes a line naming the caller
  to Evennia's rotating log — it is simply in a file rather than in the record
  that `@economy audit` reads.
- **Trigger:** Component F, or the first time anyone asks the ledger a question
  it cannot answer. Note the ledger is effectively empty before Stage 8 (one
  bootstrap tranche), so a migration is cheap for exactly as long as that holds.
- **Origin:** Stage 4 C.2 (noted in the `currency_commands.py` module docstring).
- **Status:** SCHEDULED (Component F)

---

### `@economy audit` counts the Treasury as a holder but excludes its balance
- **What:** `audit()` returns `wallet_count` over every wallet holder while
  `wallet_sum` deliberately excludes the Treasury, so `audit_report()` renders
  `Wallets: nothing (1 holder)` on a freshly minted economy — the one holder
  being the Treasury, whose balance is on the line below.
- **Why deferred:** Cosmetic. The invariant is exact either way and `delta`
  is unaffected; only the parenthetical is misleading. Fixing it means choosing
  whether the count follows the sum (excluding the Treasury) or the enumeration
  (including it), which is a display decision worth making deliberately rather
  than in passing.
- **Trigger:** Component F's documentation pass, or the first time it confuses
  someone reading an audit.
- **Origin:** Stage 4 C.2 in-game walkthrough, 2026-08-02.
- **Status:** OPEN

---

### `@economy burn` log line reads as an inbound transfer
- **What:** Both mint and burn log `-> treasury #N`, which is right for a mint
  and backwards for a burn.
- **Why deferred:** One f-string. Bundled here rather than patched alone so the
  log line is fixed in the same pass as the `actor` field above, which rewrites
  it anyway.
- **Trigger:** Whenever the `actor` field lands.
- **Origin:** Stage 4 C.2 in-game walkthrough, 2026-08-02.
- **Status:** SCHEDULED (with the `actor` field)

---

### No command moves money from a player INTO the Treasury
- **What:** There is no `donate`, and `pay` refuses the Treasury (its
  `has_account` guard, whose comment anticipates exactly this). The Stage 4
  exchange-back therefore needs an admin to move the coin manually before
  `@economy burn` destroys it.
- **Why deferred:** Not an oversight — `donate` was deliberately not claimed
  (decomposition §5) and `pay`'s refusal is the same guard that stops players
  paying logged-out bodies. The direction belongs to Stage 8's `exchange`
  command, which needs the crypto side to exist before it can settle anything.
  Recorded so that a future session reads "owned by Stage 8" rather than
  "missing" and builds a stopgap that Stage 8 then has to unpick.
- **Trigger:** Stage 8 (GameGold exchange).
- **Origin:** Stage 4 C.2.
- **Status:** SCHEDULED (Stage 8)

---

### Compact amount input (`50c`, `2g30s`)
- **What:** Let `parse_amount()` accept the attached single-denomination form
  (`50c`) and the multi-denomination compact form (`2g30s`), in addition to the
  two-token form (`50 copper`) it accepts today.
- **Why deferred:** Both are the same feature and neither is needed for a
  playable currency. The shipped rule is one sentence — *exactly two
  whitespace-separated tokens, a non-negative integer and a denomination* —
  which rejects both for the same reason and is explainable to a player in a
  single error message. A compact parser needs its own grammar, its own
  ambiguity rules (is `2g30` 30 what?), and its own test surface.
- **Trigger:** Playtest evidence that typing the denomination is friction —
  most likely from `pay` in the middle of a live trade.
- **Origin:** Stage 4 A.1 (`world/currency.py::parse_amount` docstring names the
  deferral).
- **Status:** OPEN

### `copper` is both a material and a denomination
- **What:** `world/material_registry.py` registers `copper` as an INTERMEDIATE
  material (smelted from `copper_ore`, with `copper_ingot → copper` aliased),
  and Stage 4 introduces Copper as the base currency denomination.
- **Why deferred:** Harmless in Stage 4 and cheap to leave alone. The wallet is
  an `int`, there are no coin objects, and the verbs do not overlap —
  `pay 5 copper to Bob` never reaches `caller.search()`, while
  `give copper to Bob` never reaches the currency parser. Renaming either side
  now would churn the material registry and the recipe data for a collision that
  does not yet exist.
- **Narrowed by Stage 4 E.1 (2026-08-03):** `offer` was the one verb where both
  readings were plausible, and it is now settled without a rename. A comma
  segment is coin if its first character is an ASCII digit, and that rule is
  total rather than heuristic because Evennia's disambiguation syntax is a
  *suffix* (`SEARCH_MULTIMATCH_REGEX` → `copper-2`), so no valid way of naming an
  object begins with a digit. `offer copper` is the ingot, `offer 5 copper` is
  money, and no input can reasonably mean the other. What remains deferred is
  narrower than when this entry was written: **`caller.search()` disambiguating
  two objects in a room that both answer to `copper`**, which needs `CoinPile`
  to exist first.
- **Trigger:** **Stage 5 kickoff** — the same trigger as the `CoinPile` deferral
  (S4-3), and for the same reason: the moment coins are real objects, two
  different things in a room answer to `copper` and `caller.search()` has to
  disambiguate them. Decide then whether to rename the metal, name the coin
  distinctly (`copper coin`), or lean on search-multimatch UX (§12 of the
  Evennia Reference).
- **Origin:** Stage 4 A.1 review; flagged in session before A.2.
- **Status:** SCHEDULED (Stage 5, with `CoinPile`)

### Upstream `TradeHandler.finish()` is not safe to call twice
- **What:** The contrib's cleanup nulls `part_a_offers` / `part_b_offers` but
  leaves `part_a_accepted`, `part_b_accepted` and `trade_started` set to `True`.
  A second `finish()` therefore re-enters the completion branch and dies in
  `for obj in None` with a `TypeError`.
- **Why deferred:** **Not reachable in play.** A successful teardown deletes
  `ndb.tradehandler` from both parties, so no command can obtain the handler
  again, and the timeout script's `is_valid()` refuses once the trade has
  started. It is reachable only from a held reference — a test, `@py`, or
  future code.
- **Why it is recorded anyway:** it is *currently* what prevents a double
  currency settlement, by accident, in someone else's code. Our own one-shot
  flag (S4-R3) covers us, but anyone reading `_settle_currency` should know the
  belt is doing work the braces are also doing, and that the belt is upstream's
  and may change.
- **Trigger:** An Evennia upgrade that touches `barter.py`, or the first time
  something legitimately needs to call `finish()` more than once.
- **Origin:** Stage 4 E.2, found while reasoning about S4-R3.
- **Status:** OPEN (recorded, not scheduled)

### Trade item moves bypass move hooks and `get` locks
- **What:** `finish()` moves goods with a direct `obj.location =` assignment, so
  no move hook fires and no lock is consulted. The upgrade is
  `move_to(quiet=True)` inside our `PWTradeHandler`.
- **Why deferred:** Harmless today — no current item relies on a move hook
  during a trade, and there is no item that may not be traded. The change only
  starts paying when there is something to enforce.
- **Trigger:** The **no-trade flag** (quest-bound, soulbound or otherwise
  untradeable items). Do the two together: the flag without lock enforcement is
  decorative, and the enforcement without the flag has nothing to enforce.
- **Note:** This is also why currency settlement lives inside `finish()` rather
  than in a move hook (Evennia Reference §7.5) — the hook never fires.
- **Origin:** Stage 2 barter hardening; homed here at Stage 4 F.2, previously
  recorded only in `world/README_barter.md`.
- **Status:** OPEN

### `MINT_SOURCES` / `BURN_REASONS` vocabulary
- **What:** The two whitelists in `world/currency.py`, currently
  `{"crypto_exchange", "admin_correction"}` each.
- **Why deferred:** Deliberately minimal. Every entry is a door money can walk
  through, so the list should grow only against a demonstrated need, never
  pre-emptively. The symmetry between the two is intentional: an unvalidated
  free-text burn reason would let the ledger fill with unrecognised tags while
  the invariant still balanced perfectly.
- **Trigger:** A real settlement scenario that neither tag describes honestly.
- **Origin:** Stage 4 A.2 (decision D8).
- **Status:** OPEN

### Bank / post office (coin and gear storage at a place)
- **What:** A location where a player can deposit coin and equipment and
  withdraw it later, plus — optionally, and separately — a way to send coin or
  goods to a player who is elsewhere.
- **Why deferred:** It is the *replacement* for a mechanic that was deliberately
  rejected, not a missing convenience. `pay` is same-room permanently (Currency
  decomposition §6/B.2 and the module docstring of
  `commands/currency_commands.py` both state the rule and its reasoning): coin is
  carried on the body and, from Stage 5, stays with the corpse to be looted —
  owner-only for a grace window, then by anyone (death-consequence policy,
  roadmap Rev 26) — so carrying a large sum is a risk the player chooses. A global `pay` would cancel
  that risk for free — empty your pockets remotely from inside the dungeon and
  the decision costs nothing. A bank restores the *option* while keeping the
  cost, because reaching it is a journey that can go wrong. Building it before
  `CoinPile` exists would mean designing storage against a risk that is not yet
  implemented.
- **Trigger:** After Stage 5 (`CoinPile` / death-drop), which is what makes
  carrying risky in the first place. Player demand for remote settlement is a
  *secondary* signal and must be answered with this, never by widening `pay`.
- **Origin:** Stage 4 B.2 design session (2026-07-30); the rejection of remote
  payment is recorded in the Currency decomposition Rev 4.
- **Status:** BLOCKED (Stage 5 `CoinPile`)

### `PAY_CONFIRM_THRESHOLD` — confirmation for large payments
- **What:** An optional threshold above which `pay` asks for confirmation before
  transferring.
- **Why deferred:** `pay` ships with **no** confirmation, deliberately. Most of
  the protection is already structural: D1 requires an explicit denomination, so
  the dangerous mistake — meaning Silver and typing a bare number — is a syntax
  error rather than a silent transfer of a hundredth of the intended sum. What
  remains is socially recoverable, since there are no NPC vendors and a
  misdirected payment sits in another player's hands rather than being destroyed.
  Both parties see the amount echoed back through `format_copper`, which is the
  cheap version of a confirmation. Adding a prompt before anyone has been hurt by
  its absence is speculative UX.
- **Trigger:** Playtest evidence of players fat-fingering the *denomination*
  (`gold` for `silver`), not merely the digits.
- **Constraint on the fix:** an `ndb` two-step or an explicit `confirm` argument
  — **never a `yield`**. There is no `yield` anywhere in the codebase, and `pay`
  is the one command where S4-R1's atomicity rule applies, so it is the worst
  possible place to introduce the first one.
- **Origin:** Stage 4 B.2 (considered and rejected in the design session).
- **Status:** OPEN

---

## GameGold

### Cold staking (PIVX-style P2CS)

- **What:** Pay-to-Cold-Staking outputs, so a coin owner can delegate staking
  rights to a node that never holds spending authority. In GameGold terms: the
  **temple runs as the delegate staking node**, and a player can stake without
  running an Orange Pi, keeping a wallet online, or handing anyone their keys.
- **Why deferred:** Not because it is unimportant — because it is *not*
  genesis-only, which was the assumption that made it look urgent. Bitcoin
  script reserves `OP_NOP` opcodes for exactly this: new behaviour redefined into
  a reserved opcode at a fixed activation height, no chain split. On a chain with
  no exchange listings, no third-party wallet implementations and a handful of
  operators, a later activation costs roughly what a genesis rule costs. Building
  it now, by contrast, has an immediate price: **a consensus patch carried
  against upstream from day one**, which is the same budget that
  `GameGold_Design.md` Rev 3's exit trigger depends on — the option to leave
  blackcoin-more for Peercoin stays cheap only while the patch set stays small.
- **Reference implementation:** PIVX's P2CS. Read it at source when the trigger
  fires; nothing in this entry has been verified against PIVX's current code.
- **Trigger:** **After mainnet, and only once there is a real staker who is not
  the maintainer.** Before that the feature has no user — delegating to yourself
  is just running your own node with extra consensus rules.
- **Origin:** Session 2026-09-04 (GameGold platform review; option A chosen —
  launch without cold staking, option B documented as the future path).
- **Status:** OPEN (post-mainnet; no code blocker, only an absent user)

---

### GameGold block explorer
- **What:** A Django-based, staking-focused block explorer for the GameGold
  chain.
- **Why deferred:** Part of the much-later GameGold epic; no chain deployment to
  explore yet.
- **Trigger:** GameGold epic (post-mainnet).
- **Origin:** Working memory / GameGold design context — not written in any doc
  (roadmap Stage 8 names GameGold but not the explorer); this is its only home.
- **Status:** BLOCKED (GameGold not yet deployed)
