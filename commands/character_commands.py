"""
Character-related commands for PolishedWorld

Commands for viewing character stats, skills, and vital status.
"""

from evennia import Command

from world.professions import PROFESSIONS, grant_profession
from world.progression import progress_within_level, render_progress_bar


class CmdStatus(Command):
    """
    View your vital status
    
    Usage:
        status
        vitals
    
    Shows your current health, hunger, thirst, and fatigue levels.
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
        
        # Health
        health = char.traits.health
        msg += f"  |yHealth:|n  {health.value:>3}/{health.max:<3} "
        msg += f"({health.percent():>6}) - {health.desc()}\n"
        
        # Hunger
        hunger = char.traits.hunger
        msg += f"  |yHunger:|n  {hunger.value:>3}/{hunger.max:<3} "
        msg += f"({hunger.percent():>6}) - {hunger.desc()}\n"
        
        # Thirst
        thirst = char.traits.thirst
        msg += f"  |yThirst:|n  {thirst.value:>3}/{thirst.max:<3} "
        msg += f"({thirst.percent():>6}) - {thirst.desc()}\n"
        
        # Fatigue
        fatigue = char.traits.fatigue
        msg += f"  |yFatigue:|n {fatigue.value:>3}/{fatigue.max:<3} "
        msg += f"({fatigue.percent():>6}) - {fatigue.desc()}\n"
        
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
            msg += f"  |y{stat.name:14}|n {stat.value:>3}"
            
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
            msg += f"  |y{skill.name:14}|n {skill.value:>3}%  "
            
            # Description
            msg += f"({skill.desc()})"
            
            # Show breakdown if there's a modifier
            if skill.mod != 0:
                msg += f"\n    └─ base {skill.base:>2} + current {skill.current - skill.base:>+3} + mod {skill.mod:>+3}"
            
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
            cap = skill.max if skill.max is not None else 100

            if skill_key not in improvable:
                # No call-site routes this skill through
                # attempt_skill_improvement, so its bar could never move. Saying
                # so is more informative than drawing a permanently empty bar,
                # and more honest than dropping the row.
                column = f"{'(not yet trainable)':<{self._BAR_COLUMN}}"
            elif now >= cap:
                # ⚠️ TODO(D.2): this branch dies with the cap. `improve_skill_on_use`
                # short-circuits at the ceiling and freezes the XP total inside
                # [threshold(cap), threshold(cap + 1)), so the bar here would show
                # a partial fill that never moves again -- worse than no bar.
                column = f"{'(at maximum)':<{self._BAR_COLUMN}}"
            else:
                # Derived on read from the lifetime total (P-1). Nothing about
                # this bar is stored, and no figure from it is shown (P-8).
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
    
    Shows all your character information: stats, skills, and vital status.
    Only you can see this information.
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
                msg += f"  |y{stat.name:14}|n {stat.value:>3}"
                
                if stat.mod != 0:
                    msg += f"  (base {stat.base} + mod {stat.mod:>+2})"
                
                msg += "\n"
        
        # === VITAL STATUS ===
        if hasattr(char, 'traits'):
            msg += "\n|wVital Status:|n\n"
            msg += "|g" + "-" * 60 + "|n\n"
            
            for trait_key in ['health', 'hunger', 'thirst', 'fatigue']:
                trait = getattr(char.traits, trait_key)
                msg += f"  |y{trait.name:14}|n {trait.value:>3}/{trait.max:<3} "
                msg += f"({trait.percent():>6}) - {trait.desc()}\n"
        
        # === SKILLS ===
        if hasattr(char, 'skills'):
            skill_keys = sorted(list(char.skills.all()))
            
            if skill_keys:
                msg += "\n|wSkills:|n\n"
                msg += "|g" + "-" * 60 + "|n\n"
                
                for skill_key in skill_keys:
                    skill = getattr(char.skills, skill_key)
                    msg += f"  |y{skill.name:14}|n {skill.value:>3}%  ({skill.desc()})\n"
        
        msg += "\n" + "|w" + "=" * 60 + "|n"
        
        self.caller.msg(msg)


class CmdChooseProfession(Command):
    """
    Choose your starting profession

    Usage:
        profession
        profession <name>

    With no argument, lists the professions you can choose and the advanced
    recipes each one teaches. With a name, commits you to that trade and
    teaches you its recipes.

    Choosing a profession is a ONE-TIME decision: once chosen it cannot be
    changed. It grants recipe *knowledge* only -- it does not alter your
    characteristics or skills, and how well you craft still depends on your
    Craft skill. You can always learn other recipes later by being taught
    them or by studying a scroll.
    """

    key = "profession"
    aliases = ["professions"]
    locks = "cmd:all()"
    help_category = "Character"

    def func(self):
        caller = self.caller
        chosen = caller.db.profession
        arg = self.args.strip().lower()

        # No argument -> show current choice (if any) and the available list.
        if not arg:
            msg = "\n|wProfessions:|n\n"
            msg += "|g" + "=" * 40 + "|n\n"
            if chosen:
                msg += f"  You follow the |y{chosen}|n's craft.\n\n"
            else:
                msg += "  You have not yet chosen a profession.\n\n"
            for pkey in sorted(PROFESSIONS):
                recipes = ", ".join(PROFESSIONS[pkey])
                msg += f"  |y{pkey}|n: {recipes}\n"
            msg += "|g" + "=" * 40 + "|n"
            if not chosen:
                msg += "\nType |wprofession <name>|n to commit to one. The choice is permanent."
            caller.msg(msg)
            return

        # Already chosen -> refuse. This sentinel is the idempotency guard: it
        # makes the grant a once-per-character event, safe across @reload and
        # re-puppet (this command is B's only grant path).
        if chosen:
            caller.msg(
                f"You have already taken up the |y{chosen}|n's craft; "
                "a profession is chosen only once. Type |wprofession|n to review it."
            )
            return

        # Unknown key -> reject by name, listing the valid choices.
        if arg not in PROFESSIONS:
            valid = ", ".join(sorted(PROFESSIONS))
            caller.msg(f"There is no '|y{arg}|n' profession. Choose one of: {valid}.")
            return

        # Commit: seed the recipes FIRST, then stamp the sentinel LAST, so a
        # failure mid-grant leaves the character retry-able (unset sentinel)
        # rather than committed-but-untaught. grant_profession is idempotent.
        learned = grant_profession(caller, arg)
        caller.db.profession = arg
        if learned:
            caller.msg(
                f"You take up the |y{arg}|n's craft. "
                f"You now know how to make: {', '.join(learned)}."
            )
        else:
            caller.msg(
                f"You take up the |y{arg}|n's craft. You already knew its recipes."
            )
