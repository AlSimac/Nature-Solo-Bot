from enum import Enum

from .trait_card import TraitCard
from .solo_species import SoloSpecies
from .trait import Trait
from .trait_cards import HUNTER

class TreeColor(Enum):
    PINK = 0
    BLUE = 1

class Species:
    """Represents a species in the game."""

    def __init__(self, solo_card: SoloSpecies, round_created: int):
        """Initialize a species with a name and traits."""
        self.solo_species = solo_card
        self.trait_cards: list[TraitCard] = []
        self.round_created: int = round_created
        self.population: int = 1
        self.size: int = 1
        self.is_hunter: bool = False
        self.food: int = 0
        self.tree_color = TreeColor.PINK

    @property
    def traits(self) -> list[Trait]:
        """Return the trait definitions carried by this species' cards."""
        return [card.trait for card in self.trait_cards]

    def add_trait_card(self, card: TraitCard, *, max_traits: int) -> bool:
        if len(self.trait_cards) >= max_traits:
            return False

        self.trait_cards.append(card)
        self._refresh_hunter_status()
        return True

    def remove_trait_card(self, card: TraitCard) -> bool:
        if card not in self.trait_cards:
            return False

        self.trait_cards.remove(card)
        self._refresh_hunter_status()
        return True

    def replace_trait_card(
        self,
        old_card: TraitCard,
        new_card: TraitCard,
        *,
        max_traits: int,
    ) -> bool:
        if old_card not in self.trait_cards or len(self.trait_cards) > max_traits:
            return False

        card_index = self.trait_cards.index(old_card)
        self.trait_cards[card_index] = new_card
        self._refresh_hunter_status()
        return True

    def _refresh_hunter_status(self) -> None:
        self.is_hunter = any(
            card.trait.effect_id == HUNTER.effect_id
            for card in self.trait_cards
        )