"""Module identifiers and trait-deck configuration."""

from dataclasses import dataclass, field

from nature_solo_bot.game.model.nature_symbols import BAMBOO_GROVE_SYMBOL_BY_TRAIT_AND_FOOD
from nature_solo_bot.game.model.solo_cards import BAMBOO_GROVE_SOLO_CARDS
from nature_solo_bot.game.model.solo_species import SoloSpecies

from .symbol import SymbolName
from .trait import Trait
from .trait_cards import BAMBOO_GROVE_TRAITS, LONG_DIGESTION, TERRITORIAL

BAMBOO_GROVE = "bamboo_grove"
BAMBOO_GROVE_FOOD_VALUES = [1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4]

@dataclass(frozen=True)
class ModuleDefinition:
    """Trait-card configuration for one game module."""

    traits: tuple[Trait, ...]
    promo_traits: tuple[Trait, ...] = ()
    solo_symbols: dict[tuple[Trait, int], SymbolName] = field(default_factory=dict)
    default_solo_symbol: SymbolName = SymbolName.SEEDLING
    food_values: list[int] = field(default_factory=list)
    solo_deck: tuple["SoloSpecies", ...] = ()

    def traits_for_deck(self, promo: bool) -> tuple[Trait, ...]:
        """Return the traits included in this module's deck."""
        return self.traits + self.promo_traits if promo else self.traits

    def solo_symbol_for(self, card_trait: Trait, food_value: int) -> SymbolName:
        """Return the configured solo symbol, or the placeholder when not mapped."""
        return self.solo_symbols.get(
            (card_trait, food_value),
            self.default_solo_symbol,
        )

MODULE_DEFINITIONS: dict[str, ModuleDefinition] = {
    BAMBOO_GROVE: ModuleDefinition(
        traits=tuple(BAMBOO_GROVE_TRAITS),
        promo_traits=(LONG_DIGESTION, TERRITORIAL),
        solo_deck=BAMBOO_GROVE_SOLO_CARDS,
        food_values=BAMBOO_GROVE_FOOD_VALUES,
        solo_symbols=BAMBOO_GROVE_SYMBOL_BY_TRAIT_AND_FOOD,
    ),
}
