from nature_solo_bot.const import BAMBOO, MEAT, PLANT

from .trait import Trait


class TraitCard:
    """Physical card carrying a trait on a species."""

    def __init__(self, trait: Trait, stored_food: dict[str, int] | None = None):
        self.trait = trait
        self.stored_food: dict[str, int] = stored_food.copy() if stored_food is not None else {}
        self.stored_food.setdefault(PLANT, 0)
        self.stored_food.setdefault(MEAT, 0)
        self.stored_food.setdefault(BAMBOO, 0)
