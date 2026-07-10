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
from evennia import create_object
from evennia.utils import logger
from world.survival_buffs import DeathWeakness
from world.improvement import improvement_roll, tier_for

from django.conf import settings
from evennia.utils import search


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
        Attempt one Legend improvement roll on a skill and apply the result.

        The on-use analogue of spending an Improvement Roll in the tabletop
        game, and the single chokepoint for on-use skill growth. It does NOT
        decide *whether* a use is eligible (success-only, real-difficulty,
        cooldown) -- that gate lives in the caller (Component B.2). By the time
        this runs, the decision to attempt improvement has already been made.

        Improvement is measured against the skill's *permanent* learned level
        (`.current`), NOT its effective `.value`. `.value` folds in situational
        `.mod` (e.g. a +20 tool buff); a temporary bonus must not raise the
        roll's target and make a skill *harder to permanently improve*. So we
        read and write `.current` throughout and let the MVP cap (100) hold.

        Args:
            skill_key (str): key of the skill, e.g. "craft" or "hunting".

        Returns:
            dict or None: None if this character has no such skill. Otherwise a
            summary the felt-progress layer consumes:
              - "skill_key" (str)
              - "rolled" (bool): False when already at cap (no roll is wasted
                on a mastered skill).
              - "old" / "new" (int): permanent skill % before / after.
              - "delta" (int): new - old (0 when maxed).
              - "beat" (bool): did the roll beat current skill (the 1D4+1
                outcome)? False when not rolled.
              - "crossed" (list[int]): which of 25/50/75/100 were passed this
                tick -- the celebration hooks for C.2.

        Multiplayer note: this is a read-modify-write on `.current`. Evennia's
        Twisted reactor runs single-threaded and does not preempt a command
        mid-call, so concurrent uses serialise safely without an explicit lock.
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
        if old >= cap:
            return {"skill_key": skill_key, "rolled": False, "old": old,
                    "new": old, "delta": 0, "beat": False, "crossed": []}

        int_char = self.stats.int.value   # full INT added to the 1D100 (Legend)
        res = improvement_roll(old, int_char)

        # CounterTrait's setter already clamps via _enforce_boundaries, but we
        # clamp here too so the returned old/new/delta are exact regardless.
        new = min(cap, old + res["gained"])
        skill.current = new

        crossed = [t for t in (25, 50, 75, 100) if old < t <= new]

        return {"skill_key": skill_key, "rolled": True, "old": old, "new": new,
                "delta": new - old, "beat": res["beat"], "crossed": crossed}

            # Real-time seconds between on-use improvement ticks *per skill*. A balance
    # knob (dev value; tune once playtesting shows the grind's real shape). Real
    # time, not game time: this throttles wall-clock action spam, not in-game
    # duration.
    improvement_cooldown = 30

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
        place for the copy across all four call sites (craft, repair, hunt-attack,
        hunt-harvest), and the single seam the threshold celebration (C.2) will
        compose onto.

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
        # nothing to say. A rolled tick always has delta >= 1 (Legend's +1 floor),
        # so rolled=True is a sufficient gate.
        if not result or not result.get("rolled"):
            return ""

        # Re-fetch for the display label ("Crafting", not "craft"). The skill
        # existed when the tick fired; guard against a mid-command removal by
        # falling back to a title-cased key.
        skill = self.skills.get(result["skill_key"])
        label = skill.name if skill is not None else result["skill_key"].title()

        lines = [f"Your {label} improves! (+{result['delta']}, now {result['new']}%)"]

        # C.2 tier-celebration: fire only on the tick that actually crosses a
        # desc-tier boundary (a genuine named rank-up), never on the raw quarter
        # marks. Computed from the permanent old/new ints via tier_for (NOT
        # skill.desc(), which reads the buff-inflated .value), so a tool buff can
        # neither fake nor mask a crossing. Naturally idempotent: improvement is
        # monotonic (delta >= 1) and boundaries sit >= 15 apart while a single
        # tick gains at most 5, so each boundary is crossed on exactly one tick.
        # descs is None on an un-migrated character -> tier_for returns "" -> skip.
        descs = skill.descs if skill is not None else None
        old_tier = tier_for(result["old"], descs)
        new_tier = tier_for(result["new"], descs)
        if new_tier and new_tier != old_tier:
            lines.append(f"Your {label} reaches a new tier: |y{new_tier}|n.")

        return "\n".join(lines)

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
        """Interrupt resting when moving, but allow the move itself."""
        if self.ndb.resting:
            self.stop_resting("You get up, interrupting your rest.")
        return super().at_pre_move(destination, move_type=move_type, **kwargs)
