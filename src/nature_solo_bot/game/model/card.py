"""Card model stub."""


from src.nature_solo_bot.game.model import trait
from enum import Enum

class Card:
    """Represents a card in the game."""
    NATURE_FOOD_VALUES = [1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4]

    def __init__(self, name: str, food_value: int, trait: trait.Trait):
        """Initialize a card with a name, food value, and trait."""
        self.name: str = name
        self.food_value = food_value
        self.trait = trait

    @staticmethod
    def init_deck(promo: bool = False) -> list["Card"]:
        """Initialize a deck of cards for the game."""
        cards_in_deck = []

        for nature_trait in trait.NatureTrait:
            cards_in_deck.extend(
                Card(
                    name=nature_trait.value.name,
                    food_value=food_value,
                    trait=nature_trait.value,
                )
                for food_value in Card.NATURE_FOOD_VALUES
            )

        if promo:
            promo_trait = trait.Trait(name="Avid Forager", effect_id="avid_forager")
            cards_in_deck.extend(
                Card(
                    name=promo_trait.name,
                    food_value=food_value,
                    trait=promo_trait,
                )
                for food_value in Card.NATURE_FOOD_VALUES
            )

        return cards_in_deck
