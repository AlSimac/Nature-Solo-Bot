"""Card model stub."""

from copy import deepcopy

from nature_solo_bot.game.model.state import GameState

from . import trait
from .modules import MODULE_DEFINITIONS
from .nature_symbols import NATURE_SYMBOL_BY_TRAIT_AND_FOOD
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
    def init_trait_decks(promo: bool = False, module: str | None = None) -> list["Card"]:
        """Initialize a deck of cards for the game."""
        cards_in_deck = []

        # Core Nature trait deck
        if module is None:
            deck_name = "Nature"
            traits = [*NATURE_TRAITS]
            food_values = Card.NATURE_FOOD_VALUES

            if promo:
                traits.append(AVID_FORAGER)

            module_definition = None

        else:
            module_definition = MODULE_DEFINITIONS.get(module)

            if module_definition is None:
                raise ValueError(f"Unsupported game module: {module}")

            deck_name = module
            traits = list(module_definition.traits_for_deck(promo))
            food_values = module_definition.food_values

        for module_trait in traits:
            for food_value in food_values:
                if module_definition is None:
                    solo_symbol = NATURE_SYMBOL_BY_TRAIT_AND_FOOD[(module_trait, food_value)]
                else:
                    solo_symbol = module_definition.solo_symbol_for(module_trait, food_value)

                cards_in_deck.append(
                    Card(
                        name=module_trait.name,
                        food_value=food_value,
                        trait=module_trait,
                        solo_symbol=solo_symbol,
                        deck=deck_name,
                    )
                )

        return cards_in_deck

    @staticmethod
    def init_solo_deck(state: GameState | None = None) -> list["SoloSpecies"]:
        """Initialize a deck of solo cards for the game."""
        solo_deck = [deepcopy(solo_card) for solo_card in NATURE_SOLO_CARDS]

        if state is None:
            return solo_deck

        for module in state.modules:
            module_definition = MODULE_DEFINITIONS.get(module)

            if module_definition is None:
                raise ValueError(f"Unsupported game module: {module}")

            solo_deck.extend(deepcopy(module_definition.solo_deck))

        return solo_deck
