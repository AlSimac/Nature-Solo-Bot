from .solo_species import SoloSpecies
from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.trait import Trait


class Species:
    """Represents a species in the game."""

    def __init__(self, solo_card: SoloSpecies, traits: list[Trait], round_created: int):
        """Initialize a species with a name and traits."""
        self.solo_species = solo_card
        self.traits: list[Trait] = traits
        self.round_created: int = round_created
        self.population: int = 1
        self.size: int = 1
        self.food: int = 0