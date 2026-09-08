# PolishedWorld — Skill Progression (XP) Decomposition

> **Rev 8 · 2026-08-24** — **Component D.2 is delivered and Stage 4.5 is closed.** The 100% cap is gone and Legend's second band is live. §6 gains a Delivered block covering the five locked decisions (no numeric ceiling, `descs` untouched, write-time migration, the bar's accepted resolution limit, and `int_bonus` reporting the *applied* INT). The substantive finding is **why a read-time migration was not available here**: B.2 could solve its equivalent problem read-time because *we owned the read*, but a `CounterTrait`'s ceiling is enforced inside **Evennia's own `current` setter**, so a stored `max=100` clamps before any reader sees it. The repair therefore runs at write time through the single writer (P-2) — idempotent by construction, and immune to the restored-backup case a one-shot script cannot cover. Also records that **the cap lived in eight places, not the five that were inventoried**, and that the three extra ones were all prose; that `improvement_roll` had **zero** tests before this task, so the 416-test baseline proved nothing about the arithmetic being changed; the **fifth falsified production claim** (`world/recipes.py`'s *"max craft quality is 110 (skill cap 100)"*) — the first caught *before* it went false rather than after; and a **provably equivalent mutant** (`> 100` vs `>= 100` in the `target` expression differ for no integer input), which corrects a claim this task's own code comment makes about where the band boundary is expressed. **Component E leaves the epic** rather than holding it open: it is BLOCKED on content nobody has scheduled, and a stage held open by an unscheduled trigger blocks Stage 5 without anyone having decided to.
> **Rev 7 · 2026-08-15** — **Component D.1 is delivered, and the fourth false claim of the epic was produced by this document's own test protocol.** §6 gains a Delivered block covering the four locked decisions (D-1 bar resolution, D-2 when the bar renders, D-3 `CmdProgress`, D-4 captions for bars that cannot move), the evaluation and **rejection** of Evennia's `health_bar` contrib, and the measurement that decided D-1. That measurement is the substantive finding: a whole-cell bar **goes silent at high skill** — 23% of ticks move a 20-cell bar at skill 90 — which is the exact silence D.1 exists to remove, displaced one level down. Eighth-block partials give 8× resolution and resolve every banked XP up to skill ~95. Also records the **fourth falsified production claim**: `_improvement_feedback`'s *"a single tick can now move at most ONE point"*, disproven in-game when a tick took Craft 20 → 60 — because §6's protocol tells the tester to set `.current` by hand, and the claim held only while `.current` had no writer but the engine. Same shape as F7: the spec's own protocol manufactures the state the spec's prose says cannot occur. Two corrections to Rev 6 recorded: the dead SHA `9395ac7` (rewritten to `649224e` before push, cited twice) and the fact that **no recipe in the catalogue requires a tool**, which makes `crafting_base.py`'s `tool_broke` branch unreachable and is a second content dependency alongside §7's.
> **Rev 6 · 2026-08-13** — **Component C is delivered, and the epic's most expensive finding is a deviation the spec's own test protocol forced.** §5 gains a Delivered block covering C.1, C.2 and the three sub-decisions. The deviation is **F7**: `.current` raised from outside a bank would have *de-levelled* the character on her next use, and the paragraph that guarantees someone will do this is §5's own in-game protocol, which says to craft until the level moves — hours of work anyone will shortcut by setting `.current` by hand. The repair tops the total up to `xp_threshold(.current)` rather than clamping the level down, so P-1's direction is restored rather than suspended. Also records **three false claims found inside production files** in one epic — `world/improvement.py`'s pacing sentence, `_improvement_feedback`'s "rolled=True is a sufficient gate", and the tier celebration's idempotence argument — all the same shape: prose asserting what a mechanism guarantees, left standing after the mechanism changed. And a **false pass**: the F7 step first "succeeded" because the craft it used failed, so the engine never ran and "the level stayed put" was produced by nothing happening. A step expecting *nothing changed* needs an independent receipt that the code ran (Testing Reference Rev 5 §11). Six mutations recorded, one honest gap stated, and the fact that `improve_skill_on_use` had **zero** tests before this — the 363-test baseline would have stayed green if it had been deleted.
> **Rev 5 · 2026-08-05** — **P-5 gains the threshold it was missing.** "Tightened never" was written as an absolute, and it is not one: the ratchet exists because a tightening de-levels *people*, so it starts at first real players and not before. Pre-launch, recalibration in either direction is free, and several are expected. Without the threshold P-5 would be cited to block a legitimate early rebalance — the rule would outlive its own reason. Also: §7's BLOCKED status is unchanged but **reframed** — the catalogue being small is an ordinary early-development state, not a finding, and Rev 4 wrote it as an alarm. `min_skill = 30` on `LeatherBootsRecipe` is a **placeholder**, so E.1 assigns every value rather than filling in the blanks around it. New hazard recorded in §7: **`min_skill` would carry two jobs** — it is already a hard access floor read from `.value`, and E.2 would read it as a difficulty datum from `.current`. One number, two purposes, two readings; raising it so a recipe teaches longer also locks lower-skill crafters out of it entirely.
> **Rev 4 · 2026-08-05** — **the three open sub-decisions are closed**, and closing them added a component. XP grain scaled to material cost is **rejected, not deferred**: with a per-skill cooldown the binding resource is *ticks*, so any per-craft scaling makes "the most expensive recipe you can afford, once per window" strictly dominant — and flat grain is degenerate in the mirror direction, making the *cheapest* recipe dominant. Both are the same bug; the fix is neither, it is the `meaningful` seam that `attempt_skill_improvement` already carries and has never used. That becomes **Component E** (§7), recorded as **BLOCKED on recipe content** rather than scheduled, because with eight recipes topping out at `min_skill = 30` the gate would strand every crafter above 60 — strictly worse than the grind it removes. `improvement_cooldown` is **frozen** rather than tuned (one knob per job; the curve is the knob). `CmdScribe` is **taken in** as a sixth call-site, so **P-6 changes from five to six**. Also records the measured pacing this epic actually produces — 38 ticks today vs 2 931 after C.1, a 77× slowdown — and the fact that two independent throttles now multiply.
> **Rev 3 · 2026-08-05** — record Component B as delivered, with **five deviations, one of them structural**: B.2 shipped as a read-time fallback rather than a written backfill. The reason is a measurement, not a preference — `at_object_creation` gives every new character non-zero skills, so a one-shot migration is one-shot only for the characters alive when it ran, and the population it must cover has no end. Section 4's original text is left standing and the Delivered block is appended below it, the same shape Rev 2 used for A.1 — the superseded design stays readable, and the block says which parts of it did not survive contact with the code. Components A, C and D unchanged, and **C.1's dependency list is unchanged** — it still needs a working store, and it has one.
> **Rev 2 · 2026-08-03** — record Task A.1 as delivered with its three additive deviations (calibration-matrix tests, two extra tests, clamped constants), each motivated by P-5's promise that the constants will be recomputed. Sharpens section 3's seed-error note: the error is one-directional and bounded by construction, and the two correction loops are bounded for different reasons -- the step-down loop is dead at the shipped calibration and live at others, which is exactly why the matrix test exists. Components B-D unchanged.
> **Rev 1 · 2026-08-03** — first version. Decomposes **Stage 4.5**: reinterpret Legend's Improvement Roll so its output banks XP toward the next whole percentage point instead of adding points directly. Four components, six tasks, deliberately ordered so the first two are inert. Supersedes the "no hidden XP accumulator" half of the Stage 1 pacing decision (roadmap Rev 14 decision log); the other three halves of that decision stand.
> **Canonical:** `docs/PolishedWorld_Skill_Progression_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

---

## 1. What this epic is, in one paragraph

Legend's Improvement Roll is a reward mechanic for a table that meets once a
week. Measured against the shipped system at INT 12, **43 successful crafts move
a skill from 0 to 100** — roughly 22 minutes of pure cooldown, under two hours
including gathering. That is not a pacing curve; in a world that is online
continuously it is no curve at all. This epic keeps the roll **verbatim** and
changes only what its result means: `1D100 + INT > current` banks **2–5 XP**
instead of adding 1D4+1 points, and the guaranteed floor banks **1 XP**. Between
each whole percentage point stands an exponential threshold.

**The percentage remains the single mechanical truth.** Every skill check, every
`min_skill` gate, every tool buff, every desc-tier still reads `skill.current`
and none of them learns that XP exists. What changes is only how often
`.current` moves.

---

## 2. Locked decisions (do not relitigate)

| ID | Decision |
|---|---|
| **P-1** | Lifetime-total XP per skill is the **sole persisted truth**. Level and progress bar are *derived*, never stored. |
| **P-2** | `skill.current` becomes a **materialised cache with exactly one writer** — the same discipline `world/currency.py` holds over the wallet Attribute (**S4-R2**). |
| **P-3** | The Legend roll is unchanged. `world/improvement.py::improvement_roll()` is not touched by this epic; only its caller reinterprets the result. |
| **P-4** | Curve shape: exponential, **doubling every `SKILL_XP_DOUBLING_SPAN` points**. RuneScape's ×2-per-7-levels is ruled out by measurement (94% of playtime in the top quartile of a 100-point scale). |
| **P-5** | Calibration is **not fixed by this epic**. Constants carry provisional values plus the documented procedure to recompute them. Generous now, tightened never — lowering the curve later is free, raising it de-levels people. **⚠️ The ratchet starts at first real players, not now** *(Rev 5)*. It exists because a tightening takes skill away from someone who earned it; with nobody to take it from, recalibration in either direction costs nothing but a `@reload`. Several rebalances are expected before launch and P-5 does not forbid them — it forbids the *last* one from being upward. State which side of that line a proposed change is on before invoking this rule. |
| **P-6** | Scope is the **shared primitive**, so all **six** improvement call-sites move together: craft, repair, hunt-attack, hunt-harvest, disassemble, **scribe**. Scribe was five-not-six by omission rather than by decision (see §2's resolved sub-decisions and §8); a rule of the form "some Craft rolls teach and some do not, and you are not told which" is not learnable by a player, and P-5 says generosity is the safe side to err on. |
| **P-7** | No hard cap at 100. Legend's >100% band (formula already in `world/improvement.py`'s docstring) becomes reachable. |
| **P-8** | No second number is shown to the player. The cosmetic 1–99 badge stays rejected — the bar shows progress *within* the percentage, not a parallel level. |

### Explicitly rejected

- **INT as an XP multiplier.** INT is already inside the roll (`1D100 + INT`) and
  decides how often you bank 2–5 rather than 1. A multiplier on top would pay for
  the same characteristic twice, and worst at high skill, where the roll's INT
  effect is already decisive. Rejected, not deferred.
- **Storing XP-within-current-level.** If the curve is recalibrated, a stored
  "47 XP toward the next point" becomes a number whose meaning silently changed,
  and every character lands in a state no real history could produce. Lifetime
  total is a *fact about what the player did*; the curve is only an
  interpretation of it (P-1).
- **Storing the progress bar.** Anything stored alongside a derived value can
  drift out of step with it. A bar computed on read cannot.
- **XP grain scaled to material cost.** *(Rejected 2026-08-05, was the first
  open sub-decision.)* The lever is real, but it is aimed at the wrong target and
  it misfires. The cooldown is **per skill**, so the binding resource is *ticks*,
  not materials — the moment XP scales per craft, "the most expensive recipe you
  can afford, once per window" becomes strictly dominant. That is arithmetic, not
  a risk. It also couples wealth to progression, which in a 100% player-driven
  economy is the one feedback loop worth refusing outright. And the problem it
  was meant to solve is **symmetric**: flat grain makes the *cheapest* recipe
  dominant (grind a hundred spoons), scaled grain makes the *dearest* one
  dominant (grind a hundred swords). Scaling does not fix the degeneracy, it
  swaps which recipe is degenerate. The actual fix is difficulty relative to the
  crafter, which is Component E — and note the distinction, because they look
  alike: E scales on *how hard the task is for you*, which nobody can buy, not on
  *what the task cost*, which is exactly what a rich player has more of.

### Sub-decisions — all three closed 2026-08-05

- **[RESOLVED] XP grain scaling by recipe value → rejected.** See *Explicitly
  rejected* above. The replacement is Component E (§7).
- **[RESOLVED] `improvement_cooldown = 30` → frozen, and reclassified.** It is
  no longer an anti-spam guard; it is the wall-clock floor under the whole curve
  (2 931 ticks × 30 s ≈ 24 h from craft 20 to 100). It stays at 30 for two
  reasons. First, **P-5**: raising it is a tightening, and the only lever allowed
  to move under recalibration is the curve. Second, and more important, **two
  knobs doing one job is how a system becomes uncalibratable** — halving the
  cooldown and halving `SKILL_XP_BASE` produce the same observable change, so
  after the fact nobody can tell which one did it. **The curve is the calibration
  knob; the cooldown is held fixed.** C.1 rewrites its comment accordingly. It is
  rarely the binding constraint for craft anyway: materials, gathering time and a
  successful roll all bite first.
- **[RESOLVED] `CmdScribe` → it trains.** Sixth call-site, folded into C.1. See
  P-6 and §8.

### Measured pacing (2026-08-05, 400 simulated careers, INT 10)

Craft 20 → 100, counting eligible ticks:

| | ticks | at 30 s cooldown |
|---|---|---|
| shipped system (`main`) | 38 | **19 minutes** |
| after C.1 at (6, 20) | 2 931 | **24.4 hours** |

A **77× slowdown**, which is the epic working as intended — 19 minutes to mastery
is not a balance problem, it is a broken system. But it also means (6, 20) is
generous only *relative to a curve that could be far steeper*; in absolute terms
it is a serious commitment of player time, and P-5's "generous now" should be
read with that in mind.

⚠️ **Two throttles now multiply, and only one of them is documented as a
throttle.**

| level | XP per point | mean grain | ticks per point |
|---|---|---|---|
| 20 | 12 | 3.25 | 3.7 |
| 60 | 48 | 2.25 | 21.3 |
| 95 | 161 | 1.38 | 117.1 |

Legend's roll already self-throttles — the grain falls from 3.25 to 1.38 because
the roll must *exceed* your own skill — and `world/improvement.py`'s docstring
says so in as many words: *"This is the pacing engine — no hidden XP accumulator
is needed."* This epic adds an accumulator on top of it. That is a deliberate
choice, but after C.1 that sentence is **false in its own file**, and a
contradiction inside the source is the same failure the Evennia Reference Rev 21
had to fix. C.1 corrects it.

---

## 3. Component A — the curve, as pure functions

Nothing calls this component. That is deliberate: it is arithmetic with an exact
answer, and arithmetic with an exact answer should be provable before anything
depends on it. Same stance `world/skillcheck.py` and `world/improvement.py`
already take.

### Task A.1 — `world/progression.py` + settings constants

- **Goal:** A pure module that converts between lifetime XP and level, in both
  directions, for any level including above 100.
- **Dependencies:** none. No Evennia imports.
- **Implementation:**

  Two constants in `server/conf/settings.py`, with the recompute procedure in a
  comment beside them (P-5):

  ```python
  SKILL_XP_BASE = 6            # XP cost of the very first point (0 -> 1)
  SKILL_XP_DOUBLING_SPAN = 20  # points over which the per-point cost doubles
  ```

  Let `r = 2 ** (1 / SPAN)`. Then the cost of the *n*-th point is
  `BASE · r^(n−1)`, and the total XP needed to *be* at level `L` is the geometric
  sum:

  ```
  threshold(L) = BASE · (r^L − 1) / (r − 1)          threshold(0) = 0
  ```

  Three public functions:

  - `xp_threshold(level)` → int. Floored. **Strictly increasing**, because every
    per-point cost is ≥ `BASE` ≥ 1, so flooring the cumulative sum can never
    produce two equal thresholds.
  - `level_for_xp(total_xp)` → int. Invert the closed form for a seed, then
    correct:

    ```
    seed = floor( log(1 + total_xp·(r−1)/BASE) / log(r) )
    ```

    The seed can be off by one in either direction because `xp_threshold` floors
    and `log` is inexact, so the seed is followed by a **bounded** correction —
    step up while `xp_threshold(L+1) <= total_xp`, step down while
    `L > 0 and xp_threshold(L) > total_xp`. In practice this runs zero or one
    iterations. It stays O(1) and needs no precomputed table, which is what makes
    P-7 (no cap) free rather than a special case.
  - `progress_within_level(total_xp)` → `(earned, needed, fraction)` for the
    *current* level. Pure arithmetic on the two surrounding thresholds; nothing
    is stored (P-1).

- **Why a closed form rather than a table:** a table has to end somewhere, and
  P-7 says the curve does not. A table would also have to be regenerated on every
  recalibration, which turns a settings change back into a migration — exactly
  what P-1 exists to prevent.
- **Testing — unit:** the load-bearing test is the **round-trip invariant**,
  `level_for_xp(xp_threshold(L)) == L` for every `L` in `0..500` — 500, not 100,
  because P-7 makes above-cap levels real. A second test asserts strict
  monotonicity of `xp_threshold` over the same range. A third asserts
  `level_for_xp(xp_threshold(L) - 1) == L - 1`, which is the off-by-one the
  seed-plus-correction exists to defeat: without the correction loop this is the
  test that fails.
- **Testing — `evennia shell` (pure logic, no game needed):**

  ```
  from world.progression import xp_threshold, level_for_xp
  print(xp_threshold(1), xp_threshold(20), xp_threshold(60), xp_threshold(100))
  print(all(level_for_xp(xp_threshold(n)) == n for n in range(501)))
  ```

  Expect the second line to print `True`. **What it proves:** the two functions
  are actual inverses, so a level can never be lost or gained by round-tripping
  through storage.
- **Commit:** `feat(progression): add pure XP curve module and calibration settings`

#### Delivered 2026-08-03 — three deviations, all additive

Shipped on `feature/skill-progression`; 334 tests green (316 baseline + 18 new).
Nothing specified above was dropped. Three things were added, and the reason is
the same in each case: the spec assumed the shipped calibration is the only one
the code will ever run under, and P-5 says in writing that it is not.

1. **The invariant tests run over a calibration matrix**, not only at
   `(BASE=6, SPAN=20)`. Measured, not argued: delete the step-*down* correction
   from `level_for_xp` and all three specified tests still pass at (6, 20) --
   but fail 176 cases at (6, 7), 61 at (3, 10) and 268 at (1, 5). Tested at the
   shipped numbers alone the suite cannot tell correct code from code missing
   half its correction logic, and would first go red at the moment someone
   recalibrates. The matrix lives in `tests/test_progression.py::CALIBRATIONS`.
2. **Two tests not in the spec.** `test_cost_doubles_over_one_span` puts P-4's
   defining property in executable form; `TestCalibrationSafety` covers the
   clamps in (3).
3. **`_calibration()` clamps both constants to a minimum of 1.** This follows
   directly from the termination argument for the step-up loop: the proof that
   the seed can never be low by more than one depends on `BASE >= 1`. At
   `BASE = 0` every threshold flattens to 0 and the loop would not terminate --
   though in practice the seed's division by `BASE` raises ZeroDivisionError
   first. At `SPAN = 0` the `1 / span` exponent raises. A typo in settings.py
   should not be able to hang or crash a craft.

**Sharper than the note in section 3 above:** the seed is not merely "off by one
in either direction". With exact arithmetic it can *only* be low, and only by
one -- `xp_threshold` floors, so the seed's set of qualifying levels is a subset
of the true one, and an error of two would need two consecutive exact thresholds
inside the same unit interval when the gap between them is `BASE * r^L >= 1`.
The step-*down* loop exists purely to absorb `log()`'s inexactness, which is why
it is dead at (6, 20) and live elsewhere. Both loops stay; they are bounded for
different reasons.

**Verified in the running server, not only in `evennia shell`:** shell is a
separate process and cannot prove the game can import the module or that
`@reload` picked up the settings block. The in-server check first returned
`AttributeError: 'Settings' object has no attribute 'SKILL_XP_BASE'`, then
`(6, 20, 174053)` after `@reload` -- which is the evidence that it reads live
settings rather than defaults. See Testing Reference Rev 4 §3 for the
argument-passing `@py` idiom this needed.

---

## 4. Component B — storage and backfill

Also inert. Storage exists; nothing reads it for gameplay yet.

### Task B.1 — the XP store

- **Goal:** Persist lifetime-total XP per skill, with exactly one writer.
- **Dependencies:** A.1.
- **Implementation:** A `skill_xp` Attribute holding `{skill_key: int}`,
  reached through a handler on `Character` (`@lazy_property`), mirroring the
  `currency` pattern **including its omission**: no `AttributeProperty` is
  declared for it, so there is no `char.skill_xp = {...}` shortcut for code
  outside the handler to reach for. That is how P-2's single-writer rule is
  enforced by construction rather than by review (**D6**'s reasoning, applied to
  a second Attribute).

  ⚠️ Evennia deserialises Attribute containers into `_SaverDict`, which **fails**
  `isinstance(x, dict)`. Membership and iteration must go through
  `collections.abc.Mapping` (Evennia Reference; the same trap bit the survival
  layer).
- **Testing — unit:** a fresh character has no `skill_xp` Attribute at all until
  the first write (the Attribute is not created by `at_object_creation`); reading
  an unbanked skill returns 0; a write then a read round-trips; the handler is
  the only path that mutates.
- **Commit:** `feat(progression): add per-skill lifetime XP store`

### Task B.2 — one-time backfill

- **Goal:** Give existing characters an XP total consistent with the level they
  already have, so nobody is de-levelled by the switch.
- **Dependencies:** B.1.
- **Implementation:** For each skill the character has, if it has no XP entry,
  set `xp = xp_threshold(skill.current)` — the *minimum* total consistent with
  standing at that level. Guarded with the `get(...) is None` pattern, because
  `TraitHandler.add()` defaults to `force=True` and a careless backfill destroys
  a live value (Evennia Reference §3.5). Runs from `at_init`/a one-shot admin
  command, never on every login.
- **Why the floor and not the midpoint:** the floor is the only value derivable
  from what we actually know. Anything higher invents progress the player did not
  make, and would show a partially-filled bar on a skill that has never banked a
  single point.
- **Testing — in-game:**

  | Step | Command | Expect | Proves |
  |---|---|---|---|
  | 1 | `@py self.skills.craft.current` | your existing craft % | pre-state captured |
  | 2 | run the backfill | — | — |
  | 3 | `@py str(self.skill_xp.get("craft"))` | `xp_threshold(<that %>)` | XP matches the level |
  | 4 | `@py self.skills.craft.current` | **unchanged** | backfill is level-neutral |
  | 5 | run the backfill **again** | — | — |
  | 6 | repeat step 3 | **same number** | the guard holds; idempotent |

  Step 5–6 is the whole point of the task. A backfill that is not idempotent is a
  data-loss bug waiting for a second `@reload`.
- **Commit:** `feat(progression): backfill lifetime XP from existing skill levels`

#### Delivered 2026-08-05 — five deviations, one of them structural

Shipped on `feature/skill-progression` as a single commit (`30c7f04`); **363
tests green** (334 baseline + 29 new). In-game protocol run against the live
server, all eleven steps as predicted. Component B remains **inert**: the store
exists, and nothing reads it for gameplay until C.1.

**The structural deviation — B.2 is a fallback, not a backfill.**

The spec above asks for a written one-time backfill, guarded with
`get(...) is None`, whose headline property is idempotence. That is not what
shipped, and the reason is a measurement taken before any code was written:
`at_object_creation` starts every character with **non-zero skills** —
perception 25, stealth 20, athletics 25, hunting 25, and craft = DEX + INT = 20
at default stats. A one-shot migration is therefore one-shot only for the
characters alive when it ran. Every character created afterwards would stand at
craft 20 with 0 XP, and C.1 — which makes `.current` a materialised cache of
`level_for_xp(total)` — would de-level her to 0 on her first craft. **The
population a migration must cover has no end, so a migration cannot close the
hole.**

What shipped instead: `SkillXPHandler.get()` returns the stored total if one
exists, and otherwise returns `xp_threshold(int(skill.current))` computed on
read and **never written**. The Attribute is not created until the first genuine
bank.

This is not a weaker guarantee than the guarded backfill; it is a different and
stronger one. Idempotence stops being a property a guard must maintain and
becomes a property of **there being no write** — the same proof shape
`world/currency.py` uses for the wallet, and the structural escape §11.23 of the
Evennia Reference describes. It also survives things a migration does not: a
restored backup, a character created after the migration ran, and an admin who
never remembered to run anything.

The cost, stated plainly: until a skill's first bank the causal direction is the
**reverse** of P-1 — the level is the truth and the XP is derived from it. It
inverts to P-1's direction permanently at the first `add()` and never inverts
back. An explicit backfill has the identical inversion; it merely lasts one
instant instead of lasting until first use. P-1 is therefore not relitigated,
only its start condition is.

**The other four deviations.**

1. **B.1's test spec "reading an unbanked skill returns 0" is replaced.** It
   describes the bug, not the behaviour. Two tests take its place: an unbanked
   skill reads *the floor for its level*, and a skill the character does not
   have reads 0 — that second case is the only true zero, and it is why `get()`
   cannot simply be "return the threshold".
2. **The handler lives in a new `world/skill_xp.py`,** not in
   `world/progression.py`. The latter's docstring promises no Evennia objects,
   no I/O and no trait reads, and that promise is what tells the next reader its
   tests belong on the cheap `EvenniaTestCase`. A handler in the same file makes
   the promise false and blurs the two base classes. Same division as
   `world/improvement.py` (pure roll maths) beside `world/currency.py` (handler).
3. **`add()` does not raise on an unknown skill key.** This looks inconsistent
   with D7 and is the one deviation shipped with reservations. It follows
   `Character.improve_skill_on_use`, which already made this exact call in the
   opposite direction and said so in a comment — it returns None for an unknown
   skill "rather than raising, so a shared call site that passes a key this
   character lacks stays safe" — and it is the only caller that will reach
   `add()`. A second guard could only fire for a caller that had already
   bypassed the first, and its only effect would be to abort a live craft.
   `all()` unions stored keys with real skills as the compensating control, so
   an orphaned entry is findable rather than silent. **Recorded in
   `docs/BACKLOG.md` as SCHEDULED against C.1's call-site review.**
4. **`__repr__` calls `all()`,** which is a database read inside a repr. Cheap
   and debug-only, but worth knowing before someone logs handlers in a loop.

**Measured, not asserted — three mutations.** (a) `add()` banking onto 0 instead
of onto the floor: 4 failures. (b) `isinstance(store, Mapping)` →
`isinstance(store, dict)`, the `_SaverDict` trap: 6 failures. (c) `get()` caching
its fallback: 8 failures, five of them from the calibration matrix — a cached
floor computed under one calibration is simply a wrong number under the next,
which is precisely what P-5 guarantees we will walk into. An earlier draft of
the test docstring claimed mutation (a) reddened only one class; it reddened
two, and the docstring was corrected rather than the claim softened.

**`.current` is a float.** `CounterTrait` stores 20.0, not 20. The `int()` at the
call site is explicit and truncates downward, which is the correct direction: the
floor must be the *smallest* total consistent with the level. Recorded in Evennia
Reference Rev 21 §3.5.

**Carry into C.1:** the store's API is `get(skill_key)`, `add(skill_key, amount)`
and `all()`. Deliberately no `level()` / `progress()` read-throughs — C.1 needs
`level_for_xp` inside `improve_skill_on_use` anyway, and guessing those
signatures one component early is guessing about code that is still dead.


---

## 5. Component C — the primitive changes engine

The first task in this epic that changes what a player experiences. Five of the
six call-sites are **not touched**: they call `attempt_skill_improvement`, which
calls `improve_skill_on_use`, and only the latter changes (P-6). The sixth,
`CmdScribe`, is *added* by C.1 — see the sub-decisions below.

### Task C.1 — bank XP instead of adding points

- **Goal:** `improve_skill_on_use` banks the roll result as XP, recomputes the
  level from the new total, and writes `.current` only if it moved.
- **Dependencies:** A.1, B.1, B.2.
- **Implementation:** The shape stays; the middle changes.

  ```
  res      = improvement_roll(old_level, int_char)   # UNCHANGED (P-3)
  new_xp   = old_xp + res["gained"]                  # 1, or 2-5
  new_level = level_for_xp(new_xp)
  ```

  `.current` is then assigned only when `new_level != old_level` — a write per
  craft would be pointless churn on a value that changes once in dozens.

  ⚠️ **The roll's target is the level, not the XP.** `improvement_roll` takes
  `old_level` and compares `1D100 + INT` against it, exactly as before. That
  preserves Legend's self-throttle as a *third* difficulty ramp (grain falls 3.5
  → 1.3 across the scale, a factor of 2.7) on top of the curve. It is mild
  compared to the curve's ~30×, which is why the curve does essentially all the
  pacing work — worth knowing before anyone tunes one thinking it moves the other.

  The returned dict keeps its existing keys so the felt-progress layer keeps
  working, and gains `xp_gained`, `xp_total` and the progress triple. **`delta`
  is now usually 0** — see the ordering hazard below.
- **Testing — unit:** the tests worth writing are the ones that would catch a
  wrong *reinterpretation*, not a wrong roll. (a) A tick at a known XP total
  moves the total by exactly the roll's `gained`. (b) A tick that does not cross
  a threshold leaves `.current` **untouched** — assert the Attribute was not
  written, not merely that the value is equal. (c) A tick that crosses exactly
  one threshold raises `.current` by exactly 1, even when `gained` is 5 — the
  curve, not the roll, decides the level. (d) With `improvement_roll`
  monkeypatched to always return the floor, a skill still reaches level N after
  exactly `xp_threshold(N)` ticks: the deterministic pacing check.
- **Testing — in-game:**

  | Step | Command | Expect | Proves |
  |---|---|---|---|
  | 1 | `@py str((self.skills.craft.current, self.skill_xp.get("craft")))` | level + XP | baseline |
  | 2 | `craft twine` | craft succeeds, **no** "improves!" line | a tick that banks without levelling is silent |
  | 3 | repeat step 1 | XP **up**, level **same** | XP accrues under the surface |
  | 4 | craft repeatedly until the level moves | "improves!" fires once | the threshold is what levels you |
  | 5 | `@py str(self.skill_xp.get("hunting"))` after a hunt | XP present | P-6 — hunting moved too, with no call-site edit |

- **Also in C.1, from the 2026-08-05 sub-decision close-out** — three small edits
  that belong in this commit because they are all consequences of the same
  reinterpretation:
  1. **Sixth call-site.** `CmdScribe` (`commands/crafting_commands.py`) gets
     `imp = caller.attempt_skill_improvement("craft", outcome)` plus the standard
     `_improvement_feedback` routing, exactly like the other five. It is a real
     Craft roll with a material cost and a failure mode; excluding it was an
     omission. P-6 now reads six.
  2. **Reclassify `improvement_cooldown`.** Its comment currently calls it a
     "balance knob". Rewrite it to say what it now is: the wall-clock floor under
     the curve, **held fixed**, with the curve as the sole calibration lever. Do
     not change the value.
  3. **Correct `world/improvement.py`'s docstring.** It states that the roll's
     self-throttle "is the pacing engine — no hidden XP accumulator is needed".
     After this task that is false in its own file. Correct it in place and say
     what superseded it, the way Testing Reference Rev 4 handled its own reversal
     — do not delete the old claim silently.
- **Commit:** `feat(progression): bank improvement rolls as XP; derive level from total`

### ⚠️ Ordering hazard — C without D feels *worse* than before

Stage 1's entire premise was that mechanically-correct progression can still ship
as an invisible backend that feels dead, and its felt-progress layer exists to
prevent exactly that. C makes `delta == 0` the common case, so
`_improvement_feedback` — which returns `""` unless a tick rolled and moved —
goes quiet for dozens of crafts at a stretch. **On the branch between C and D the
game is strictly less legible than it is on `main` today.**

Two ways to handle it, and the choice belongs to Adam:

- **C ships with a minimal line** ("Your Crafting improves." with no number) and
  D replaces it with the bar. Costs one throwaway string; the branch is always
  playable.
- **C ships silent** and D lands immediately after. Cheaper, but do not playtest
  the intermediate state and conclude the pacing is wrong — it will feel wrong for
  a reason that D fixes.

### Task C.2 — feedback reads the new shape

- **Goal:** `_improvement_feedback` handles `delta == 0` without lying.
- **Dependencies:** C.1.
- **Implementation:** The current copy is
  `f"Your {label} improves! (+{result['delta']}, now {result['new']}%)"` — with
  `delta == 0` that reads "+0", which is worse than silence. The gate becomes
  "did the level move?" for the exclamation, with the banked-but-not-levelled case
  handled per the hazard decision above. The desc-tier celebration is untouched:
  it already fires on crossing, and crossings are strictly rarer now.
- **Testing — unit:** `delta == 0` never produces a message containing `+0`; a
  level-crossing tick still produces the tier celebration exactly once.
- **Commit:** `fix(progression): feedback copy for ticks that bank without levelling`

#### Delivered 2026-08-12/13 — C.1 and C.2, with one deviation the protocol forced

Shipped on `feature/skill-progression` as three commits — `81ab2d9` (C.1),
`6a9c762` (the tests), `07ffef4` (C.2) — plus `649224e`, a comments-only
follow-up explained below. **391 tests green** (363 baseline + 28 new). The
in-game protocol was run against the live server; all twelve steps behave as
predicted, and one of them did not on the first attempt (see *The false pass*).

The ordering hazard was resolved in favour of **C ships with a throwaway line**.
The reason is calendar, not design: at ~5 h/week the gap between C and D can be a
week of wall clock, and "do not playtest the intermediate state" is not a
constraint that survives seven days of the branch sitting there. The line is
`You feel your grasp of {label} steady a little.` — no number (P-8) and, by
deliberate choice, **not the word "improves"**, which is reserved for a tick
where the percentage actually moved. Lending it to a silent tick would teach a
meaning D.1 then has to take back. It carries a `TODO(D.1)` and is one branch.

**The deviation — F7, a floor repair the spec does not mention.**

B.2 closed the "never banked" hole by deriving the floor on read. The hole left
standing is *banked, then `.current` raised from outside*: an admin `@py`, a
restored backup, a legacy write. After that the stored total implies a lower
level than the cache shows, and `level_for_xp` would **de-level the character**
on her next successful use.

This is not a theoretical branch, and the proof is in this document. §5's own
in-game protocol says *"craft repeatedly until the level moves"*, which at any
interesting skill level takes hours — so the first person to test C.1 sets
`.current` by hand, and the second thing they do is craft. The spec's test
procedure and the spec's blind spot are the same paragraph.

What shipped: before the roll, if the stored total is below `xp_threshold(old)`,
top it up to that floor through `add()`. It is B.2's rule applied to a *present*
entry that has fallen behind rather than to an absent one, it routes through the
single writer (P-2), and in every normal life it is one comparison that changes
nothing. Measured in-game: craft set to 60 by hand against a total of 188 (level
21); the next successful craft left the level at 60 and moved the total to 1191 —
`xp_threshold(60)` plus the tick's grain. Without the repair the same craft would
have printed `improves! (+-39, now 21%)`.

Note the direction. The repair **tops the total up** rather than clamping the
level down; a `max(old, ...)` guard would also preserve the level but would leave
the total permanently inconsistent with it and the progress bar permanently
meaningless. P-1's direction is restored, not suspended.

**The three sub-decisions, all delivered in C.1.**

1. **Sixth call-site.** `CmdScribe` now routes through
   `attempt_skill_improvement("craft", outcome)` and `_improvement_feedback`,
   placed after the result message so a feedback line reads as the next beat, as
   in `CmdDisassemble`. **P-6 reads six**, verified in-game.
2. **`improvement_cooldown` reclassified, value untouched at 30.** Its comment
   now states what it is — the wall-clock floor under the curve (~2 931 ticks ×
   30 s ≈ 24 h), held fixed, with the curve as the sole calibration lever — and
   why: halving this and halving `SKILL_XP_BASE` are observationally identical,
   so two knobs doing one job make the system uncalibratable after the fact.
3. **`world/improvement.py`'s docstring corrected in place.** The claim that the
   self-throttle *"is the pacing engine — no hidden XP accumulator is needed"* is
   marked SUPERSEDED with the measurement that falsified it (a factor of 2.4 is a
   texture, not a curve) and with what replaced it. The old sentence is quoted so
   a later reader sees the file was wrong rather than seeing a file that was
   always right.

**Two more stale claims, found only because we went looking.** C.2 shipped the
three-outcome branch but left the prose around it describing the two-outcome
world. `_improvement_feedback` still asserted *"a rolled tick always has
delta >= 1 ... so rolled=True is a sufficient gate"* — with the counter-example
three lines below it — and the tier celebration's idempotence argument still
rested on `delta >= 1` and on "a tick gains at most 5", where the 5 is now XP
rather than points. Both are superseded in place in `649224e`, a commit proved to
be comments-only by comparing the module's AST with docstrings stripped before
and after (identical). **That is three false claims in one epic**, each of the
same shape: prose asserting the sufficiency of a mechanism that has since
changed. The pattern is now explicit — when a mechanism changes, the sentences
asserting what it guarantees are part of the change.

**The false pass — and what it says about how in-game steps must be written.**

The F7 step first "passed" without running. The craft it used **failed**, the
success-only gate returned before the engine was reached, and the step's expected
observation — *the level stays at 60* — was produced by nothing happening at all.
It read exactly like success.

The rule that falls out: **a test step whose expected outcome is "nothing
changed" must carry an independent receipt that the code ran.** Here that is the
success message plus a moved XP total. This is the in-game twin of the unit-test
finding below, and both were found the same way — by asking what else could
produce this observation. Recorded in Testing Reference Rev 5 §11.

**Measured, not asserted — six mutations.** (1) `.current` written
unconditionally: **1 failure**, and only one — every value-equality assertion in
the file stays green, because the value written equals the value already there.
Only a spy on the property setter distinguishes them, which is why §5's test (b)
demands the Attribute not be written rather than the value be equal. (2)
Reverting the central line to `old + gained`: **12 failures** across six of seven
classes. (3) The F7 repair deleted: **2 failures**, both de-levellings. (4) The
cap short-circuit deleted: **2 failures and 1 error**. (5) The `delta == 0`
branch deleted, i.e. the "+0" copy: **3 failures**. (6) The practice line
reworded to borrow "improves": **1 failure** — worth running because the sentence
reads fine and passes both other feedback tests.

**One gap stated rather than hidden:** moving the tier celebration back out of
the `delta > 0` branch is green in every test. It is a genuine no-op there
(`old == new` means the tiers match), so its placement is structure, not
behaviour. It sits inside the branch because D.1 will be rewriting the code
around it — but the green suite is not evidence that it must.

**The engine had no tests at all before this.** All 363 baseline tests would have
stayed green if `improve_skill_on_use` had been deleted outright;
`attempt_skill_improvement` and `_improvement_feedback` were equally uncovered.
`tests/test_improvement_engine.py` is the first net under any of them, so "the
suite is still green" is not evidence about this method — the mutations are.

**Calibration is pinned, not swept, in this file** — `override_settings(6, 20)`
— which is the opposite of `tests/test_progression.py` and `tests/test_skill_xp.py`.
Those sweep because what they assert must hold under any constants P-5 hands
them. Several assertions here are only *meaningful* where one point costs more
than one tick's grain; at a degenerate calibration "the level rises by exactly 1"
would be a false failure.

**A curve fact the tests found.** `xp_threshold` floors, and at (6, 20) the raw
cost of point 2 is 6.21 XP — so points 1, 2 and 3 all cost exactly 6. "Each point
costs strictly more than the one before" is **false** at the shipped calibration
near the origin; the curve is exponential in the limit, not monotonically strict
at integer resolution. The assertion was written that way first and the test
caught it.

**Carry into D.1:** `improve_skill_on_use` returns `progress` — the
`(earned, needed, fraction)` triple from `progress_within_level` — on every
branch including the capped one, so the bar has its input without a second read.
Measured live at craft 21: `(6, 12, 0.5)`. D.1's job is to delete the practice
line, not to add a branch beside it.

---

## 6. Component D — the bar, and the ceiling

### Task D.1 — derived progress bar

- **Goal:** Show progress *within* the current percentage point, computed on read.
- **Dependencies:** A.1, C.1.
- **Implementation:** `progress_within_level()` renders to a bar in
  `_improvement_feedback` and in `CmdProgress`. Nothing is stored (P-1, and the
  rejection above).

  ⚠️ **Never use `|` in the bar art.** Evennia's colour parser reads `|_` as a
  space, `|/` as a line break, `|-` as a tab and `||` as a literal pipe — a bar
  drawn with pipes will render as garbage. Use `█`/`░` or `#`/`-`.
- **Testing — in-game:** craft once, read the bar, craft again, read it again —
  the bar must move on a tick where the percentage did **not**. That single
  observation is the whole justification for the component: it is what restores
  Stage 1's felt-progress promise under a curve that levels rarely.
- **Commit:** `feat(progression): derived progress bar within the current point`

#### Delivered 2026-08-15 — D.1, four locked decisions and a fourth false claim

Shipped on `feature/skill-progression`. **416 tests green** (391 baseline + 25
new), full suite 585 s. Five files changed plus one new test module; the in-game
protocol was run against the live server and every step is accounted for below,
including the two steps this document got wrong.

**The measurement that decided the bar's resolution.** §6's original text
specified `█`/`░` and said nothing about width or granularity, because it assumed
the bar's problem was rendering. It is not; it is *resolution against a moving
denominator*. A tick banks 1–5 XP while `needed` grows exponentially, so the
share of the bar one tick moves shrinks all the way up the curve. Simulated over
10 000 ticks at INT 12, the proportion that move at least one cell of a 20-cell
whole-block bar:

| skill | needed | N=10 | N=20 | N=40 | N=20, eighth-blocks |
|---|---|---|---|---|---|
| 20 | 12 | 0.99 | 1.00 | 1.00 | 1.00 |
| 40 | 24 | 0.80 | 0.95 | 1.00 | 1.00 |
| 60 | 48 | 0.47 | 0.69 | 0.92 | 1.00 |
| 80 | 96 | 0.19 | 0.37 | 0.59 | 1.00 |
| 90 | 136 | 0.11 | 0.23 | 0.42 | 1.00 |
| 99 | 186 | 0.07 | 0.14 | 0.28 | 0.88 |

At skill 90 a whole-cell bar is identical to the previous one on **four crafts in
five** — the silence C.1 created and this component exists to remove, displaced
one level down. It would also have made this document's own in-game step ("craft
again, the bar must move") true only below about skill 50, i.e. a protocol that
passes where nobody plays and fails where they do.

Eighth-block partials (`▏▎▍▌▋▊▉`) give 160 states across 20 cells and resolve
**every single banked XP** until `needed` exceeds 160, which the curve does not
reach until skill ~95. Above that the bar is coarser than the grain again; that
is an accepted floor, stated rather than hidden, because no fixed-width bar can
resolve a `needed` that D.2 is about to make unbounded.

**Evennia's `health_bar` contrib — evaluated and rejected.**
`evennia/contrib/rpg/health_bar/health_bar.py::display_meter(cur, max, …)` takes
its arguments in the same order `progress_within_level` returns them, so
`display_meter(*progress[:2])` would have worked mechanically. Rejected for three
reasons, the third decisive:

1. It draws with **background colours** (`|[G` over spaces), not glyphs. With
   `show_values=False` and no `pre_text` the string is blank — invisible in any
   client that does not render background colour, as its own docstring notes for
   screen readers.
2. `show_values=True` writes `"6 / 12"` inside the bar. That is precisely the
   second progression figure **P-8** rejects, and it would have to be un-taught.
3. `fillcolor_index` picks red→yellow→green **by fullness**. On a health meter
   red means danger; on a progress bar "nearly empty" means *early in the point*,
   so the bar would turn red every time the player levels. Points 1 and 2 are
   workaroundable; point 3 means working around them leaves four lines of
   arithmetic we write anyway.

**The four locked decisions.**

- **[RESOLVED] D-1 — bar resolution: 20 cells with eighth-block partials.**
  Alternatives: 20 whole cells (silent at high skill, and would have required
  rewriting this section's own protocol step to name a skill band); 40 whole
  cells (still 0.42 at skill 90, and 40 characters is wide for a message stream).
  Confirmed in Adam's client that the partial glyphs render at sub-cell widths —
  a rendering check with three fractions one-eighth apart, chosen so that a
  font falling back to full blocks produces two *identical* rows rather than a
  judgement about pixel widths.
- **[RESOLVED] D-2 — the bar renders on `delta == 0` only.** A level-up resets
  the numerator (measured: 59 → 60 yields `(0, 48, 0.0)`), so a bar under
  "improves!" would be near-empty and read as a demotion in the same breath as
  the praise. Drawing it *full* instead was considered and rejected outright: a
  bar showing anything other than `progress` is a second truth, which is the
  class of bug P-1 exists to prevent. One felt-progress signal per tick.
- **[RESOLVED] D-3 — `CmdProgress` keeps the session delta; the skip-unchanged
  rule falls.** The rule was correct while a tick moved the percentage nearly
  every time; after C.1 "unchanged" is the normal case, so the command answered
  *"No skills have improved since you logged in"* for hours — the same silence
  C.2 fixed one level down, in the feedback line. Every skill is now listed every
  time and the delta becomes a `(+n)` **suffix** on the rows that earned one.
  Retiring the login snapshot entirely was rejected: the two figures answer
  different questions at different grains ("what did this session buy me" vs
  "how far into the next point am I"), so neither subsumes the other, and C.3
  had shipped one commit earlier.
- **[RESOLVED] D-4 — a bar that cannot move is replaced by a caption.**
  `(not yet trainable)` for skills no call-site routes through
  `attempt_skill_improvement`; `(at maximum)` at the cap, where the total freezes
  inside `[threshold(cap), threshold(cap+1))` and a bar would show a partial fill
  that never moves again. Drawing dead bars reads as broken; hiding the rows
  hides that three of five skills are untrained content.

**Deviation — `improvable_skills` is a seventh place that can drift.** D-4 needs a
predicate for "cannot be trained", and it cannot be derived: a skill with no
stored XP entry is either untrainable *or* trainable-but-untouched, and a fresh
character would have Craft mislabelled until her first craft. So it is declared,
as `Character.improvable_skills`, **display-only and explicitly not a gate** —
the policy of which uses teach remains "which call-sites exist" (P-6). Drift
costs a wrong caption and nothing else, but a wrong caption is silent, so
`TestImprovableSkillsSet` holds the set against the call-sites by **AST** (a text
grep matches the call inside the three docstrings that quote it) and against
`HARVEST_TEMPLATES` as data, since `CmdHarvest` passes `part["skill"]` and no AST
can resolve a dict lookup. That gap is stated in the test rather than papered
over.

**The fourth false claim — and this document produced it.** In-game, a tick moved
Craft from **20 to 60 in one move**, and reproduced on demand:

```
craft=20 xp=1195  →  craft  →  Your Crafting improves! (+40, now 60%)
craft=40 xp=1399  →  craft  →  Your Crafting improves! (+24, now 64%)
```

`_improvement_feedback` asserted *"a single tick can now move at most ONE point,
so each boundary is crossed on exactly one tick"* — a claim C.2 wrote while
retiring two older ones. It is false whenever `.current` sits below what the
stored total buys, and it is **§6's own in-game protocol that puts it there**:
steps 10 and 11 tell the tester to set `.current` by hand. This is F7's shape
exactly — the spec's protocol manufactures the state the spec's prose says cannot
occur — and it is the fourth claim of this epic to fail the same way. The
behaviour is correct: P-1 says XP is the truth and `.current` is a cache, so the
cache catching up is the system working. Superseded in place with both prior
versions left visible. What survives is weaker and sufficient: the celebration
fires only on a tier *change* and the level is monotonic, so a tier is announced
at most once per character; a multi-point jump names the tier landed in and says
nothing about those passed through, because `tier_for` reports standing, not
history.

**Two errors in this document's protocol, corrected.** Step 7 predicted
`(+1, now 41%)` from 200 banked XP; at level 60 that buys four points, and the
prediction was written against level 40 without being checked against the curve.
Step 10/11 leave `.current` out of sync with the total and are what produced the
jump above — the cleanup must precede the out-of-band writes, not follow them.
Both are the protocol's fault, not the code's.

**Verified in-game.** Every branch of `_improvement_feedback` was exercised
against the live server:

- `delta == 0` → labelled bar, no digit, no "improves"
- three consecutive ticks at Craft 64 (xp 1409 → 1410 → 1412) → three
  **different** bars, percentage steady at 64% throughout. That is the single
  observation this whole component rests on, and no earlier run had produced it
- `delta > 0` → "improves!" plus tier line, **no bar**
- gated out → silence. Proved by an accidental double-craft: a *successful* craft
  produced no feedback line at all because `improvement_cooldown` had not
  elapsed, while the XP counter moved between readings — an absence with an
  independent receipt, which is §11's rule applied without being asked
- `progress` shows every skill, captions the three untrainable ones, shows
  `(at maximum)` at the cap, and reads `.current` not `.value` (`value=84.0
  current=64` displayed as `64%` with no `(+20)`)

**Mutation-verified — seven introduced and measured.** Removing the partials
fails the resolution test; removing the width compensation fails the constant-
width test; `_BAR_EMPTY = "|"` fails the glyph whitelist; drawing the bar on
`delta > 0` fails D-2's test; re-introducing the skip rule fails five tests;
reading `.value` in `CmdProgress` fails the buff test. The seventh is the
interesting one: **removing the `fraction` clamp changed nothing** — the clamp
around `eighths` already covers −0.3, 1.5, `None` and NaN, so it read as dead
code. It is not: `int(inf * 160)` raises `OverflowError`, and a dedicated test
was added for the one input the other guard cannot save.

**Second content dependency, alongside §7's.** The recipe catalogue was read live
during the protocol: **all eight recipes have `tools=[]`**. No recipe requires a
tool, which makes `world/crafting_base.py`'s `tool_broke` branch unreachable in
current content, and means the `.value`-vs-`.current` guard in the improvement
path defends against a state the catalogue cannot presently produce. The guard
stays — it is correct — but "verified in play" is not true of it until a recipe
takes a tool. Same content dependency that blocks Component E, and it belongs
next to it.

### Task D.2 — Legend's >100% band

- **Goal:** Lift the cap (P-7).
- **Dependencies:** C.1.
- **Implementation:** The rule is **already written**, in `world/improvement.py`'s
  docstring under *"Deliberate deferral — skills above 100%"*, with the exact
  expressions:

  ```
  target      = 100 if skill_value > 100 else skill_value
  int_applied = int_char // (2 ** max(0, (skill_value - 1) // 100))
  beat        = (roll + int_applied) > target
  ```

  Gains stay 1D4+1 / +1. The `max=100` on the skill traits must be raised or
  removed, and `improve_skill_on_use`'s `cap` short-circuit (`old >= cap` returns
  `rolled=False`) removed with it.
- **Why it is nearly free:** the curve has no table and no terminus (A.1), so
  above-100 levels need no new arithmetic — only the roll's second band and the
  trait cap.
- **Testing — unit:** at skill 150 the INT applied is halved and the target is
  100, not 150; at 250 it is quartered. `improvement_roll` at exactly 100 uses
  the ≤100 band (the boundary the `>` in the docstring formula decides).
- **Commit:** `feat(progression): implement Legend's above-100% improvement band`

#### ✅ Delivered 2026-08-24 — `a970883`, 429 tests green

The task above is left standing; this block says which parts of it survived
contact with the code. Two did not: the cap lived in **eight** places rather than
the five this spec names, and the trait `max` could not simply be "raised or
removed" on existing characters without deciding *where* the removal happens.

**The five decisions, locked as A/B/C before any code was written.**

| # | Question | Locked | Why |
|---|---|---|---|
| 1 | Unbounded, or a new number? | **No `max` at all** | A number would be a second throttle on a curve that already strangles the top of the scale. Measured at (6, 20) with INT 12: a point costs 192 XP at skill 100, 1 086 at 150 (~8 h of pure 30 s cooldown) and 6 144 at 200 (~44 h). `improvement_cooldown` was frozen for exactly this reason; a ceiling would have re-introduced the shape. Site count 5 → 0. |
| 2 | What does `tier_for` show at 140? | **`descs` untouched** | `tier_for` already returns the highest label above the highest bound, so 140 reads `master`. New bands would need rewriting in `at_object_creation`, in `HUNTING_SKILL_DEFAULTS` *and* on every existing character's stored trait — the migration surface of decision 3, doubled, for cosmetics. Deferred to `docs/BACKLOG.md` (*UX & Item Identity*). |
| 3 | Migration for existing characters' `max` | **Constructor + write-time repair** | See the finding below. |
| 4 | The bar above 100 | **Accept and document** | See the accepted limit below. |
| 5 | What `int_bonus` means in the second band | **The applied figure** | `total` is documented as `roll + int_bonus`. Reporting the raw INT score would have falsified that line the moment anyone passed 100 — the same shape of stale claim this epic has retracted five times, written with open eyes. |

**⚠️ The finding: a read-time migration was not available, and B.2's rule is why.**

B.2 shipped as a read-time fallback rather than a written backfill, and §4's
Delivered block gives the reason: the population a one-shot script must cover has
no end. That reasoning applies here and its *remedy* does not, for a reason worth
stating plainly — **B.2 owned the read**. `SkillXPHandler.get()` is ours, so a
fallback had somewhere to live. A `CounterTrait`'s ceiling is enforced inside
Evennia's own setter:

```python
@current.setter
def current(self, value):
    if isinstance(value, (int, float)):
        self._data["current"] = self._check_and_start_timer(self._enforce_boundaries(value))
```

`_enforce_boundaries` returns `self.max` when the value reaches it. So on a
pre-D.2 character `skill.current = 101` **silently stores 100**, and by the time
any reader looks, the clamping has already happened. There is nothing to
intercept. The write has to occur.

It occurs in `improve_skill_on_use`, beside the F7 floor repair, rather than in a
one-shot command — for B.2's stated reason plus one more: a script covers only
the characters alive when someone remembered to run it, and **does not survive a
restored backup**. Routing it through the single writer (P-2) makes it idempotent
by construction: after the first tick there is nothing left to write, forever.
`at_object_creation` and `HUNTING_SKILL_DEFAULTS` stop setting `max` in the same
commit, so the repair is not manufacturing work for itself.

**⚠️ The cap lived in eight places. Three were prose, and prose has no tests.**

The five inventoried: `improvement_roll`'s single band; the `old >= cap`
short-circuit; `max=100` on five traits; `HUNTING_SKILL_DEFAULTS`; the
`(at maximum)` caption and its test (deleted, not adjusted — a test whose
mechanism no longer exists is a false claim wearing a test's name).

The three that were not, all found by the prose-verification loop after the code
was believed complete:

1. `attempt_skill_improvement`'s cooldown comment — *"a maxed skill (rolled=False)
   can't grow, so it shouldn't burn a cooldown"*. `rolled` is now always `True` on
   the non-`None` path, so the second half of that condition is a shape check
   rather than a signal, and the cooldown is in practice burned on every eligible
   attempt.
2. `_improvement_feedback`'s *"returns `progress` on every branch including the
   capped one"* — there is one branch now.
3. `world/recipes.py`'s *"max craft quality is 110 (skill cap 100 → crit_score
   10), so no craft ever reached 125"* — **the fifth falsified production claim of
   this epic, and the first caught before it went false.** `crit_score` is
   `.value // 10`; a crafter at skill 250 stamps 125 and reopens the branch the
   comment justified removing. The removal still stands, for a better reason: the
   band helper is the single place quality is classified.

**The accepted limit: the bar's resolution runs out at skill ~96, not at 100.**

D-1 gives 20 cells × 8 eighth-blocks = 160 renderable states, and at (6, 20) a
point first costs more than 160 XP at level **96** (161). Above that a single
banked XP can leave the art unchanged. At 150 a point costs 1 086 XP, so one
grain moves 0.15 of an eighth and — because the second band halves applied INT,
dropping the beat rate to ~6% — nearly every tick *is* one grain. The bar steps
about once every seven ticks up there. **That is D.1's own silence returning
fifty points higher up**, and it is accepted rather than overlooked: a longer bar
breaks D-1's 20 cells and the column alignment for a band almost nobody reaches,
and a caption would be dishonest (the bar is coarse, not dead). Revisit only if a
player is ever observed above ~130.

**Two things deliberately left alone.**

- `crossed` stays `(25, 50, 75, 100)`. 100 remains the top celebration, which is
  where mastery honestly sits; marks at 125 or 150 would celebrate altitudes the
  curve makes nearly unreachable.
- `world/skillcheck.py::opposed_check` keeps its **own** unimplemented >100% rule
  (highest mastered skill drops to 100, the excess penalises everyone). It is a
  separate decision with its own motivation. `world/improvement.py`'s old
  deferral note bundled the two into one sentence, which made them look like one
  decision; they are not, and lifting this cap does not decide that one.

**Mutations — five run, one survivor, and the survivor is provable.**

| # | Mutation | Predicted | Killed | |
|---|---|---|---|---|
| M1 | `max(0, …)` dropped from the INT divisor | 1 | 1 — `…never_multiplies_the_int` | ✅ |
| M2 | `target = 100 if skill_value >= 100 else …` | 0 | 0 | ✅ |
| M3 | `beat = total > skill_value` (band removed) | 1 | 2 — `…target_is_100_and_not_the_skill`, `…gain_is_untouched_by_the_band` | ⚠️ |
| M4 | the `max` repair removed | 1 | 1 — `…legacy_trait…is_repaired…` | ✅ |
| M5 | `"int_bonus": int_char` (raw, not applied) | 1 | 3 — `…halved_one_point_later`, `…quartered_in_the_third_band`, `…roll_plus_the_applied_int` | ⚠️ |

**⚠️ M2 is a provably equivalent mutant, not a gap in the tests.** For every
integer input, `100 if sv > 100 else sv` and `100 if sv >= 100 else sv` return
the same value — at `sv == 100` the first yields `sv` (100) and the second yields
100. §11b's question (*"which input class does no test cover?"*) has no answer
here, because no input distinguishes them. **That correction matters beyond the
mutation run:** `improvement_roll`'s shipped comment claims the `>` is *"what
puts a skill of exactly 100 in the FIRST band … a decision, not an accident of
arithmetic"*. The decision is real; it is **not expressed there**. The entire
band boundary is carried by `(skill_value - 1) // 100` in the INT divisor. The
comment is corrected in place rather than deleted, since a reader who trusts it
would mutate the wrong line.

M1 is the one worth keeping in mind for its own sake: Python floors toward
negative infinity, so `(0 - 1) // 100 == -1` and `2 ** -1` is the **float** 0.5.
Without `max(0, …)` a skill of 0 gets `int_char // 0.5` — a *doubled* bonus, and
a float. The guard is not defensive tidiness; the band inverts at the bottom of
the scale without it.

**⚠️ `improvement_roll` had zero tests before this task.** P-3 kept the module
untouched through Components A–C, and `tests/test_improvement_engine.py` says
outright that it tests "the reinterpretation, not the roll". D.2 is the first
change to that module since it was written, so the 416-test baseline it inherited
proved nothing whatsoever about the arithmetic being changed. `tests/test_improvement_roll.py`
is new: 9 tests. Total 416 → **429** (5 deleted with the mechanisms they guarded,
18 added).

**Deviations — three, all in delivery rather than in design.**

1. **The `max=100` removals were delivered as one full block plus four
   "same, but with this line" abbreviations.** One of the four was applied with a
   duplicated comma and the server refused to start (`SyntaxError`, `0: "clumsy",,`).
   The delivery contract says ERSÄTT/MED blocks cover *entire* units because the
   prose is part of the patch; four abbreviations are four patches that were
   described rather than delivered. It failed loudly here only by luck — an
   abbreviation covering a *condition* rather than a dict entry would have
   compiled.
2. **The in-game protocol's step 6 was arithmetically wrong**, and the unit test
   for the same behaviour was right. The protocol said to add a fixed 192 XP; the
   character had a real stored total of 1 414 (level 64), so it reached 1 606 and
   not the 5 466 that buys point 101. The test computes
   `xp_threshold(101) - get()` — an absolute set. **The protocol and the test
   should have been the same expression** and were not.
3. **Two of the three prose sites above were missed by the delivered blocks** and
   found only by the verification loop, which is the third occurrence of this
   exact shape in this epic.

**In-game verification (2026-08-24), all thirteen steps.** The two that carry the
result: `craft twine from fiber-1, fiber-2, fiber-3` →
`Your Crafting improves! (+1, now 101%)`, and the invariant read back as
`(101, 101)` — `.current == level_for_xp(total)` holding **above** 100, which is
the property the deleted short-circuit existed to defend and now holds
unconditionally. `skill.max` read `100` before the craft and `None` after it,
proving the repair fired inside a real tick and not inside a `@py` call.

---

## 7. Component E — the difficulty gate ⛔ BLOCKED, and **no longer part of this epic**

> **Moved out 2026-08-24, at Stage 4.5 close-out.** E is blocked on a content
> trigger that belongs to no scheduled stage, and a stage held open by an
> unscheduled trigger blocks the next one without anyone having decided to —
> here, Stage 5 (Combat), which must not begin before 4.5 closes. Keeping E
> inside the epic would have made that blockage implicit; moving it makes the
> cost visible and the trigger armed. The section below stands unchanged as the
> design; its home is now `docs/BACKLOG.md` (*Crafting & Tools*, BLOCKED), which
> already carried the blocker entry, and the roadmap's Stage 4.5 entry records
> the close-out. Nothing about the design changed — only which document is
> responsible for remembering it.

**Status: BLOCKED on recipe content. Do not schedule it after D; it is not a
"later" task, it is a task with an unmet precondition.** Written down now because
it is the answer to a question that was open for two revisions, and an answer
nobody wrote down is indistinguishable from an oversight.

*(Rev 5 — tone correction.)* Rev 4 wrote the blocker as though a problem had been
discovered. Nothing is wrong: the catalogue is small because the game is early,
which is the expected state and not a defect. What follows is a **sequencing**
fact — E reads a difficulty ladder, the ladder does not exist yet, so E waits.
The numbers below are what makes it concrete, not an alarm.

### Why it exists

Components A–D make progression *slow*. They do nothing about making it
*meaningful*. With a flat grain, the optimal way to reach craft 100 is to pick
the cheapest recipe you know and repeat it 2 931 times — the curve taxes the
grind but does not object to it. Scaling the grain by material cost inverts the
exploit rather than removing it (see §2, *Explicitly rejected*).

The lever that removes it is difficulty **relative to the crafter**, and the seam
for it already exists and has never been used. `attempt_skill_improvement`'s
gate 2 carries this comment:

> *"Real difficulty: `meaningful` must be True. Trivial/auto-pass call sites pass
> `meaningful=False` so AFK-farmable actions don't reward. Currently a **seam**,
> not a policy: both live call sites are meaningful and use the default. When
> trivial checks exist, they opt out here — we don't build the difficulty
> heuristic speculatively."*

Crafting something far below your skill **is** the trivial case that seam was
built for. It is also Legend-faithful: routine tasks do not earn an Improvement
Roll. P-3 is untouched — the roll is not modified, it simply is not attempted.

### ⛔ Why it cannot ship yet — the ladder does not reach

The gate needs a per-recipe difficulty. One exists: `MongooseCraftRecipe.min_skill`.
Its current state, measured 2026-08-05:

| recipes in `world/recipes.py` | 8 |
| with `min_skill` set | **1** (`LeatherBootsRecipe`, 30) |
| all others | default 0 |

With a trivial band of 30 points, a recipe stops teaching once your skill exceeds
its `min_skill` by more than the band. The highest `min_skill` in the game is 30.
**Therefore nothing in the game teaches Craft above 61**, and a crafter who
reaches 61 can never improve again. That is not a tuning problem to be softened
with a smaller band — a band of 50 merely moves the wall to 81 — it is a
statement that the recipe catalogue does not span the skill scale.

A dead end is strictly worse than the grind it replaces. Shipping E against the
current catalogue would be a regression.

**Rejected mitigation — a soft gate that reduces XP rather than blocking it.**
It looks like the safe version and is not. At high skill the roll's grain is
already at its floor of 1 (the mean is 1.38 at level 95), so a "trivial crafts
bank less" rule has almost no effect at exactly the levels where grinding is
worth doing. It buys the appearance of a fix at the cost of a second mechanic to
calibrate.

### Trigger

The recipe catalogue spans the skill scale: `min_skill` values form a ladder with
**no gap wider than `SKILL_TRIVIAL_BAND`** from 0 up to the intended ceiling. In
practice that means recipes at roughly 0 / 20 / 40 / 60 / 80, not eight recipes
clustered at the bottom. That is a content milestone, not an engineering one, and
it belongs to whichever stage grows the crafting catalogue.

### Tasks, when unblocked

**E.1 — `min_skill` for the whole catalogue.** Assign a deliberate `min_skill` to
**every** recipe — including `LeatherBootsRecipe`, whose 30 is a placeholder and
not a value to build a ladder around. This is a fresh pass over the whole
catalogue, not a fill-in-the-blanks around one anchor. Pure data in
`world/recipes.py`, inside OpenCode's permitted scope (`AGENTS.md`) — bulk,
mechanical, no production logic. Depends on the catalogue being large enough to
ladder; until then it is guessing.

⚠️ **`min_skill` would be carrying two jobs, and they disagree about which value
to read.** Today it is a **hard access floor**: `crafting_base.py:263` refuses the
craft outright when `_skill_value() < min_skill`, and it reads `.value` on
purpose, so a tool buff may lift you over the bar ("are you good enough to
*attempt* this right now"). E.2 would read the same field as a **difficulty
datum**, and must read `.current` — a temporary buff must not make a task count
as harder, and therefore more instructive, than it is.

One number, two purposes, two readings. The consequence is not subtle: raise a
recipe's `min_skill` so that it keeps teaching at higher skill, and you have also
locked every lower-skill crafter out of it completely. With several rebalancing
passes expected, that coupling makes each pass harder to predict than it looks.

Two ways out, and E.2 must pick one **explicitly** rather than inherit the
coupling by accident:
  - **Accept it**, and state that `min_skill` means "the level this recipe is
    written for" with both effects following from that single meaning. Cheapest,
    and arguably the honest reading — a recipe you are barely qualified for is
    also the one that teaches you most.
  - **Give E its own field** (e.g. `teaches_until`), decoupling access from
    instruction at the cost of a second number per recipe to keep coherent.

Recorded here rather than decided, because the answer depends on what the grown
catalogue actually looks like — which is the same thing E is blocked on.

**E.2 — the gate itself.** One constant (`SKILL_TRIVIAL_BAND`, read per call via
`getattr(settings, ...)` following A.1's precedent) and one expression at the
craft call-site computing `meaningful=` from the recipe's `min_skill` against the
crafter's `.current`. ⚠️ Read `.current`, not `.value` — a tool buff must not
make a task count as harder than it is. No change to
`attempt_skill_improvement`; the seam is already shaped for this.

**E.3 — the other five call-sites: explicitly deferred, not forgotten.** Repair,
hunt-attack, hunt-harvest, disassemble and scribe have **no difficulty datum**
comparable to `min_skill`. Inventing one per site is a separate design problem
(is a repair's difficulty the item's condition? is a hunt's the creature's?), and
guessing five heuristics to be consistent with one real one is how a system
acquires four wrong answers. They keep `meaningful=True` — the generous side,
per P-5 — until each has a difficulty of its own. **Say this out loud in the
code**, or the asymmetry reads as a bug to the next person.

### Interaction with the rest of the epic

E is not a dependency of anything. A–D ship and work without it; the grind it
removes is unpleasant rather than broken, and the 24-hour curve makes
spoon-grinding tedious enough that it is unlikely to be anyone's first choice
before E lands.

---

## 8. Carry-forward

- **`CmdScribe` rolls Craft but grants no improvement** — **ANSWERED
  2026-08-05: it trains.** Folded into C.1 as the sixth call-site; P-6 updated
  from five to six. The reasoning is in §2's resolved sub-decisions. Kept here
  rather than deleted because this bullet is what forced the answer, and the
  `docs/BACKLOG.md` entry it points at moves to SCHEDULED rather than closing —
  it is not done until C.1 ships.
- **Calibration** is a settings change by construction (P-1). When there are
  players, recompute from observed action rates — not from genre benchmarks.
  RuneScape's ~250 h per skill buys a world with 23 skills and twenty years of
  content behind it.
- **`docs/PolishedWorld_Skill_Improvement_Decomposition.md`** (Rev 4) owns the
  Stage 1 layer this builds on. Its call-site inventory is marked as a planning
  snapshot; read it as history, not as a map.
