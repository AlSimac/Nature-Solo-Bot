from .trait_card import TraitCard
from .trait_cards import HUNTER


class HunterCard(TraitCard):
    """Physical Hunter trait card; it has no food value or Solo symbol."""

    def __init__(self):
        super().__init__(HUNTER)