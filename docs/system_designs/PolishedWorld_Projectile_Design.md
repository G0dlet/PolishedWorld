# PolishedWorld — Projectile Design Notes (bows, slings and thrown weapons, ammunition in bundles, range in rooms, the shot, breakage and recovery)

> **Rev 1 · 2026-11-10** — first version, docs only, with roadmap Rev 70, BACKLOG Rev 97, README Rev 49 and the series handoff `docs/system_designs/HANDOFF.md` Rev 12. Written from a design chat, the twentieth note in the one-system series, off the queue at Adam's request: how PolishedWorld should handle projectiles. It takes the mechanic half of the queue's *bowyery & fletching\** and leaves the crafts to that note (RWQ12). The chat first drafted the design outside the series method, without prior art; the prior art was read afterwards (§2) and changed four proposals — distance belongs to the encounter (RWP7), shots between rooms wait for Stage 5 (RWP10), breakage falls with skill (RWP19), recovery follows MUME (RWP20) — and two claims in the draft were corrected: there is no wind and no light level in code. Two things were found while writing and are recorded as questions: every single letter for a prefix is taken or reads as a Legend or engine word, so this note uses the stem RW (RWQ16); and a creature's deletion sends what it holds to its home, so an arrow carried inside a fleeing or dying quarry would land in Limbo (RWQ15). **Nothing here is locked.** Every numbered item is a given (RWG…), a proposal (RWP…) or an open question (RWQ…); Stage 5's design session and a decomposition lock them. Code read at `main` `fac8e2b`; Evennia at `v6.1.0`.
> **Canonical:** `docs/system_designs/PolishedWorld_Projectile_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before any decomposition).
**Home:** `docs/roadmap.md`, Stage 5, the dated *Projectiles* line (Rev 70); `docs/BACKLOG.md`, *Read EvAdventure's twitch combat before Stage 5's design* (annotated Rev 97, §2.7).
**When to read:** at Stage 5's design session (distance, the hit, shots between rooms and the haven: RWP7, RWP10, RWQ13); at any hunting decomposition that touches the shot (Hunting TP7, TP12; RWP23); when *bowyery & fletching\** is written (arrows, the bundle's yield, the training arrow: RWP6, RWQ6); when Storage's counted goods are decomposed (bundles are counts, as Storage DP9's bins are: RWP4).
**Departs from shipped behaviour in six places**, listed with their source lines in §6. The largest: `hunt` starts to care what the hunter holds.

---

## 1. The idea in one paragraph

A bow is the short end of a long craft. The arrows were cut, headed and bound by the fire the night before; the bundle rides in a quiver on the hip. In the meadow the hunter waits for the wind to drop, draws, holds, looses — and then walks out into the grass to find what she shot: one arrow in the rabbit, one snapped on a stone, one gone for good into the brook. A sling is cheaper and humbler: a lump of clay rolled smooth and dried in the sun, which crumbles where it strikes. Nothing flies through the server and nothing ticks; a shot is decided in one moment, and everything else is the world remembering where the arrows lie.

---

## 2. Prior art

Text games have solved projectiles for decades. The lineage this note follows is MUME's — shoot, then recover your arrows from the floor and the bodies; DragonRealms gives the model for range and aim; Aardwolf gives the warning about shooting between rooms. Sources read on 2026-11-10.

### 2.1 DragonRealms — the model for range and aim

In DragonRealms distance is a state between two combatants, not a property of the room: missile, pole and melee range, changed with advance and retreat. Outdoors a fight starts at missile range, indoors or in a cave at pole range. Aiming is a process: an unaimed shot uses about three quarters of the skill, a fully aimed one about a quarter more than the skill, and the game says when further aiming will not help ([Combat](https://elanthipedia.play.net/Combat), [Aim command](https://elanthipedia.play.net/Aim_command)).

**Worth taking:** distance per encounter, the room setting only where it starts (RWP7); aim as a ramp with a cap (RWP13). **Not for PolishedWorld now:** the balance-and-position layer — Stage 5's to weigh.

### 2.2 MUME — the lesson: shoot, then recover

MUME's `recover` gathers spent ammunition from the floor and from corpses into the worn container it came from, never from a living target, and `recover all` takes anyone's. Non-magical missiles break, more often against hard targets and on the killing shot, and a bowstring can snap. Its players list the costs plainly: a quarry that flees takes the arrows with it, forgetting to recover loses them, and being hit cancels a shot ([Newbie guide to missile weapons](https://docs.mume.org/wiki/pages/Newbie_Guide_to_Missile_Weapons), [Shoot](https://docs.mume.org/wiki/pages/Shoot)).

**Worth taking:** recovery from ground and body as one search (RWP20), more breakage on the killing shot (RWP19), the fleeing quarry carrying the arrow (RWP19, Hunting TP12), being hit cancels the shot (RWP18). **Not for PolishedWorld:** shops that sell arrows (pillar 1); magical ammunition that never breaks (every projectile needs a sink); free sling stones searched from the ground — the stone bullet was struck in the alpha content epic (`world/recipes.py:609`).

### 2.3 Aardwolf and MUME — the warning: shooting between rooms

Aardwolf lets archers shoot into the next room, and its help says outright that shooting a mob from there and then running in to backstab is a good way to kill; its counterweights are that the target comes looking for the shooter and that shots cannot pass through safe rooms ([Aardwolf archery help](https://www.aardwolf.com/blog/?p=598)). MUME's own guide teaches the loop of loading, stepping in, shooting and escaping, over and over.

**Worth taking:** the reason shots between rooms wait (RWP10). **Not for PolishedWorld:** shots between rooms before there is a haven and a target that answers back.

### 2.4 Achaea — no lesson for this note

The series looks for an Achaea lesson in every note. Achaea's archery sits in the Chivalry and Subterfuge class skills, and other classes shoot only with bows bought from the artefact shop ([Archery](https://wiki.achaea.com/Archery)), so it says nothing about how a crafted economy feeds bows and arrows. The slot goes to MUME (§2.2).

### 2.5 Project Gorgon — bundles, drying, and arrows back from the body

Project Gorgon has no ammunition slot: the right arrows are drawn from the inventory. Arrows are made in batches of a hundred, the shafts must first dry in real time so an archer has to plan ahead, and autopsying a corpse can return the arrows shot into it. Knowing a creature's anatomy raises the archer's chance of a critical ([Gorgon's archery system](https://wiki.projectgorgon.com/wiki/Elder_Game:_Gorgon%27s_Archery_System)).

**Worth taking:** bundles (RWP4), drawing without a slot (RWP5), arrows back from the body (RWP19). **Not for PolishedWorld now:** anatomy-driven criticals (RWQ14, Stage 5); drying time belongs to the bowyery & fletching note.

### 2.6 Armageddon — fragile arrows, kept in check by skill

Armageddon's players find its arrows too fragile; the answer in the same thread is that a better archer loses fewer, and that scarce arrows keep a strong skill in check ([forum thread](https://gdb.armageddon.org/index.php?msg=120955)).

**Worth taking:** breakage and loss that fall with skill (RWP19).

### 2.7 The tool — Evennia at `v6.1.0`

Evennia has no range and no ammunition. EvAdventure (`evennia.contrib.tutorials.evadventure`) — BACKLOG's first reading for Stage 5 — has twitch combat but its only missile is `EvAdventureThrowable`, a one-use consumable weapon (`objects.py:270`); there is no notion of distance, loading or recovery. What the project already uses carries the rest: the Cooldowns contrib (`evennia.contrib.game_systems.cooldowns`, `CooldownHandler` at `cooldowns.py:62`, on characters as `caller.cooldowns`) and the containers contrib under the project's `Container` (`typeclasses/containers.py:32`). One engine fact matters (RWQ15): `DefaultObject.delete()` clears an object's contents to their home before deleting it (`evennia/objects/objects.py:1538`, `:1579`, `:1348`).

---

## 3. Design goals

- **RWG1 — Every projectile is player-made.** No NPC sells an arrow or a bow (pillar 1). Each projectile has a source and a sink; this design is what gives the shipped bow, sling, spear and bullet their sink.
- **RWG2 — Real time with cooldowns, not rounds.** Roadmap Stage 5's stance. Legend's Combat Actions become beats of the one timed-action slot (`world/timed_actions.py`).
- **RWG3 — Nothing flies and nothing ticks.** A shot resolves in one synchronous call. Spent ammunition carries a timestamp and is read when someone looks.
- **RWG4 — One writer for ammunition counts.** One module lowers and raises counts; commands never do (P-2).
- **RWG5 — The hunting shot is not combat.** Hunting §16 makes Stage 5 not a prerequisite for the shot; whatever this note adds to `hunt` must work without Combat Styles.
- **RWG6 — Skill shows in reading, not typing.** Wind, light, distance and the stalk decide a shot; no reaction-time minigame (Hunting and Fishing decided the same).
- **RWG7 — Damage goes through the one chokepoint**, `apply_health_damage()` (`typeclasses/characters.py:1184`), on the hit-location model roadmap Rev 20 locked.

---

## 4. Legend alignment

**Rules as written:**

- **Ranged Combat styles** — p. 14: each style starts at DEX×2, tracked separately per style (Close Combat at STR+DEX).
- **Ranged weapon qualities** — p. 105: Range is the effective range and the maximum is twice it; Load is the Combat Actions to reload; STR/DEX minimums cost −5 % per point below; Size is how forceful the ammunition is, read against a parrying shield.
- **Ranged weapons table** — p. 109: short bow 1D6, 80 m, Load 1, 9/11, L, ENC 1, AP/HP 4/4; sling 1D8, 200 m, Load 1, –/11, L, ENC —, 1/2; staff sling 2D6, 100 m, Load 3, H, ENC 2; long bow 1D8, 175 m, Load 1, 13/11, H; javelin 1D8, 30 m, H, ENC 1. Damage Modifier applies to all of these (Y).
- **Ammunition** — p. 110: arrows, wood-headed arrows and sling bullets are AP/HP 1/1 and too light to score ENC; broadhead arrows lose 25 % range and add 2 damage against the unarmoured; the fishing arrow gives +10 % to Survival; sling bullets can be retrieved easily. No rule for recovering arrows.
- **Ranged attacks** — p. 140: missiles are parried only by shields; otherwise the defender dives aside with an opposed Evade (p. 136). Each Combat Action spent aiming adds the shooter's critical range — one tenth of the skill, rounded up.
- **Situational modifiers** — p. 141: wind (−5 / −10 / −50 %, gale an automatic miss), target movement (−10 / −20 %), visibility (−20 % partial darkness or mist, −40 % darkness or fog), size (−10 % per SIZ under 5, +10 % per 10 SIZ over 20), target and attacker condition. Within a group not cumulative; groups add.
- **Firing into a crowd** — pp. 141–143: a hit on a covered location strikes someone adjacent.
- **Ranged fumbles** — p. 131: a d20 table — lose the target, drop, snare, the string snaps or the weapon is lost, damage to the weapon, hit an ally, misfire.
- **Throwing** — p. 47: Athletics for improvised objects, one metre of range per point STR exceeds the object's ENC; thrown weapons use their own skill.

**In code:** five skills — perception, stealth, athletics, craft, hunting (`world/chargen.py:59–65`); no Ranged Combat style and no Evade for characters. Creatures carry `flee_skill`, which the hunt reads as Evade (Hunting TP-L3).

**Departures and readings:**

- **RWP-L1 — Before Stage 5 the hunting shot rolls `hunting`.** Track and kill is one skill today (Hunting TP-L1); a first Ranged Combat style would be a second skill for the same act (RWQ1).
- **RWP-L2 — Combat Actions become beats.** Load N is a timed action of N beats; aiming adds its bonus per beat. A beat's length in seconds is a calibration constant (RWQ10).
- **RWP-L3 — Metres become three distances** — close, open, far (§8).
- **RWP-L4 — Beyond effective range, −20 %.** Legend gives no penalty between effective and maximum range; this one is the project's, flagged as not Legend (RWQ5).
- **RWP-L5 — Arrow recovery is the project's own rule** (§10); Legend has none.
- **RWP-L6 — Within a modifier group the worst term applies.** Legend says only that a group does not add up; which term counts is this note's reading.
- **RWP-L7 — Damage dice wait for Stage 5.** Before creatures have General HP and Critical Wounds (roadmap Rev 20), a hunt's win kills or wounds by Hunting TP12's margin and the launcher changes only the odds.

---

## 5. The loop

1. **Make.** A bullet is rolled from clay; later an arrow is cut, headed and fletched (*bowyery & fletching\**). It comes out as a bundle (RWP4, RWP6).
2. **Carry.** The bundle rides in a worn quiver or pouch (RWP5).
3. **Load.** A beat or more, nothing spent yet (RWP12).
4. **Aim.** Optional; the bonus rises to a cap (RWP13).
5. **Loose.** Everything is checked again, the count drops by one, one roll decides (RWP16–RWP18).
6. **Find.** Walk out and `recover` what the grass and the body give back (RWP19, RWP20).

---

## 6. Departures from shipped behaviour

Each row is a change to behaviour that `main` has today; each is a proposal for the slice that ships it (§16).

| # | Shipped today | Proposed | Where shipped |
|---|---|---|---|
| Y1 | `hunt` resolves with nothing in hand, at any distance, as one opposed roll | With a launcher it reads the launcher's terms and spends ammunition at release; without one only at close distance after a good stalk (RWP23, RWQ8) | `commands/hunting_commands.py:96–106` |
| Y2 | `BOW`, `SLING`, `SPEAR` and `SLING_BULLET` are plain `typeclasses.objects.Object` with only `enc`, each marked *SINK: none* | Launcher, Ammunition and Throwable typeclasses with Legend's stats (RWP1–RWP3) | `world/prototypes.py:463–473`, `:802–813`, `:830–855` |
| Y3 | Every sling bullet is its own object; one lump of clay makes one bullet | Bundles with a count; the yield per lump is the bowyery note's (RWP4, RWP6) | `world/recipes.py:603–622` |
| Y4 | Twenty `enc` 0 items count as 1 ENC by counting objects | A bundle counts as its `count` (RWP4, RWQ3) | `world/encumbrance.py:50`, `:180` |
| Y5 | A creature's death creates an empty corpse and deletes the creature, whose contents Evennia sends home | Projectiles the creature carries go into the corpse first (RWP19, RWQ15) | `typeclasses/creatures.py:61–112`; `evennia/objects/objects.py:1538`, `:1579` (6.1.0) |
| Y6 | Rooms have no distance of any kind | Rooms have an authored span; the six seeded rooms get one (RWP7) | `world/seed_data.py:81–144` |

Unchanged: the hunt's claim (`commands/hunting_commands.py:84–89`) and its 30 s cooldown (`:26`, `:106`); harvest and its templates; and the corpse's `crumble`, which deletes what a body holds (`typeclasses/corpse.py:166`) — arrows left in a body past its time are lost with it, a sink MUME's players know well (§2.2).

---

## 7. Launchers, ammunition and bundles

**RWP1 — `Launcher`.** A mixin beside `DurableObject` (`typeclasses/durable.py:31`) for the bow, the sling and later the staff sling: `ranged_category`, `range_m`, `load_beats`, `damage`, `damage_mod`, `str_min`, `dex_min`, `missile_size` and `ammo_kind`, all from p. 109; state `loaded`, held in `ndb` (RWP17).

**RWP2 — `Ammunition`.** A tag `ammo_kind` (arrow, bullet) and `head` (wood, bone, clay; later flint and metal), `range_mult`, `damage_bonus`, `break_chance` and `maker`.

**RWP3 — `Throwable`.** For the spear and the javelin, later the dagger and the hatchet: `range_m` and `damage`; a throw sends the object itself, which then follows the projectile's fate (§10).

**RWP4 — One bundle, not one object per projectile.** A bundle is one object with a `count`, as Storage's bins hold counts (Storage DG3, DP9) and Project Gorgon makes arrows by the hundred (§2.5). Twenty arrows per hunter and ten hunters would otherwise be hundreds of rows, each shot a move or a delete, each `get arrow` a multimatch.

- **Merge** on receive when prototype, `head`, quality and `maker` match, through the one receive path (`receive_or_set_down`, `typeclasses/characters.py:1624`); otherwise two bundles stand side by side.
- **Split** on `drop 5 arrows` and `give 5 arrows to X`, in the same synchronous call. Barter moves objects by assignment, which runs no hook, so a part of a bundle is split off before it is offered.
- **Weight** counts the `count`, not the object (Y4, RWQ3).

**RWP5 — Quivers and pouches are worn containers.** A quiver (arrows) and a bullet pouch (sling) are `Container`s with a small ENC capacity, worn on the body; the shipped rules hold — no nesting, `put` only into containers (`typeclasses/containers.py:44`). There is no ammunition slot: ammunition of the launcher's kind is drawn from a worn container first, then from the inventory (§2.5), and a bundle in a backpack costs time (RWQ4).

**RWP6 — The craft makes bundles.** `SlingBulletRecipe` makes one bullet per lump and says its batch size waits for the mechanic that uses it (`world/recipes.py:606–608`). Legend prices bullets in tens (p. 110). The yield per lump, and every arrow recipe, is the bowyery & fletching note's.

---

## 8. Range in a room-based world

**RWP7 — Distance belongs to the encounter, not the room.** Each shooter–target pair has a distance: close, open or far. A room's authored span — `tight` (indoors, dense wood), `open` (a clearing, the meadow, the brook) or `wide` (open plain, a lake shore), `open` when unset — sets only the distance an encounter starts at, as DragonRealms starts indoor fights at pole range and outdoor ones at missile range (§2.1). Moving the distance (advance, retreat) is Stage 5's. The distance lives in `ndb` on the encounter, never on the room, so two hunters in one meadow can stand at different distances from their quarry.

**RWP8 — The stalk sets the distance in a hunt.** Hunting TP7 already gives the shot a term from the stalk's tier. The same tier says how far the quarry stands: *unseen and close* puts it at close range whatever the room; a poor stalk leaves it at the room's starting distance. Stalking well is how a javelin hunter gets a throw at all.

| Distance | Stands for | Short bow (80 m) | Sling (200 m) | Javelin (30 m) | Improvised throw |
|---|---|---|---|---|---|
| Close | up to about 10 m | effective | effective | effective | by STR − ENC (p. 47) |
| Open | up to about 50 m | effective | effective | beyond effective | out of range |
| Far | up to about 200 m | beyond effective | effective | out of range | out of range |

**RWP9 — Beyond effective range costs −20 %; past maximum the shot is refused** before anything is spent (RWP-L4, RWQ5).

**RWP10 — Shots between rooms wait for Stage 5.** An exit could be authored as a sightline (`db.sightline`) for shots into the next room, one distance step beyond that room's span. Aardwolf and MUME show what it invites: shoot from outside, step back, repeat — kiting a target that cannot reach the shooter (§2.3). When it comes, the target learns where the shot came from and the haven blocks it (Comfort EP9, EP10; RWQ13).

**RWP11 — Stage 6 replaces the bands with distance.** XYZGrid and wilderness rooms carry coordinates (Evennia Reference §14), so distance becomes arithmetic and the table above the fallback for authored rooms. Spans are room data and never stored on a projectile, so nothing migrates.

---

## 9. The shot

**RWP12 — `load`** is a timed action of the launcher's `load_beats` (sling 1, short bow 1, staff sling 3). It needs the launcher in hand and ammunition of its kind carried, and only marks the launcher loaded.

**RWP13 — `aim`** adds the shooter's critical range, one tenth of the skill rounded up, per beat (p. 140), up to a cap (RWQ10) — as DragonRealms' aim rises until the game says more will not help (§2.1). Moving, starting another timed action or being targeted ends it.

**RWP14 — One modifier function.** `shot_modifiers()` sums p. 141's groups (RWP-L6), the range term (RWP9), aim and `physical_modifier()` (`typeclasses/characters.py:603`, the −20 % overload). It returns each term with a label, so the shooter is told why a shot was hard: *the wind gusts across the meadow*. Two of its groups read systems that do not exist yet: wind (no wind in code — `WEATHER_STATES` is clear, raining, snowing, foggy, `world/weather.py:23`; Hunting TP-W1 proposes one) and light (no light level in code; Light LP1 and LP10 propose `light_modifier()`). Until they ship, those terms are zero.

**RWP15 — `throw <item> at <target>`** uses the weapon's own skill for spears and javelins and Athletics for anything improvised (p. 47). The thrown object leaves the hand and follows §10.

**RWP16 — Release** goes through `shoot <target>`, or `hunt <animal>` with a loaded launcher, and starts the shot's cooldown on `caller.cooldowns` as `hunt` does today. Before Stage 5 only creatures can be targeted.

**RWP17 — Spend at release.** `load` takes nothing; the resolver lowers the bundle's count in the same call that rolls the shot. A reload of the server clears the loaded mark and the aim (both `ndb`) and never costs an arrow.

**RWP18 — Re-check at release.** Launcher still in hand, ammunition still carried, target still in reach and alive, the timed action still current (`world/timed_actions.py:168`). Any failure cancels the shot for free. Being hit while loading or aiming cancels it too, as in MUME (§2.2), once anything can hit a character (Stage 5).

---

## 10. Breakage, loss and recovery

**RWP19 — What a shot does to its projectile** (RWP-L5):

- **A hit** puts the projectile in the target. On a creature it is held with the quarry and goes into the corpse on death (Y5); it breaks on a roll against its `break_chance`, more often on a killing shot (§2.2). A wounded quarry that bolts (Hunting TP12) carries the arrow away: it is found where the quarry falls, or lost with the trail. On a character (Stage 5) it stays in the wound until removed.
- **A miss** joins the room's spent pile unless the room loses it on a roll against its `loss_chance` — high over water, in a `wide` room and in darkness, low on bare ground.
- **Skill spends fewer arrows.** Both chances fall as the shooter's skill rises (§2.2, §2.6). A skilled archer is cheaper to keep supplied, which makes skill an economic lever and not only a better roll.
- **A sun-dried clay bullet that hits always crumbles** — the cheap, honest ammunition. A fired bullet breaks less often, after the kiln (Pottery PQ16).
- **Spent piles age lazily.** One pile per room and kind, with a timestamp, swept when the room is read, as corpses are (`typeclasses/rooms.py:358`). Rain, snow and passing feet bury it; after a calibrated span it is gone.

**RWP20 — `recover` is a search, not a pick-up.** One command gathers what the room holds — the spent pile and the projectiles in any corpse there — into the right worn container, as MUME's `recover` does; nothing is taken from a living target, and a body's own locks hold (a player's corpse in its grace window, `typeclasses/corpse.py:279–293`). Finding the pile is a Perception test whose difficulty rises with grass, snow, darkness and the room's span; a success returns part of the pile at a time. A spent pile is never listed by `look`, only hinted at. Anyone may search, as with MUME's `recover all` (RWQ9).

**RWP21 — The launcher wears.** A bow and a sling take wear on use (`DurableObject.apply_wear`, `typeclasses/durable.py:43`). A ranged fumble (p. 131) can snap the string: the bow keeps its condition but cannot shoot until restrung with twine, a `repair` that reads `db.repair_materials` (`commands/repair_commands.py:121`).

**RWP22 — Arrows wait for a feather.** Fletching needs feathers, and the feather is an orphan with no source until a bird can be harvested (`world/material_registry.py:231–235`). Legend's wood-headed arrow (p. 110) is still fletched. The sling needs neither, which is why it leads the layers (§16, RWQ6).

---

## 11. Hunting and the world the shot reads

| System | What the shot reads or writes | Seam |
|---|---|---|
| Hunting | Keeps `opposed_check(hunting, flee_skill)`; adds the launcher's terms, spends at release, takes distance from the stalk (RWP8) | `commands/hunting_commands.py:96–106`; Hunting TP7, TP12 |
| Creatures | Target size from `siz` — −10 % per SIZ under 5 (p. 141) | `typeclasses/creatures.py:48` (default 8) |
| Corpse | Holds embedded projectiles; `recover` reads it; `crumble` deletes them with the body | `typeclasses/corpse.py:166` |
| Weather | Rain and snow raise loss and burial; wind once it exists | `world/weather.py:23`; Hunting TP-W1 |
| Light | Partial darkness −20 %, darkness −40 % once a light level exists | Light LP1, LP10 |
| Encumbrance | Overloaded −20 % on the roll; bundles weigh by count | `typeclasses/characters.py:603`; `world/encumbrance.py:63` |
| Fishing | The fishing arrow, +10 % to Survival (p. 110) | Fishing FP3 |
| Activity log | A shot that spends and a recovery are economic events (RWQ7) | `world/activity_log.py:60` |

**RWP23 — What `hunt` does without a launcher.** Today a won `hunt` kills with bare hands. Proposed: a weaponless hunt is possible only at close distance after a good stalk, with a penalty; with a launcher it reaches as far as the launcher does. It gives the sling a reason to exist on day one without taking the hunt from anyone (Y1, RWQ8).

**RWP24 — Damage waits.** Before Stage 5 the launcher changes the odds, never hit points (RWP-L7). Its dice, Impale and Stun Location enter with General HP and Critical Wounds.

**RWP25 — The rabbit and the size term.** Read as written, a SIZ 2 rabbit costs −30 % to hit, which would make the shipped quarry a poor target for any launcher. The rabbit's SIZ is still open (Hunting TQ6); the size term is calibrated with it, not after.

---

## 12. The shape in Evennia

**RWP26 — One pure module owns the shot.** `world/ranged.py`: `shot_modifiers()`, `resolve_shot()` and the count writes (RWG4), over `opposed_check` (`world/skillcheck.py:127`). It imports no command and can be tested without the database: every p. 141 group, the within-group rule, the distances and the aim cap.

**RWP27 — Thin commands.** `load`, `aim`, `shoot`, `throw` and `recover` start timed actions or call the resolver; `hunt` gains the launcher path. In-game protocols start with `inventory`, as the Testing Reference asks.

---

## 13. Economy

Ammunition is the steadiest sink PolishedWorld can have: every shot either breaks, loses or returns its projectile, and the losses fall on the materials that already have sources.

| Material | Source today | New sink | Ready? |
|---|---|---|---|
| Clay | the clay bank at the Brook (`world/prototypes.py:447–461`) | bullets that crumble | yes |
| Leather | `LeatherRecipe` | sling, quiver, pouch | yes |
| Twine | plant fibre | bowstrings, restringing | yes |
| Stick, wood | deadfalls, trees | shafts, wood-headed arrows | yes |
| Bone | creature harvest | bone heads | yes |
| Feather | none — bird harvest is DATA (`world/material_registry.py:231`) | fletching | blocked on a bird |
| Flint | the flint scatter | knapped heads (series queue) | later |

**Services it creates:** the fletcher who sells bundles, the bowyer who strings and restrings, the hunter who sells arrows found in the meadow, and the one who finds other people's.

**Logging:** whether a shot and a recovery are new activity-log kinds or fields on `consume` and `gather` is decided with Hunting TQ10 (RWQ7).

---

## 14. Multiplayer and server load

A shot is safe when it reads and writes in one synchronous call at release; Evennia runs commands one at a time on the reactor, so the races are across time, not threads.

- **Counted twice:** a hunter loads, then gives the bundle away — nothing was taken at load (RWP17), and release re-checks (RWP18).
- **Two hunters, one quarry:** the shipped claim refuses the second (`commands/hunting_commands.py:84–89`); `at_death`'s pk check is the second line.
- **Two players, one pile:** `recover` lowers the pile's count and deletes it at zero in the same call; the second finds what is left.
- **Bundles that should merge after a barter:** assignment runs no hook, so two bundles stand until the next receive (RWP4).
- **Aim stacked forever:** capped, and ended by moving, another timed action or being targeted (RWP13).
- **Load:** no script per projectile and no ticker per pile; a shot is one roll, a few attribute reads, one count write and one room message. One spent pile per room and kind keeps a busy meadow at a few objects.

---

## 15. Immersion extras

- **Fletching by the fire** — the evening's work before the morning's hunt; the Comfort note's good evening has a task in it.
- **The maker's line** — a recovered bundle says whose hands made it, as a garment does (Textiles WP9): finding someone else's arrows in the meadow is a small story.
- **The signal arrow** — Legend's whistling arrow (p. 110), heard far off; a call for help before there is any other.
- **Practice butts** — a straw butt at the clearing, after MUME's archery targets: arrows that never break there, and a place to learn the commands.

---

## 16. Layers — a suggested order

1. **Now — this document.** Docs only.
2. **Slice 1 — the sling.** No new material: RWP1, RWP2, RWP4, RWP5, RWP7, RWP8, RWP12–RWP14, RWP16–RWP20, RWP23, RWP26, RWP27 and rows Y1–Y6. The hunting shot is not combat (RWG5), so it can ship before Stage 5; when is the roadmap's to decide.
3. **Slice 2 — arrows and the bowyer's kit**, with *bowyery & fletching\**: RWP6, RWP21, RWP22.
4. **Slice 3 — throwing**: RWP3, RWP15.
5. **At Stage 5:** Combat Styles and the character's Evade, shields and missile size, damage dice (RWP24), firing into a crowd, shots between rooms with the haven (RWP10), anatomy (RWQ14).
6. **At Stage 6:** coordinates replace the bands (RWP11).

**Prerequisites for slice 1:** RWQ1, RWQ3, RWQ5, RWQ8 and RWQ15 locked. **Not prerequisites:** the webclient, Stage 4.6, wind and light (their terms read zero until they ship).

---

## 17. Seams in today's code (read at `fac8e2b`; Evennia at `v6.1.0`)

| Need | Seam | Where |
|---|---|---|
| The shot | claim, roll, cooldown | `commands/hunting_commands.py:26`, `:84–89`, `:96–106` |
| The escape | flee or delete | `commands/hunting_commands.py:152` |
| Creatures | death, corpse, size | `typeclasses/creatures.py:48`, `:61–112` |
| Corpses | crumble; grace lock | `typeclasses/corpse.py:166`, `:279–293` |
| Lazy sweep | room receive | `typeclasses/rooms.py:358` |
| Rolls | skill and opposed | `world/skillcheck.py:58`, `:127` |
| Timed actions | busy, start, current, claim, interrupt | `world/timed_actions.py:89`, `:107`, `:168`, `:198`, `:229` |
| Cooldowns | character handler | `typeclasses/characters.py:155` |
| Overload | modifier; penalty | `typeclasses/characters.py:603`; `world/encumbrance.py:63` |
| Weight | small items; receiving | `world/encumbrance.py:50`, `:180` |
| Receiving | one path | `typeclasses/characters.py:1624` |
| Damage | chokepoint | `typeclasses/characters.py:1184` |
| Skills | the five; improvable set | `world/chargen.py:59–65`; `typeclasses/characters.py:892` |
| Containers | class; refusal | `typeclasses/containers.py:32`, `:44` |
| Wear and repair | durable; materials | `typeclasses/durable.py:31`, `:43`; `commands/repair_commands.py:121` |
| Goods | bullet, sling, spear, bow; clay bank | `world/prototypes.py:463–473`, `:802–813`, `:830–855`, `:447–461` |
| Recipes | sling, bow, bullet | `world/recipes.py:421–430`, `:457–466`, `:603–622` |
| Registry | feather | `world/material_registry.py:231–235` |
| Weather | states | `world/weather.py:23` |
| Log | kinds | `world/activity_log.py:60` |
| Seeded rooms | six | `world/seed_data.py:81–144` |
| Engine | delete clears contents home | `evennia/objects/objects.py:1348`, `:1538`, `:1579` |
| Contribs | throwable; cooldowns | `evennia/contrib/tutorials/evadventure/objects.py:270`; `evennia/contrib/game_systems/cooldowns/cooldowns.py:62` |

Re-read every row against live source before a decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **RWQ1** — Which skill takes the shot before Stage 5? *Leaning (chat, 2026-11-10): `hunting` (RWP-L1); Stage 5 introduces styles once, for melee and missiles together.*
- **RWQ2** — A bundle or one object per projectile? *Leaning (chat): a bundle (RWP4).*
- **RWQ3** — Does weight count a bundle's `count` (Y4)? *Leaning (chat): yes, with a test that twenty arrows in one bundle weigh what twenty loose ones would.*
- **RWQ4** — Ammunition drawn from a backpack: a penalty, or one extra load beat? *Leaning (chat): one extra beat.*
- **RWQ5** — Beyond effective range: −20 %, or nothing? *Leaning (chat): −20 %, flagged as not Legend; refused past maximum (RWP9).*
- **RWQ6** — Arrows before birds: wait for a feather source, or ship an unfletched training arrow with a penalty? *Leaning (chat): wait, and let the sling carry slice 1 (RWP22).*
- **RWQ7** — Activity log: new kinds for a shot and a recovery, or fields on `consume` and `gather`? *Decide with Hunting TQ10.*
- **RWQ8** — The weaponless `hunt` (Y1, RWP23): as today, or only at close distance after a good stalk? *Leaning (chat): close only.*
- **RWQ9** — Other people's arrows: anyone may recover them, or only the shooter for a grace window? *Leaning (chat): anyone, with the maker's line on the bundle (§15).*
- **RWQ10** — How long is a beat, and how many beats of aim? *Leaning (chat): one calibration constant now, set with Stage 5's cooldown model.*
- **RWQ11** — Do fog or night shrink a room's span? *Leaning (chat): no; the visibility terms carry it, and span stays authored data.*
- **RWQ12** — One note or two? *Leaning (chat): this note owns the mechanic; the queue's* bowyery & fletching\* *owns the crafts (arrows, drying, yields, bows by wood).*
- **RWQ13** — Shots between rooms (RWP10): never, at Stage 5 with the haven and a target that comes looking, or earlier? *Leaning (chat): Stage 5, after the haven is decided.*
- **RWQ14** — Does knowing an animal, from hunting and harvesting it, add to a shot, as Project Gorgon's anatomy feeds criticals (§2.5)? *Leaning (chat): no new term before Stage 5's criticals.*
- **RWQ15** — Found while writing: `delete()` clears an object's contents to their home (`evennia/objects/objects.py:1579`), and a quarry is deleted when it dies (`typeclasses/creatures.py:112`) and when it escapes with no exit (Hunting D5), so a projectile held inside it would land in its home. *Leaning: no projectile ever lives inside a creature; the quarry carries a count (`db.carried_projectiles`), turned into objects in the corpse at death and into the room's spent pile when it is deleted on escape — with a test for each path.*
- **RWQ16** — The letter. Every single letter is taken by a series note or a departure row, or reads as a Legend or engine word (AP, HP, MP — Legend's Magic Points — SP, XP; IP and OQ are taken elsewhere). *Leaning: the stem RW, for ranged weapons (RWP/RWQ/RWG, 0 hits across `docs/`, `world/`, `commands/`, `typeclasses/`, `server/`); departure rows Y, which had no hits.*

---

## 19. Considered and not proposed

- **An ammunition slot.** Too fiddly and too narrow (§2.5); a worn quiver does its work (RWP5).
- **Projectiles in flight as objects or scripts.** Nothing flies and nothing ticks (RWG3).
- **One object per arrow.** Hundreds of rows and a multimatch on every `get` (RWP4).
- **Ammunition that never breaks** (MUME's magical arrows). Every projectile needs a sink (RWG1).
- **Sling stones searched from the ground** (MUME). The stone bullet was struck in the alpha content epic, and a free source has no maker (pillar 1).
- **Shots between rooms from the first slice** (Aardwolf). Kiting before there is a haven (RWP10).
- **A reaction-time aiming minigame.** Skill is in reading (RWG6).
- **DragonRealms' balance and position layer.** Stage 5's to weigh, if at all.
- **An NPC fletcher or arrow shop.** Pillar 1.
