from world.prototypes import SEED_PROTOTYPES
from evennia import Command, CmdSet, spawn
from evennia import create_object
from evennia.utils import search
from evennia.utils.utils import inherits_from
from typeclasses.plants import Plant, Seed  # Importera dina växtklasser
from typeclasses.compost import Compost

class CmdPlant(Command):
    """
    Plantera en växt eller ett träd.
    
    Användning:
      plant <växttyp>
      
    Exempel:
      plant ros
      plant tall
    """
    
    key = "plant"
    aliases = ["plantera"]
    locks = "cmd:all()"
    
    def func(self):
        caller = self.caller
        
        if not self.args:
            caller.msg("What do you whant to plant?")
            return
            
        seed = caller.search(self.args, location=caller)
        if not seed:
            return

        if not inherits_from(seed, "typeclasses.plants.Seed"):
            caller.msg("You can only plant seeds.")
            return

        plant_type = seed.db.plant_type
        if not plant_type:
            caller.msg("This seed appears to be dead.")
            return

        # Create the plant
        new_plant = create_object(
            Plant,
            key=plant_type,
            location=caller.location
        )

        # Remove the seed
        seed.delete()

        caller.msg(f"You plant the {plant_type} seed.")
        caller.location.msg_contents(
            f"$You() $conj(plant) a {plant_type} seed.",
            from_obj=caller,
            exclude=caller
        )

class CmdHarvest(Command):
    """
    Skörda en växt.
    
    Användning:
      harvest <växt>
      
    Exempel:
      harvest ros
    """
    
    key = "harvest"
    aliases = ["skörda"]
    locks = "cmd:all()"
    
    def func(self):
        caller = self.caller
        
        if not self.args:
            caller.msg("Vad vill du skörda?")
            return
            
        target = self.args.strip()
        plants = [obj for obj in caller.location.contents 
                 if obj.typeclass_path == "typeclasses.plants.Plant"]
        
        plant = None
        for obj in plants:
            if obj.key.lower() == target.lower():
                plant = obj
                break
                
        if not plant:
            caller.msg("Det finns ingen sådan växt här.")
            return
            
        success, message = plant.harvest(caller)
        caller.msg(message)

class CmdChop(Command):
    """
    Hugga ett träd.
    
    Användning:
      chop <träd>
      
    Exempel:
      chop tall
    """
    
    key = "chop"
    aliases = ["hugg"]
    locks = "cmd:all()"
    
    def func(self):
        caller = self.caller
        
        if not self.args:
            caller.msg("Vilket träd vill du hugga?")
            return
            
        target = self.args.strip()
        trees = [obj for obj in caller.location.contents 
                if obj.typeclass_path == "typeclasses.plants.Tree"]
        
        tree = None
        for obj in trees:
            if obj.key.lower() == target.lower():
                tree = obj
                break
                
        if not tree:
            caller.msg("Det finns inget sådant träd här.")
            return
            
        success, message, wood = tree.chop(caller)
        caller.msg(message)
        if success:
            # Här kan du lägga till logik för att ge ved till spelaren
            caller.msg(f"Du fick {wood} vedklampar.")

class CmdCollectCompost(Command):
    """
    Samla kompost.
    
    Användning:
      collect compost
      samla kompost
    """
    
    key = "collect compost"
    aliases = ["samla kompost"]
    
    def func(self):
        # Hitta all kompost i rummet
        composts = [obj for obj in self.caller.location.contents 
                   if isinstance(obj, Compost)]
        
        if not composts:
            self.caller.msg("Det finns ingen kompost att samla här.")
            return
            
        total_nutrients = 0
        for compost in composts:
            nutrients = compost.db.nutrients
            total_nutrients += nutrients
            compost.delete()
            
        if total_nutrients > 0:
            # Här kan du lägga till logik för att ge näringspoäng till spelaren
            self.caller.msg(f"Du samlar {total_nutrients} näringspoäng från komposten.")
        else:
            self.caller.msg("Komposten innehåller ingen näring.")

class CmdCreateSeed(Command):
    """
    Create a seed for testing.
    
    Usage:
      createseed <seedtype>
    """

    key = "createseed"
    locks = "cmd:perm(Builder)"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: createseed <seedtype>")
            return

        seedtype = self.args.strip().upper() + "_SEED"
        if seedtype not in SEED_PROTOTYPES:
            self.caller.msg(f"Invalid seed type. Valid types are: {', '.join(SEED_PROTOTYPES.keys())}")
            return

        seed = spawn(SEED_PROTOTYPES[seedtype], location=self.caller)[0]
        self.caller.msg(f"Created {seed.key}.")


class PlantCmdSet(CmdSet):
    """
    Samlar alla växt-relaterade kommandon.
    """
    
    def at_cmdset_creation(self):
        self.add(CmdPlant())
        self.add(CmdHarvest())
        self.add(CmdChop())
        self.add(CmdCollectCompost())
        self.add(CmdCreateSeed())
