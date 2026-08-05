# PolishedWorld — Skill Progression (XP) Decomposition

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
| **P-5** | Calibration is **not fixed by this epic**. Constants carry provisional values plus the documented procedure to recompute them. Generous now, tightened never — lowering the curve later is free, raising it de-levels people. |
| **P-6** | Scope is the **shared primitive**, so all five improvement call-sites move together: craft, repair, hunt-attack, hunt-harvest, disassemble. |
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

### Open sub-decisions (answer before Component C)

- **[OPEN] XP grain scaling by recipe value.** The original sketch had XP
  proportional to material cost. It is a real lever — it is most of what gives
  RuneScape its shape without a brutal curve — but it interacts with the economy:
  it makes the most material-expensive craft the optimal grind, which is either a
  welcome sink or an exploit depending on how prices settle. **Not needed for
  A–D to ship.** If deferred, `xp_gained` stays `roll_result` and the multiplier
  slots in at one place in C.1.
- **[OPEN] `improvement_cooldown = 30` under the new regime.** With XP grains
  the cooldown becomes the dominant throttle rather than a spam guard. It is a
  calibration knob (P-5), listed here so it isn't tuned by accident.

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

The first task in this epic that changes what a player experiences. The five
call-sites are **not touched**: they call `attempt_skill_improvement`, which
calls `improve_skill_on_use`, and only the latter changes (P-6).

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

---

## 7. Carry-forward

- **`CmdScribe` rolls Craft but grants no improvement** (`docs/BACKLOG.md`,
  *Crafting & Tools*, OPEN). This epic has to answer it: it is the one roll-site
  of six that banks nothing, and "what earns progress" is precisely this epic's
  question. Decide it in C.1 or explicitly punt it again, but do not leave it
  unmentioned a second time.
- **Calibration** is a settings change by construction (P-1). When there are
  players, recompute from observed action rates — not from genre benchmarks.
  RuneScape's ~250 h per skill buys a world with 23 skills and twenty years of
  content behind it.
- **`docs/PolishedWorld_Skill_Improvement_Decomposition.md`** (Rev 4) owns the
  Stage 1 layer this builds on. Its call-site inventory is marked as a planning
  snapshot; read it as history, not as a map.
