import unittest
from collections import Counter
from unittest.mock import patch

from nature_solo_bot.game.model.card import Card
from nature_solo_bot.game.model.modules import (
    BAMBOO_GROVE,
    MODULE_DEFINITIONS,
    ModuleDefinition,
)
from nature_solo_bot.game.model.solo_cards import NATURE_SOLO_CARDS
from nature_solo_bot.game.model.symbol import SymbolName
from nature_solo_bot.game.model.trait_cards import (
    ARBOREAL,
    AVID_FORAGER,
    BAMBOO_GROVE_TRAITS,
    CLAWED,
    FOLIVORE,
    LONG_DIGESTION,
    MONOPHAGOUS,
    NATURE_TRAITS,
    ROOT_EATING,
    STALKING,
    TERRITORIAL,
)


class CardTest(unittest.TestCase):
    def test_init_solo_deck_copies_species_with_their_symbols(self):
        deck = Card.init_solo_deck()

        self.assertEqual(
            Counter(card.name for card in deck),
            Counter({card.name: 1 for card in NATURE_SOLO_CARDS}),
        )
        self.assertEqual(len(deck), 6)
        self.assertTrue(
            all(
                card.pink_symbols
                and card.blue_symbols
                and card.pink_symbols_last_round
                and card.blue_symbols_last_round
                for card in deck
            )
        )
        self.assertIsNot(deck[0], deck[1])
        self.assertIsNot(deck[0].pink_symbols, deck[1].pink_symbols)

    def test_init_nature_deck(self):
        deck = Card.init_trait_decks()

        self.assertEqual(len(deck), 88)
        self.assertTrue(all(card.trait is not None for card in deck))
        clawed_food_one = next(
            card for card in deck if card.trait is CLAWED and card.food_value == 1
        )
        clawed_food_two = next(
            card for card in deck if card.trait is CLAWED and card.food_value == 2
        )
        self.assertIs(clawed_food_one.solo_symbol, SymbolName.SEEDLING)
        self.assertIs(clawed_food_two.solo_symbol, SymbolName.GEAR)

    def test_promo_deck_assigns_avid_forager_symbols(self):
        deck = Card.init_trait_decks(promo=True)

        avid_forager_cards = [card for card in deck if card.trait is AVID_FORAGER]
        self.assertEqual(len(avid_forager_cards), len(Card.NATURE_FOOD_VALUES))
        self.assertTrue(all(card.solo_symbol is SymbolName.SEEDLING for card in avid_forager_cards))

    def test_init_bamboo_grove_deck(self):
        deck = Card.init_trait_decks(module=BAMBOO_GROVE)

        self.assertEqual(len(deck), len(BAMBOO_GROVE_TRAITS) * 8)
        self.assertEqual({card.trait for card in deck}, set(BAMBOO_GROVE_TRAITS))
        self.assertTrue(all(card.deck == BAMBOO_GROVE for card in deck))
        arboreal_cards = [card for card in deck if card.trait.name == "Arboreal"]
        self.assertEqual(
            Counter(card.solo_symbol for card in arboreal_cards),
            Counter(
                {
                    SymbolName.GEAR: 4,
                    SymbolName.CAT: 4,
                }
            ),
        )
        arboreal_food_three = [
            card for card in arboreal_cards if card.food_value == 3
        ]
        self.assertEqual(
            Counter(card.solo_symbol for card in arboreal_food_three),
            Counter(
                {
                    SymbolName.GEAR: 1,
                    SymbolName.CAT: 2,
                }
            ),
        )

    def test_init_bamboo_grove_deck_includes_module_promo_traits(self):
        deck = Card.init_trait_decks(promo=True, module=BAMBOO_GROVE)

        self.assertIn(LONG_DIGESTION, {card.trait for card in deck})
        self.assertIn(TERRITORIAL, {card.trait for card in deck})

    def test_promo_bamboo_deck_assigns_solo_symbols(self):
        deck = Card.init_trait_decks(promo=True, module=BAMBOO_GROVE)

        expected = {
            (ARBOREAL, 2): Counter({SymbolName.GEAR: 3}),
            (ARBOREAL, 3): Counter(
                {
                    SymbolName.GEAR: 1,
                    SymbolName.CAT: 2,
                }
            ),
            (ARBOREAL, 4): Counter({SymbolName.CAT: 2}),
            (FOLIVORE, 2): Counter({SymbolName.LEAF: 3}),
            (FOLIVORE, 3): Counter({SymbolName.LEAF: 3}),
            (FOLIVORE, 4): Counter({SymbolName.ARMADILLO: 2}),
            (MONOPHAGOUS, 2): Counter({SymbolName.SEEDLING: 3}),
            (MONOPHAGOUS, 3): Counter({SymbolName.SEEDLING: 3}),
            (MONOPHAGOUS, 4): Counter({SymbolName.SEEDLING: 2}),
            (ROOT_EATING, 2): Counter({SymbolName.VULTURE: 3}),
            (ROOT_EATING, 3): Counter({SymbolName.VULTURE: 3}),
            (ROOT_EATING, 4): Counter({SymbolName.ARMADILLO: 2}),
            (STALKING, 2): Counter({SymbolName.CAT: 3}),
            (STALKING, 3): Counter({SymbolName.CAT: 3}),
            (STALKING, 4): Counter({SymbolName.CAT: 2}),
            (LONG_DIGESTION, 2): Counter({SymbolName.LEAF: 3}),
            (LONG_DIGESTION, 3): Counter({SymbolName.LEAF: 3}),
            (LONG_DIGESTION, 4): Counter({SymbolName.LEAF: 2}),
            (TERRITORIAL, 2): Counter({SymbolName.SEEDLING: 3}),
            (TERRITORIAL, 3): Counter({SymbolName.SEEDLING: 3}),
            (TERRITORIAL, 4): Counter({SymbolName.SEEDLING: 2}),
        }

        for (trait, food_value), symbols in expected.items():
            cards = [
                card
                for card in deck
                if card.trait is trait and card.food_value == food_value
            ]
            self.assertEqual(
                Counter(card.solo_symbol for card in cards),
                symbols,
            )

    def test_init_trait_decks_rejects_unsupported_module(self):
        with self.assertRaisesRegex(ValueError, "Unsupported game module"):
            Card.init_trait_decks(module="unknown")

    def test_init_trait_decks_uses_registered_module_definitions(self):
        test_module = "test_module"
        with patch.dict(
            MODULE_DEFINITIONS,
            {test_module: ModuleDefinition(traits=tuple(NATURE_TRAITS[:1]))},
        ):
            deck = Card.init_trait_decks(module=test_module)

        self.assertEqual(len(deck), len(Card.NATURE_FOOD_VALUES))
        self.assertTrue(all(card.trait is NATURE_TRAITS[0] for card in deck))
        self.assertTrue(all(card.deck == test_module for card in deck))
        self.assertTrue(all(card.solo_symbol is SymbolName.SEEDLING for card in deck))


if __name__ == "__main__":
    unittest.main()
