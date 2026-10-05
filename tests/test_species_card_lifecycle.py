import random
import unittest

from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.hunter_card import HunterCard
from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.model.solo_species import SoloSpecies
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.state import GameState
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

        removed = player.return_extinct_species(species)

        self.assertTrue(removed)
        self.assertNotIn(species, player.species)
        self.assertIs(player.hand[-1], card)
        self.assertEqual(card.food_value, original_food_value)
        self.assertIs(card.solo_symbol, original_solo_symbol)

    def test_solo_card_goes_to_players_solo_discard_when_species_goes_extinct(self):
        player = Player(name="Rani")
        solo_card = SoloSpecies(name="Extinct species")
        species = Species(solo_card=solo_card, round_created=1)
        player.species.append(species)
        original_deck = list(player.solo_deck)

        removed = player.return_extinct_species(species)

        self.assertTrue(removed)
        self.assertEqual(player.solo_discard, [solo_card])
        self.assertEqual(player.solo_deck, original_deck)

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
            max_traits=3,
        )

        self.assertTrue(replaced)
        self.assertNotIn(card, player.hand)
        self.assertIs(species.trait_cards[0], hunter_card)
        self.assertIs(nature_discard[0], card)
        self.assertTrue(species.is_hunter)

    def test_extinction_removes_hunter_card_without_a_return_pile(self):
        player = Player(name="Rani")
        species = Species(solo_card=SoloSpecies(), round_created=1)
        hunter_card = HunterCard()
        species.add_trait_card(hunter_card, max_traits=3)
        player.species.append(species)

        removed = player.return_extinct_species(species)

        self.assertTrue(removed)
        self.assertEqual(species.trait_cards, [])
        self.assertFalse(species.is_hunter)
        self.assertEqual(player.hand, [])

    def test_hunter_effect_does_not_replace_traits_when_species_is_full(self):
        player = Player(name="Rani")
        species = Species(solo_card=SoloSpecies(), round_created=1)
        player.species.append(species)
        cards = Card.init_nature_deck()[:3]

        for card in cards:
            player.hand.append(card)
            self.assertTrue(player.play_trait_card(card, species, max_traits=3))

        nature_discard = []
        added = PreparationRules.add_hunter_card(
            species,
            player,
            max_traits=3,
            nature_discard=nature_discard,
            rng=random.Random(42),
            state=GameState(),
        )

        self.assertFalse(added)
        self.assertEqual(nature_discard, [])
        self.assertEqual(species.trait_cards, cards)
        self.assertEqual(len(species.trait_cards), 3)
        self.assertFalse(species.is_hunter)


if __name__ == "__main__":
    unittest.main()
