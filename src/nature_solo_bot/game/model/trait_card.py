from .trait import Trait


class TraitCard:
    """Physical card carrying a trait on a species."""

    def __init__(self, trait: Trait):
        self.trait = trait
