# commands/mentor_commands.py
"""
Mentor system commands.
"""

from evennia import Command


class CmdMentor(Command):
    """
    Become a mentor to new players.
    
    Usage:
        mentor <player>
        mentor list
        mentor remove <player>
        
    As a mentor, you can:
    - Give items freely to your mentees
    - See when they're online
    - Get notified of their progress
    
    Requirements:
    - At least one skill at 50+
    - Have crafted at least 10 items
    """
    
    key = "mentor"
    aliases = ["teach", "guide"]
    locks = "cmd:all()"
    help_category = "Social"
    
    def func(self):
        """Execute mentor command."""
        caller = self.caller
        
        if not self.args:
            caller.msg("Usage: mentor <player> or mentor list")
            return
        
        if self.args == "list":
            self.list_mentees()
            return
        
        if self.args.startswith("remove "):
            self.remove_mentee(self.args[7:])
            return
        
        # Check requirements
        if not self.check_mentor_requirements():
            return
        
        # Find target
        target = caller.search(self.args)
        if not target:
            return
        
        if target == caller:
            caller.msg("You cannot mentor yourself.")
            return
        
        if hasattr(target.db, 'mentor') and target.db.mentor:
            caller.msg(f"{target.name} already has a mentor.")
            return
        
        # Add as mentee
        caller.add_mentee(target)
    
    def check_mentor_requirements(self):
        """Check if player qualifies to be a mentor."""
        caller = self.caller
        
        # Check skills
        has_skill = False
        for skill in ["crafting", "engineering", "survival"]:
            if caller.skills.get(skill).value >= 50:
                has_skill = True
                break
        
        if not has_skill:
            caller.msg("|rYou need at least one skill at 50+ to become a mentor.|n")
            return False
        
        # Check crafting experience
        craft_count = sum(caller.db.craft_counts.values()) if hasattr(caller.db, 'craft_counts') else 0
        if craft_count < 10:
            caller.msg(f"|rYou need to craft at least 10 items to become a mentor (current: {craft_count}).|n")
            return False
        
        return True
    
    def list_mentees(self):
        """List current mentees."""
        caller = self.caller
        mentees = caller.db.mentees or []
        
        if not mentees:
            caller.msg("You are not mentoring anyone.")
            return
        
        caller.msg("|wYour Mentees:|n")
        for mentee in mentees:
            online = " |g(online)|n" if mentee.has_account else " |x(offline)|n"
            caller.msg(f"  {mentee.name}{online}")
    
    def remove_mentee(self, name):
        """Stop mentoring someone."""
        caller = self.caller
        target = caller.search(name)
        if not target:
            return
        
        caller.remove_mentee(target)
