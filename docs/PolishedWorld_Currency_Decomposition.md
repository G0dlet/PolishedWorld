# PolishedWorld — In-game Currency Decomposition (Stage 4)

> **Rev 2 · 2026-07-26** — §5 reconciled against reality. The §11.20 correction has landed on `main` (Reference **Rev 15**, commit `386fba9f`) together with the Recipe-Knowledge **Rev 11** follow-up, so those two items move from *pending* to *done*. **§11.14 is now re-verified** rather than deferred: the collision is real, but its mechanism is `CmdSet.add()`'s dedup-then-append inside `at_cmdset_creation`, not `_union` — same direction (later wins), different code path, and a *permanent* deletion rather than a merge-scoped one. Reference §11.14 was updated in the same commit. No design decision changes; Components A–F untouched.

> **Rev 1 · 2026-07-26** — first version. Decomposes Stage 4 (In-game Currency) into Components A–F. Locks four design decisions ahead of any code: the **Treasury pattern** for the mint point (the faucet transfers, never mints — Principle 4 stands unbroken), the **wallet-as-integer** representation (a single Copper `int`; denominations are rendering, not storage), **wallet retained on death** in Stage 4 with `CoinPile` materialisation deferred to Stage 5, and a **mint/burn-only transaction log** whose integrity guarantee is a recomputed invariant rather than a per-transfer trail. Command surface kept minimal (`wallet`, `pay`, `work`, `@economy`), with `offer` extended rather than re-keyed. Carries a **correction to Evennia Reference §11.20**: the runtime merge in `cmdhandler.get_and_merge_cmdsets()` gives the tie to the *later-merged* set, not the earlier one — so a runtime cmdset such as barter's `CmdsetTrade` correctly overrides a same-keyed command in `CharacterCmdSet`, and there is no `status` collision to fix.
> **Canonical:** `docs/PolishedWorld_Currency_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Branch:** `feature/currency` (from `main` @ `e69158d6`)
**Roadmap entry:** Stage 4 — In-game currency *(small, foundational)*
**Hard ordering constraint:** must land **before Stage 8 (GameGold)**.

---

## 1. Purpose

The economy is barter-only today. Stage 4 adds the medium of exchange that several
already-shipped and already-planned systems assume: Stage 3's recipe buy/sell
(currently pure barter), Stage 1's training-via-teacher, and above all **Stage 8
GameGold, which is defined as 1:1 with in-game Gold** — Gold must exist as a
currency before a crypto layer can bridge to it.

Scope is deliberately small. This stage builds a wallet, a way to move money
between players, a way to put money on the barter table, and the single mint path
that Stage 8 will later plug the real exchange into. It does **not** build shops,
prices, banking, interest, or taxation.

---

## 2. Locked decisions

These were resolved in the Stage 4 design session and are **not open for
relitigation** during implementation. Each has a doc-patch obligation in
Component F.

### S4-1 · Mint point: the Treasury pattern

**The temple faucet transfers; it never mints.**

The tension this resolves: `PolishedWorld_Economic_Philosophy.md` Principle 4
states Gold is minted at exactly one point (the GameGold exchange) and that the
faucet merely redistributes exchange-minted Gold. But
`PolishedWorld_GameGold_Economy.md`'s **Phase 1 — MVP (No Crypto)** funds the
early economy through that same faucet, at a time when no exchange exists and
therefore no exchange-minted Gold exists to redistribute. Taken literally, the
faucet would have to mint — making it a second mint point and breaking Principle
4 silently for four stages.

The resolution keeps Principle 4 literally true:

- A **Treasury** object (the temple) holds Gold and has its own wallet.
- Gold enters the world through a **bootstrap tranche**: a single mint into the
  Treasury, executed through the exchange code path and tagged
  `crypto_exchange`, against a **recorded GameGold reserve obligation** that is
  settled at Stage 8 when the matching GameGold is donated and staked.
- The faucet pays players by **transferring out of the Treasury**. It never
  calls the mint primitive.

Three reasons this beats a time-limited exception:

1. **Stage 4's faucet code is Stage 8's faucet code.** Nothing is rewritten when
   the exchange goes live; only the funding source of the Treasury changes from
   a pledged tranche to real exchange throughput.
2. **It preserves the `add()` lock as a testable invariant.** `add()` is a mint
   primitive, never a transfer path — under a minting faucet, the faucet would
   be a caller of `add()`, which is precisely what the lock forbids. Here it has
   exactly one caller in the entire codebase.
3. **The reserve obligation exists either way.** This makes it visible and
   quantified now, rather than discovered as an under-reserved exchange at Stage
   8. It also disciplines tranche size: mint only as much Gold as can actually
   be backed.

Secondary benefit: a Treasury with a finite balance **can run dry**. That is a
feature, not a defect — it is diegetic (temple donations are finite), it bounds
faucet farming in a way that complements the existing low-reward + cooldown
design, and it gives a single readable number for total Gold in existence.

### S4-2 · Representation: wallet as a single Copper integer

Storage is **one `int`, denominated in Copper**. The locked denominations
(1 Gold = 100 Silver = 10,000 Copper) are a **rendering** concern applied at
display time, never a storage concern.

Rationale: no denomination drift, no negative-Silver bugs, no conversion logic
duplicated at every call site, no rounding. This matches the roadmap's own Stage
4 design note ("keep denominations as a single base-unit integer under the
hood").

**Deliberate deviation flagged:** `PolishedWorld_GameGold_Economy.md`'s
`CurrencyHandler` sketch stores `character.db.currency` as a per-denomination
dict. That sketch is superseded. Component F patches the doc rather than leaving
two contradictory designs in the repo.

**No coin objects in Stage 4.** Currency reaches the barter table through a
handler-level bridge in `world/barter.py` (Component E), not by materialising
objects. Rejected alternative — physical stacking `CoinPile` objects — carries
merge/split races, an unbounded number of ways for money to move (every
`move_to` path becomes an audit surface), and interacts badly with
`PlayerCorpse.return_appearance`, which deletes all corpse contents at expiry
(see S4-3).

### S4-3 · Death: wallet retained in Stage 4

On death the wallet is **untouched**. Gold is neither created nor destroyed, so
economic integrity is intact.

Be honest about what this is: a **staged** implementation of Principle 5, not a
fulfilment of it. Principle 5 states that on death currency drops to the room and
waits until looted — carrying wealth is supposed to carry risk. Under S4-3 it
carries none.

The fulfilment is the **hybrid materialisation** design: the wallet stays
canonical, and currency materialises into a `CoinPile` object only when it must
exist outside a character (dropped on death, dropped on the ground),
dematerialising back into a wallet when picked up, with the conserving invariant
`wallet_delta + pile_amount == 0`.

**Deferred to Stage 5**, trigger *Stage 5 kickoff*. Rationale: death today occurs
only through starvation; the risk-of-carrying-wealth mechanic has no stakes to
attach to until combat exists. Building droppable currency now solves a problem
that cannot yet arise. S4-2's storage form is unchanged by the upgrade — the
hybrid is purely additive.

Canonical home is `docs/BACKLOG.md` (Component F.1), with a one-line pointer in
the roadmap's Stage 5 entry.

### S4-4 · Transaction log: mint and burn only

**Persistent log records mint and burn events. Player-to-player transfers are not
logged.** Integrity is guaranteed instead by a recomputed invariant:

```
Σ(all character wallets) + Treasury  ==  Σ(mint) − Σ(burn)
```

exposed as `@economy audit`.

Rationale: the question Stage 8's audit must answer is *"how much Gold exists,
and does every unit trace to a real exchange?"* That requires mint and burn
records. Transfers are zero-sum by construction and contribute nothing to it. The
invariant is also a **stronger** guarantee than a log: it detects any discrepancy
regardless of which code path caused it, in O(characters), storing nothing. A log
only catches what it happened to record.

The log therefore grows only with the number of exchanges (Stage 8) and tranches
(exactly one in Stage 4) — effectively zero rows before Stage 8.

Bounded growth matters here for an architectural reason, not a hardware one: an
append-only structure stored in an Evennia Attribute is deserialised **in its
entirety on every access**, so its cost scales with total history rather than
with the write. That is why A.3 persists the ledger on a global Script and why
an unbounded transfer trail would have been the wrong shape regardless of what
the server runs on.

Note this satisfies the GameGold Economy doc literally: *"Log all currency
creation (critical for crypto auditing)."* It is the transfer log that the doc
never asked for.

**Deferred:** per-transfer forensic logging to Evennia's rotating file `logger`,
opt-in behind a settings flag. Trigger: an actual forensic need (a suspected
duplication incident). Note the honest strength of this deferral — it rests on
YAGNI alone, not on any resource ceiling, so it is a cheap decision to reverse
if forensics ever become worth the write volume. BACKLOG entry in F.1.

---

## 3. Architecture

```
world/currency.py
├── module-level pure functions      ← denomination maths, parsing, rendering
│     to_copper() · split_denominations() · format_copper() · parse_amount()
└── CurrencyHandler                  ← per-object wallet
      .value            int, Copper
      .add(n, source)   MINT PRIMITIVE — whitelisted sources only, always logged
      .burn(n, reason)  BURN PRIMITIVE — exchange-back only (Stage 8 consumer)
      .transfer_to(target, n, reason)   ← the ONLY player-facing movement path
      .can_afford(n) · .format()

typeclasses/characters.py     @lazy_property currency  →  CurrencyHandler
typeclasses/treasury.py       Treasury(DefaultObject), same handler
world/economy_log.py          mint/burn ledger + audit invariant

commands/currency_commands.py  CmdWallet · CmdPay · CmdEconomy(admin) · CmdWork
world/barter.py                currency clause on offer + settlement in finish()
commands/character_commands.py CmdStatus gains a trade branch (Component F)
```

**The mint/transfer separation is the load-bearing invariant of this stage.**
`add()` accepts a `source` argument validated against a whitelist
(`crypto_exchange`, `admin_correction`) and raises on anything else.
`transfer_to()` performs a decrement and a matching increment and **never calls
`add()`**. A unit test asserts that `add()` rejects an unknown source — that test
is the guard against the regression this whole design exists to prevent.

---

## 4. Multiplayer & race discipline

Evennia runs the Twisted reactor single-threaded. A command's `func()` executes
atomically **provided it never yields**. That gives three hard rules:

**S4-R1 · Never split check-and-commit across a yield point.**
`can_afford()` and the debit must occur in one unbroken synchronous sequence
inside `transfer_to()`. No `yield`, no `utils.delay`, no deferred call between
them. Splitting them is the duplication vector for this entire stage.

**S4-R2 · No code outside `world/currency.py` writes the wallet attribute.**
Every mutation goes through the handler. Direct `character.db.wallet = n`
anywhere else is a review-blocking defect.

**S4-R3 · Barter settlement must be idempotent.** `PWTradeHandler.finish()` can
be reached from more than one path (voluntary accept, forced teardown). Currency
settlement sets a one-shot flag on the handler so a second entry moves nothing.

**S4-R4 · Offered currency is re-validated at completion, not only at offer.**
Money can be spent between the offer and the final accept — the same failure mode
`_all_offers_in_hand()` already guards for items. Component E adds the sibling
guard. Validating only at offer time is precisely the upstream barter `finish()`
bug (Evennia Reference §7.5).

Standard write-path test matrix from Testing Reference §10 applies: two players
same command same tick, disconnect mid-action, target deleted mid-use, 10+ in a
room. **Two-party tests require two sessions** — `@ipuppet` switches your session
and cannot provide both parties (§10).

---

## 5. Command-key inventory (live-verified 2026-07-26)

Verified against Evennia `main`: all default cmdset modules (`general`,
`building`, `system`, `comms`, `account`, `help`, `batchprocess`) plus every
contrib we merge — `extended_room` (`@desc`, `@detail`, `@roomstate`, `time`),
`crafting` (`craft`), `clothing` (`wear`, `remove`, `cover`, `uncover`,
`inventory`+`inv`/`i`), `containers` (`put`, `get`), `barter` (`trade`/`barter`,
`offer`, `accept`/`agree`, `decline`, `evaluate`/`eval`, `status`/`offers`/`deal`,
`end trade`, `trade help`).

| Key | Status | Decision |
|---|---|---|
| `wallet`, `purse` | free | **claim** (Component B.1) |
| `pay` | free | **claim** (B.2) |
| `work` | free | **claim** (D.1) |
| `@economy` | free | **claim** (C.2) |
| `coins`, `money`, `price`, `balance`, `donate` | free | **do not claim** — see below |
| `give`, `get`, `drop`, `inventory` | **taken** (default cmdset) | never touch |
| `offer` | **ours** via `CmdPWOffer` | **extend**, don't re-key (E.1) |
| `status` | shared with barter — **no collision**, see below | leave alone |

`coins` is deliberately **not** taken as a `wallet` alias: when `CoinPile` lands
in Stage 5 it would read as both a command and an object in the room. `price`,
`balance` and `donate` have no consumer in Stage 4 — player shops do not exist in
the roadmap, and Treasury funding is an admin action. Claiming keys speculatively
costs collision surface for nothing.

### `status` is shared safely — and Evennia Reference §11.20 needs correcting

`commands/character_commands.py::CmdStatus` (key `status`, alias `vitals`, in
`CharacterCmdSet`) and barter's `CmdStatus` (key `status`, aliases `offers`,
`deal`, in `CmdsetTrade`) share a key at equal priority (both 0). An earlier
draft of this document predicted a silent deletion, following Evennia Reference
§11.20. **That prediction was wrong, and so is §11.20.** In-game observation
shows both commands working: vitals outside a trade, the offer table inside one.

The error is in which function the rule was derived from. `cmdsethandler.update()`
folds `new_current = cmdset + new_current`, which puts the *accumulated* set in
the `cmdset_a` role — and `_union`'s docstring states *"cmdset_a: Cmdset given
higher priority in the case of a tie."* Hence the "lower set wins" conclusion.
But `update()`'s own docstring says plainly that its result **will likely not
match** the true current cmdset, which is computed at run time by
`cmdhandler.get_and_merge_cmdsets()`.

The runtime merge groups same-priority sets with:

```python
tempmergers[prio] = yield tempmergers[prio] + cmdset
```

Here `self` is the accumulator and `cmdset_a` is the **incoming** set, so a tie
resolves in favour of whatever is merged **later**. `get_and_merge_cmdsets()`
confirms the direction explicitly: *"Object's cmdset is merged last (and will
thus take precedence over same-named and same-prio commands on Account and
Session)."*

**The real rule is the intuitive one: on a priority tie, the later-merged cmdset
wins.** A runtime-added set (`CmdsetTrade`, added when a trade starts and sitting
above `CharacterCmdSet` in the stack) overrides a same-keyed command in the
default cmdset for the duration, and hands the key back when it is removed.

Consequences beyond this stage, handled in Component F.1:

- ✅ **§11.20 is corrected** — landed as a standalone commit on `main` before any
  currency work, per the reasoning below: a reference-doc lesson that steers
  design decisions should not be buried in a Stage 4 doc commit. Reference
  **Rev 15**, commit `386fba9f`.
- ✅ **Stage 3 H.1's premise did not hold.** Declining to key an `accept` was
  justified by §11.20. Under the correct rule, a global `accept` would have lost
  to barter's inside a trade and worked outside it — no breakage either way.
  Extending `learn` remains the better UX, so nothing needed rebuilding; only the
  stated reasoning was wrong. Corrected in Recipe-Knowledge **Rev 11**, and in
  the `CmdTeach` comment in `commands/default_cmdsets.py`.
- ✅ **§11.14 (containers `look`) re-verified independently.** The collision is
  real — both `CmdContainerLook` and `CmdExtendedRoomLook` inherit `key = "look"`
  from `default_cmds.CmdLook` — but the mechanism is **not** the merge operator.
  `self.add(SomeCmdSet)` inside `at_cmdset_creation` is not a merge: `CmdSet.add()`
  copies the other set's *commands* in, removing any equal command already present
  before appending ("later added commands will simply replace existing ones").
  Same direction as §11.20 (later wins), different code path, and a **permanent**
  deletion for the life of the cmdset rather than one scoped to a runtime set's
  presence. Reference §11.14 updated in the same commit.

**Practical rule this leaves for Stage 4:** claiming a key that a runtime contrib
cmdset also uses is survivable, but only when the two meanings are genuinely
context-separated (vitals vs offer table). It is still not something to do on
purpose. Every key in the table above is unique against the full inventory.

## 6. Components

### Component A — Currency foundation

#### A.1 — Denomination maths as pure functions

- **Goal:** A dependency-free module that converts, parses and renders Copper
  amounts, with no database or typeclass involvement.
- **Dependencies:** none.
- **Implementation:** `world/currency.py`.
  Constants `COPPER_PER_SILVER = 100`, `COPPER_PER_GOLD = 10_000`.
  `to_copper(gold=0, silver=0, copper=0) -> int`.
  `split_denominations(copper) -> (gold, silver, copper)`.
  `format_copper(copper) -> str` — renders largest-first, omits zero
  denominations, singular/plural correct, and renders `0` as `"nothing"`.
  `parse_amount(text) -> int | None` — accepts `"50 copper"`, `"1 gold"`,
  `"3 silver"`, with abbreviations `g`/`s`/`c`; returns `None` on anything
  unparseable rather than raising, so commands own the error message. Negative
  and non-integer inputs rejected. Compact multi-denomination form (`"2g30s"`)
  is **out of scope** — BACKLOG.
- **Testing:** `tests/test_currency.py` with `EvenniaTestCase` (no DB needed —
  the lightest base class that works, per AGENTS §0A). Round-trip property:
  `split_denominations(to_copper(g,s,c))` reconstructs the input for a spread of
  values. Boundary cases: `0`, `9_999`, `10_000`, `10_001`. `parse_amount`
  rejects `"-5 copper"`, `"1.5 gold"`, `"gold"`, `""`.
- **Commit:** `feat(currency): denomination maths and parsing helpers`

#### A.2 — `CurrencyHandler` and the mint/transfer separation

- **Goal:** A per-object wallet handler in which minting and transferring are
  structurally distinct code paths.
- **Dependencies:** A.1.
- **Implementation:** `CurrencyHandler` in `world/currency.py`, backed by a
  single int Attribute (`db_attribute="wallet"`, default `0`).
  `.value` → int. `.can_afford(n)` → bool. `.format()` → `format_copper(.value)`.
  `.add(amount, source)` — **mint primitive**. Validates `source` against
  `MINT_SOURCES = {"crypto_exchange", "admin_correction"}` and raises
  `ValueError` otherwise; rejects `amount <= 0`; writes a ledger entry (A.3)
  before mutating.
  `.burn(amount, reason)` — burn primitive, symmetric; the Stage 8 exchange-back
  consumer. Included now so the ledger is complete from the start.
  `.transfer_to(target, amount, reason)` → bool. Check, decrement, increment, in
  one unbroken synchronous sequence (S4-R1). Never calls `.add()`. Returns
  `False` on insufficient funds without partial mutation.
  Wire `@lazy_property currency` onto `Character` following the existing
  `stats`/`traits`/`skills`/`cooldowns` pattern in `typeclasses/characters.py`.
  ⚠️ Do **not** initialise the wallet in `at_object_creation` with a value that
  would clobber an existing balance on a re-run; guard the backfill the same way
  the TraitHandler backfills are guarded (`.add()` defaults to `force=True` —
  Evennia Reference §3.5 lesson, same shape of trap).
- **Testing:** `tests/test_currency.py` extended, `EvenniaTest` with
  `character_typeclass` pinned. **The load-bearing test:** `add()` with
  `source="faucet"` raises — this is the regression guard for S4-1. Also:
  `transfer_to` conserves total across both wallets; insufficient funds returns
  `False` and leaves both wallets untouched; `transfer_to` to self is rejected.
  In-game smoke, atomic one-shot `@py` per Testing Reference §1:
  `@py me.msg(str(me.currency.value))`
  `@py me.msg(str(me.currency.add(500, source="admin_correction")))`
  `@py me.msg(me.currency.format())`
- **Commit:** `feat(currency): CurrencyHandler with separated mint and transfer paths`

#### A.3 — Mint/burn ledger and the audit invariant

- **Goal:** A persistent record of every mint and burn, plus a recomputable
  invariant over the whole economy.
- **Dependencies:** A.2.
- **Implementation:** `world/economy_log.py`. Ledger persisted on a global
  Script (not a Character Attribute — an append-only structure in an Attribute
  deserialises wholesale on every access). Entry shape: timestamp, kind
  (`mint`/`burn`), amount in Copper, source/reason tag, recipient key + dbref.
  `total_minted()`, `total_burned()`, `append(...)`.
  `audit()` → dict with `wallet_sum`, `treasury`, `expected`, `delta`, `ok`.
  Enumerate characters with
  `ObjectDB.objects.typeclass_search("typeclasses.characters.Character", include_children=True)`
  — **verified live** in `evennia/typeclasses/managers.py`. Audit is an
  infrequent admin action, so full enumeration is acceptable.
- **Testing:** unit — after a mint of 500 and a transfer of 200 between two
  characters, `audit()["delta"] == 0`; after a burn, likewise. Deliberately
  corrupt one wallet directly and assert `ok is False` (this proves the invariant
  actually detects what a log would miss).
- **Commit:** `feat(currency): mint/burn ledger and economy audit invariant`

---

### Component B — Player commands

#### B.1 — `wallet`

- **Goal:** A player can see what they are carrying.
- **Dependencies:** A.2.
- **Implementation:** `commands/currency_commands.py::CmdWallet`,
  key `wallet`, alias `purse` (both verified free, §5). Read-only, no state.
  Renders via `format_copper`. Empty wallet gets a distinct message, not
  `"0 Copper"`.
- **Testing:** `EvenniaCommandTest`, asserting message content at zero, at
  a sub-Silver amount, and at a mixed multi-denomination amount.
- **Commit:** `feat(currency): wallet command`

#### B.2 — `pay`

- **Goal:** Direct player-to-player payment without a trade session.
- **Dependencies:** A.2, B.1.
- **Implementation:** `CmdPay`, key `pay`. Syntax
  `pay <amount> <denomination> to <target>`. Never touches `give` (owned by the
  default cmdset). Target resolved with `caller.search()` in the current room.
  Validate-then-commit ordering (Evennia Reference §11.9): resolve target, parse
  amount, check affordability, then a single `transfer_to`. Reject self-payment,
  non-Character targets, and zero/negative amounts. Both parties are messaged.
- **Testing:** `EvenniaCommandTest` asserting **message and side-effect** (both
  wallet values), per AGENTS §0A. Failure paths: insufficient funds leaves both
  wallets unchanged; unparseable amount; absent target; target in another room.
  In-game two-session test per §10.
- **Commit:** `feat(currency): pay command for direct player transfers`

---

### Component C — Treasury and admin surface

#### C.1 — `Treasury` typeclass

- **Goal:** An in-world object that holds the temple's Gold and is the faucet's
  funding source.
- **Dependencies:** A.2.
- **Implementation:** `typeclasses/treasury.py::Treasury(ObjectParent,
  DefaultObject)` with its own `@lazy_property currency`. `get:false()` in
  `at_object_creation` (same pattern as `Corpse`). A settings key resolves the
  canonical Treasury by dbref, mirroring the `DEFAULT_RESPAWN_DBREF` pattern
  already in `characters.py::_get_respawn_location` (Evennia Reference §11.15 —
  `search_object()` resolves `#dbref` strings). A module-level `get_treasury()`
  returns it or `None`; every consumer must handle `None` rather than assume.
- **Testing:** creation, get-lock refuses pickup, `get_treasury()` returns
  `None` cleanly when the setting is unset.
- **Commit:** `feat(currency): Treasury typeclass as the faucet funding source`

#### C.2 — `@economy` admin command

- **Goal:** Mint the bootstrap tranche, read the Treasury, and run the audit.
- **Dependencies:** A.3, C.1.
- **Implementation:** `CmdEconomy`, key `@economy`, `Developer`-locked.
  Subcommands: `@economy` (Treasury balance + total minted/burned),
  `@economy audit` (the invariant, with a loud failure render),
  `@economy mint <amount> <denomination>` (the bootstrap tranche — mints into
  the **Treasury**, source `crypto_exchange`, and prints the resulting **GameGold
  reserve obligation** explicitly so the number is never implicit).
  Mint requires a typed confirmation; this is the one command in the game that
  creates value from nothing.
- **Testing:** unit — mint raises the Treasury balance and the ledger total by
  the same amount; audit reports `ok` afterwards. Permission test: a
  non-Developer caller is refused.
- **Commit:** `feat(currency): @economy admin command for minting and auditing`

---

### Component D — Temple faucet

#### D.1 — `work` and the task table

- **Goal:** A new player with nothing can earn their first Copper without buying
  crypto — the cold-start solution (Principle 6).
- **Dependencies:** A.2, C.1.
- **Implementation:** `CmdWork`, key `work`. Task table from
  `PolishedWorld_GameGold_Economy.md` (sweep floors 25c/1h, fetch water 35c/1h,
  organize books 50c/2h, light candles 25c/1h, clean altar 35c/2h) as a named
  module constant so tuning is anchored. Cooldowns via `CooldownHandler`
  (Evennia Reference §6) — real wall-clock seconds, which is the correct unit for
  throttling player action spam. **The payout is
  `treasury.currency.transfer_to(caller, ...)`** — never `add()`. That is S4-1
  expressed in one line of code.
  Handle the dry Treasury explicitly and diegetically ("the temple's coffers are
  empty"), not as an error. Tasks are location-gated to the temple room.
- **Testing:** payout moves Copper out of the Treasury and into the wallet with
  zero net change (assert both sides). Cooldown blocks the immediate repeat.
  Empty Treasury pays nothing and leaves the cooldown **unset** (a failed
  attempt must not consume the cooldown). Cooldown isolation per Testing
  Reference §7 — do not use a helper that calls `cooldowns.clear()`.
- **Commit:** `feat(currency): temple faucet work command funded by Treasury transfer`

---

### Component E — Barter bridge

#### E.1 — Currency clause on `offer`

- **Goal:** A player can put money on the trade table alongside items.
- **Dependencies:** A.2, B.2.
- **Implementation:** Extend `CmdPWOffer` in `world/barter.py` — we already own
  the key through the globals patch, so this is §11.20's prescribed "extend the
  owner" rather than a new command. Syntax `offer 50 copper` / mixed with items.
  The amount is recorded **on the trade handler**, not materialised as an object.
  Modifying an offer resets both accepts (contrib behaviour — preserve it).
  Affordability is checked at offer time as UX, but is **not** the guard; E.2 is.
  Rendering comes free: barter's own `CmdStatus` correctly overrides ours inside a
  trade (§5), so the offer table already exists — extend what it prints, and
  verify the render format against the live contrib rather than reconstructing it.
- **Testing:** offer records the amount without mutating either wallet; a
  re-offer replaces rather than accumulates; offering more than you hold is
  refused at offer time; `status` inside the trade shows the currency line for
  both sides, and `status` outside a trade still shows vitals (regression guard
  on the shared key).
- **Commit:** `feat(barter): currency clause on offer`

#### E.2 — Settlement in `finish()` and the stale-currency guard

- **Goal:** Currency settles atomically with items, and cannot be double-spent
  between offer and accept.
- **Dependencies:** E.1.
- **Implementation:** Add `_offered_currency_still_held(handler)` as the sibling
  of the existing `_all_offers_in_hand(handler)`, and call it from the same two
  places — `PWTradeHandler.finish()` and `CmdPWAccept.func()`. A stale currency
  offer cancels the whole trade with the existing single "Trade cancelled"
  message path. Settlement runs inside `finish()` alongside the item moves,
  guarded by a one-shot flag (S4-R3).
  ⚠️ Note the existing hazard documented in the project's barter findings:
  `finish()` assigns `obj.location` directly, bypassing move hooks. Currency
  settlement must therefore live in `finish()` itself, not in a move hook that
  will never fire.
- **Testing:** two sessions (§10). Happy path: both wallets move by the offered
  amounts, items move, totals conserved. **Stale path:** offer 50c, other party
  accepts, offerer `pay`s the money away, then completes the accept → trade
  cancels, nothing moves, both wallets intact. Forced teardown (decline, timeout)
  moves no currency. Double-`finish` moves currency exactly once.
- **Commit:** `feat(barter): settle offered currency in finish() with stale-offer guard`

---

### Component F — Documentation reconciliation

#### F.1 — Doc patches

- **Goal:** No contradictory economy design remains in the repo, and every
  deferral has exactly one home.
- **Dependencies:** A–E complete.
- **Implementation:**
  - `PolishedWorld_Economic_Philosophy.md` **Rev 2 → 3** — Principle 4 gains the
    bootstrap-tranche paragraph (one mint *path*, one mint *code path*; the
    tranche is a pre-settlement with a recorded reserve obligation). Principle 5
    gains a one-line pointer noting the Stage 4 staging of death behaviour.
  - `PolishedWorld_GameGold_Economy.md` **Rev 2 → 3** — new Treasury section;
    the `CurrencyHandler` sketch corrected to the single-Copper-int storage form
    with the dict-storage deviation flagged explicitly; the faucet sketch's
    `character.currency.add(...)` replaced with
    `treasury.currency.transfer_to(...)`; Phase 1 reworded; a Phase↔Stage
    cross-reference added (Phase 1 ≈ Stages 4–7, Phase 2–3 ≈ Stage 8).
  - `PolishedWorld_Evennia_Reference.md` — **two separate patches:**
    **(i) §11.20 correction, Rev 14 → 15, landed on `main` BEFORE Stage 4 work
    begins.** The tie rule is inverted: derive it from
    `cmdhandler.get_and_merge_cmdsets()` (later-merged set wins), not from
    `cmdsethandler.update()`, whose own docstring disclaims matching runtime.
    Record the worked counter-example (barter `status` vs `CmdStatus`, observed
    in game), note that Stage 3 H.1's premise was therefore unfounded though its
    decision stands on UX grounds, and flag §11.14 as needing its own
    verification since it runs through `CmdSet.add()`, not the runtime merge.
    This is a standalone `fix(docs)` commit — it is not currency work and should
    not wait on Stage 4.
    **(ii) §7 update, Rev 15 → 16, with the Stage 4 close-out.** Status corrected
    from "Planned" to live (`world/barter.py` is merged); §7.2's installation
    sketch updated to the PolishedWorld hardening layer; §7.4 amended — the
    contrib's coins-as-objects note stands as *contrib* behaviour, but
    PolishedWorld bridges at handler level instead, and why.
  - `docs/BACKLOG.md` **Rev 12 → 13** — new *Economy* section with:
    `CoinPile` materialisation (trigger: Stage 5 kickoff), per-transfer forensic
    logging (trigger: forensic need, opt-in settings flag), compact
    multi-denomination parsing (`"2g30s"`), faucet task-table tuning anchored to
    the named constant, player shops / `price` command.
  - `docs/PolishedWorld_Recipe_Knowledge_Decomposition.md` **Rev 10 → 11** —
    H.1's stated rationale corrected to match the fixed §11.20. The decision does
    not change; the reasoning behind it does, and a decomp that argues from a
    disproved premise is exactly the stale-doc failure the project guards against.
  - `docs/roadmap.md` **Rev 10 → 11** — Stage 4 closed; one-line pointer in the
    Stage 5 entry to the `CoinPile` backlog item; the open death-consequence
    decision-log entry updated with what Stage 4 actually settled.
  - `docs/README.md` **Rev 5 → 6** — index this document **and**
    `PolishedWorld_Economic_Philosophy.md`, which is currently absent from the
    index despite being first in the economy reading order.
  - `docs/PolishedWorld_SourceSink_Ledger.md` **Rev 1 → 2** — the Currency row
    moves from `[BLOCKED: Stage 4]` to `[EXISTS]`, with the Treasury named as the
    holding point and the bootstrap tranche named as the sole Stage 4 mint.
- **Testing:** n/a (docs). Verify every Rev header moved, per the mandatory-bump
  rule in `docs/README.md`.
- **Commit:** `docs(currency): Stage 4 close-out — reconcile economy docs to the Treasury pattern`

---

## 7. Explicitly out of scope

Player shops · prices and price discovery · banking, deposits, interest ·
taxation or rent · the GameGold exchange itself (Stage 8) · coin objects
(Stage 5) · compact multi-denomination parsing · per-transfer logging ·
training-via-teacher payment (Stage 1 backlog item; it consumes this stage's
`transfer_to` but is not built here).

## 8. Definition of done

- A player can hold, see, earn, pay and trade currency.
- `add()` has exactly one caller in the codebase, and a test proves it rejects
  every other source.
- `@economy audit` reports `delta == 0` on a live server.
- No repo document still describes the faucet as a mint, or the wallet as a
  per-denomination dict.
- Evennia Reference §11.20 states the correct tie rule, and no repo document
  still argues from the inverted one.
