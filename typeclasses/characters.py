"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
import random
from evennia.objects.objects import DefaultCharacter
from evennia.utils import lazy_property
from evennia.contrib.rpg.traits import TraitHandler
from evennia.contrib.game_systems.clothing import ClothedCharacter

from .scripts import TraitsUpdateScript
from .objects import ObjectParent


class Character(ObjectParent, DefaultCharacter):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like this.

    """

    pass


class CharacterBase(ClothedCharacter):
    """Base Characterclass for PolishedWorld."""

    @lazy_property
    def stats(self):
        return TraitHandler(self, db_attribute_key="stats")

    @lazy_property
    def traits(self):
        return TraitHandler(self, db_attribute_key="traits")

    @lazy_property
    def skills(self):
        return TraitHandler(self, db_attribute_key="skills")


    def at_object_creation(self):
        """Anropas nar en ny karaktar skapas."""
        super().at_object_creation()

        # Grundlaggande attribute
        self.setup_stats()

        # Overlevnadsegenskaper
        self.setup_traits()

        # Fardigheter
        self.setup_skills()

        # Lagg till hunger/torst-skript
        self.scripts.add(TraitsUpdateScript)

    def setup_stats(self):
        stats_data = {
            "strength": "Strength",
            "dexterity": "Dexterity",
            "constitution": "Constitution",
            "intelligence": "Intelligence",
            "wisdom": "Wisdom",
            "charisma": "Charisma"
        }
        for stat_key, stat_name in stats_data.items():
            self.stats.add(stat_key, stat_name, trait_type="static", base=10, mod=0, min=1, max=20)

    def setup_traits(self):
        traits_data = {
            "hunger": ("Hunger", "gauge", 0, 100, 0),
            "thirst": ("Thirst", "gauge", 0, 100, 0),
            "fatigue": ("Fatigue", "gauge", 0, 100, 0),
            "health": ("Health", "gauge", 0, 100, 100)
        }
        for trait_key, (trait_name, trait_type, min_val, max_val, base_val) in traits_data.items():
            self.traits.add(trait_key, trait_name, trait_type=trait_type, min=min_val, max=max_val, base=base_val)

    def setup_skills(self):
        skills_data = {
            "hunting": "Hunting",
            "crafting": "Crafting",
            "fishing": "Fishing",
            "mining": "Mining",
            "woodcutting": "Woodcutting"
        }
        for skill_key, skill_name in skills_data.items():
            modifier = self.calculate_skill_modifier(skill_key)
            self.skills.add(skill_key, skill_name, trait_type="counter", base=0, mod=modifier, min=0, max=100)
            self.add_skill_description(skill_key)

    def add_skill_description(self, skill_key):
        skill_descs = {
            0: "unskilled",
            20: "novice",
            40: "competent",
            60: "proficient",
            80: "expert",
            95: "master"
        }
        getattr(self.skills, skill_key).descs = skill_descs

    def calculate_skill_modifier(self, skill_name):
        if skill_name in ["hunting", "fishing"]:
            return (self.stats.dexterity.value - 10) // 2
        elif skill_name in ["crafting", "mining"]:
            return (self.stats.strength.value - 10) // 2
        elif skill_name in ["woodcutting"]:
            return (self.stats.constitution.value - 10) // 2
        return 0

    def update_survival_needs(self, time_passed):
        trait_rates = {
            "hunger": 1.0,    # hunger points per hour
            "thirst": 1.5,    # thirst points per hour
            "fatigue": 0.5    # fatigue points per hour
        }

        # self.msg(f"update_survival_needs: time_passed = {time_passed} seconds")
        time_in_hours = float(time_passed) / 3600.0
        # self.msg(f"update_survival_needs: time_in_hours = {time_in_hours}")

        for trait_name, rate in trait_rates.items():
            try:
                trait_data = self.traits.trait_data.get(trait_name, {})
                if not trait_data:
                    continue
                
                old_value = trait_data.get("current", trait_data.get("base", 0))
                max_value = trait_data.get("max", 100)
                change = rate * time_in_hours
                new_value = min(old_value + change, max_value)
            
                # Debug information
                # self.msg(f"Updating {trait_name}:")
                # self.msg(f"- Rate: {rate}/hour")
                # self.msg(f"- Old value: {old_value}")
                # self.msg(f"- Change: +{change}")
                # self.msg(f"- New value: {new_value}")
            
                # Uppdatera värdet direkt i trait_data
                self.traits.trait_data[trait_name]["current"] = new_value
            
                if (new_value / max_value) >= 0.8:
                    self.msg(f"You are feeling very {trait_name}!")
                
            except Exception as e:
                self.msg(f"Error updating {trait_name}: {str(e)}")
    
    def update_all_traits(self, time_passed):
        self.update_survival_needs(time_passed)

    def update_all_skills(self):
        for skill in self.skills.all():
            modifier = self.calculate_skill_modifier(skill.name)
            skill.mod = modifier

    def improve_skill(self, skill_name, amount):
        if hasattr(self.skills, skill_name):
            skill = getattr(self.skills, skill_name)
            new_value = min(skill.base + amount, skill.max)
            skill.base = new_value
            self.msg(f"Your {skill.name} skill has improved to {new_value}!")
        else:
            self.msg(f"You don't have a skill named {skill_name}.")

    def at_say(self, message, msg_self, msg_location, receivers, msg_receivers, **kwargs):
        """
        Overskrider at_say for att lagga till en chans att forbattra charisma nar man pratar.
        """
        super().at_say(message, msg_self, msg_location, receivers, msg_receivers, **kwargs)

        # 5% chans att forbattra charisma nar man pratar
        if random.random() < 0.05:
            current_charisma = self.stats.charisma.value
            if current_charisma < self.stats.charisma.max:
                self.stats.charisma.base += 1
                self.msg("Your charisma has improved from talking!")
