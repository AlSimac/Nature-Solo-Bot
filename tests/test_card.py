import unittest

from src.nature_solo_bot.game.model.card import Card


class CardTest(unittest.TestCase):
    def test_init_nature_deck(self):
        deck = Card.init_nature_deck()

        self.assertEqual(len(deck), 88)
        self.assertTrue(all(card.trait is not None for card in deck))


if __name__ == "__main__":
    unittest.main()