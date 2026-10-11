"""Card model stub."""

from copy import deepcopy

from . import trait
from .nature_symbols import SYMBOL_BY_TRAIT_AND_FOOD
from .solo_cards import NATURE_SOLO_CARDS
from .solo_species import SoloSpecies
from .symbol import SymbolName
from .trait_card import TraitCard
from .trait_cards import AVID_FORAGER, NATURE_TRAITS


class Card(TraitCard):
    """Represents a card in the game."""

    NATURE_FOOD_VALUES = [1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4]

    def __init__(
        self,
        name: str,
        food_value: int,
        trait: trait.Trait,
        solo_symbol: SymbolName,
        deck: str,
    ):
        """Initialize a card with a name, food value, and trait."""
        super().__init__(trait)
        self.name: str = name
        self.food_value = food_value
        self.solo_symbol = solo_symbol
        self.deck = deck

    @staticmethod
    def init_nature_deck(promo: bool = False) -> list["Card"]:
        """Initialize a deck of cards for the game."""
        cards_in_deck = []

        nature_traits = [*NATURE_TRAITS]
        if promo:
            nature_traits.append(AVID_FORAGER)

        for nature_trait in nature_traits:
            cards_in_deck.extend(
                Card(
                    name=nature_trait.name,
                    food_value=food_value,
                    trait=nature_trait,
                    solo_symbol=SYMBOL_BY_TRAIT_AND_FOOD[(nature_trait, food_value)],
                    deck="Nature",
                )
                for food_value in Card.NATURE_FOOD_VALUES
            )

        return cards_in_deck

    @staticmethod
    def init_solo_deck() -> list["SoloSpecies"]:
        """Initialize a deck of solo cards for the game."""
        return [deepcopy(solo_card) for solo_card in NATURE_SOLO_CARDS]
