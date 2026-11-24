"""
Character-related commands for PolishedWorld

Commands for viewing character stats, skills, and vital status.
"""

from evennia import Command

from world import body
from world import hero_points
from world import wounds
from world import fatigue as fatigue_rules
from world.progression import progress_within_level, render_progress_bar


def _whole(number):
    """
    A trait number as the player reads it: a whole number, truncated.

    Every trait's `.value` (and a gauge's `.max`) is `(...) * mult`, and
    `mult` defaults to the float 1.0, so a CON stored as 7 reads back as 7.0
    (evennia/contrib/rpg/traits/traits.py, StaticTrait/CounterTrait/
    GaugeTrait). The one exception: a gauge whose `.base` is an int rounds
    its own `.current` on read (`GaugeTrait._update_current`), so a hunger of
    99.6 already reads 100 before it gets here. Truncated, not rounded, as
    `progress` already does.
    """
    return int(number)


def _percent(value):
    """
    A percentage as a gauge's `percent()` prints it by default: one decimal
    and a sign (`"{:3.1f}%"`, evennia/contrib/rpg/traits/traits.py), so a row
    read through the wound module looks as a trait's row does.
    """
    return f"{value:3.1f}%"


def _wound_lines(char):
    """
    The wounded locations under the health line, one indented line each
    (`wounds.report`, WN11); nothing for a body with only Minor Wounds.
    """
    return "".join(f"    {line}\n" for line in wounds.report(char))


class CmdStatus(Command):
    """
    View your vital status
    
    Usage:
        status
        vitals
    
    Shows your current health, hunger, thirst, and fatigue levels.
    Under health, a line for each badly wounded part of your body: its
    Hit Points, the wound, and what it does to you.
    Only you can see this information.
    """
    
    key = "status"
    aliases = ["vitals"]
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Display vital status"""
        char = self.caller
        
        # Check if character has traits
        if not hasattr(char, 'traits'):
            self.caller.msg("You have no vital status to display.")
            return
        
        # Build status display
        msg = "\n|wVital Status:|n\n"
        msg += "|g" + "=" * 40 + "|n\n"
        
        # Health: read through the wound module (WN-T3), never the trait;
        # out of 100, and where the hurt is on the lines under it (WN-T11).
        current, maximum, percent = wounds.health_shown(char)
        msg += f"  |yHealth:|n  {current:>3}/{maximum:<3} "
        msg += f"({_percent(percent):>6}) - {char.health_desc()}\n"
        msg += _wound_lines(char)
        
        # Hunger
        hunger = char.traits.hunger
        msg += f"  |yHunger:|n  {_whole(hunger.value):>3}/{_whole(hunger.max):<3} "
        msg += f"({hunger.percent():>6}) - {hunger.desc()}\n"
        
        # Thirst
        thirst = char.traits.thirst
        msg += f"  |yThirst:|n  {_whole(thirst.value):>3}/{_whole(thirst.max):<3} "
        msg += f"({thirst.percent():>6}) - {thirst.desc()}\n"
        
        # Fatigue: Legend's level (fatigue_desc(), S3.1) and, below Fresh,
        # what the level costs on physical tests (S3.2 adds it to the rolls).
        fatigue = char.traits.fatigue
        msg += f"  |yFatigue:|n {_whole(fatigue.value):>3}/{_whole(fatigue.max):<3} "
        msg += f"({fatigue.percent():>6}) - {char.fatigue_desc()}"
        penalty = fatigue_rules.penalty_for(fatigue.value)
        if penalty:
            msg += f" (-{penalty}% to physical tests)"
        msg += "\n"
        
        msg += "|g" + "=" * 40 + "|n"
        
        self.caller.msg(msg)


class CmdStats(Command):
    """
    View your character statistics
    
    Usage:
        stats
    
    Shows your Mongoose Legend characteristics (STR, DEX, CON, SIZ, INT, POW, CHA).
    Only you can see this information.
    """
    
    key = "stats"
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Display character stats"""
        char = self.caller
        
        # Check if character has stats
        if not hasattr(char, 'stats'):
            self.caller.msg("You have no stats to display.")
            return
        
        # Build stats display
        msg = "\n|wCharacter Statistics:|n\n"
        msg += "|g" + "=" * 40 + "|n\n"
        
        # Mongoose Legend characteristics
        for stat_key in ['str', 'dex', 'con', 'siz', 'int', 'pow', 'cha']:
            stat = getattr(char.stats, stat_key)
            msg += f"  |y{stat.name:14}|n {_whole(stat.value):>3}"
            
            # Show breakdown if there's a modifier
            if stat.mod != 0:
                msg += f"  (base {stat.base:>2} + mod {stat.mod:>+3})"
            
            msg += "\n"
        
        msg += "|g" + "=" * 40 + "|n"
        
        self.caller.msg(msg)


class CmdSkills(Command):
    """
    View your skills
    
    Usage:
        skills
    
    Shows all your learned skills and their current values.
    Only you can see this information.
    """
    
    key = "skills"
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Display skills"""
        char = self.caller
        
        # Check if character has skills
        if not hasattr(char, 'skills'):
            self.caller.msg("You have no skills to display.")
            return
        
        # Get all skills
        skill_keys = sorted(list(char.skills.all()))
        
        if not skill_keys:
            self.caller.msg("You have not learned any skills yet.")
            return
        
        # Build skills display
        msg = "\n|wSkills:|n\n"
        msg += "|g" + "=" * 50 + "|n\n"
        
        for skill_key in skill_keys:
            skill = getattr(char.skills, skill_key)
            
            # Skill name and value
            msg += f"  |y{skill.name:14}|n {_whole(skill.value):>3}%  "
            
            # Description
            msg += f"({skill.desc()})"
            
            # Show breakdown if there's a modifier
            if skill.mod != 0:
                msg += f"\n    └─ base {_whole(skill.base):>2} + current {_whole(skill.current - skill.base):>+3} + mod {skill.mod:>+3}"
            
            msg += "\n"
        
        msg += "|g" + "=" * 50 + "|n"
        
        self.caller.msg(msg)


class CmdProgress(Command):
    """
    View where each of your skills stands

    Usage:
        progress

    Shows every skill, how far it has climbed into its next percentage point,
    and how many points it has gained since you logged in. Only you can see this.
    """

    key = "progress"
    locks = "cmd:all()"
    help_category = "Character"

    # Reserved width for the bar column, so the untrainable/maxed captions that
    # replace a bar leave the rest of the row aligned. Must be >= the widest
    # caption below and >= the bar's own cell count.
    _BAR_COLUMN = 20

    def func(self):
        """
        Display each skill's standing, its progress bar and its session gain.

        WHAT D.1 CHANGED, AND WHY IT IS A DESIGN CHANGE AND NOT A REDRAW
        ----------------------------------------------------------------
        This command used to show *only* growth since login and to skip every
        skill that had not moved. That was correct while a tick moved the
        percentage nearly every time. After C.1 a level moves roughly once in
        dozens of ticks, so "unchanged" became the normal case and the command
        answered "No skills have improved since you logged in" for hours at a
        stretch -- the same silence C.2 fixed one level down, in the feedback
        line.

        So the skip-unchanged rule falls (locked D-3): every skill is listed
        every time, and the session delta becomes a *suffix* on the rows that
        earned one rather than the reason a row exists. The login snapshot is
        kept, not retired -- the two figures answer different questions at
        different grains ("what did this session buy me" vs "how far into the
        next point am I"), so one does not subsume the other.

        Both readings are taken from `.current`, never `.value`: the snapshot is
        recorded from `.current` at login, and a worn tool's +20 must not
        masquerade as either progress or standing.

        WHAT D.2 CHANGED, AND THE LIMIT IT KNOWINGLY ACCEPTS
        ----------------------------------------------------
        The `(at maximum)` caption is gone with the cap that produced it. There
        is no longer a state in which a skill's bar is frozen, so there is no
        longer a caption standing in for one; `(not yet trainable)` survives,
        because a skill with no call-site still has a bar that cannot move.

        The accepted limit, recorded here rather than rediscovered: **the bar's
        resolution runs out at skill ~96, not at 100.** D-1 gives 20 cells x 8
        eighth-blocks = 160 renderable states, and at (6, 20) a point first costs
        more than 160 XP at level 96 (161) -- from there one banked XP can leave
        the art unchanged. It degrades gracefully rather than breaking, but it
        degrades: at 150 a point costs 1 086 XP, so a single grain moves 0.15 of
        one eighth and the bar visibly steps about once every seven ticks. That
        is D.1's own silence returning fifty points higher up.

        It is accepted, not overlooked. The alternatives were a longer bar above
        100 (breaks D-1's 20 cells and the column alignment for a band almost
        nobody reaches) and a caption (dishonest -- the bar up there is coarse,
        not dead). Revisit only if a player is ever observed above ~130.
        """
        char = self.caller

        if not hasattr(char, "skills"):
            self.caller.msg("You have no skills to display.")
            return

        skill_keys = sorted(char.skills.all())
        if not skill_keys:
            self.caller.msg("You have no skills to display.")
            return

        # Baseline captured at login (Character.at_post_puppet). Coalesce
        # None -> {} for the edge where this runs before any puppet snapshot.
        snapshot = char.login_skill_snapshot or {}
        improvable = getattr(char, "improvable_skills", frozenset())
        rule = "|g" + "=" * 48 + "|n"

        lines = ["\n|wSkill progress:|n", rule]
        for skill_key in skill_keys:
            skill = char.skills.get(skill_key)
            if skill is None:
                continue
            now = int(skill.current)

            if skill_key not in improvable:
                # No call-site routes this skill through
                # attempt_skill_improvement, so its bar could never move. Saying
                # so is more informative than drawing a permanently empty bar,
                # and more honest than dropping the row.
                column = f"{'(not yet trainable)':<{self._BAR_COLUMN}}"
            else:
                # Derived on read from the lifetime total (P-1). Nothing about
                # this bar is stored, and no figure from it is shown (P-8). This
                # is now the ONLY branch a trainable skill can take, at any
                # level -- there is no ceiling to special-case (D.2).
                _earned, _needed, fraction = progress_within_level(
                    char.skill_xp.get(skill_key)
                )
                column = render_progress_bar(fraction, self._BAR_COLUMN)

            row = f"  |y{skill.name:<12}|n {now:>3}%  {column}"

            before = snapshot.get(skill_key)
            if before is not None and now > before:
                row += f"  (|G+{now - int(before)}|n)"

            lines.append(row)

        lines.append(rule)
        self.caller.msg("\n".join(lines))


class CmdSheet(Command):
    """
    View your complete character sheet
    
    Usage:
        sheet
        character
        char
    
    Shows all your character information: stats, vital status, the three
    values combat will read (Combat Actions, Strike Rank and the Damage
    Modifier) and skills. Only you can see this information.
    """
    
    key = "sheet"
    aliases = ["character", "char"]
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Display complete character sheet"""
        char = self.caller
        
        # Character name and title
        msg = "\n" + "|w" + "=" * 60 + "|n\n"
        msg += f"|W  {char.name}|n\n"
        msg += "|w" + "=" * 60 + "|n\n"
        
        # === CHARACTERISTICS ===
        if hasattr(char, 'stats'):
            msg += "\n|wCharacteristics:|n\n"
            msg += "|g" + "-" * 60 + "|n\n"
            
            for stat_key in ['str', 'dex', 'con', 'siz', 'int', 'pow', 'cha']:
                stat = getattr(char.stats, stat_key)
                msg += f"  |y{stat.name:14}|n {_whole(stat.value):>3}"
                
                if stat.mod != 0:
                    msg += f"  (base {stat.base} + mod {stat.mod:>+2})"
                
                msg += "\n"
        
        # === VITAL STATUS ===
        if hasattr(char, 'traits'):
            msg += "\n|wVital Status:|n\n"
            msg += "|g" + "-" * 60 + "|n\n"
            
            # Health through the wound module (WN-T3), as `status` reads it.
            current, maximum, percent = wounds.health_shown(char)
            msg += f"  |y{'Health':14}|n {current:>3}/{maximum:<3} "
            msg += f"({_percent(percent):>6}) - {char.health_desc()}\n"
            msg += _wound_lines(char)

            for trait_key in ['hunger', 'thirst', 'fatigue']:
                trait = getattr(char.traits, trait_key)
                msg += f"  |y{trait.name:14}|n {_whole(trait.value):>3}/{_whole(trait.max):<3} "
                # Fatigue's label is Legend's level, read from the one table
                # (S3.1); hunger and thirst keep the trait's own desc().
                if trait_key == "fatigue":
                    label = char.fatigue_desc()
                else:
                    label = trait.desc()
                msg += f"({trait.percent():>6}) - {label}\n"
        
        # === COMBAT (BD9) ===
        # Read now, never stored (BD7): fatigue lowers Combat Actions and
        # Strike Rank, so the block follows the Fatigue row above it. A body
        # without the characteristics gets no block.
        derived = body.derived(char)
        if derived is not None:
            modifier = body.format_damage_modifier(derived["damage_modifier"])
            msg += "\n|wCombat:|n\n"
            msg += "|g" + "-" * 60 + "|n\n"
            msg += f"  |y{'Combat Actions':16}|n {derived['combat_actions']:>5}\n"
            msg += f"  |y{'Strike Rank':16}|n {derived['strike_rank']:>5}\n"
            msg += f"  |y{'Damage Modifier':16}|n {modifier:>5}\n"

        # === SKILLS ===
        if hasattr(char, 'skills'):
            skill_keys = sorted(list(char.skills.all()))
            
            if skill_keys:
                msg += "\n|wSkills:|n\n"
                msg += "|g" + "-" * 60 + "|n\n"
                
                for skill_key in skill_keys:
                    skill = getattr(char.skills, skill_key)
                    msg += f"  |y{skill.name:14}|n {_whole(skill.value):>3}%  ({skill.desc()})\n"
        
        msg += "\n" + "|w" + "=" * 60 + "|n"
        
        self.caller.msg(msg)


# What `hero glancing off|on` answers (HE3; chosen at HE-T3's STOPP 0). Each
# says what the choice costs, in the book's words.
GLANCING_OFF = (
    "Glancing Blow is off. A Major Wound will stand, and your Hero Points are kept."
)
GLANCING_ON = (
    "Glancing Blow is on. A Major Wound will cost a Hero Point and be a "
    "Serious Wound instead."
)
GLANCING_ALREADY = "Glancing Blow is already {}."
HERO_USAGE = "Usage: hero, hero glancing on, hero glancing off."


class CmdHero(Command):
    """
    Your Hero Points, and Glancing Blow

    Usage:
        hero
        hero glancing off
        hero glancing on

    Hero Points are the grit an adventurer has put by. You begin with two,
    and earn one for every day of the world's time you play - six hours at
    the keyboard - up to {cap}, the most anyone holds.

    Glancing Blow: when a blow would give you a Major Wound and you have a
    Hero Point, the point is spent and the wound is a Serious one instead.
    It works by itself. Switch it off to keep your points, and on again
    whenever you like; switching costs nothing.

    Only you can see this information.
    """

    key = "hero"
    locks = "cmd:all()"
    help_category = "Character"

    def get_help(self, caller, cmdset):
        """
        The help text, with the cap read from `hero_points.CAP` when it is
        asked for (chosen at HE-T3's STOPP 0): a cap typed into the text
        could not be told from one read until the cap changed. The search
        index keeps the unformatted docstring; only matching reads it.
        """
        return self.__doc__.format(cap=hero_points.CAP)

    def func(self):
        """Show the points and the switch, or set the switch (HE3)."""
        char = self.caller
        words = self.args.strip().lower().split()
        if not words:
            held = f"{hero_points.points(char)}/{hero_points.CAP}"
            state = "on" if hero_points.glancing_on(char) else "off"
            char.msg(
                f"  |y{'Hero Points':16}|n {held:>5}\n"
                f"  |y{'Glancing Blow':16}|n {state:>5}\n"
                "  Switch it with hero glancing off or hero glancing on."
            )
            return
        if len(words) == 2 and words[0] == "glancing" and words[1] in ("on", "off"):
            on = words[1] == "on"
            if hero_points.set_glancing(char, on):
                char.msg(GLANCING_ON if on else GLANCING_OFF)
            else:
                char.msg(GLANCING_ALREADY.format(words[1]))
            return
        char.msg(HERO_USAGE)
