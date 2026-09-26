"""Card model stub."""


from .solo_cards import NATURE_SOLO_CARDS
from .solo_species import SoloSpecies
from .trait_cards import AVID_FORAGER, NATURE_TRAITS
from . import trait
from enum import Enum

class Card:
    """Represents a card in the game."""
    NATURE_FOOD_VALUES = [1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4]

    def __init__(self, name: str, food_value: int, trait: trait.Trait):
        """Initialize a card with a name, food value, and trait."""
        self.name: str = name
        self.food_value = food_value
        self.trait = trait

    @staticmethod
    def init_nature_deck(promo: bool = False) -> list["Card"]:
        """Initialize a deck of cards for the game."""
        cards_in_deck = []

        for nature_trait in NATURE_TRAITS:
            cards_in_deck.extend(
                Card(
                    name=nature_trait.name,
                    food_value=food_value,
                    trait=nature_trait,
                )
                for food_value in Card.NATURE_FOOD_VALUES
            )

        if promo:
            promo_trait = AVID_FORAGER
            cards_in_deck.extend(
                Card(
                    name=promo_trait.name,
                    food_value=food_value,
                    trait=promo_trait,
                )
                for food_value in Card.NATURE_FOOD_VALUES
            )

        return cards_in_deck

    @staticmethod
    def init_solo_deck() -> list["SoloSpecies"]:
        """Initialize a deck of solo cards for the game."""
        cards_in_deck = []

        for solo_card in NATURE_SOLO_CARDS:
            cards_in_deck.extend(
                SoloSpecies() for _ in range(len(NATURE_SOLO_CARDS))
            )

        return cards_in_deck
