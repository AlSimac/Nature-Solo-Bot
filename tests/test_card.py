import unittest

from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.symbol import SymbolName
from src.nature_solo_bot.game.model.trait_cards import AVID_FORAGER, CLAWED


class CardTest(unittest.TestCase):
    def test_init_nature_deck(self):
        deck = Card.init_nature_deck()

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
        deck = Card.init_nature_deck(promo=True)

        avid_forager_cards = [card for card in deck if card.trait is AVID_FORAGER]
        self.assertEqual(len(avid_forager_cards), len(Card.NATURE_FOOD_VALUES))
        self.assertTrue(
            all(card.solo_symbol is SymbolName.SEEDLING for card in avid_forager_cards)
        )


if __name__ == "__main__":
    unittest.main()
