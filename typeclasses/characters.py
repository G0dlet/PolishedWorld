"""
PolishedWorld Character typeclass

Implements Mongoose Legend characteristics with Evennia's Traits contrib.
Includes survival mechanics (hunger, thirst, fatigue) and skill system.
"""

from evennia.contrib.game_systems.clothing import ClothedCharacter
from evennia.utils import lazy_property
from evennia.utils.utils import delay, inherits_from
from evennia.contrib.rpg.traits import TraitHandler
from evennia.contrib.rpg.buffs import BuffHandler
from evennia.contrib.game_systems.cooldowns import CooldownHandler

from .objects import ObjectParent
from evennia import create_object, AttributeProperty
from evennia.utils import logger
from world.survival_buffs import DeathWeakness
from world.death_contract import death_message
from world.improvement import improvement_roll, tier_for
from world.currency import CurrencyHandler
from world import encumbrance
from world import survival_ticker
from world import timed_actions
from world.progression import (
    level_for_xp,
    progress_within_level,
    render_progress_bar,
    xp_threshold,
)
from world.skill_xp import SkillXPHandler
from world.chargen import derive_health_max, start_or_resume_chargen

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

# Who counts as a giver when a receive is refused (W2.1): the same path the
# encumbrance walk skips characters by, so a statue or an NPC counts too.
_CHARACTER_PATH = "evennia.objects.objects.DefaultCharacter"


class Character(ObjectParent, ClothedCharacter):
    """
    PolishedWorld character with Mongoose Legend integration.

    Uses three separate TraitHandlers:
    - stats: Mongoose Legend characteristics (STR, DEX, CON, SIZ, INT, POW, CHA)
    - traits: Survival gauges (hunger, thirst, fatigue, health)
    - skills: Learnable skills using percentile system (0-100%)

    Encumbrance: read-only `carried_enc`, `enc_limit`, `encumbrance_state`,
    computed on every read (world/encumbrance.py). A move that would put the
    character above twice the limit is refused (`at_pre_object_receive`). A
    move that carries the character across the limit is announced
    (`at_object_receive`, `at_object_leave`); a path that runs no hook --
    `delete()`, a direct `location =`, `move_hooks=False` (death), a change
    to STR or SIZ -- crosses it silently (W2.2 Q4). A step through an exit
    while past the limit costs fatigue (`at_post_move`, W3.2).
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
            base=derive_health_max(self.stats.con.value),
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
        # Placeholder bases. A character born through an account has every
        # base below re-derived from its characteristics by the chargen menu
        # (world.chargen.SKILL_BASE_PAIRS, CC5) before it can play; these
        # numbers survive only on characters made without one (test
        # fixtures, a builder's `create`). Counter traits: `.base` is the
        # starting score, `.current` the score after improvement.
        self.skills.add(
            "perception", "Perception",
            trait_type="counter",
            base=25,  # placeholder; chargen derives INT + POW (Legend p.13)
            current=25,
            mod=0,
            min=0,
            # No max (D.2, P-7). A CounterTrait with max set CLAMPS INSIDE ITS
            # OWN SETTER -- `.current = 105` on a max=100 trait silently stores
            # 100 -- which would break `.current == level_for_xp(total)` where no
            # reader could see it. The curve is the ceiling now, not this field.
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
            base=20,  # placeholder; chargen derives DEX + INT
            current=20,
            mod=0,
            min=0,
            # No max (D.2, P-7) -- see the note on `perception` above.
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
            base=25,  # placeholder; chargen derives STR + DEX
            current=25,
            mod=0,
            min=0,
            # No max (D.2, P-7) -- see the note on `perception` above.
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
        # upgrade. base/current are read from the placeholder stats here; the
        # chargen menu re-derives both from the characteristics the player
        # chose (CC5), as it does every skill above.
        craft_base = self.stats.dex.value + self.stats.int.value
        self.skills.add(
            "craft", "Crafting",
            trait_type="counter",
            base=craft_base,
            current=craft_base,
            mod=0,
            min=0,
            # No max (D.2, P-7) -- see the note on `perception` above. The cap
            # this comment used to defer is lifted; skill_check() has always
            # handled >100 faithfully, and improvement_roll now does too.
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
        # base=25 is a placeholder like those above; chargen derives INT + CON,
        # Track's pair (CC5). Drives the hunt skill-check (H2.2) and, later,
        # hide-harvesting (H4.1).
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
            # No max (D.2, P-7) -- see the note on `perception` above.
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
        """
        Broadcast awakening when a player re-takes control; then, for a
        character born through an account and not yet made, the creation
        menu (CC3.2) -- started, or resumed where it was left.
        """
        super().at_post_puppet(**kwargs)  # här är super() OK - sätter inte location

        # C.3: the `progress` baseline is taken at every puppet.
        self.snapshot_skill_baseline()

        if self.location:
            self.location.msg_contents(
                f"The stone form of {self.key} stirs, color flowing back "
                "into their flesh as they draw breath.",
                exclude=[self],
            )

        # CC3.2: last, so the menu is the final thing on the screen. Its
        # cmdset replaces the character's until node_done -- that is the gate.
        start_or_resume_chargen(self)
      
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

    @property
    def carried_enc(self):
        """
        Total ENC this character carries, read live (W1.1, WD4).

        Read-only and uncached (WD3 b): every read walks the inventory
        through `world.encumbrance.carried_enc`, the single reader.

        Returns:
            int
        """
        return encumbrance.carried_enc(self)

    @property
    def enc_limit(self):
        """
        This character's carrying limit, STR + SIZ, read live (WD1).

        Returns:
            int
        """
        return encumbrance.enc_limit(self)

    @property
    def encumbrance_state(self):
        """
        FREE, OVERLOADED or CEILING (WD2), computed on every read.

        Nothing is stored: the band follows the inventory and the
        characteristics the moment either changes.

        Returns:
            str: one of the constants in `world.encumbrance`.
        """
        return encumbrance.encumbrance_state(self)

    def physical_modifier(self):
        """
        The modifier on this character's physical skill tests (W3.1).

        Legend core p.86: an overloaded character takes -20% on every test
        that requires a physical action. Past the limit means OVERLOADED or
        CEILING; at or under it the modifier is 0. Read live at the moment of
        each roll and never stored, so the penalty follows the load (a timed
        craft reads it when it completes, not when it starts).

        The six physical rolls add this to their own modifiers: craft
        (`MongooseCraftRecipe.do_craft`), `disassemble`, `scribe`, `repair`,
        `hunt` (as `attacker_mod`) and `harvest`. A new skill test decides
        whether it is physical (the census in tests/test_encumbrance.py).
        Later penalties of the same kind (the fatigue levels, BACKLOG) are
        added here, so the call sites never change again.

        Returns:
            int: 0 when FREE, `encumbrance.OVERLOAD_PENALTY` otherwise.
        """
        if self.encumbrance_state != encumbrance.FREE:
            return encumbrance.OVERLOAD_PENALTY
        return 0

    def snapshot_skill_baseline(self):
        """
        Record each skill's permanent level as the `progress` baseline (C.3).

        Reads `.current`, never `.value` -- a tool buff worn at login must not
        skew the baseline. Called from `at_post_puppet`, so a fresh dict every
        puppet resets the baseline on reconnect (the "since login" semantics
        we want), and from the chargen menu's last node, so the derived bases
        and the profession bonus are not reported as growth (CC3.1). Cheap (a
        handful of skills) and per-character, so no shared state across
        concurrent players. (Comprehension is fine here: real method code, not
        an @py exec, so the §11.16 exec-locals gotcha does not apply.)
        """
        self.login_skill_snapshot = {
            key: self.skills.get(key).current for key in self.skills.all()
        }

    def update_health_max(self):
        """
        Helper method to recalculate max health when CON changes.
        Should be called whenever CON is modified.
        """
        new_max = derive_health_max(self.stats.con.value)
        current_percent = self.traits.health.percent(formatting=None)
        
        self.traits.health.base = new_max
        self.traits.health.current = int(new_max * current_percent / 100)

    def health_desc(self):
        """
        The health label, read against the gauge's percent -- not its value.

        Health's `descs` are keyed 0-100, but its max is CON x 2 (12-36 once
        character creation varies CON). `GaugeTrait.desc()` compares the keys
        with the absolute value, so a full 20/20 read `critically wounded`
        (BACKLOG *Health `descs` use a 0-100 scale*). The scale was the bug,
        not the bound: this reader keeps Evennia's own rule -- each key is an
        inclusive UPPER bound, anything above the top key takes the top label
        -- and only swaps the value for `percent()`. That keeps health on the
        same reading as the other gauges and the skills, and leaves the open
        question of which reading is meant (BACKLOG *`descs` tables are read
        as upper bounds but shaped like lower bounds*) to its own entry.

        Under that rule the stored table reads naturally: `dead` only at
        exactly 0, `near death` above 0 up to 10%, `healthy` above 90%. The
        stored table is already percent-shaped, so no character's data
        changes -- existing characters read right with no migration.

        Keys are walked in sorted order rather than trusting the stored
        order, so a table written out of order still reads correctly.

        Returns:
            str: the label, or "" if the trait carries no `descs`.
        """
        health = self.traits.health
        descs = health.descs
        if not descs:
            return ""
        pct = health.percent(formatting=None)
        label = ""
        for bound in sorted(descs):
            label = descs[bound]
            if pct <= bound:
                return label
        return label

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

        WHAT D.2 CHANGED HERE -- THERE IS NO CEILING ANY MORE
        -----------------------------------------------------
        This method used to open with an `old >= cap` short-circuit that returned
        `rolled=False` and banked nothing, and the comment above it argued at
        length that the guard was load-bearing rather than redundant. Both the
        guard and the argument are gone, and the argument is worth restating so
        nobody reintroduces either: the guard existed *because there was a cap*.
        It kept the lifetime total frozen inside [threshold(100), threshold(101))
        so that `.current == level_for_xp(total)` stayed true at a ceiling where
        `.current` could not follow the total upward. With the ceiling removed
        the invariant holds unconditionally, which is a stronger property than
        the one the guard was defending, not a weaker one.

        Nothing replaces it as a limit, and nothing needs to. At (6, 20) with
        INT 12 a point costs 192 XP at skill 100, 1 086 at 150 and 6 144 at 200 --
        roughly 8 and 44 hours of pure 30 s cooldown respectively -- and Legend's
        second band halves the applied INT the moment you pass 100. The curve and
        the rulebook throttle the top of the scale between them; a number here
        would be a third throttle nobody could later attribute an effect to.

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
              - "rolled" (bool): **always True on this path since D.2.** The key
                is kept rather than dropped because `_improvement_feedback` and
                the tests read this dict without knowing which branch built it,
                and a shape that changes shape is how a KeyError gets discovered
                inside a live craft. Treat it as a shape contract, not a signal.
              - "old" / "new" (int): permanent skill % before / after. **These
                are now usually equal**; the level moves once in dozens of ticks.
              - "delta" (int): new - old. **Usually 0.** Any caller that treats
                a non-zero delta as "a tick happened" is now wrong; use "rolled".
              - "beat" (bool): did the roll beat the band's target (the 1D4+1
                outcome)?
              - "crossed" (list[int]): which of 25/50/75/100 were passed this
                tick -- the celebration hooks. D.2 deliberately did NOT extend
                this list above 100: 100 stays the top celebration, which is
                where "mastery" honestly sits, and inventing 125/150 marks would
                celebrate altitudes the curve makes nearly unreachable.
              - "xp_gained" (int): XP banked by this tick.
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

        # D.2 CAP-LIFT REPAIR -- the migration, and the reason it is not a
        # migration script.
        #
        # at_object_creation no longer sets `max`, so every character created
        # from D.2 onward is already correct. Characters that existed BEFORE it
        # carry max=100 inside their stored trait, and that number is enforced
        # by Evennia's own setter:
        #
        #     @current.setter
        #     def current(self, value):
        #         self._data["current"] = ..._enforce_boundaries(value)
        #
        # so `skill.current = 105` on such a trait silently stores 100. This is
        # exactly B.2's problem with the opposite remedy available: B.2 could
        # solve it read-time because WE owned the read (SkillXPHandler.get);
        # here the enforcement lives in a setter we do not own, so a read-time
        # fallback has nothing to intercept -- by the time we read, the value is
        # already clamped. The write has to happen.
        #
        # It happens HERE rather than in a one-shot admin command for B.2's
        # stated reason: a script only covers the characters alive when someone
        # remembered to run it, and does not survive a restored backup. Routing
        # it through the single writer (P-2) makes it idempotent by construction
        # -- after the first tick there is nothing left to write, forever.
        if skill.max is not None:
            skill.max = None

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

        int_char = self.stats.int.value   # INT offered to the roll; improvement_
                                          # roll divides it down above 100 (D.2)
        res = improvement_roll(old, int_char)

        # Bank first, then derive. `add()` returns the new lifetime total, which
        # keeps this a single read-modify-write rather than a read, a write and
        # a second read.
        new_xp = self.skill_xp.add(skill_key, res["gained"])

        # The curve, not the roll, decides the level -- a grain of 5 usually
        # moves nothing at all. No clamp: D.2 removed the ceiling, and a
        # `min(cap, ...)` here would be the ceiling wearing a different name.
        new = level_for_xp(new_xp)

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

    # D.1, DISPLAY ONLY. Skill keys that some call-site actually routes through
    # attempt_skill_improvement, so `progress` can say "(not yet trainable)"
    # instead of drawing a bar that is guaranteed never to move. Perception,
    # stealth and athletics have no call-site at all; an empty bar beside them
    # reads as broken, and hiding the rows would hide the fact that three of
    # five skills are untrained content.
    #
    # ⚠️ NOT A GATE. The policy of which uses teach is "which call-sites exist"
    # (P-6, six of them), and this set must never be read to decide whether a
    # tick may fire -- that would be two knobs for one job, and the second one
    # would be the wrong one. It is a label, so drift costs a wrong caption and
    # nothing else. tests/test_improvement_engine.py::TestImprovableSkillsSet
    # holds it against the call-sites and the harvest table so the drift is
    # caught rather than trusted.
    improvable_skills = frozenset({"craft", "hunting"})

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
        # happened.
        #
        # ⚠️ SUPERSEDED (Stage 4.5, D.2). This used to read "a maxed skill
        # (rolled=False) can't grow, so it shouldn't burn a cooldown". There is
        # no maxed skill any more and `rolled` is always True on the non-None
        # path, so the second half of the condition below is now a shape check
        # rather than a signal -- kept because a dict arriving here without the
        # key means it did not come from the engine, and that is worth failing
        # on. The cooldown is in practice burned on every eligible attempt.
        # No await between ready-check and add -> no race (single-threaded
        # reactor), so check+set stays atomic.
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

        THREE OUTCOMES, ONE SIGNAL EACH (Stage 4.5, C.2 then D.1)
        ---------------------------------------------------------
        This used to be a two-way gate: a tick either rolled (and then always
        gained at least Legend's +1, so it always had something to announce) or
        it did not. C.1 broke that equivalence. A tick now banks XP nearly every
        time and moves the percentage roughly once in dozens, so `rolled` and
        "something visible happened" have come apart:

            not rolled            -> ""                      (gated out only)
            rolled, delta == 0    -> the derived progress bar (the common case)
            rolled, delta > 0     -> "improves!" + any tier celebration

        C.2 filled the middle branch with a wordless practice line as a
        placeholder; D.1 replaced it with the bar the placeholder was standing in
        for. The bar is computed from `result["progress"]` on read and stored
        nowhere (P-1), and it carries no figure (P-8).

        WHY THE BAR IS NOT ALSO DRAWN ON A LEVELLING TICK (locked D-2)
        --------------------------------------------------------------
        One felt-progress signal per tick. On a levelling tick the strongest true
        thing to say is that the percentage moved, and the bar there would be the
        *new* point's bar -- near-empty, because a level-up resets the numerator
        (measured: 59 -> 60 yields `(0, 48, 0.0)`). Printing an empty bar directly
        under "improves!" reads as a demotion in the same breath as the praise.
        The alternative considered and rejected was drawing it full instead: that
        is a bar showing something other than `progress`, i.e. a second truth,
        which is the whole class of bug P-1 exists to prevent.

        Args:
            result (dict or None): the attempt_skill_improvement summary, or None
                when the attempt was gated out (the common case). Callers may pass
                it straight through -- no pre-check needed.

        Returns:
            str: the message to show the player, or "" when there's nothing to
                announce (the attempt was gated out). Callers guard with
                `if text:` before messaging.
        """
        # Gated out: nothing to say.
        #
        # ⚠️ D.2 note. Both this comment and the Returns line above used to name
        # a second silent case -- "a maxed skill whose tick didn't roll". There
        # is no maxed skill any more: `improve_skill_on_use` returns None or a
        # dict with rolled=True, and nothing else. The `rolled` half of the guard
        # below is therefore dead as a *signal* and kept only as a shape check;
        # if it ever fires, the dict came from somewhere that is not the engine.
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
            # C.1, and the thing this branch exists to make legible.
            #
            # `improve_skill_on_use` returns "progress" on the one branch it
            # still has, so the bar has its input without a second read of the
            # XP store. (Until D.2 this sentence named "every branch including
            # the capped one"; the capped branch is gone.) The tuple is unpacked
            # rather than indexed so that a
            # change in its shape fails here loudly instead of drawing a wrong
            # bar quietly; `_earned`/`_needed` are deliberately unused, since
            # showing either of them would be the second progression figure P-8
            # rejects.
            _earned, _needed, fraction = result["progress"]
            return f"|y{label}|n  {render_progress_bar(fraction)}"

        lines = [f"Your {label} improves! (+{result['delta']}, now {result['new']}%)"]

        # Tier-celebration: fire only on the tick that actually crosses a
        # desc-tier boundary (a genuine named rank-up), never on the raw quarter
        # marks. Computed from the permanent old/new ints via tier_for (NOT
        # skill.desc(), which reads the buff-inflated .value), so a tool buff can
        # neither fake nor mask a crossing.
        #
        # It sits INSIDE the delta > 0 branch on purpose. It would be a harmless
        # no-op outside it -- old == new means the tiers match -- but structure
        # is a better guarantee than an argument. D.1 rewrote the branch above
        # it and this line was not touched, which is the guarantee paying out.
        # Crossings are strictly rarer after C.1, which is what makes this line
        # worth more, not less: it is now the rarest and therefore the most
        # meaningful thing this method can say.
        #
        # ⚠️ TWO SUPERSEDED VERSIONS OF THIS ARGUMENT, BOTH LEFT VISIBLE.
        #
        # It first read "improvement is monotonic (delta >= 1) and boundaries sit
        # >= 15 apart while a single tick gains at most 5". Both halves went stale
        # at C.1: delta is usually 0, and the "at most 5" is 5 XP rather than 5
        # percentage points.
        #
        # C.2 replaced it with "a single tick can now move at most ONE point, so
        # each boundary is crossed on exactly one tick". **That is false, and it
        # was falsified in-game during D.1's own protocol**: a tick took Craft
        # from 20 to 60 in one move. It held only under the unstated assumption
        # that `.current` has no writer but this method -- and the D.1 protocol
        # itself tells the tester to set `.current` by hand, which is the same
        # shape as C.1's F7 finding. When `.current` sits below what the stored
        # total buys, the level snaps up to the truth (P-1 working, not failing)
        # and delta is however many points that is.
        #
        # What actually holds, and it is all this line needs: the celebration
        # fires only when the tier CHANGES, and the level is monotonic, so a
        # given tier is announced at most once per character. A multi-point jump
        # therefore announces the tier landed in and says nothing about the ones
        # passed through -- `tier_for` reports where you stand, not where you
        # have been. That is deliberate and not a gap: intermediate tiers are
        # unreachable except through an out-of-band write.

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
        Consequence hook for a character hitting 0 HP.

        Not permadeath -- by decision, not by default: roadmap decision log,
        Death-consequence policy (i). This method is the mechanism that policy
        describes; the player-facing promise is in `world/death_contract.py`.

        Spawns a PlayerCorpse where the character fell, moves all non-soulbound
        inventory (worn items stripped first) into it, relocates the character to
        their respawn point, restores health/hunger/thirst, clears survival
        conditions, applies a timed post-death weakness, and tells the player
        the contract: where the body lies, how long it keeps their belongings
        (owner-first for a grace window), and that the weakness passes.

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
            # D7: end any timed action FIRST. The relocation below moves with
            # move_hooks=False, so at_pre_move -- the hook that normally does
            # this -- never runs, and a rest would otherwise keep ticking at the
            # respawn point. First, so an action's on_interrupt (a rest's "gets
            # up") never sees a half-moved body or an emptied inventory.
            # Not silenced (T13): the actor hears the action's interrupt_msg
            # just before "You have died.", which is true.
            # Guarded like the corpse spawn below: a failing interrupt must not
            # abort the death sequence and strand the character at 0 HP.
            # interrupt() empties the slot before it messages anyone, so the
            # slot is clear even when this logs.
            try:
                timed_actions.interrupt(self)
            except Exception:
                logger.log_trace(
                    f"at_character_death: timed-action interrupt failed for {self}"
                )

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

            # The contract line names the room the corpse is in, read from the
            # corpse itself, so it is never claimed when no corpse was made.
            # Sent BEFORE the debuff below: DeathWeakness.at_apply messages the
            # owner at once ("You claw back from the edge of death..."), and a
            # player must read that they died before they read that they came
            # back.
            self.msg(death_message(corpse.location if corpse else None))

            # Timed post-death debuff. remove-then-add guarantees a fresh single
            # stack with a fresh duration on re-death (buffs.add otherwise stacks).
            self.buffs.remove(DeathWeakness.key)
            self.buffs.add(DeathWeakness)
        finally:
            # Always clear the guard, even on exception, so a later legitimate
            # death is never silently swallowed.
            self.ndb._dying = False

    def start_resting(self):
        """
        Begin resting: occupy the shared timed-action slot and schedule the
        first recovery tick (Epic A, TA1.3).

        Two refusals, in this order. The order follows T8's precedent for
        `work`: the gate about the action the player NAMED runs first.

        1. "You are not tired." -- checked here, before the slot is touched, so
           a refused rest never occupies the slot and never has to give it back.
        2. "You are already <label>." -- written by `timed_actions.start()`
           itself (T2) when the slot holds anything, a chore included. Nothing
           is said here; `None` is the whole signal.

        Busy AND fully rested therefore answers "You are not tired.". Both are
        true; the one that wins is about the action the player asked for.

        Nobody hears "settles down" until `start()` has succeeded: those lines
        must never be sent for a rest that did not begin.

        The tick is the module-level `_rest_tick(char, marker)` (T10) -- the
        callback shape `_finish_task` already has. The room's "gets up" on an
        interrupt is `_announce_getting_up`, run by `interrupt()` as
        `on_interrupt`.
        """
        fatigue = self.traits.get("fatigue")
        if fatigue is None:
            return
        if fatigue.current >= fatigue.max:
            self.msg("You are not tired.")
            return
        marker = timed_actions.start(
            self,
            "rest",
            self.rest_interval,
            _rest_tick,
            label="resting",
            interrupt_msg="You get up, interrupting your rest.",
            on_interrupt=_announce_getting_up,
        )
        if marker is None:
            return
        self.msg("You settle down to rest.")
        if self.location:
            self.location.msg_contents(
                f"{self.key} settles down to rest.", exclude=self
            )

    def stop_resting(self, reason="You stop resting."):
        """
        End a rest in progress. A no-op unless the slot holds a REST (T12).

        "Safe to call from anywhere" is the contract this method has always
        had, and the shared slot is what makes it need a guard: a bare
        `interrupt(self, reason)` ends whatever occupies the slot, so calling
        this while working would cancel the chore and tell the worker "You stop
        resting.". The key check keeps the method about rest.

        Everything past the guard is `timed_actions.interrupt()`: it empties the
        slot, sends `reason` -- which overrides the "You get up, interrupting
        your rest." recorded at start (T4) -- and runs `_announce_getting_up` for
        the room. The pending tick is not cancelled; it fires, `is_current()`
        finds its marker gone, and it stops without touching the gauge.

        Args:
            reason (str): what the actor is told.

        Returns:
            bool: True if a rest was ended, False if there was none.
        """
        record = timed_actions.is_busy(self)
        if record is None or record.key != "rest":
            return False
        return timed_actions.interrupt(self, reason)

    def at_pre_move(self, destination, move_type="move", **kwargs):
        """
        Interrupt whatever timed action is in progress, but allow the move.

        One line for every timed action there is or will be (Epic A, D1). The
        hook knows that something was interrupted, never what: the sentence the
        player sees is the `interrupt_msg` the action recorded at start ("You
        break off what you were doing." for a chore, "You get up, interrupting
        your rest." for a rest), and a rest's `on_interrupt` tells the room
        "<name> gets up.". A new timed action joins by passing its own messages
        to `start()`; it does not edit this method.

        `interrupt()` is a silent no-op on an empty slot, so an idle character
        who moves is not messaged and pays for nothing.

        Clearing the slot is what cancels the action. The pending delay still
        fires on schedule, `claim()` (work) or `is_current()` (rest) finds the
        marker gone, and the callback returns without effect.

        This hook does not run for `move_to(..., move_hooks=False)` or a direct
        `location =` assignment. Death relocates with `move_hooks=False`, which
        is why `at_character_death()` calls `interrupt()` itself (D7).
        """
        timed_actions.interrupt(self)
        return super().at_pre_move(destination, move_type=move_type, **kwargs)

    def at_post_move(self, source_location, move_type="move", **kwargs):
        """
        Look around, then charge a step taken while overloaded (W3.2).

        Legend halves an overloaded character's Movement (core p.86); here
        every room entered through an exit costs `OVERLOAD_MOVE_FATIGUE`
        fatigue while the band is OVERLOADED or CEILING (WD3, Q4). The cost is
        flat and read live: no buff, no rate multiplier, nothing stored.

        Only walking costs (Q1). An exit moves with `move_type="traverse"`
        (Evennia `objects.py:3734`); `home` and `@tel` use `"teleport"`, and a
        script's bare `move_to` defaults to `"move"` -- neither pays. Death
        relocates with `move_hooks=False`, so this hook never runs for it.

        The gauge clamps at its `min` (Q5): a step at 0 leaves 0, and fatigue
        at 0 has no consequence until *Fatigue-exhaustion consequence* ships.

        The survival warning is checked on both sides of the drain. The check
        before sets the baseline in `ndb.survival_buckets` -- empty after a
        reload until the next tick, up to 1800 s away -- and never warns,
        since only the ticker lowers a gauge and it checks right after. The
        check after warns once if the step crossed into a worse bucket (Q2,
        tightened in session 6). No message of its own: the warning and the
        `inventory` line say what happened and why.

        The gauge is read with `traits.get()` and skipped if absent, as the
        ticker does: an exception here would make `move_to` return False after
        the move has happened (`objects.py:1331`), and the exit would tell a
        character who did move "You cannot go there."
        """
        super().at_post_move(source_location, move_type=move_type, **kwargs)
        if move_type != "traverse":
            return
        if self.encumbrance_state == encumbrance.FREE:
            return
        fatigue = self.traits.get("fatigue")
        if fatigue is None:
            return
        survival_ticker._check_survival_warnings(self)   # baseline (reload)
        fatigue.current -= encumbrance.OVERLOAD_MOVE_FATIGUE
        survival_ticker._check_survival_warnings(self)

    def at_pre_object_receive(self, arriving_object, source_location, **kwargs):
        """
        Refuse anything that would put this character above the ceiling (W2.1).

        The ceiling is OVERLOAD_FACTOR x the limit (WD2). The sum after the
        move comes from the reader (`encumbrance.enc_after_receiving`), never
        from arithmetic here: the twenty-to-one rule, a container's contents
        and an item already carried are the reader's business.

        `move_to` asks this hook before every move into the character
        (`get`, `give`, `get ... from`, and the five product sites through
        `receive_or_set_down`, W5.1), passes `move_type` and its other
        `kwargs` on, and logs and refuses if the hook raises -- so there is no
        `try/except` here. It does not run for a direct `location =`
        assignment or `move_hooks=False`; barter moves by assignment and is
        checked before the swap instead (`world/barter.py`, W5.1 Q5).

        On a refusal the character is told; a giving character is told too,
        since `CmdGive` prints only its generic line. The refusal also sets
        `ndb._enc_refused`, which `CmdGet` (commands/inventory_commands.py)
        reads to drop the contrib's own "This can't be picked up." -- one
        refusal, one sentence (W2.2 Q3). With `enc_quiet=True` in `kwargs`
        the hook refuses all the same but says nothing and sets no flag:
        `receive_or_set_down`'s caller sends the one line (W5.1 Q2).

        Returns:
            bool: False refuses the move; the object stays where it was.
        """
        if not super().at_pre_object_receive(arriving_object, source_location, **kwargs):
            return False
        ceiling = encumbrance.OVERLOAD_FACTOR * encumbrance.enc_limit(self)
        if encumbrance.enc_after_receiving(self, arriving_object) > ceiling:
            if kwargs.get("enc_quiet"):
                return False
            self.msg("You cannot carry any more.")
            self.ndb._enc_refused = True
            if (
                source_location is not None
                and source_location != self
                and inherits_from(source_location, _CHARACTER_PATH)
            ):
                source_location.msg(
                    f"{self.get_display_name(source_location)} cannot carry any more."
                )
            return False
        return True

    def at_object_leave(self, moved_obj, target_location, move_type="move", **kwargs):
        """
        Announce leaving the overloaded band (W2.2).

        `move_to` calls this before `moved_obj` moves (objects.py:1290), so
        *before* is the current sum and *after* is the reader's sum with the
        object at `target_location` (`encumbrance.enc_without`) -- never
        `carried_enc - item_enc`, which misses the twentieth item at `enc` 0.
        `move_to(None)` returns before any hook (objects.py:1244), so
        `target_location` is never None here.

        Args:
            moved_obj (Object): the object leaving this character.
            target_location (Object): where it is going.
            move_type (str): passed on to `super()`.
            **kwargs: passed on to `super()`.
        """
        super().at_object_leave(moved_obj, target_location, move_type=move_type, **kwargs)
        before = encumbrance.carried_enc(self)
        after = encumbrance.enc_without(self, moved_obj, target_location)
        self._announce_enc_crossing(before, after)

    def at_object_receive(self, moved_obj, source_location, move_type="move", **kwargs):
        """
        Announce entering the overloaded band (W2.2).

        `move_to` calls this after `moved_obj` has arrived (objects.py:1322),
        so *before* is the reader's sum with the object back at
        `source_location` (`encumbrance.enc_without`) and *after* is the
        current sum. `create_object(location=self)` calls it too, with
        `source_location` None and before the new object's Attributes are set
        (objects.py:1975): the newcomer weighs 0 at that moment, so only the
        twentieth item at `enc` 0 can cross there.

        Args:
            moved_obj (Object): the object that arrived.
            source_location (Object or None): where it came from.
            move_type (str): passed on to `super()`.
            **kwargs: passed on to `super()`.
        """
        super().at_object_receive(moved_obj, source_location, move_type=move_type, **kwargs)
        before = encumbrance.enc_without(self, moved_obj, source_location)
        after = encumbrance.carried_enc(self)
        self._announce_enc_crossing(before, after)

    def _announce_enc_crossing(self, before, after):
        """
        Tell the character when `before` and `after` sit on different sides of
        the limit (W2.2 Q2). OVERLOADED <-> CEILING is no crossing: W3 prices
        `!= FREE`, and no `move_to` enters CEILING (W2.1). Both sums go
        through the reader's band rule (`encumbrance.band`) against one read
        of the limit.

        No `try/except`, as in `at_pre_object_receive`: if the leave hook
        raises, `move_to` logs and refuses the move (objects.py:1291); the
        receive hook makes the reads `at_pre_object_receive` has just made,
        without error, for the same `move_to`.
        """
        limit = encumbrance.enc_limit(self)
        was_free = encumbrance.band(before, limit) == encumbrance.FREE
        now_free = encumbrance.band(after, limit) == encumbrance.FREE
        if was_free == now_free:
            return
        self.msg("You are no longer overloaded." if now_free else "You are overloaded.")

    def receive_or_set_down(self, objs):
        """
        Put new objects in this character's hands, or at its feet (W5.1 Q1).

        The one way a product reaches its maker: craft, forage, harvest,
        inscribe and scribe all call this, and none writes a fallback of its
        own. Each object goes through `move_to`, so the ceiling hook runs
        (W2.1) and a delivery that crosses the limit is announced (W2.2).
        `enc_quiet=True` keeps a refusal silent (Q2): the caller sends one
        line, after its own result line, from `set_down_message`.

        A refused object is moved to `self.location`. With no location (Q6),
        or a location that refuses it, the character keeps it after all,
        hooks off, and a warning is logged: a load above the ceiling in a
        case that should not occur beats a product at `location` None.

        Products arrive one at a time and in order, so a batch that fills the
        character part-way lands as "the first ones held, the rest set down",
        with the twenty-to-one rule read afresh for each.

        Args:
            objs (iterable of Object): new objects, normally at `location`
                None (spawned) -- never in this character already.

        Returns:
            list: the objects set down, in order; empty when all were taken.
        """
        set_down = []
        for obj in objs:
            if obj.move_to(self, quiet=True, enc_quiet=True):
                continue
            if self.location is not None and obj.move_to(self.location, quiet=True):
                set_down.append(obj)
                continue
            logger.log_warn(
                f"receive_or_set_down: {obj.key}(#{obj.id}) refused by "
                f"{self.key}(#{self.id}) with nowhere to set it down "
                f"(location {self.location!r}); kept above the ceiling."
            )
            obj.move_to(self, quiet=True, move_hooks=False)
        return set_down

    def set_down_message(self, objs):
        """
        The one line for what `receive_or_set_down` set down (W5.1 Q2).

        One object is named; several are counted, so a command's own line
        ("You harvest 6 ...") stays true and this one says how many of them
        did not stay in hand.

        Args:
            objs (list): what `receive_or_set_down` returned; not empty.

        Returns:
            str
        """
        if len(objs) == 1:
            return f"You cannot carry the {objs[0].get_display_name(self)}; you set it down."
        return f"You cannot carry {len(objs)} of them; you set them down."


# --- Rest callbacks (Epic A, TA1.3) -------------------------------------------
# Module level, not methods (T10). `timed_actions.start()` invokes its callback
# as `callback(char, *args, marker)` (T1), so a bound method would receive the
# character twice. This is the shape `_finish_task` (work) already has and
# `_complete_craft` (craft, TA2.1) will have: one callback shape for every timed
# action, each directly callable from a test without a running reactor.


def _rest_tick(char, marker):
    """
    One recovery step of a rest. Reschedules itself while the rest continues.

    The tuning knobs stay on the class (`rest_interval`, `rest_recovery`) and
    are read through `char`, so a subclass can still override them.

    Three ways out, and who empties the slot in each:

    - **Not current** -- a stale marker, an emptied slot, a deleted or an
      unpuppeted character. `is_current()` refuses. It clears the slot only for
      the unpuppeted body (T3); a stale tick must not clear anything, because
      the slot may now hold a newer rest or a chore that is none of its
      business.
    - **The rest ends here** -- fully rested, or no fatigue gauge at all. This
      function empties the slot with `claim()` (T11), as the first statement of
      the branch: before any message, so a `msg()` that raises cannot leave the
      character resting forever. `claim()` cannot be refused at that point --
      `is_current()` said yes in this same synchronous call, and the reactor is
      single-threaded -- so its return value is not consulted.
    - **Otherwise** -- reschedule with `delay(..., marker)` directly. Not via
      `start()`: the slot is occupied by this very rest, so `start()` would
      refuse it.

    Args:
        char (Character): the resting character.
        marker (object): the identity token `start()` minted for this rest.
    """
    if not timed_actions.is_current(char, marker):
        return
    fatigue = char.traits.get("fatigue")
    if fatigue is None:
        timed_actions.claim(char, marker)
        return
    fatigue.current += char.rest_recovery   # auto-clamps to max
    if fatigue.current >= fatigue.max:
        timed_actions.claim(char, marker)
        char.msg("You feel fully rested.")
        if char.location:
            char.location.msg_contents(
                f"{char.key} gets up, looking refreshed.", exclude=char
            )
        return
    delay(char.rest_interval, _rest_tick, char, marker)   # reschedule


def _announce_getting_up(char):
    """
    The room's half of an interrupted rest: `on_interrupt` for "rest".

    `timed_actions.interrupt()` runs this after the actor's own message, and
    only for a puppeted character -- under statue logout nobody is there to be
    seen getting up. Module level rather than a lambda in `start_resting()` so
    a test can assert identity on it and a traceback names it.
    """
    if char.location:
        char.location.msg_contents(f"{char.key} gets up.", exclude=char)
