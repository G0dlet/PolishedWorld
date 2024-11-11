from evennia import DefaultObject, ON_DEMAND_HANDLER, create_object, utils
from typeclasses.compost import Compost
from random import randint

class Plant(DefaultObject):
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
        
        # Snabba tider för testning (i sekunder)
        self.growth_stages = {
            0: "seed",
            30: "sprout",
            60: "young",
            90: "mature",
            120: "flowering",
            150: "harvestable",
            180: "withering",
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
            death_time = 210  # Tiden till död i sekunder
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
            case "sprout":
                self.db.size = 2
            case "young":
                self.db.size = 3
            case "mature":
                self.db.size = 4
            case "flowering":
                self.db.size = 4
                if self.db.fruits == 0:
                    self.db.fruits = randint(1, 3)
            case "harvestable":
                pass
            case "withering":
                self.db.health = 50
            # Ta bort "dead" fallet eftersom det hanteras av den schemalagda transformationen

    def transform_to_compost(self):
        """
        Förvandla växten till kompost.
        """
        # Kontrollera att växten fortfarande existerar
        if not self.pk or not self.location:
            return
            
        # Skapa kompostobjekt
        compost = create_object(
            Compost,
            key=f"kompost",
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
