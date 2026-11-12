# PolishedWorld Tone Guide

> **Rev 1 · 2026-11-12** — first version, docs only, with roadmap Rev 73, README Rev 53, `docs/PolishedWorld_Core_Instructions.md` Rev 7 and `AGENTS.md` Rev 10. Written from a tone chat in which Adam settled on *cozy dark hard fantasy* (sometimes called grimcozy) as the name for what the roadmap's North star line already says — *hard roads, warm hearths*. This guide is the writing and review half of that line; its mechanics stay in `docs/system_designs/PolishedWorld_Comfort_Design.md`, and where the two meet this guide defers to it. **Nothing mechanical is decided here.**
> **Canonical:** `docs/PolishedWorld_Tone_Guide.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** reference (tone and writing).
**Home:** `docs/roadmap.md`, *North star*, the tone line (Comfort EP1).
**When to read:** before writing any room, item, creature or message text; at the start of every decomposition, beside Comfort EP2's three questions; when reviewing content an agent wrote (`AGENTS.md` §3, `desc` style).
**Sibling:** `docs/PolishedWorld_Art_Style_Guide.md` is this guide for pixels.

---

## 1. Core statement

**The world is indifferent; warmth is something players make for each other.**

PolishedWorld is cozy dark hard fantasy. The road is cold, hungry and lethal, and that is why a hot meal, a barred door and a shared fire feel earned. Comfort is never free and never sold by the game: it is built, cooked, mended and shared by players (Comfort EG6, pillar 1).

The working image for every system and every line of text is *the hearth against the dark* — the roadmap's *hard roads, warm hearths*. Like that line, this is a lens, not a fifth pillar: no epic is justified by tone, but every epic is read through it.

---

## 2. Three strands

Every piece of content leans on at least two of these. They are strands of one tone, not design pillars; the four pillars stay the roadmap's.

### 2.1 Cozy — tactile, personal, small

Comfort lives in physical acts: brewing tea, cooking over a fire, mending worn leather, oiling a blade. Stakes are personal and local: a settlement's winter stores, a friend's broken leg, a roof before the first snow. Nobody saves the world; people keep each other alive.

### 2.2 Dark — the outside does not care

The wilderness is bleak and unforgiving. Monsters are frightening, not loot. Resources are scarce and seasons punish the unprepared. Those who rule are corrupt, distant or both, and the law protects whoever can pay for it — lore and texture today; no law system exists. Morality is grey: hunger makes honest people do dishonest things.

### 2.3 Hard — rules with a price

The world follows rules players can learn, plan around and be rewarded for knowing. Magic, when it comes (Stage 7), follows strict rules and always costs something — Legend's Magic Points, blood, ingredients, time or risk. It cannot solve every problem, and using it should feel like a decision.

**Without Cozy** the tone becomes grimdark misery. **Without Dark** it becomes a farming sim. **Without Hard** it becomes whimsy, and comfort loses its value.

---

## 3. Refuges and routines

The Cozy strand takes two concrete forms in play: places to shelter and habits that keep people alive.

### 3.1 Refuges

The heart of play is the place one comes back to: a temple, a tavern's common room, a workshop, later a home. What makes it warm is players' work — the fire is someone's wood, the meal someone's cooking (Comfort EG6). Two kinds are designed, neither built:

- **Havens** — a few authored rooms, flagged by staff, where bodies are safe and goods set down are not (Comfort EP9–EP13). The Old Temple first.
- **Homes** — raised from player-made materials and kept up in goods (`docs/system_designs/PolishedWorld_Housing_Design.md`).

Upkeep **shows, never calls** (Comfort EP3): one comes home to a cold hearth and a thin roof, never to a ruin that fell in a moment, and nothing cozy sends a message to someone who is elsewhere.

### 3.2 Mundane routines

Cooking, crafting, mending and maintaining gear are core play, not filler between fights. Players should be able to spend real time on them and enjoy it, and they are where found families form: the one who always cooks, the one who sharpens everyone's blades.

Maintenance is already a sink: tools and garments wear on the shared `condition` axis and are mended with `repair` (Stage 2, Components B and D), which keeps crafters in demand.

---

## 4. Tone in the game systems

The rule: the road takes, the hearth gives back — and the hearth gives **time, not power**. Comfort lengthens a good state and never strengthens one (Comfort EG3, EP5). *Built* means on `main` today; everything else is a design note's proposal.

| System | The road (what it takes) | The hearth (what it gives back) | Status |
| --- | --- | --- | --- |
| Survival | Hunger, thirst and fatigue drain everywhere | Food and drink answer them; a good state begun in comfort lasts longer | Gauges built; comfort read proposed (Comfort EP4–EP5) |
| Economy | No NPC vendors; nothing exists unless someone made it | Every meal, cloak and door is a gift or a trade between players | Built (pillar 1) |
| Wear and mending | Tools and garments wear with use | A skilled player mends them | Built (`condition`, `repair`) |
| Refuges | Outside a haven nothing guards you | A haven guards bodies; a home keeps the weather out | Proposed (Comfort EP9–EP13, Housing) |
| Seasons and weather | Winter is the main antagonist; storms punish the unprepared | Shelter, fire and stores turn preparation into safety | Weather and seasons built; Temperature Design proposed |
| Rooms | The wild described as cold and wide | Interiors written warm, with the weather heard on the roof | Room states built (`typeclasses/rooms.py`); conventions Comfort EP16, EP19 |
| Magic | Costs and can fail | Small, practical rites: warding a door, blessing a hearth | Not built (Stage 7) |
| Wounds and healing | Legend's hit locations make harm lasting | Healing takes time, care and someone who stays | Stage 5; natural healing in Stage 4.6 |
| Company | Alone, nobody is coming to help | Company is one of comfort's six sources | Proposed (Comfort EP4, §12) |

---

## 5. Writing style

Write what a cold, tired person would notice. Concrete things, few adjectives, no epic language.

- **Lead with the senses.** Smell, temperature, sound and texture before sight: smoke, wet wool, frost on iron.
- **Contrast stays outside the window.** A warm room mentions the weather it keeps out; the harshness is heard from inside, never let in (Comfort EG2). Indoor descriptions can carry the weather with the room states that exist today: `$state(raining, Rain drums on the roof.)` (Comfort EP16).
- **Small, specific objects.** A chipped bowl, a patched blanket, a tallow candle — not "a cozy room". Plenty, never opulence (Comfort EP19).
- **Present tense, the thing itself.** A description describes the place or object, not the viewer (`AGENTS.md` §3, `desc` style). *You* belongs to messages about what the character does: the threshold line, a craft's result.
- **Understate danger.** Tracks in the mud frighten more than "a terrifying beast lurks here". Danger in echoes is far off (Comfort EP18).
- **Show human traces.** Signs that someone made, mended or left something. The economy should be visible in the text.
- **Short.** Three to five sentences for a room. Players read them many times.

### 5.1 Example — one room, cold and warm

Illustrative only: no fire state exists on rooms today, and this is not a proposal for one.

> Wind pushes snow through the gaps in the shutters. The hearth holds only grey ash and the smell of old smoke. Frost has crept along the inside of the door.

> The hearth crackles, throwing long shadows across the beams. The room smells of woodsmoke, wet wool and something simmering in the pot. Outside, the wind worries at the shutters, but it cannot get in.

### 5.2 Do and don't

| Don't | Do |
| --- | --- |
| A cozy, warm tavern full of happy people. | Steam rises from a row of drying boots by the fire. Someone laughs, low, over a dice game. |
| A dark and evil forest filled with horrors. | The pines stand too close together. Something has stripped the bark from one trunk, high up. |
| You feel safe here. | The bar across the door is new oak, still pale where it was cut. |
| An ancient, powerful magic glows. | The ward-marks on the lintel are fresh, and the hand that painted them was shaking. |

---

## 6. Pacing and agency

Hard consequences, unhurried pace. Danger is real, but the game never rushes the player.

- **Deliberate, not frantic.** Crafting and resting are timed acts (Epic A), and the routines that follow them should be too: lingered over, never reflex tests.
- **Consequences stick, but not in a moment.** Wounds, wear and an unprepared winter matter; nothing is lost in an instant while its owner is away (Farming and Cooking designs).
- **Stakes stay personal.** Large threats exist, but players meet them as weather, not as quests to save the world.
- **Grounded choices.** Players decide what to share, what to hoard and whom to trust. Moral grey comes from scarcity, not from scripted villains.
- **Quiet defiance.** Lighting a fire in a hostile land is an act of resistance. Small acts of care should be visible and recognised.

---

## 7. What breaks the tone

- **Survival as a chore tax.** A drain with no satisfying answer is grind, not atmosphere.
- **Upkeep that calls.** Timers and messages that demand attention from elsewhere (Comfort EP3).
- **Comfort as power.** A bonus to skills, rolls or rates turns the hearth into a queue (Comfort EG3, §19).
- **Edgelord darkness.** Gore and cruelty for shock. Dark here means indifferent and scarce, not sadistic.
- **Misery without relief.** If no hearth is reachable, players quit rather than persevere.
- **Whimsy and free comfort.** Magic that solves problems for free, or safety simply given, removes the value of everything players build.
- **The chosen one.** Prophecies and world-saving pull focus from personal stakes.
- **Meta voice.** Jokes, pop culture and game words in descriptive text ("You gained +5 warmth!"). Numbers belong in `status` and `sheet`, not in prose.

---

## 8. Review checklist

Run new rooms, items, creatures and systems through these before committing.

- [ ] Comfort EP2's three questions are answered: where is the danger, where is the refuge, what does the threshold say?
- [ ] It leans on at least two strands: Cozy, Dark, Hard.
- [ ] If it takes something from the player, a hearth gives something back — time, not power.
- [ ] Comfort comes from players or their work, never from the world for free.
- [ ] It feeds a refuge or a routine players will want to return to.
- [ ] Any magic involved has a clear cost and a way to fail.
- [ ] The stakes are personal or local.
- [ ] The text leads with senses and concrete objects, in three to five sentences.
- [ ] It is free of meta language, numbers in prose and shock-value cruelty.
