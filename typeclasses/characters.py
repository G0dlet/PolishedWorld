"""
PolishedWorld Character typeclass

Implements Mongoose Legend characteristics with Evennia's Traits contrib.
Includes survival mechanics (hunger, thirst, fatigue) and skill system.
"""

from evennia.contrib.game_systems.clothing import ClothedCharacter
from evennia.utils import lazy_property
from evennia.utils.utils import delay
from evennia.contrib.rpg.traits import TraitHandler
from evennia.contrib.rpg.buffs import BuffHandler
from evennia.contrib.game_systems.cooldowns import CooldownHandler

from .objects import ObjectParent
from evennia import create_object, AttributeProperty
from evennia.utils import logger
from world.survival_buffs import DeathWeakness
from world.improvement import improvement_roll, tier_for
from world.currency import CurrencyHandler
from world.progression import level_for_xp, progress_within_level, xp_threshold
from world.skill_xp import SkillXPHandler

from django.conf import settings
from evennia.utils import search


# Tag category under which a Character's learned (known) crafting recipes live.
# Stage 3 / Component A. The known-recipe set is TAG-based, NOT an
# AttributeProperty set (§2 lock), for three reasons:
#   1. Queryable -- we can later find *who* knows recipe X with a tag search,
#      which an Attribute-stored set cannot do efficiently.
#   2. No mutable-default sharing trap -- there is no per-class list/dict that
#      could accidentally be shared across instances.
#   3. Case-insensitive round-trip -- the TagHandler lowercases keys on both
#      write and read, so callers need not normalise.
# We store the canonical *recipe name* (MongooseCraftRecipe.name, the recipe-
# registry key, e.g. "cloth" or "linen shirt"), never a prototype_key.
KNOWN_RECIPE_CATEGORY = "known_recipe"


class Character(ObjectParent, ClothedCharacter):
    """
    PolishedWorld character with Mongoose Legend integration.

    Uses three separate TraitHandlers:
    - stats: Mongoose Legend characteristics (STR, DEX, CON, SIZ, INT, POW, CHA)
    - traits: Survival gauges (hunger, thirst, fatigue, health)
    - skills: Learnable skills using percentile system (0-100%)
    """

    @lazy_property
    def stats(self):
        """
        Handler for Mongoose Legend characteristics (Static traits).

        These are the core attributes that define a character's 
        physical and mental capabilities. Each is calculated as base + mod.
        
        - STR (Strength): Physical power
        - DEX (Dexterity): Agility and reflexes  
        - CON (Constitution): Health and stamina
        - SIZ (Size): Physical mass and reach
        - INT (Intelligence): Reasoning and memory
        - POW (Power): Willpower and magical potency
        - CHA (Charisma): Personality and leadership
        """
        return TraitHandler(
            self, 
            db_attribute_key="stats",
            db_attribute_category="stats"
        )
    
    @lazy_property
    def traits(self):
        """
        Handler for survival traits (Gauge traits with rate support).

        These depletable resources affect character survival and performance.
        All use the Gauge type which empties from max (base + mod).
        
        - hunger: Food need (0=starving, 100=full)
        - thirst: Water need (0=dehydrated, 100=hydrated)
        - fatigue: Rest need (0=exhausted, 100=well-rested)
        - health: Hit points (0=dead, max=CON-based)
        
        Supports .rate for automatic changes (e.g., gradual hunger increase).
        """
        return TraitHandler(
            self, 
            db_attribute_key="traits",
            db_attribute_category="traits"
        )
    
    @lazy_property
    def skills(self):
        """
        Handler for learnable skills (Counter traits).

        Mongoose Legend uses a percentile system where skills range 
        from 0-100%. Base represents starting skill, current tracks 
        progress, and mod can apply temporary bonuses/penalties.
        
        Skills will be added dynamically as characters learn them.
        Common skills might include:
        - Athletics, Stealth, Perception
        - Combat skills (Swords, Bows, Unarmed, etc.)
        - Craft skills (Smithing, Carpentry, Cooking, etc.)
        - Lore skills (Nature, History, Magic, etc.)
        """
        return TraitHandler(
            self, 
            db_attribute_key="skills",
            db_attribute_category="skills"
        )
    
    @lazy_property
    def buffs(self):
        """
        Handler for temporary effects (Evennia buffs contrib).

        Carries survival rate-modifiers (e.g. hot/cold environment scaling
        hunger/thirst depletion) and condition markers (starving, dehydrated).
        Default dbkey "buffs" does not collide with the stats/traits/skills
        handlers, which use their own namespaced db attributes.
        """
        return BuffHandler(self)

    @lazy_property
    def cooldowns(self):
        return CooldownHandler(self, db_attribute="cooldowns")

    @lazy_property
    def currency(self):
        """
        Wallet handler: a single int Attribute denominated in Copper (S4-2).

        Note what is NOT here: no matching `self.currency...` call in
        at_object_creation, and no AttributeProperty declaration. Both are
        deliberate. The handler reads its Attribute with default=0, so a
        character who has never touched money simply has none and the Attribute
        is not created until the first mutation. That means existing characters
        need no backfill -- and because nothing writes a starting value, the
        TraitHandler.add(force=True) shape of trap (Evennia Reference 3.5)
        cannot clobber a live balance here.

        It also means there is no `char.wallet = 500` shortcut for anything
        outside world/currency.py to reach for, which is how S4-R2 is enforced
        by construction rather than by review.
        """
        return CurrencyHandler(self, db_attribute="wallet")

    @lazy_property
    def skill_xp(self):
        """
        Per-skill lifetime XP store (Stage 4.5, P-1). Storage only -- as of
        Component B nothing reads this for gameplay; Component C makes it the
        thing that moves `.current`.

        Note what is NOT here, and it is the same list as `currency` above: no
        `at_object_creation` initialisation and no AttributeProperty
        declaration. Both deliberate, both for D6's reason -- there is no
        `char.skill_xp = {...}` shortcut for code outside world/skill_xp.py to
        reach for, so P-2's single-writer rule holds by construction rather
        than by review.

        Unlike `currency` there is also no backfill task anywhere, and that is
        a stronger claim than "we did the migration". The handler derives an
        absent entry from the skill's own `.current` on read, so a character
        created after any migration would have run is still consistent, and
        cannot be de-levelled by Component C. See world/skill_xp.py's
        absent-entry rule for why a one-shot migration could not have covered
        that population.
        """
        return SkillXPHandler(self, db_attribute="skill_xp")

    def at_object_creation(self):
        """
        Called once when character is first created.

        Initializes all Mongoose Legend characteristics with base values,
        sets up survival traits at full, and prepares skills system.
        """
        super().at_object_creation()
        
        # === MONGOOSE LEGEND CHARACTERISTICS ===
        
        self.stats.add(
            "str", "Strength",
            trait_type="static",
            base=10,
            mod=0
        )
        
        self.stats.add(
            "dex", "Dexterity", 
            trait_type="static",
            base=10,
            mod=0
        )
        
        self.stats.add(
            "con", "Constitution",
            trait_type="static", 
            base=10,
            mod=0
        )
        
        self.stats.add(
            "siz", "Size",
            trait_type="static",
            base=10,
            mod=0
        )
        
        self.stats.add(
            "int", "Intelligence",
            trait_type="static",
            base=10, 
            mod=0
        )
        
        self.stats.add(
            "pow", "Power",
            trait_type="static",
            base=10,
            mod=0
        )
        
        self.stats.add(
            "cha", "Charisma",
            trait_type="static",
            base=10,
            mod=0
        )

        # === SURVIVAL TRAITS ===
        # Gauges that deplete and can recover with rate
        # All start at maximum (100) for a fresh, healthy character
        
        self.traits.add(
            "hunger", "Hunger",
            trait_type="gauge",
            base=100,
            mod=0,
            min=0,
            # Rate will be set by game systems (e.g., -0.1 per second = slowly getting hungry)
            rate=0,
            descs={
                0: "starving",
                20: "famished", 
                40: "hungry",
                60: "peckish",
                80: "satisfied",
                95: "full"
            }
        )
        
        self.traits.add(
            "thirst", "Thirst",
            trait_type="gauge", 
            base=100,
            mod=0,
            min=0,
            rate=0,
            descs={
                0: "dying of thirst",
                20: "parched",
                40: "thirsty", 
                60: "could drink",
                80: "hydrated",
                95: "quenched"
            }
        )
        
        self.traits.add(
            "fatigue", "Fatigue",
            trait_type="gauge",
            base=100, 
            mod=0,
            min=0,
            rate=0,
            descs={
                0: "exhausted",
                20: "drained",
                40: "tired",
                60: "weary", 
                80: "rested",
                95: "energetic"
            }
        )
        
        self.traits.add(
            "health", "Health",
            trait_type="gauge",
            # Base health derived from CON (Mongoose Legend: HP based on CON)
            base=self.stats.con.value * 2,
            mod=0,
            min=0,
            rate=0,  # Natural healing rate can be set later
            descs={
                0: "dead",
                10: "near death",
                25: "critically wounded",
                50: "badly hurt",
                75: "injured",
                90: "bruised",
                100: "healthy"
            }
        )

        # === SKILLS ===
        # Skills start empty and are added as character learns them
        # Using Counter type allows for base skill + improvements (current)
        # Example initialization of common starting skills:
        
        # Basic survival skills everyone starts with
        self.skills.add(
            "perception", "Perception",
            trait_type="counter",
            base=25,  # 25% base chance (INT + POW based in Mongoose Legend)
            current=25,
            mod=0,
            min=0,
            max=100,
            descs={
                0: "oblivious",
                20: "unaware",
                40: "attentive",
                60: "observant",
                80: "sharp",
                95: "eagle-eyed"
            }
        )
        
        self.skills.add(
            "stealth", "Stealth", 
            trait_type="counter",
            base=20,  # DEX + INT based
            current=20,
            mod=0,
            min=0,
            max=100,
            descs={
                0: "clumsy",
                20: "obvious",
                40: "careful",
                60: "sneaky",
                80: "stealthy",
                95: "invisible"
            }
        )
        
        self.skills.add(
            "athletics", "Athletics",
            trait_type="counter", 
            base=25,  # STR + DEX based
            current=25,
            mod=0,
            min=0,
            max=100,
            descs={
                0: "feeble",
                20: "weak",
                40: "capable",
                60: "athletic",
                80: "strong",
                95: "mighty"
            }
        )

        # Generic Craft skill. Mongoose Legend: Craft is an Advanced skill with
        # base = DEX + INT. MVP uses ONE generic Craft skill; Legend's
        # specialised Craft (Weaver), Craft (Cooper), etc. are a post-MVP
        # upgrade. base/current are read from stats so the skill scales if
        # starting characteristics ever change.
        craft_base = self.stats.dex.value + self.stats.int.value
        self.skills.add(
            "craft", "Crafting",
            trait_type="counter",
            base=craft_base,
            current=craft_base,
            mod=0,
            min=0,
            # Legend permits skills >100%; capped at 100 for MVP to match the
            # other skills. Lift this when skill-progression (Component 5) lands,
            # since skill_check() already handles >100 faithfully.
            max=100,
            descs={
                0: "unskilled",
                20: "novice",
                40: "apprentice",
                60: "journeyman",
                80: "skilled",
                95: "master",
            },
        )

        # Hunting skill. Custom PolishedWorld skill -- Legend has no "Hunting"
        # Common skill; its nearest analogue is the Advanced "Track" skill
        # (base INT+CON). Named "hunting" deliberately to avoid colliding with
        # the "survival" trait-gauge category (hunger/thirst/fatigue). Flat
        # base=25 follows the perception/athletics baseline convention -- every
        # character starts with a little woodcraft. Drives the hunt skill-check
        # (H2.2) and, later, hide-harvesting (H4.1).
        #
        # NOTE: keep these values in sync with HUNTING_SKILL_DEFAULTS in
        # world/character_migrations.py so backfilled characters are identical
        # to freshly created ones.
        self.skills.add(
            "hunting", "Hunting",
            trait_type="counter",
            base=25,
            current=25,
            mod=0,
            min=0,
            max=100,
            descs={
                0: "helpless",
                20: "novice",
                40: "competent",
                60: "tracker",
                80: "hunter",
                95: "master hunter",
            },
        )

    def at_post_unpuppet(self, account=None, session=None, **kwargs):
        """
        Override default: keep character in room as statue instead
        of removing them from the world. The visual statue presentation
        is handled by get_display_name and return_appearance overrides.
        """
        # Bail if any sessions are still puppeting (multisession scenarios)
        if self.sessions.count():
            return
    
        # Note: we deliberately do NOT call super() here.
        # Default behavior would set self.location = None, which would
        # break the statue logout system.
    
        if self.location:
            self.db.prelogout_location = self.location  # safety, behåll konventionen
            self.location.msg_contents(
                f"{self.key}'s body slowly turns to weathered stone, "
                "their final pose frozen in place.",
                exclude=[self],
            )

    def at_post_puppet(self, **kwargs):
        """Broadcast awakening when a player re-takes control."""
        super().at_post_puppet(**kwargs)  # här är super() OK - sätter inte location

        # C.3: snapshot each skill's permanent level (.current, never .value --
        # a tool buff worn at login must not skew the baseline) so `progress` can
        # report growth since this login. A fresh dict every puppet also resets
        # the baseline on reconnect -- the "since login" semantics we want. Cheap
        # (a handful of skills) and per-character, so no shared state across
        # concurrent players. (Comprehension is fine here: real method code, not
        # an @py exec, so the §11.16 exec-locals gotcha does not apply.)
        self.login_skill_snapshot = {
            key: self.skills.get(key).current for key in self.skills.all()
        }

        if self.location:
            self.location.msg_contents(
                f"The stone form of {self.key} stirs, color flowing back "
                "into their flesh as they draw breath.",
                exclude=[self],
            )
      
    # === Display & Appearance ===

    def get_display_name(self, looker=None, **kwargs):
        """
        Show 'stone statue of X' in room listings when in statue state.
        """
        base_name = super().get_display_name(looker=looker, **kwargs)
        if self.is_statue:
            return f"|wstone statue of {base_name}|n"
        return base_name

    def return_appearance(self, looker, **kwargs):
        """
        Statue description instead of character description in statue state.
        """
        if self.is_statue:
            return (
                f"|wA weathered stone statue depicting {self.key}.|n\n"
                "The carved figure stands silent and unmoving, "
                "its features captured in fine detail. "
                "It seems to be waiting."
            )
        return super().return_appearance(looker, **kwargs)

    def get_display_things(self, looker, **kwargs):
        """
        Hide the carried-items list from other observers.

        Inherited behaviour (DefaultObject.get_display_things, reached via
        ClothedCharacter) lists everything a character carries when looked at.
        This predates the clothing contrib -- ClothedCharacter only added a
        worn-item filter on top of the same exposure. For PolishedWorld a looker
        should see what someone is *wearing* (that line comes from
        get_display_desc) but not inventory their pockets, so we return the carry
        list only to the character themselves. Builders can still use `examine`
        to inspect contents.
        """
        if looker is not self:
            return ""
        return super().get_display_things(looker, **kwargs)

    # === Properties ===
    
    @property
    def is_statue(self):
        """
        True when no account is currently puppeting this character.
        Used by display/appearance overrides for the statue logout system.
        """
        return not self.has_account

    def update_health_max(self):
        """
        Helper method to recalculate max health when CON changes.
        Should be called whenever CON is modified.
        """
        new_max = self.stats.con.value * 2
        current_percent = self.traits.health.percent(formatting=None)
        
        self.traits.health.base = new_max
        self.traits.health.current = int(new_max * current_percent / 100)

    def improve_skill_on_use(self, skill_key):
        """
        Attempt one Legend improvement roll on a skill and bank the result as XP.

        The on-use analogue of spending an Improvement Roll in the tabletop
        game, and the single chokepoint for on-use skill growth. It does NOT
        decide *whether* a use is eligible (success-only, real-difficulty,
        cooldown) -- that gate lives in the caller. By the time this runs, the
        decision to attempt improvement has already been made.

        WHAT STAGE 4.5 CHANGED HERE
        ---------------------------
        The roll is untouched (P-3): `improvement_roll` still takes the skill's
        *level* and still returns 1 on the floor, 2-5 on a beat. What changed is
        what that number means. It used to be added to `.current` directly, which
        put a Craft skill from 20 to 100 in roughly 38 eligible ticks -- 19
        minutes of wall clock. It is now banked as lifetime XP, and the level is
        recomputed from the total through an exponential curve
        (`world/progression.py`). Same roll, same grain, ~77x the pacing.

        Two throttles therefore multiply, and only the second is a knob:
        Legend's roll self-throttles because it must *exceed* your own skill (the
        grain falls from ~3.25 to ~1.38 across the scale), and the curve makes
        each point cost more than the last. The curve does essentially all of the
        work; do not tune one thinking it moves the other.

        P-1 / P-2: lifetime XP is the sole persisted truth. `.current` is a
        materialised cache of `level_for_xp(total)` with exactly one writer --
        this method -- the same discipline `world/currency.py` holds over the
        wallet Attribute (S4-R2).

        Improvement is measured against the skill's *permanent* learned level
        (`.current`), NOT its effective `.value`. `.value` folds in situational
        `.mod` (e.g. a +20 tool buff); a temporary bonus must not raise the
        roll's target and make a skill *harder to permanently improve*.

        Args:
            skill_key (str): key of the skill, e.g. "craft" or "hunting".

        Returns:
            dict or None: None if this character has no such skill. Otherwise a
            summary the felt-progress layer consumes:
              - "skill_key" (str)
              - "rolled" (bool): False when already at cap (no roll is wasted
                on a mastered skill, and no XP is banked -- see the cap note).
              - "old" / "new" (int): permanent skill % before / after. **These
                are now usually equal**; the level moves once in dozens of ticks.
              - "delta" (int): new - old. **Usually 0.** Any caller that treats
                a non-zero delta as "a tick happened" is now wrong; use "rolled".
              - "beat" (bool): did the roll beat current skill (the 1D4+1
                outcome)? False when not rolled.
              - "crossed" (list[int]): which of 25/50/75/100 were passed this
                tick -- the celebration hooks.
              - "xp_gained" (int): XP banked by this tick (0 when not rolled).
              - "xp_total" (int): lifetime XP for this skill after the bank.
              - "progress" (tuple): `(earned, needed, fraction)` within the
                current point, from `progress_within_level`. Component D.1 draws
                its bar from this; nothing about it is stored (P-1).

        Multiplayer note: this is a read-modify-write on the XP Attribute and on
        `.current`. Evennia's Twisted reactor runs single-threaded and does not
        preempt a command mid-call, so concurrent uses serialise safely without
        an explicit lock. Do not introduce a yield, `utils.delay` or deferred
        between the read and the write.
        """
        skill = self.skills.get(skill_key)
        if skill is None:
            # Unknown/unlearned skill: silent no-op rather than raising, so a
            # shared call site that passes a key this character lacks stays safe.
            return None

        old = int(skill.current)
        # max may be None on a legacy/handcrafted trait; fall back to 100 to
        # match at_object_creation's skills.add(..., max=100).
        cap = skill.max if skill.max is not None else 100

        # Already mastered -> don't waste a roll (or a celebration) on it.
        #
        # ⚠️ DO NOT "SIMPLIFY" THIS AWAY once `min(cap, ...)` below appears to
        # make it redundant. It is what keeps `.current == level_for_xp(total)`
        # true at the ceiling. Without it, XP would keep accruing at cap while
        # `.current` stood still, the cache would silently diverge from the
        # truth, and D.2's cap lift would then teleport the character several
        # points at once. With it, the total freezes inside
        # [threshold(cap), threshold(cap + 1)) and the invariant holds.
        if old >= cap:
            capped_xp = self.skill_xp.get(skill_key)
            return {"skill_key": skill_key, "rolled": False, "old": old,
                    "new": old, "delta": 0, "beat": False, "crossed": [],
                    "xp_gained": 0, "xp_total": capped_xp,
                    "progress": progress_within_level(capped_xp)}

        # P-1 repair, and the one branch that is a no-op in every normal life.
        # `.current` is supposed to be written only by this method, but an admin
        # `@py`, a restored backup or a legacy write can leave it standing above
        # what the stored total implies -- and then `level_for_xp` below would
        # DE-LEVEL the character. Top the total up to the level's own floor
        # first, so the grain lands on a consistent base. This is exactly B.2's
        # absent-entry rule (`xp_threshold(.current)`) applied to a *present*
        # entry that has fallen behind, and it routes through the single writer.
        floor_xp = xp_threshold(old)
        stored_xp = self.skill_xp.get(skill_key)
        if stored_xp < floor_xp:
            self.skill_xp.add(skill_key, floor_xp - stored_xp)

        int_char = self.stats.int.value   # full INT added to the 1D100 (Legend)
        res = improvement_roll(old, int_char)

        # Bank first, then derive. `add()` returns the new lifetime total, which
        # keeps this a single read-modify-write rather than a read, a write and
        # a second read.
        new_xp = self.skill_xp.add(skill_key, res["gained"])

        # The curve, not the roll, decides the level -- a grain of 5 usually
        # moves nothing at all. Clamp to cap so old/new/delta stay exact.
        new = min(cap, level_for_xp(new_xp))

        # Write ONLY on a real move (P-2). The common case is that the level did
        # not change, and a write per craft would be pointless churn on the
        # Attribute behind the trait.
        if new != old:
            skill.current = new

        crossed = [t for t in (25, 50, 75, 100) if old < t <= new]

        return {"skill_key": skill_key, "rolled": True, "old": old, "new": new,
                "delta": new - old, "beat": res["beat"], "crossed": crossed,
                "xp_gained": res["gained"], "xp_total": new_xp,
                "progress": progress_within_level(new_xp)}

    # Real-time seconds between on-use improvement ticks *per skill*. Real time,
    # not game time: this throttles wall-clock action spam, not in-game duration.
    #
    # NO LONGER A BALANCE KNOB, and this is a frozen value (Stage 4.5,
    # sub-decision closed 2026-08-05). It is the wall-clock floor underneath the
    # whole XP curve: ~2 931 eligible ticks from Craft 20 to 100 x 30 s is
    # ~24 hours, and that multiplication is the only thing turning an abstract
    # curve into a duration.
    #
    # It stays at 30 for two reasons. P-5 first: raising it is a *tightening*,
    # and the curve is the only lever allowed to move under recalibration.
    # More importantly, two knobs doing one job is how a system becomes
    # uncalibratable -- halving this and halving SKILL_XP_BASE produce the same
    # observable change, so after the fact nobody can say which one did it.
    # THE CURVE IS THE CALIBRATION KNOB (server/conf/settings.py); this is held
    # fixed. It is rarely the binding constraint for craft anyway: materials,
    # gathering time and a successful roll all bite first.
    improvement_cooldown = 30

    # C.3: per-login baseline of every skill's permanent level, captured in
    # at_post_puppet and diffed on demand by the `progress` command to show
    # growth *this session*. default=None + autocreate=False, and we always
    # ASSIGN a fresh dict at login (never mutate in place), sidestepping the
    # mutable-default sharing trap; readers coalesce None -> {}.
    login_skill_snapshot = AttributeProperty(default=None, autocreate=False)

    def attempt_skill_improvement(self, skill_key, outcome, meaningful=True):
        """
        Gated entry point for on-use skill growth. Call sites route every
        relevant skill_check through here; this decides whether the use is
        eligible and, if so, performs one improvement roll via
        improve_skill_on_use.

        Three gates, all of which must pass (Component B.2 design lock):
          1. Success-only: only a passed check teaches. A failed/fumbled attempt
             (outcome["success"] is False) never improves -- mirrors RuneQuest's
             "experience check on success" and stops failure from paying.
          2. Real difficulty: `meaningful` must be True. Trivial/auto-pass call
             sites pass meaningful=False so AFK-farmable actions don't reward.
             Currently a *seam*, not a policy: both live call sites (craft, hunt)
             are meaningful and use the default. When trivial checks exist, they
             opt out here -- we don't build the difficulty heuristic speculatively.
          3. Cooldown: at most one tick per skill per `improvement_cooldown` real
             seconds (Cooldowns contrib). The direct anti-spam rate-limiter -- a
             hunter firing many checks still banks only one improvement per window.

        Args:
            skill_key (str): the skill the check exercised, e.g. "craft"/"hunting".
            outcome (dict): a world.skillcheck.skill_check result (needs the
                "success" bool). opposed_check callers pass the *winning side's
                own* skill_check dict (e.g. result["attacker"]), and only when
                the player actually won.
            meaningful (bool): False to opt a trivial call site out of gate 2.

        Returns:
            dict or None: the improve_skill_on_use summary (for felt-progress)
            when a tick fired, else None (gated out -- the common case, so
            callers MUST handle None).
        """
        # Gates 1 + 2: cheap booleans first, before touching the cooldown store.
        if not meaningful or not outcome.get("success"):
            return None

        # Gate 3: per-skill cooldown, namespaced so skills throttle
        # independently (improving craft doesn't block a hunting tick).
        cd_key = f"improve_{skill_key}"
        if not self.cooldowns.ready(cd_key):
            return None

        # Eligible. Apply the roll, then start the window *only if* a real tick
        # happened: a maxed skill (rolled=False) can't grow, so it shouldn't burn
        # a cooldown. No await between ready-check and add -> no race (single
        # -threaded reactor), so check+set stays atomic.
        result = self.improve_skill_on_use(skill_key)
        if result and result["rolled"]:
            self.cooldowns.add(cd_key, self.improvement_cooldown)
        return result

    def _improvement_feedback(self, result):
        """
        Render the player-facing feedback for one improvement result.

        Presentation layer for on-use skill growth: the improvement primitive
        (world/improvement.py) stays pure and silent; every call site that fires
        a tick routes its result dict through here and messages the return. One
        place for the copy across all SIX call sites (craft, repair, hunt-attack,
        hunt-harvest, disassemble, scribe -- P-6), and the single seam the
        threshold celebration composes onto. The count has been wrong here twice;
        if you add a seventh, this line is part of the change.

        THREE OUTCOMES NOW, NOT TWO (Stage 4.5, C.2)
        --------------------------------------------
        This used to be a two-way gate: a tick either rolled (and then always
        gained at least Legend's +1, so it always had something to announce) or
        it did not. C.1 broke that equivalence. A tick now banks XP nearly every
        time and moves the percentage roughly once in dozens, so `rolled` and
        "something visible happened" have come apart:

            not rolled            -> ""                      (gated out, or capped)
            rolled, delta == 0    -> the practice line        (the common case)
            rolled, delta > 0     -> "improves!" + any tier celebration

        The middle branch is the whole reason C.2 exists. The old copy would have
        rendered it as "(+0, now 40%)", which is worse than silence: it is a
        message that fires to tell you nothing changed.

        Args:
            result (dict or None): the attempt_skill_improvement summary, or None
                when the attempt was gated out (the common case). Callers may pass
                it straight through -- no pre-check needed.

        Returns:
            str: the message to show the player, or "" when there's nothing to
                announce (gated out, or a maxed skill whose tick didn't roll).
                Callers guard with `if text:` before messaging.
        """
        # Gated out (None) or a maxed skill that burned no growth (rolled=False):
        # nothing to say.
        #
        # ⚠️ This comment used to read "A rolled tick always has delta >= 1
        # (Legend's +1 floor), so rolled=True is a sufficient gate." That was
        # true when the roll's gain went straight onto `.current`. After C.1 the
        # gain is XP and the percentage is derived, so rolled=True is NO LONGER
        # sufficient for the "improves!" line -- it is only sufficient for
        # "something happened at all". The delta check below is what replaced it.
        if not result or not result.get("rolled"):
            return ""

        # Re-fetch for the display label ("Crafting", not "craft"). The skill
        # existed when the tick fired; guard against a mid-command removal by
        # falling back to a title-cased key.
        skill = self.skills.get(result["skill_key"])
        label = skill.name if skill is not None else result["skill_key"].title()

        if not result.get("delta"):
            # Banked, but the percentage did not move -- the common case after
            # C.1, and the one the ordering hazard in the decomposition is about.
            #
            # ⚠️ THROWAWAY COPY. TODO(D.1): delete this branch and render the
            # derived progress bar from result["progress"] instead.
            #
            # It exists so the branch between C and D is never LESS legible than
            # `main` is today. Stage 1's whole premise was that mechanically
            # correct progression can still ship as an invisible backend that
            # feels dead; going silent for dozens of crafts would walk straight
            # back into that.
            #
            # Two constraints on the wording, and they are why this is not just
            # the old line with the numbers stripped out:
            #   * It must NOT say "improves". That word is reserved for a tick
            #     where the number actually moved, and lending it to a tick where
            #     nothing visible happened teaches the player a meaning that D.1
            #     then silently takes back.
            #   * It must carry NO number. Any figure shown here is a second
            #     progression stat, which P-8 rejects outright, and it would have
            #     to be un-taught when the bar arrives.
            return f"You feel your grasp of {label} steady a little."

        lines = [f"Your {label} improves! (+{result['delta']}, now {result['new']}%)"]

        # Tier-celebration: fire only on the tick that actually crosses a
        # desc-tier boundary (a genuine named rank-up), never on the raw quarter
        # marks. Computed from the permanent old/new ints via tier_for (NOT
        # skill.desc(), which reads the buff-inflated .value), so a tool buff can
        # neither fake nor mask a crossing.
        #
        # It sits INSIDE the delta > 0 branch on purpose. It would be a harmless
        # no-op outside it -- old == new means the tiers match -- but structure
        # is a better guarantee than an argument, and D.1 will be editing the
        # branch above it. Crossings are strictly rarer after C.1, which is what
        # makes this line worth more, not less: it is now the rarest and
        # therefore the most meaningful thing this method can say.
        #
        # ⚠️ The idempotence argument here used to read "improvement is monotonic
        # (delta >= 1) and boundaries sit >= 15 apart while a single tick gains
        # at most 5". Both halves are stale: after C.1 delta is usually 0, and
        # the "at most 5" is 5 XP, not 5 percentage points. The conclusion
        # survives and is in fact stronger -- the level is monotonic (a tick can
        # only bank XP forward), boundaries still sit >= 15 apart, and a single
        # tick can now move at most ONE point, so each boundary is crossed on
        # exactly one tick.
        # descs is None on an un-migrated character -> tier_for returns "" -> skip.
        descs = skill.descs if skill is not None else None
        old_tier = tier_for(result["old"], descs)
        new_tier = tier_for(result["new"], descs)
        if new_tier and new_tier != old_tier:
            lines.append(f"Your {label} reaches a new tier: |y{new_tier}|n.")

        return "\n".join(lines)

    # --- Recipe knowledge (Stage 3, Component A) ---
    # A per-character set of *known* crafting recipes, stored as Tags under
    # KNOWN_RECIPE_CATEGORY (see module top for why tags beat an
    # AttributeProperty set). This is storage + query ONLY -- the gate that
    # turns "does this character know recipe X?" into a craft allow/deny lives
    # in Component B. B/C/D all read through these three helpers, so the
    # storage shape can change later without touching call sites.

    def knows_recipe(self, name):
        """
        Return True if this character has learned the recipe `name`.

        Args:
            name (str): the canonical recipe-registry name
                (MongooseCraftRecipe.name, e.g. "cloth" or "linen shirt"),
                NOT a prototype_key. Case is irrelevant -- the TagHandler
                lowercases keys on both write and read.

        Returns:
            bool: True if the recipe tag is present on this character.
        """
        return self.tags.has(name, category=KNOWN_RECIPE_CATEGORY)

    def learn_recipe(self, name):
        """
        Teach this character the recipe `name`, idempotently.

        We check knows_recipe() FIRST and only add the tag if it is new. That
        lets call sites (a `learn` command, reading a scroll) distinguish the
        two outcomes from the return value -- "You study the scroll and learn
        to weave cloth." vs. "You already know this." -- WITHOUT wasting the
        scroll / materials on a recipe the character already has.

        tags.add is itself idempotent at the DB level (a matching key+category
        is re-used, never duplicated), so the guard exists purely to produce
        the return signal, not to prevent duplicate rows.

        Args:
            name (str): canonical recipe-registry name (see knows_recipe).

        Returns:
            bool: True if newly learned this call, False if already known.

        Multiplayer note: this is a read-then-write on the tag set. Evennia's
        Twisted reactor is single-threaded and does not preempt a command
        mid-call, so two near-simultaneous learn attempts serialise safely;
        the worst case is the second seeing knows_recipe() True and returning
        False -- exactly the intended "already known" outcome.
        """
        if self.knows_recipe(name):
            return False
        self.tags.add(name, category=KNOWN_RECIPE_CATEGORY)
        return True

    def known_recipes(self):
        """
        Return the list of recipe names this character has learned.

        Returns:
            list[str]: canonical recipe names (lowercased by the TagHandler),
                always a list -- empty when nothing is known. Order is
                unspecified (tag/cache order); presentation-layer callers that
                need determinism should sort there.
        """
        return self.tags.get(category=KNOWN_RECIPE_CATEGORY, return_list=True)

    # --- Rest / fatigue recovery ---
    rest_interval = 10    # seconds between recovery ticks (lower during dev)
    rest_recovery = 5     # fatigue restored per interval (integer; gauge is int-based)
    
    def apply_health_damage(self, amount, source=None):
        """
        Single chokepoint for all HP loss. Subtracts `amount` from health and
        fires at_character_death() if that reaches the health minimum (0).

        Every damage source -- survival conditions now, combat later -- must
        route through here so death can never be bypassed, and so the future
        dying-state (H7.4) has exactly one place to hook.

        Args:
            amount (int): HP to remove. <= 0 is a no-op, so callers can pass a
                summed total without special-casing a zero-damage tick.
            source (Object | str | None): what dealt the damage; forwarded to
                at_character_death as `killer` for future attribution/logging.
        """
        if amount <= 0:
            return
        health = self.traits.get("health")
        if health is None:
            return
        # Already at/below min: a death is in progress or already resolved this
        # tick. Do nothing. This is defense-in-depth for future direct callers
        # (combat); the summation in the ticker is the primary double-death guard.
        if health.current <= health.min:
            return
        health.current -= amount
        if health.current <= health.min:
            # GaugeTrait has no min-callback, so we detect the threshold crossing
            # explicitly rather than relying on the trait to notify us.
            self.at_character_death(killer=source)

    def _get_respawn_location(self):
        """
        Resolve where this character respawns on death.

        Priority: per-character override (db.respawn_location), then a global
        default from settings (DEFAULT_RESPAWN_DBREF -- points at the GameGold
        temple once it's built), then the character's home, then current
        location as a last resort. Every step is guarded so a stale or missing
        dbref can never strand a dead player.
        """
        override = self.db.respawn_location
        if override:
            return override
        dbref = getattr(settings, "DEFAULT_RESPAWN_DBREF", None)
        if dbref:
            matches = search.search_object(dbref)
            if matches:
                return matches[0]
        return self.home or self.location

    def at_character_death(self, killer=None):
        """
        Consequence hook for a character hitting 0 HP. NOT permadeath.

        Spawns a PlayerCorpse where the character fell, moves all non-soulbound
        inventory (worn items stripped first) into it, relocates the character to
        their respawn point, restores health/hunger/thirst, clears survival
        conditions, and applies a timed post-death weakness.

        This is the single consequence chokepoint (H7.1). In normal play H7.2's
        apply_health_damage is the only caller; the reentrancy guard below is
        defense-in-depth against a direct or duplicate call (e.g. two damage
        sources resolving in one tick) so one death never spawns two corpses.

        Args:
            killer (Object | str | None): whatever dealt the fatal blow, kept for
                future logging / PvP attribution. Mechanically unused for now.
        """
        # Reentrancy guard. ndb (non-persistent) suffices: a death resolves
        # synchronously in one call, and a post-reload session can't be mid-death.
        # Unset ndb reads as None (falsy), so the first entry always proceeds.
        if self.ndb._dying:
            return
        self.ndb._dying = True
        try:
            location = self.location

            # Spawn the corpse where they fell. A character with no location is
            # not in the world -- skip the corpse but still respawn/heal so we
            # can never strand them in a dead state.
            corpse = None
            if location:
                try:
                    corpse = create_object(
                        "typeclasses.corpse.PlayerCorpse",
                        key=f"corpse of {self.key}",
                        location=location,
                        attributes=[("owner", self.id)],
                    )
                except Exception:
                    # A failed corpse spawn must not abort respawn. Log and fall
                    # through: the player keeps their items rather than voiding
                    # them -- the safe failure for a player-driven economy.
                    logger.log_trace(
                        f"at_character_death: PlayerCorpse spawn failed for {self}"
                    )

            # Drop inventory into the corpse. list() snapshots contents because
            # we mutate it while iterating.
            if corpse:
                for obj in list(self.contents):
                    if obj.tags.has("soulbound"):
                        continue
                    try:
                        if obj.db.worn:
                            obj.remove(self, quiet=True)
                        # move_to returns False on failure WITHOUT raising, so a
                        # silent stranding would otherwise vanish from the loot. Log
                        # it and leave the item on the character (safe economic
                        # failure: they keep it rather than it disappearing).
                        if not obj.move_to(corpse, quiet=True, move_hooks=False):
                            logger.log_err(
                                f"at_character_death: {obj} (#{obj.id}) failed to "
                                f"move to corpse of {self}; item retained on character."
                            )
                    except Exception:
                        # One bad item must not abort the whole death sequence.
                        logger.log_trace(
                            f"at_character_death: failed to move {obj} to corpse"
                        )

            # Relocate to respawn. respawn_location gets its temple default in
            # H7.3; the fallback chain guarantees a valid destination today
            # (self.home always exists).
            destination = self._get_respawn_location()
            if destination:
                self.move_to(destination, quiet=True, move_hooks=False)

            # Restore vitals (decision 2: reset hunger/thirst -- respawned "fresh").
            health = self.traits.get("health")
            if health:
                health.current = health.max
            for gauge_key in ("hunger", "thirst"):
                gauge = self.traits.get(gauge_key)
                if gauge:
                    gauge.current = gauge.max

            # Clear survival conditions now so the next tick doesn't flash
            # "Starving" on a freshly-fed character (the ticker would clear them
            # anyway once the gauge reads above min; this just avoids the lag).
            for condition_key in ("starving", "dehydrated"):
                self.buffs.remove(condition_key)

            # Timed post-death debuff. remove-then-add guarantees a fresh single
            # stack with a fresh duration on re-death (buffs.add otherwise stacks).
            self.buffs.remove(DeathWeakness.key)
            self.buffs.add(DeathWeakness)

            self.msg("|RYou have died.|n")
        finally:
            # Always clear the guard, even on exception, so a later legitimate
            # death is never silently swallowed.
            self.ndb._dying = False

    def start_resting(self):
        """Begin resting. Schedules the first recovery tick."""
        fatigue = self.traits.get("fatigue")
        if fatigue is None:
            return
        if fatigue.current >= fatigue.max:
            self.msg("You are not tired.")
            return
        self.ndb.resting = True
        self.msg("You settle down to rest.")
        if self.location:
            self.location.msg_contents(
                f"{self.key} settles down to rest.", exclude=self
            )
        delay(self.rest_interval, self._rest_tick)

    def stop_resting(self, reason="You stop resting."):
        """Stop resting (no-op if not resting). Safe to call from anywhere."""
        if not self.ndb.resting:
            return
        self.ndb.resting = False
        self.msg(reason)
        if self.location:
            self.location.msg_contents(f"{self.key} gets up.", exclude=self)

    def _rest_tick(self):
        """
        One recovery step. Reschedules itself while resting continues.

        Stops (without rescheduling) if resting was cancelled, the character
        is no longer actively puppeted (offline-safe via has_account), or the
        fatigue gauge is full.
        """
        if not self.ndb.resting or not self.has_account:
            self.ndb.resting = False
            return
        fatigue = self.traits.get("fatigue")
        if fatigue is None:
            self.ndb.resting = False
            return
        fatigue.current += self.rest_recovery   # auto-clamps to max
        if fatigue.current >= fatigue.max:
            self.ndb.resting = False
            self.msg("You feel fully rested.")
            if self.location:
                self.location.msg_contents(
                    f"{self.key} gets up, looking refreshed.", exclude=self
                )
            return
        delay(self.rest_interval, self._rest_tick)   # reschedule

    def at_pre_move(self, destination, move_type="move", **kwargs):
        """Interrupt timed activities when moving, but allow the move itself."""
        if self.ndb.resting:
            self.stop_resting("You get up, interrupting your rest.")
        if self.ndb.working:
            # A temple chore in progress (commands/work_commands.py). Clearing
            # the marker is what cancels it: the pending delay still fires on
            # schedule, finds the marker gone, and returns without paying.
            #
            # This exists for the message, not for the correctness -- the
            # location re-check in `_finish_task` would refuse the payout
            # anyway. But refusing it twenty seconds later in silence reads as
            # the command being broken, and a player who walks out mid-chore
            # should be told at the moment they do it. Same shape and same
            # reasoning as the resting interrupt above.
            self.ndb.working = None
            self.msg("You break off what you were doing.")
        return super().at_pre_move(destination, move_type=move_type, **kwargs)
