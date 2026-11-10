# PolishedWorld — Names, Recognition & Introductions Design Notes (strangers by description, the short description, recog and introduce, every name through a looker, the statue and the body, finding people)

> **Rev 1 · 2026-11-10** — first version, docs only, with roadmap Rev 68, BACKLOG Rev 95, README Rev 45 and the series handoff `docs/system_designs/HANDOFF.md` Rev 8. Written from a design chat, the eighteenth note in the one-system series and the one decided next (roadmap Rev 67, decision log *Order after the webclient*, amended): it takes in the queue's entry *names, recognition & introductions\** and BACKLOG *Strangers by description — `rpg/rpsystem`*, with Evennia's `rpg/rpsystem` contrib read at the pinned `v6.1.0` as the tool. **Nothing here is locked.** Every numbered item is a proposal (UP…), a goal (UG…) or an open question (UQ…); the letter is *U*, for the unknown, free across `docs/`, `world/`, `commands/`, `typeclasses/` and `server/` when checked; this document's departure rows are K1–K9 — *K* for *ken*, to know, free when checked (Temperature's KP… shares the letter, not the shape). Adam answered the chat's proposal with a bare "kör", so its five questions are recorded with the chat's leanings (UQ1–UQ5), and the scope leaning he took on 2026-11-10 is UQ11. Three things were found while writing that the chat did not weigh, recorded rather than decided: `craft` finds its ingredients through the same search the contrib replaces, so the multimatch change reaches crafting as well as hunting (UQ6); the contrib writes a recog into an Attribute that only its own creation hook makes, so a character created before the contrib loses every recog silently (UQ7); and account-level commands name accounts, which the chat did not list (UQ8). Prior art was read on 2026-11-10; code seams were read against `main` at `4422b65` (Evennia 6.1.0) and `feature/webclient` at `dda7156`.
> **Canonical:** `docs/system_designs/PolishedWorld_Names_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before any decomposition).
**Home:** `docs/roadmap.md`, Stage 5, the dated *Strangers* line (Rev 67, annotated Rev 68): this is that stage's first slice of code, after its design session and before combat code. `docs/BACKLOG.md`, *Strangers by description — `rpg/rpsystem`* (SCHEDULED; annotated Rev 95), and *A screen-reader pass* (annotated Rev 95, §2.1).
**When to read:** at Stage 5's design session, which decides targeting by description and recog with this document (UP17, UP18); when that slice is decomposed; when the newcomer's economy note is written — it reads how a newcomer learns names here (UP23); with *barbers, tattoos & appearance\** (disguise and masks, UP9), *languages & tongues\** (`rplanguage`, UP21), *law/crime/bounties* (a description as evidence, UG4), *heraldry, banners & signs\** and *letters & notice boards* (letters of introduction, UQ4) from the design-series queue; when *Automated test players* gives an agent a body (UP24); when Homunculus JQ17 is decided (UP25).

---

## 1. The idea in one paragraph

You come in out of the rain, and by the fire sits *a weathered woman in a wool cloak*. That is all you know of her, and all the game will tell you. She has a name, but it is hers to give: if she says it, you can keep it, and from then on she is Maren to you — in the room, in her poses, in what she says, in the statue she becomes when she sleeps, and in the body you find if the road kills her. To the trapper who walks in after you, she is still the weathered woman, until she tells him too. Names are learned the way they are learned anywhere: by being told, by asking, by introducing yourself, and sometimes by being told a lie. A description is something you can describe to a third person — *the lanky, red-bearded man took it* — and it does not change on a whim, so it means something. The game never gives a name away on its owner's behalf: not in `who`, not in a statue, not on a corpse, not in a lesson. Strangeness is the point; illegibility is not — a name you know is short, and the game keeps it for you, so a player who reads the screen through a voice is not left behind.

---

## 2. Prior art

### 2.1 Armageddon — the lesson

Armageddon (roleplay required) is the lineage of the short description. A character is seen by a short phrase written at character creation — at most 35 characters, built on the pattern *the tall, muscular man* — which is also the set of keywords others type to reach them; it changes about as seldom as the main description, roughly once a real year, and hoods and face-wraps replace it while worn (chargen guide; *How do I create a Character?*, gdb 2011). There is no in-game way to attach a name to a description: players keep paper lists or client triggers.

**The lesson is the *Remember Me* thread (gdb, 2013).** A new player who reads the game through a screen reader asked for a server-side `remember`. Veterans answered that not knowing who is who is part of the game — the awkward moment of hailing a stranger by the wrong name — and that a client trigger does the job. The player's reply was that a screen reader must speak every word of a long description before it reaches what the person did or said, that leaving the game window to write a trigger means missing what happens in the room, and that client triggers break when two people share a description. The thread converged on limits rather than refusal: a hood, a face-wrap or a mask must defeat recognition; remembering happens only in the same room; a server-side memory keyed to the character, not to the text, does not break on identical descriptions. **Strangeness is the point; illegibility is not.** Evennia's `recog` is that server-side `remember` (keyed to the object, `rpsystem.py:836–837`), and the contrib's `enable_recog` lock (`:843`, set by its mask at `:1269`) is the hood. PolishedWorld takes both (UP5, UP9) and keeps descriptions short (UP1) — and the thread is why BACKLOG *A screen-reader pass* is annotated with this document.

### 2.2 Sindome — names shown, honour kept by people

Sindome (MOO) shows a name and a short description together, and says in its help that the displayed name is an out-of-character identifier: a character knows a name only when told it, and names are not unique. A disguised character shows as a described figure instead. The rule is kept by players and staff, not by code. **Taken:** a constrained vocabulary for the short description, chosen from menus (`@shortdesc change`), which keeps descriptions short and comparable (UP1). **Left:** names on screen with an honour rule — on a game run by one person with a few hours a week, a rule that needs policing is a rule that is not kept (§19).

### 2.3 Genesis and MUD-Dev — introduction versus naming

Genesis (fantasy) has the classic introduction system: you do not instinctively know a name, `introduce myself to all` tells everyone in the room, and `remember` keeps a list. A 2001 MUD-Dev thread names the split that matters here. In an **introduction system** the owner reveals the true name and the game substitutes it — you cannot lie with the command. In a **naming system** the viewer attaches whatever name they like — the listener's memory, which can be wrong or misled. The thread's example is the bluff: *hi, I'm Bob*, said by someone whose name is not Bob. **Taken:** both, separately — the contrib's `recog` is a naming system (a free label, bluffs possible), and a new `introduce` is a truthful introduction (UP5, UP6).

### 2.4 Haven & Hearth — the nearest genre

Haven & Hearth (a sandbox survival crafting game, the closest relative in this series) lets a player *memorize* another hearthling from a right-click, set a display name for them that only the memorizer sees, and add them as kin; kin colours then drive who may enter, take from or build on a claim. An heir can recover, at a shrine, the memories of everyone the ancestor had memorized. A parchment can carry a description of a kinsman, introducing someone the reader has never met (ringofbrodgar.com, *Glossary — Kith & Kin*; *Description of Player*). **Taken:** the per-viewer label (recog); the written introduction as a player-made object, for *letters & notice boards* (UQ4). **Left for later notes:** recognition as a permission list (law, settlements & commons); inheriting memory (absence, upkeep & inheritance).

### 2.5 The tool — Evennia's `rpg/rpsystem` at `v6.1.0`

What the contrib is, read at the tag:

- **Short description.** `SdescHandler` (`rpsystem.py:660`) stores `_sdesc`; when none is set it **falls back to the key** (`:690`). Its character's creation hook sets *A normal person* (`:1567`). The `sdesc` command (`CmdSdesc`, `:976`) lets anyone change their own at any time.
- **Recog.** `RecogHandler` (`:754`) stores, on the viewer, a map from the seen object to a free label (`:836–837`), up to 60 characters. It is a naming system (§2.3). `recog <sdesc> as <name>` and `forget <name>` (`CmdRecog`, `:1123`); `forget` finds only someone in the same room (`:1191`).
- **Display.** `ContribRPCharacter.get_display_name(looker)` (`:1509`) shows the looker's recog, else the sdesc; `get_sdesc` (`:1583`), `process_sdesc`/`process_recog` (`:1612`, `:1653`) colour them. `ContribRPObject.get_display_characters`/`get_display_things` (`:1422`, `:1437`) list characters one per line with their pose.
- **Search.** `ContribRPObject.get_search_result` (`:1326`) replaces the default for every search with candidates: it matches sdescs and the searcher's recogs, and falls back to a key search only for Builders who matched nothing (`:1339`). `DefaultObject.search` calls it (`evennia/objects/objects.py:870`).
- **Speech and pose.** `say` and `emote` are replaced (`CmdSay` `:946`, `CmdEmote` `:903`); an emote names others by `/tall`, numbered `/1-tall` (`_NUM_SEP` `:190`, `_RE_OBJ_REF_START` `:208`). `pose` (`CmdPose`, `:1022`) sets a standing line, `is here.` by default (`:1323`), at most 60 characters with the sdesc (`:1114`).
- **Mask.** `mask <sdesc>` (`CmdMask`, `:1236`) is a command, not an item: it swaps the sdesc and locks `enable_recog` (`:1268–1269`).
- **Language.** `rplanguage.obfuscate_language` and `obfuscate_whisper` (`rplanguage.py:492`, `:592`) garble text by a level from 0.0 to 1.0; `process_language` only labels it by default.
- **Multimatch.** The contrib's README asks for `N-name` (`README.md:80–81`); Evennia's default is `name-N` (`settings_default.py:417`, `:425`).

---

## 3. Design goals

- **UG1 — A stranger is a description; a name is given in play.** Nobody learns a name from the interface — only from its owner, from someone else who knows it, or from a lie (§2.3).
- **UG2 — Strangeness is the point; illegibility is not.** A known name is short and kept by the game; descriptions are short; nothing requires a client trigger to play well (§2.1).
- **UG3 — What you know is yours, and the game tells no name its owner did not give.** Recog lives on the knower; no listing, statue, body, lesson or message gives a key away (§6).
- **UG4 — A description is evidence.** It is stable and changes only through the world — a barber, a disguise, a mask — so *the lanky, red-bearded man* means the same person tomorrow, and a witness can say so (law/crime/bounties).
- **UG5 — Every name goes through a looker.** One rule for every text that names a character: it is resolved per reader (UP10).
- **UG6 — Nothing ticks.** Recognition is a dictionary read when text is drawn; no memory decays, no roll repeats (UP-L1).

---

## 4. Legend alignment

**Rules as written:**

- **No rule for names or introductions** in the core rulebook. The nearest:
- **Insight** — p. 51 (INT+POW): reading a person's verbal and non-verbal behaviour to judge motive, lies and state of mind — motive, not identity.
- **Disguise** — p. 58 (INT+CHA): changing appearance, accent and persona, usually opposed by Insight or Perception when trying not to be identified; materials to hand modify it; a fumble fools no one.
- **Language** — pp. 60–61 (INT+CHA): separate skills per language; 50 % or more is fluent, likely with an accent if not native.
- **Language (Native)** — p. 19: gained at character creation at its starting value plus 50 %.
- **Family Reputation** — p. 27: how well known a family is, with contacts or enemies.
- **Automatic success and "no test required"** — p. 42.

**In code:** of these, only Perception exists (`typeclasses/characters.py:360`); Insight, Disguise, Influence and Language are not skills today.

**Departures and readings:**

- **UP-L1 — Recognition is not rolled.** Seeing someone you have named is routine (p. 42); a roll at every meeting would be noise and would make names flicker (§19). The contrib's recog is read, never tested.
- **UP-L2 — Disguise is the roll that matters, later.** When masks and disguise come (UP9), Legend's own contest is the model: Disguise against Insight or Perception, with the materials as modifiers (p. 58). Not in the first slice.
- **UP-L3 — Language sets the garble, later.** With *languages & tongues\**, a listener's Language skill could set `obfuscate_language`'s level — 50 % (fluent) as level 0.0 — and Language (Native) at +50 % at creation (p. 19) needs a chargen place. Not in the first slice (UP21).

---

## 5. The loop

1. **Meet.** A stranger is a short description with a pose: *a weathered woman in a wool cloak is warming her hands by the fire* (UP1, UP19).
2. **Hear.** A name is said — by its owner, by a friend, or as a lie (§2.3).
3. **Name.** `introduce` gives the true name to the room; `recog` attaches any name you choose (UP5, UP6).
4. **Know.** From then on the name is everywhere that person appears to you, and nowhere to anyone else (UP10–UP15).
5. **Lose.** `forget`; later, a mask or a disguise hides the person from your recognition (UP7, UP9).

---

## 6. Departures from shipped behaviour

Each row is a change to behaviour that `main` has today; each is a proposal, for Stage 5's first slice.

| # | Shipped today | Proposed | Where shipped |
|---|---|---|---|
| K1 | `who` lists every connected account by name to every player; with Evennia's default `AUTO_CREATE_CHARACTER_WITH_ACCOUNT = True` (not overridden), the account name is the character's name | Players see how many are abroad, not who; Builders see the full list (UP14, UQ1) | `evennia/commands/default/account.py:439`, the unprivileged table `:506–518`; `evennia/settings_default.py:802` (6.1.0) |
| K2 | A statue is *stone statue of* the name, its look says the key, and turning to stone and stirring announce the key to the room | The statue is named as the looker knows its sleeper; both messages resolve per reader (UP12) | `typeclasses/characters.py:488`, `:506`, `:518`, `:527` |
| K3 | A player's corpse is keyed *corpse of* its owner's key, which anyone sees | The body is named as the looker knows its owner (UP13) | `typeclasses/characters.py:1294` |
| K4 | Sixteen room messages name the acting character by key or by `get_display_name()` with no looker | Each names its actor through `$You()` or `mapping`, resolved per reader (UP10, UP11) | §17, *Room messages* |
| K5 | The teach offer tells the student to type `learn <recipe> from <teacher's key>` | It names the teacher as the student sees them, and the command takes that (UP15) | `commands/crafting_commands.py:1265` |
| K6 | Multimatch is `name-N` (`fiber-1`, `rabbit-1`) | `N-name` (`1-fiber`, `1-rabbit`); the Testing Reference's protocols change in the same slice (UP17, UQ6) | `evennia/settings_default.py:417`, `:425` (6.1.0); `docs/PolishedWorld_Testing_Reference.md:300`, `:315`, `:779`, `:992` |
| K7 | `say`, `emote` and `pose` are Evennia's defaults | The contrib's: emotes reference others by description (`/tall`), `say` speaks as an emote, poses stand (UP19, UP20) | `evennia/commands/default/general.py:724` (6.1.0) |
| K8 | A room lists characters as one line, *Characters:* and names separated by commas | One line per character, its description or recog and its pose; statues stay under *You see:* (UP16) | `typeclasses/rooms.py:301–315` |
| K9 | Character creation asks for characteristics and a profession, nothing about appearance | It gains one step that composes the short description (UP1) | `world/chargen_menu.py:299–337` |

Unchanged: arrivals and departures (Evennia's `announce_move_from`/`announce_move_to` already pass the mover through `mapping`, `evennia/objects/objects.py:2293`, `:2349` at 6.1.0); the worn-clothing line (`clothing.py:372`, already per looker); items, creatures and the sweeper, which are objects with keys, not characters (`typeclasses/creatures.py:34`, `typeclasses/npcs.py:68`); the activity log and staff logs, which are out of character.

---

## 7. The short description

**UP1 — Composed at character creation from a small vocabulary.** One new chargen step after the profession (K9) builds the description from three choices — a build (*lanky, broad, wiry, stout* …), one feature (*red-bearded, grey-eyed, scarred, freckled* …) and a noun chosen by sex and age (*man, woman, youth, crone* …) — giving *a lanky, red-bearded man*. At most 40 characters, under Armageddon's 35 plus an article (§2.1), below the contrib's 60 (`rpsystem.py:692`). The vocabulary is the decomposition's (UQ9); Builders may set free text.

**UP2 — No `sdesc` command for players.** The contrib's `CmdSdesc` (`:976`) is not added to the character's command set; a Builder-only form sets or corrects one. A description changes only through the world: a barber's work, a disguise, a mask (UG4, UP9).

**UP3 — The long description stays the player's.** `desc` is unchanged; a help line, after Armageddon's and Sindome's advice, asks for the body and bearing only — what anyone could see.

**UP4 — Identical descriptions are allowed.** They are rare with three choices, and they resolve the way the contrib already does: `1-lanky`, `2-lanky`, and a recog that is keyed to the person, not the text (§2.1). No uniqueness check.

---

## 8. Recog and introduce

**UP5 — `recog` and `forget`, from the contrib.** `recog <description> as <name>` attaches any label to a person in the room; it is the listener's memory and may be wrong or misled (§2.3). The label shows everywhere that person appears to the recogniser, and the recogniser can type it to reach them.

**UP6 — `introduce`, new and truthful.** `introduce` (to everyone in the room) or `introduce to <description>` speaks a line — *the weathered woman introduces herself as Maren* — and sets, for each hearer, a recog equal to the speaker's key. It cannot lie; a lie is a `say` and the listener's own `recog` (§2.3). Whether it sets the recog or only offers it is UQ2.

**UP7 — `forget` works anywhere.** The contrib's `forget` resolves the name against the room's contents (`:1191`), so a person who has left cannot be forgotten. A project version looks the label up in the recogniser's own list.

**UP8 — `recog` alone lists who you know**, as the contrib does — by your label and their current description.

**UP9 — Masks defeat recognition, later, as an item.** The contrib's mechanism is right — a lock that turns every recog of the wearer off (`enable_recog`, `:843`, `:1269`) — and its form is wrong for PolishedWorld: `mask` is a free command, and pillar 1 makes every face-covering someone's craft. The hood, the face-wrap and the mask are worn items that apply the lock and replace the description while worn, with *barbers, tattoos & appearance\** and Legend's Disguise (UP-L2). Not in the first slice; `CmdMask` is not added.

---

## 9. Every name through a looker

**UP10 — One rule.** Any text that names a character is resolved per reader: room messages through `msg_contents` with `$You()` or `mapping` — Evennia's own mechanism, which calls `get_display_name(looker=receiver)` for each receiver (`evennia/objects/objects.py:1051` at 6.1.0) — and messages to one person through `other.get_display_name(that_person)`, as `teach` and `pay` already do (`commands/crafting_commands.py:1258–1263`; `commands/currency_commands.py:264`). The sixteen room messages in §17 are converted in the slice (K4).

**UP11 — A test keeps it.** A unit test, on the precedent of `tests/test_recipe_sources.py`, fails when a `msg_contents` call in `commands/`, `typeclasses/` or `world/` interpolates a character's `.key`, or calls `get_display_name()` with no looker.

**UP12 — The statue (K2).** *A stone statue of a weathered woman* to a stranger, *a stone statue of Maren* to someone who knows her; its look shows the same; turning to stone and stirring are announced per reader. The statue still lists under *You see:* (`typeclasses/rooms.py:317`).

**UP13 — The body (K3).** A player corpse is created with a plain key (*corpse*) and names itself per looker from the owner it already stores (`attributes=[("owner", self.id)]`, `typeclasses/characters.py:1294–1296`): *the body of a weathered woman*, or *the body of Maren*. Finding a friend dead is then something the road can show you.

**UP14 — `who` (K1).** Players see a count — *seven travellers are abroad in the world* — and Builders see the full table. A list of the people you have named who are online (Haven & Hearth's kin candles, §2.4) would tell you where your friends are not; it is UQ1.

**UP15 — The lesson (K5).** The teach offer reads *Maren offers to teach you twine — type `learn twine from Maren`* to someone who knows her, and *from weathered* to someone who does not; the student's `learn` already finds the teacher through the search (`commands/crafting_commands.py:1450`), which matches both. Teaching is a reason to introduce yourself, not an introduction by itself.

---

## 10. Finding people, poses and speech

**UP16 — Only the character takes the contrib.** `Character(ObjectParent, ClothedCharacter, ContribRPCharacter)` linearises — `DefaultCharacter` before `ContribRPObject`, as in the contrib's own class (`rpsystem.py:1500`) — and the project's display overrides keep their places in front (`typeclasses/characters.py:518`, `:527`, `:540`). Rooms do not take `ContribRPRoom` (`:1492`, an empty subclass): the project's `get_display_characters` (`typeclasses/rooms.py:301`) lists one character per line with its pose, as the contrib's does (K8). Items do not take `ContribRPObject`; they keep their keys and aliases, which the contrib's search already falls back to for objects without a description (`rpsystem.py:335`, the candidate map).

**UP17 — `N-name` multimatch (K6).** The contrib's search hands `fiber-1` to its parser as one word and matches nothing, so for a player — not a Builder (`:1339`) — `get fiber-1` and `hunt rabbit-1` find nothing, while the error message still offers `fiber-1`. The settings the contrib's README gives (`SEARCH_MULTIMATCH_REGEX` and `SEARCH_MULTIMATCH_TEMPLATE`, `README.md:80–81`) go into `server/conf/settings.py`, and the Testing Reference's protocols change in the same slice — `craft twine from 1-fiber, 2-fiber, 3-fiber` (found while writing: `craft` searches its ingredients through the same method, `commands/crafting_commands.py:315`; UQ6).

**UP18 — Builders keep the key, carefully.** A Builder whose search matches no description falls back to the key (`rpsystem.py:1339`); one whose search happens to match a description gets that match. Test protocols and `@py` recipes target characters by dbref or by `evennia.search_object`, never by name (a gotcha for the Testing Reference).

**UP19 — Poses stand, and leave with you.** The contrib's `pose` sets a line that shows after the description in the room — *is sitting by the fire* — and `is here.` by default (`rpsystem.py:1323`). The contrib keeps the pose across a move; the project resets it in `at_post_move` (`typeclasses/characters.py:1470`), so nobody arrives *sitting by the fire* in a field.

**UP20 — `say` and `emote` are the contrib's.** An emote names others by description or recog (`/weathered`, `/Maren`), each reader seeing their own word for each person; `say` is spoken as an emote (`at_pre_say`, `rpsystem.py:1569`). Evennia's own `pose` (`general.py:724`) is replaced by the contrib's (K7).

**UP21 — Language, later.** `rplanguage` stays out of the first slice: the skill set has no Language, and the obfuscation needs a level per listener (UP-L3) and languages defined in the database (`add_language`, `rplanguage.py:522`). With *languages & tongues\**.

---

## 11. The webclient

**UP22 — Two pushes, nothing else.** The room panel is already built per viewer (`room_snapshot(room, viewer)`, `world/client_state.py:198` on `feature/webclient`, WC8), so names in it change by themselves. A `recog`, `forget` or `introduce` pushes `room` to each recogniser (`push`); a changed description or pose pushes the room to everyone in it (`push_room`). A recog only changes what one person sees, so it never pushes to the room.

---

## 12. Newcomers, agents and others

**UP23 — How a newcomer learns names.** A newcomer sees everyone as a description, which is what everyone sees of them. One first-steps hint (BACKLOG *First-steps hints*) fires the first time a newcomer is in a room with another player: *Strangers are known by how they look. Introduce yourself with `introduce`; when someone tells you a name, `recog <description> as <name>`.* The newcomer's economy note reads this; the temple as the first haven (Comfort EP9) is where the first introductions happen.

**UP24 — Automated test players.** An agent has a description like anyone (UG1); its honesty to players is a line in its long description, not a mark in its short one (UQ3; BACKLOG *Automated test players*).

**UP25 — What others see of a homunculus.** *A homunculus* to a stranger; *Maren's homunculus* to someone who knows its maker — the maker's name through the looker, never the maker's key (Homunculus JQ17).

**UP26 — NPCs and creatures keep keys.** The sweeper and creatures are objects, not characters (`typeclasses/npcs.py:68`, `typeclasses/creatures.py:34`); *the old sweeper* is already a description.

---

## 13. Economy

Nothing is made, sold or used up: introductions are play, and recognition is memory (pillar 1 needs no source or sink here). Three ties for later notes: a **letter of introduction** — a player-written object that introduces its bearer to whoever reads it, after Haven & Hearth's parchment (§2.4; UQ4); **a description as evidence** — a bounty names *the lanky, red-bearded man*, and because a description is stable (UG4), that means something (*law/crime/bounties*); **disguise as a trade** — the hood and mask as worn, crafted items (UP9).

---

## 14. Multiplayer and server load

- **Recog is one dictionary per character**, read through a lazy handler (`rpsystem.py:781`); drawing a name is a dictionary lookup.
- **Room messages already cost one `get_display_name` per receiver** when they use `$You()`/`mapping` (UP10); rooms are small.
- **Search is a regular expression per candidate** (`rpsystem.py:335`), over a room's contents and the searcher's inventory — dozens, not thousands.
- **No race between players.** A recog is written only by its owner, on its owner (`:836–837`). The contrib writes into the Attribute's stored dictionary; it persists only when the Attribute exists, which the contrib's creation hook ensures (`:1562–1563`) and an older character lacks (UQ7).
- **Pushes are per change**, never per tick (UP22).

---

## 15. Immersion extras

- **The stranger at the fire** — Comfort's company (EP4) counts a stranger as much as a friend; what changes is what you can call them.
- **Names on the road** — a description is how a traveller is remembered between settlements, which *travel/roads* and *maps & navigation* inherit.
- **The body on the road** (UP13) — the first time a player finds *the body of Maren*, the death contract becomes a story.
- **Later:** a voice known through a hood (Armageddon thread); darkness hiding a description (*Light*); heraldry and a sign over a door as names at a distance.

---

## 16. Layers — a suggested order

1. **Now — this document.** Docs only.
2. **Stage 5's design session** reads it and decides targeting by description and recog (roadmap Stage 5, *Strangers*).
3. **Stage 5's first slice** — UP1–UP8, UP10–UP20, UP22–UP26 and the K-rows, with the migration of UQ7. Before combat code.
4. **With *barbers, tattoos & appearance\*** — masks, hoods and disguise as items (UP9, UP-L2).
5. **With *languages & tongues\*** — `rplanguage` and Language skills (UP21, UP-L3).
6. **With *letters & notice boards*** — the letter of introduction (UQ4).

**Prerequisites:** Stage 5's design session for 3; the webclient merged, whose panels read the same overrides (roadmap decision log, *Order after the webclient*). **Not prerequisites:** Stage 4.6, the newcomer's economy note (which reads this one), the alpha (where decision (G) measures onboarding and a cohort that knows each other gets the friction without the strangers).

---

## 17. Seams in today's code (read at `4422b65`; Evennia at `v6.1.0`)

| Need | Seam | Where |
|---|---|---|
| Character | class and display overrides | `typeclasses/characters.py:58`, `:518`, `:527`, `:540` |
| Statue | unpuppet, the two messages, the flag | `typeclasses/characters.py:472`, `:488`, `:506` |
| Body | corpse key and owner | `typeclasses/characters.py:1294–1296`; owner read by the grace lock `typeclasses/corpse.py:279–293` |
| Moves | `at_post_move` (pose reset) | `typeclasses/characters.py:1470` |
| Perception | the only social-adjacent skill | `typeclasses/characters.py:360` |
| Room listing | characters line; statues under *You see:* | `typeclasses/rooms.py:301`, `:317` |
| Room messages | `consumption_commands.py:50`; `hunting_commands.py:337`, `:346`; `crafting_commands.py:280`; `work_commands.py:468`, `:609`; `foraging_commands.py:170`, `:230`, `:244`; `currency_commands.py:324`; `typeclasses/creatures.py:84`; `typeclasses/characters.py:488`, `:506`, `:1413`, `:1732`, `:1749` | sixteen sites (K4) |
| Teaching | offer text; student's search | `commands/crafting_commands.py:1265`, `:1450` |
| Crafting search | ingredients and tools | `commands/crafting_commands.py:315`, `:324` |
| Chargen | profession confirm; done | `world/chargen_menu.py:299`, `:337` |
| Migrations | backfills | `world/character_migrations.py` |
| Webclient | per-viewer room snapshot; push; push to room | `world/client_state.py:198`, after it (`feature/webclient` at `dda7156`) |
| Contrib | sdesc, recog, commands, typeclasses | `evennia/contrib/rpg/rpsystem/rpsystem.py:660`, `:754`, `:903–1284`, `:1305–1693` |
| Search | `get_search_result` called by `search` | `rpsystem.py:1326`, `:1339`; `evennia/objects/objects.py:870` |
| Messages | `msg_contents` with `$You()`/`mapping` | `evennia/objects/objects.py:1051` |
| Multimatch | default form; README's form | `evennia/settings_default.py:417`, `:425`; `rpsystem/README.md:80–81` |
| `who` | unprivileged table; account per character | `evennia/commands/default/account.py:439`, `:506`; `evennia/settings_default.py:802` |

Re-read every row against live source before a decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **UQ1** — What does `who` show players? *Leaning (chat, 2026-11-10): a count; Builders see all. A list of named people online tells where friends are not, and is left out.*
- **UQ2** — Does `introduce` set each hearer's recog, or offer it? *Leaning (chat): set it, as Genesis does; `forget` undoes it.*
- **UQ3** — Is an automated test player recognisable? *Leaning (chat): by a line in its long description, not its short one (UP24).*
- **UQ4** — A letter of introduction as a crafted object? *Leaning (chat): yes, with* letters & notice boards*, not here.*
- **UQ5** — Does recognition fade with time apart? *Leaning (chat): no — too hard for a small player base; `forget` is the player's.*
- **UQ6** — Found while writing: `craft` resolves ingredients through the same search (`commands/crafting_commands.py:315`), so `N-name` reaches crafting protocols as well as `hunt`. *Leaning: one change everywhere, with the Testing Reference in the same slice.*
- **UQ7** — Found while writing: the contrib writes a recog into the Attribute's stored dictionary (`rpsystem.py:836–837`), which only its creation hook creates (`:1562–1563`); on a character created before the contrib the write goes to a throwaway default and is lost without an error. *Leaning: a backfill in `world/character_migrations.py` in the same slice, with a test that a recog survives a reload; the alpha instance is wiped, so only development databases need it.*
- **UQ8** — Found while writing: account-level commands (channels, `page`) name accounts, not characters. *Leaning: list them at decomposition against 6.1.0 and treat account names as out of character, as Sindome does (§2.2).*
- **UQ9** — The vocabulary of UP1: how many builds, features and nouns, and who writes them? *Leaning: about ten builds, twenty features and nouns by sex and age; enough that duplicates are rare (UP4).*
- **UQ10** — The room's character listing: one line per character with its pose, or the shipped comma line? *Leaning: one line each (K8, UP16).*
- **UQ11** — How much of the contrib? *Leaning (Adam's, taken 2026-11-10 from Claude's recommendation, BACKLOG Rev 94): sdesc, recog and pose first; masks with disguise and law/crime; `rplanguage` with* languages & tongues*. This document adds `introduce` to the first slice (UP6).*
- **UQ12** — The letter. *Leaning: U, for the unknown; departure rows K, for ken.*

---

## 19. Considered and not proposed

- **Names on screen with an honour rule** (Sindome, §2.2). Needs policing that a solo-run game cannot give.
- **Client-side triggers only** (Armageddon, §2.1). Excludes screen-reader players and fails on identical descriptions (UG2).
- **A recognition roll at every meeting.** Routine work is not tested (Legend p. 42); names would flicker (UP-L1).
- **A free `sdesc` command.** A description that changes on a whim is not evidence (UG4, UP2).
- **The contrib's `mask` as a command.** Pillar 1 — a face-covering is someone's craft (UP9).
- **`introduce` announcing a name to the whole world.** A name travels by people, not by the game (UG1).
- **An NPC who tells you names.** The game tells no name its owner did not give (UG3).
