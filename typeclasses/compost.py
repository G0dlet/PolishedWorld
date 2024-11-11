from evennia import DefaultObject

class Compost(DefaultObject):
    """
    Ett kompostobjekt som skapas när en växt dör.
    """
    def at_object_creation(self):
        """Sätt grundläggande attribut för komposten."""
        super().at_object_creation()
        
        self.db.nutrients = 10
        self.db.source_plant = ""  # Namnet på växten som blev kompost
        self.db.decay_level = 0    # 0-100
        
    def return_appearance(self, looker, **kwargs):
        """Anpassad beskrivning av komposten."""
        appearance = super().return_appearance(looker, **kwargs)
        
        if self.db.decay_level < 50:
            state = "färsk"
        elif self.db.decay_level < 100:
            state = "delvis förmultnad"
        else:
            state = "helt förmultnad"
            
        desc = f"\nEn {state} komposthög från en {self.db.source_plant}."
        desc += f"\nDen innehåller {self.db.nutrients} näringspoäng."
        
        return appearance + desc
