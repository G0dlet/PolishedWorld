"""
world/skill_xp.py

Per-skill lifetime XP store for PolishedWorld. Stage 4.5, Component B.

P-1 makes lifetime-total XP per skill the sole persisted truth of skill
progression; level and progress bar are derived from it and never stored. This
module owns that persistence and nothing else. The *shape* of the curve lives in
`world/progression.py`, which this module reads and never duplicates.

NOTHING READS THIS FOR GAMEPLAY YET. Component B is storage with no consumer,
exactly as Component A was arithmetic with no consumer. Only Component C changes
what a player experiences. If you are looking for the code that makes a craft
bank XP, it does not exist on this branch.

WHY A SEPARATE MODULE FROM progression.py
-----------------------------------------
`world/progression.py` states in its docstring that it holds no Evennia objects,
does no I/O and reads no traits -- which is what tells you its tests can run on
the cheap `EvenniaTestCase` with no object graph. This module does all three. The
split keeps that claim true and keeps the two test base classes from blurring
together. Same division as `world/improvement.py` (pure roll maths) beside
`world/currency.py` (the wallet handler).

Note the module imports nothing from Evennia, matching `world/currency.py`. The
handler is duck-typed on `obj`: it needs `obj.attributes` and `obj.skills` and
asks for nothing else.

NO ATTRIBUTE IS DECLARED ANYWHERE FOR THIS
------------------------------------------
Deliberate, and the same reasoning D6 applies to the wallet. There is no
`AttributeProperty` on Character and no `at_object_creation` initialisation for
`skill_xp`, so there is no `char.skill_xp = {...}` shortcut for code outside this
module to reach for. P-2's single-writer rule is enforced by there being no other
way in, rather than by review vigilance.

THE ABSENT-ENTRY RULE -- READ THIS BEFORE CHANGING get()
--------------------------------------------------------
A skill with no stored entry does **not** read as 0. It reads as
`xp_threshold(skill.current)`: the minimum lifetime total consistent with
standing at the level the character already has. That value is computed on read
and **never written**.

This is the whole of Component B.2, and it replaces the decomposition's
"one-time backfill" with a fallback. The reason is a measurement, not a
preference: `at_object_creation` gives every new character non-zero skills
(perception 25, stealth 20, athletics 25, hunting 25, craft = DEX + INT = 20 at
default stats). A one-shot migration is therefore one-shot only for the
characters that existed when it ran; every character created afterwards would
stand at craft 20 with 0 XP, and Component C -- which makes `.current` a
materialised cache of `level_for_xp(total)` -- would de-level her to 0 on her
first craft. That is precisely the data loss B.2 exists to prevent, and a
migration cannot prevent it because the population it must cover has no end.

Deriving on read closes it permanently and for free:

* No character can be de-levelled, regardless of when she was created, whether a
  backup was restored, or whether an admin ever remembered to run anything.
* Idempotence is not achieved by a guard, it is achieved by **not writing**. This
  is the same proof shape `world/currency.py` uses for the wallet: the
  `TraitHandler.add(force=True)` class of trap (Evennia Reference 3.5) cannot
  occur here because nothing writes a starting value.
* The Attribute is not created until the first genuine bank, so a character who
  has never improved a skill carries no XP row at all.

The cost, stated honestly: until a skill's first bank, the causal direction is
the reverse of P-1 -- the level is the truth and the XP is derived from it. It
inverts to P-1's direction permanently at the first `add()` and never inverts
back. An explicit backfill has the same inversion; it just lasts one instant
instead of lasting until first use.

⚠️ THE ONE LINE THAT CAN DE-LEVEL A CHARACTER is in `add()`: the first bank must
add the roll's grain to the *derived floor*, not to 0. `tests/test_skill_xp.py`
::TestFirstBank exists solely to hold that line down, and was mutation-verified
against it.
"""

from collections.abc import Mapping

from world.progression import xp_threshold


class SkillXPHandler:
    """
    Per-object lifetime XP store, one integer per skill key.

    Wired onto Character via `@lazy_property` in the same way as
    `stats`/`traits`/`skills`/`cooldowns`/`currency`.

    The handler property and the Attribute share the name `skill_xp` (unlike
    `currency`/`wallet`). That is safe -- `lazy_property` writes a plain instance
    attribute, and Evennia's Attribute namespace is reached only through
    `obj.attributes` -- but it is worth knowing which is which: `char.skill_xp`
    is this handler, `char.attributes.get("skill_xp")` is the stored mapping.

    ERROR CONVENTION (D7)
    ---------------------
    An invalid amount raises; it is a bug in the calling code and not a
    condition a player can be in. There is no expected-failure return value at
    all -- `add()` always either banks or raises.

    Banking into a skill key the object has no trait for does NOT raise. That
    looks inconsistent with the paragraph above, and the reason it is not is
    that `Character.improve_skill_on_use` already made this exact decision in
    the opposite direction, deliberately: it returns None for an unknown skill
    "rather than raising, so a shared call site that passes a key this character
    lacks stays safe" -- and it is the only caller that will ever reach `add()`.
    A second guard here could only fire for a caller that had already bypassed
    the first one, and its only effect would be to abort a live craft. Orphaned
    entries are instead made visible by `all()`, which unions the stored keys
    with the character's real skills.
    """

    def __init__(self, obj, db_attribute="skill_xp"):
        """
        Args:
            obj (Object): the object whose XP this is.
            db_attribute (str): Attribute key for the mapping. Matches the
                `CooldownHandler(self, db_attribute="cooldowns")` house style.
        """
        self.obj = obj
        self._db_attribute = db_attribute

    # -- reading -----------------------------------------------------------

    def _store(self):
        """
        The stored mapping, or None if the Attribute has never been written.

        Returns:
            Mapping or None: Evennia hands back a `_SaverDict`, NOT a `dict`.

        ⚠️ `isinstance(store, dict)` is **False** for a `_SaverDict` (verified
        against Evennia 6.1.0, not assumed). Every membership and iteration test
        in this module goes through `collections.abc.Mapping`. The same trap bit
        the survival layer.
        """
        return self.obj.attributes.get(self._db_attribute, default=None)

    def _derived_floor(self, skill_key):
        """
        The minimum lifetime XP consistent with the level the object already has.

        Args:
            skill_key (str): e.g. "craft".

        Returns:
            int: `xp_threshold(skill.current)`, or 0 if the object has no such
                skill (or no skills handler at all, which is how this stays safe
                on a non-Character object).

        Reads `.current`, never `.value`. `.value` folds in situational `.mod` --
        a +20 tool buff worn while the fallback is consulted would otherwise
        invent an XP floor the character never earned, and freeze it in place at
        the next bank. Same reasoning `improve_skill_on_use` gives for reading
        `.current`.

        `int()` is explicit because `CounterTrait.current` is a **float** (20.0,
        verified live). Truncation is the correct direction: the floor must be
        the *smallest* total consistent with the level.
        """
        skills = getattr(self.obj, "skills", None)
        if skills is None:
            return 0

        skill = skills.get(skill_key)
        if skill is None:
            return 0

        return xp_threshold(int(skill.current))

    def get(self, skill_key):
        """
        Lifetime-total XP for one skill.

        Args:
            skill_key (str): e.g. "craft".

        Returns:
            int: the banked total if one is stored, otherwise the derived floor
                for the level the object currently stands at (see the module
                docstring's absent-entry rule).

        This is a pure read. It writes nothing, creates no Attribute and has no
        side effect, which is what makes it idempotent by construction rather
        than by guard.
        """
        store = self._store()
        if isinstance(store, Mapping):
            banked = store.get(skill_key)
            if banked is not None:
                return int(banked)

        return self._derived_floor(skill_key)

    def all(self):
        """
        Every skill key this object has XP for, banked or derived.

        Returns:
            dict: `{skill_key: lifetime_xp}` as a plain dict (never a
                `_SaverDict`), covering the union of the object's real skills
                and any stored key. The union is what makes an orphaned
                entry -- XP banked under a key with no matching trait -- visible
                instead of silent.
        """
        keys = set()

        store = self._store()
        if isinstance(store, Mapping):
            keys.update(store.keys())

        skills = getattr(self.obj, "skills", None)
        if skills is not None:
            keys.update(skills.all())

        return {key: self.get(key) for key in sorted(keys)}

    # -- internal ----------------------------------------------------------

    def _set(self, skill_key, total):
        """
        Write one skill's total. The ONLY place the XP Attribute is written.

        Private by convention and by intent: every public mutation funnels
        through here, so there is exactly one line in the codebase that can
        change an XP total, and it is trivially auditable.

        Copies to a plain dict and assigns the whole mapping back rather than
        mutating the `_SaverDict` in place (locked decision B-4). In-place
        mutation would persist too, but assignment keeps the audit property
        above -- one write site, one statement -- and sidesteps the
        mutable-shared-state trap that `Character.login_skill_snapshot` documents
        for its own dict. The copy is a handful of keys; the cost is not
        measurable next to the Attribute write itself.
        """
        store = self._store()
        updated = dict(store) if isinstance(store, Mapping) else {}
        updated[skill_key] = int(total)
        self.obj.attributes.add(self._db_attribute, updated)

    @staticmethod
    def _require_positive(amount):
        """
        Reject anything that is not a positive int.

        `bool` is excluded explicitly because it subclasses `int` -- without
        this, `add("craft", True)` would bank one XP.

        Deliberately duplicated from `CurrencyHandler._require_positive` rather
        than imported. Six lines of validation are cheaper than a dependency
        edge from the XP store to the money module, which have no other reason
        to know about each other.
        """
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError(f"amount must be an int, got {type(amount).__name__}: {amount!r}")
        if amount <= 0:
            raise ValueError(f"amount must be positive, got {amount}")

    # -- banking -----------------------------------------------------------

    def add(self, skill_key, amount):
        """
        Bank XP toward a skill. The single writer (P-2).

        Args:
            skill_key (str): e.g. "craft".
            amount (int): positive XP to bank. Component C passes the
                improvement roll's grain: 1 on the floor, 2-5 on a beat.

        Returns:
            int: the new lifetime total.

        Raises:
            TypeError: if `amount` is not an int (or is a bool).
            ValueError: if `amount` is not positive.

        Raising rather than clamping is the opposite of what
        `world/progression.py` does with a bad level, and the difference is the
        caller. progression.py is pure arithmetic that cannot validate its own
        input and sits under a live craft. Here the amount comes from
        `improvement_roll()`, whose contract already guarantees >= 1, through a
        single chokepoint we own. A silent no-op would mean XP never banks and
        the player's skill never moves -- invisible, and far worse than a
        traceback.

        ⚠️ `self.get()`, not a raw store lookup. On the first bank for a skill
        that is the derived floor, so a character at craft 20 who banks 3 lands
        on `xp_threshold(20) + 3`, not on 3. Reading 3 back through
        `level_for_xp` in Component C would put her at level 0 -- this line is
        the difference between the epic shipping and the epic wiping everyone's
        skills.

        Multiplayer note: read-modify-write on the Attribute. Evennia's Twisted
        reactor is single-threaded and does not preempt a command mid-call, so
        concurrent banks serialise safely without a lock -- the same property
        `improve_skill_on_use` and `CurrencyHandler.transfer_to` rely on. Do not
        introduce a yield, `utils.delay` or deferred between the read and the
        write.
        """
        self._require_positive(amount)

        new_total = self.get(skill_key) + amount
        self._set(skill_key, new_total)
        return new_total

    def __repr__(self):
        return f"<SkillXPHandler({self.obj}): {self.all()}>"
