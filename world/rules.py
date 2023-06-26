from random import randint


class RollEngine:
    """
    This goups all dice rolls of PolishedWorld. These could all have been normal functions, but we
    are grouping them in a class to make them easier to partially override and replace later.

    """
    
    def roll(self, roll_string, max_number=10):
        """
        Args:
            roll_string (str): A roll using standard rpg syntax, <number>d<diesize>, like
                1d6, 2d10 etc. Max die-size is 1000.
            max_number (int): The max number of dice to roll. Defaults to 10, which is usally
                more than enough.

        Returns:
            int: The rolled result - sum of all dice rolled.

        Raises:
            TypeError: If roll_string is not on the right format otherwise doesn't validate.

        Notes:
            Since we may see user input to this function, we make sure to validate the inputs (we
            wouldn't bother much with that if it was just for developer use).

        """
        max_diesize = 1000
        roll_string = roll_string.lower()
        if "d" not in roll_string:
            raise TypeError(
                f"Dice roll '{roll_string} was not recognized. Must be `<number>d<dicesize>`."
            )
        number, diesize = roll_string.split("d", 1)
        try:
            number = int(number)
            diesize = int(diesize)
        except Exception:
            raise TypeError(f"The number and dice-size of '{roll_string}' must be numerical.")
        if 0 < number > max_number:
            raise TypeError(f"Invalid number of dice rolled (must be between 1 and {max_number})")
        if 0 < diesize > max_diesize:
            raise TypeError(f"Invalid die-size used (must be between 1 and max {max_diesize} sides)")

        # At this point we know we have valid input - roll and add dice together
        return sum(randint(1, diesize) for _ in range(number))
