from enum import Enum

from .trait_card import TraitCard
from .solo_species import SoloSpecies
from .trait import Trait
from .trait_cards import HUNTER

class TreeColor(Enum):
    PINK = 0
    BLUE = 1
    PINK_LAST_ROUND = 2
    BLUE_LAST_ROUND = 3

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
        self.plant_food: int = 0
        self.meat_food: int = 0
        self.tree_color = TreeColor.PINK
        self.solo_symbols = solo_card.pink_symbols
        self.lost_population: int = 0

    @property
    def attack_value(self) -> int:
        return self.size

    @property
    def defense_value(self) -> int:
        return self.size

    @property
    def forage_value(self) -> int:
        return self.size

    @property
    def total_food(self) -> int:
        return self.plant_food + self.meat_food

    @property
    def is_hungry(self) -> bool:
        return self.total_food < self.population

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

    def switch_tree_color(self):
        """Switch the tree color of the species."""
        if self.tree_color == TreeColor.PINK:
            self.tree_color = TreeColor.BLUE
            self.solo_symbols = self.solo_species.blue_symbols

        elif self.tree_color == TreeColor.BLUE:
            self.tree_color = TreeColor.PINK
            self.solo_symbols = self.solo_species.pink_symbols

        elif self.tree_color == TreeColor.PINK_LAST_ROUND:
            self.tree_color = TreeColor.BLUE_LAST_ROUND
            self.solo_symbols = self.solo_species.blue_symbols

        elif self.tree_color == TreeColor.BLUE_LAST_ROUND:
            self.tree_color = TreeColor.PINK_LAST_ROUND
            self.solo_symbols = self.solo_species.pink_symbols
