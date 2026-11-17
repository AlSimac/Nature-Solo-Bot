from nature_solo_bot.const import BAMBOO, MEAT, PLANT

from .trait import Trait


class TraitCard:
    """Physical card carrying a trait on a species."""

    def __init__(self, trait: Trait, stored_food: int = 0):
        self.trait = trait
        self.stored_food: dict[str, int] = {
            PLANT: 0,
            MEAT: 0,
            BAMBOO: 0,
        }
