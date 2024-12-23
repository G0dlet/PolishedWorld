from world.prototypes import SEED_PROTOTYPES
from evennia import ON_DEMAND_HANDLER, create_object, utils, spawn
from .objects import Object
from typeclasses.compost import Compost
from random import random, randint

class Plant(Object):
    """
    Växtklass med schemalagd kompostering vid död.
    """
    
    def at_object_creation(self):
        """Sätt grundläggande attribut för växten."""
        super().at_object_creation()
        
        # Grundläggande attribut
        self.db.stage = "seed"
        self.db.health = 100
        self.db.fruits = 0
        self.db.seeds = 0
        
        # Snabba tider för testning (i sekunder)
        self.growth_stages = {
            0: "seed",
            30: "sprout",
            60: "young",
            90: "mature",
            120: "flowering",  # Börja producera frön
            150: "harvestable",  # Full med frön
            180: "withering",  # Släpper frön
            210: "dead"
        }
        
        # Starta tillväxtcykeln
        try:
            ON_DEMAND_HANDLER.add(
                self,
                category="plant_growth",
                stages=self.growth_stages
            )
            
            # Schemalägga transformationen till kompost
            seed_scatter_time = 180  # När växten börjar vissna
            death_time = 210  # Tiden till död i sekunder

            utils.delay(seed_scatter_time, self.scatter_seeds)
            utils.delay(death_time, self.transform_to_compost)
            
        except Exception as e:
            self.msg(f"Error starting growth: {e}")

    def update_stage(self, stage):
        """
        Uppdatera växtens tillstånd baserat på stadium.
        """
        self.db.stage = stage
        
        match stage:
            case "seed":
                self.db.health = 100
                self.db.fruits = 0
                self.db.seeds = 0
            case "sprout":
                self.db.size = 2
            case "young":
                self.db.size = 3
            case "mature":
                self.db.size = 4
            case "flowering":
                if self.db.fruits == 0:
                    self.db.fruits = randint(1, 3)
                if self.db.seeds == 0:
                    self.db.seeds = randint(2, 5)
            case "harvestable":
                if self.db.seeds < 5:
                    self.db.seeds += randint(1, 3)
            case "withering":
                self.db.health = 50
                self.scatter_seeds()

    def scatter_seeds(self):
        """Sprid frön automatiskt om de inte skördas"""
        # Kolla om frön redan spridits
        if hasattr(self.db, "seeds_scattered") and self.db.seeds_scattered:
            return

        if self.db.seeds == 0:
            self.db.seeds = randint(2, 5)

        if self.db.seeds > 0:
            seeds_to_scatter = self.db.seeds
            success_chance = 0.7  # 70% chans att fröet överlever

            scattered = 0
            for _ in range(seeds_to_scatter):
                if random() < success_chance:
                    proto = SEED_PROTOTYPES[f"{self.key.upper()}_SEED"].copy()
                    try:
                        # Skapa fröet och sätt dess plats explicit
                        seed = spawn(proto)[0]
                        seed.move_to(self.location, quiet=True)
                        scattered += 1
                        # Debug meddelande
                        self.location.msg_contents(f"DEBUG: Seed location: {seed.location}")
                    except Exception as e:
                        self.location.msg_contents(f"Error creating seed: {e}")

            if scattered > 0:
                self.location.msg_contents(
                    f"The {self.key} drops {scattered} seeds on the ground."
                )
            self.db.seeds = 0
            self.db.seeds_scattered = True  # Markera att frön har spridits.

    def harvest_seeds(self, harvester):
        """Låt spelare skörda frön"""
        if self.db.stage not in ["flowering", "harvestable"]:
            return False, "This plant isn't ready to harvest seeds from."
            
        if self.db.seeds <= 0:
            return False, "This plant has no seeds to harvest."
            
        num_seeds = self.db.seeds
        for _ in range(num_seeds):
            seed = spawn(SEED_PROTOTYPES[f"{self.key.upper()}_SEED"], location=harvester)[0]
            
        self.db.seeds = 0
        return True, f"You harvest {num_seeds} seeds from the {self.key}."

    def transform_to_compost(self):
        """
        Förvandla växten till kompost.
        """
        # se till att frön sprids först
        self.scatter_seeds()

        # Kontrollera att växten fortfarande existerar
        if not self.pk or not self.location:
            return
            
        # Skapa kompostobjekt
        compost = create_object(
            Compost,
            key="kompost",
            location=self.location
        )
        
        # Sätt kompostens attribut
        compost.db.source_plant = self.key
        compost.db.nutrients = 10
        
        # Meddela rummet
        self.location.msg_contents(
            f"|yEn {self.key} har dött och förvandlats till en komposthög.|n"
        )
        
        # Ta bort växten
        ON_DEMAND_HANDLER.remove(self, category="plant_growth")
        self.delete()

    def at_pre_delete(self):
        """
        Körs precis innan objektet tas bort från databasen.
        Se till att frön sprids även vid oväntad borttagning.
        """
        self.scatter_seeds()
        super().at_pre_delete()

    def get_appearance(self):
        """
        Hämta växtens aktuella beskrivning.
        """
        try:
            current_stage = ON_DEMAND_HANDLER.get_stage(self, category="plant_growth")
            self.update_stage(current_stage)
        except Exception as e:
            current_stage = self.db.stage
            
        stage_desc = {
            "seed": "Ett litet frö som precis planterats.",
            "sprout": "En späd grodd som just tittat upp ur jorden.",
            "young": "En ung och livskraftig planta.",
            "mature": "En stark och fullvuxen växt.",
            "flowering": f"En vacker blomstrande växt med {self.db.fruits} knoppar.",
            "harvestable": f"En mogen växt redo att skördas med {self.db.fruits} frukter.",
            "withering": "En vissnande växt som har sett bättre dagar."
        }
        
        return stage_desc.get(current_stage, "En vanlig växt.")

    def return_appearance(self, looker, **kwargs):
        """
        Detta anropas när någon tittar på växten.
        """
        appearance = super().return_appearance(looker, **kwargs)
        desc = self.get_appearance()
        return f"{appearance}\n{desc}"


class Seed(Object):
    """A seed that can be planted to grow into a plant."""

    def at_object_creation(self):
        """Set up the basic seed properties."""
        super().at_object_creation()
        self.db.plant_type = None  # Type of plant this will grow into

    def return_appearance(self, looker, **kwargs):
        """Show what type of plant this seed will grow."""
        appearance = super().return_appearance(looker, **kwargs)
        if self.db.plant_type:
            return f"{appearance}\nThis seed will grow into a {self.db.plant_type}."
        return appearance
