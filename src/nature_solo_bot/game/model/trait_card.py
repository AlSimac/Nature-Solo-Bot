from .trait import Trait


class TraitCard:
    """Physical card carrying a trait on a species."""

    def __init__(self, trait: Trait, stored_food: int = 0):
        self.trait = trait
        self.stored_food = stored_food
