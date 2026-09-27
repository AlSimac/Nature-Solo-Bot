import random
import unittest

from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.hunter_card import HunterCard
from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.model.solo_species import SoloSpecies
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.trait_cards import HUNTER
from src.nature_solo_bot.game.rules.preparation import PreparationRules


class SpeciesCardLifecycleTest(unittest.TestCase):
    def test_trait_card_returns_to_hand_when_species_goes_extinct(self):
        player = Player(name="Rani")
        species = Species(solo_card=SoloSpecies(), round_created=1)
        card = Card.init_nature_deck()[0]
        player.species.append(species)
        player.hand.append(card)
        original_food_value = card.food_value
        original_solo_symbol = card.solo_symbol

        added = player.play_trait_card(card, species, max_traits=3)

        self.assertTrue(added)
        self.assertNotIn(card, player.hand)
        self.assertIs(species.trait_cards[0], card)

        hunter_deck = []
        removed = player.return_extinct_species(species, hunter_deck)

        self.assertTrue(removed)
        self.assertNotIn(species, player.species)
        self.assertIs(player.hand[-1], card)
        self.assertEqual(card.food_value, original_food_value)
        self.assertIs(card.solo_symbol, original_solo_symbol)

    def test_replaced_trait_card_goes_to_nature_discard(self):
        player = Player(name="Rani")
        species = Species(solo_card=SoloSpecies(), round_created=1)
        card = Card.init_nature_deck()[0]
        hunter_card = HunterCard()
        nature_discard = []
        hunter_deck = []
        player.species.append(species)
        player.hand.append(card)
        player.play_trait_card(card, species, max_traits=3)

        replaced = player.replace_trait_card(
            species,
            card,
            hunter_card,
            nature_discard,
            hunter_deck,
            max_traits=3,
        )

        self.assertTrue(replaced)
        self.assertNotIn(card, player.hand)
        self.assertIs(species.trait_cards[0], hunter_card)
        self.assertIs(nature_discard[0], card)
        self.assertTrue(species.is_hunter)

    def test_extinction_returns_hunter_card_to_hunter_stack(self):
        player = Player(name="Rani")
        species = Species(solo_card=SoloSpecies(), round_created=1)
        hunter_card = HunterCard()
        species.add_trait_card(hunter_card, max_traits=3)
        player.species.append(species)
        hunter_deck = []

        removed = player.return_extinct_species(species, hunter_deck)

        self.assertTrue(removed)
        self.assertIs(hunter_deck[-1], hunter_card)
        self.assertEqual(player.hand, [])

    def test_effect_replaces_a_seeded_random_trait_card(self):
        player = Player(name="Rani")
        species = Species(solo_card=SoloSpecies(), round_created=1)
        player.species.append(species)
        cards = Card.init_nature_deck()[:3]
        for card in cards:
            player.hand.append(card)
            self.assertTrue(player.play_trait_card(card, species, max_traits=3))

        expected_replacement = random.Random(42).choice(cards)
        nature_discard = []
        hunter_deck = []

        replaced = PreparationRules.add_hunter_card(
            species,
            player,
            max_traits=3,
            nature_discard=nature_discard,
            hunter_deck=hunter_deck,
            rng=random.Random(42),
        )

        self.assertTrue(replaced)
        self.assertIs(nature_discard[0], expected_replacement)
        self.assertEqual(len(species.trait_cards), 3)
        self.assertTrue(species.is_hunter)


if __name__ == "__main__":
    unittest.main()
