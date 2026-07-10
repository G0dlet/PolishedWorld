"""
Character-related commands for PolishedWorld

Commands for viewing character stats, skills, and vital status.
"""

from evennia import Command


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
    View your skill growth this session

    Usage:
        progress

    Shows how far each skill has climbed since you logged in -- the value at
    login, the value now, and the points gained. Skills that haven't moved are
    left out. Only you can see this.
    """

    key = "progress"
    locks = "cmd:all()"
    help_category = "Character"

    def func(self):
        """Display per-skill growth since the login snapshot."""
        char = self.caller

        if not hasattr(char, "skills"):
            self.caller.msg("You have no skills to display.")
            return

        # Baseline captured at login (Character.at_post_puppet). Coalesce
        # None -> {} for the edge where this runs before any puppet snapshot.
        snapshot = char.login_skill_snapshot or {}
        rule = "|g" + "=" * 40 + "|n"

        rows = []
        for skill_key in sorted(char.skills.all()):
            skill = char.skills.get(skill_key)
            before = snapshot.get(skill_key)
            now = skill.current
            # Skip skills absent at login (before is None) or unchanged. Growth
            # is read on .current (permanent), matching the snapshot, so a worn
            # tool buff never masquerades as progress.
            if before is None or now <= before:
                continue
            rows.append((skill.name, before, now, now - before))

        if not rows:
            self.caller.msg(
                f"\n|wProgress this session:|n\n{rule}\n"
                "  No skills have improved since you logged in.\n"
                f"{rule}"
            )
            return

        lines = ["\n|wProgress this session:|n", rule]
        for name, before, now, gain in rows:
            lines.append(f"  |y{name:14}|n {before:>3} |w→|n {now:<3} (|G+{gain}|n)")
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
