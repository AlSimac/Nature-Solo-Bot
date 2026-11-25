import random
import unittest

from src.nature_solo_bot.const import BAMBOO
from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.hunter_card import HunterCard
from src.nature_solo_bot.game.model.modules import BAMBOO_GROVE
from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.model.solo_cards import (
    CHI_CHI,
    CHOMPS,
    FENG,
    TRIM,
)
from src.nature_solo_bot.game.model.solo_species import SoloSpecies
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.state import GameState
from src.nature_solo_bot.game.model.trait import Trait
from src.nature_solo_bot.game.model.trait_card import TraitCard
from src.nature_solo_bot.game.model.trait_cards import (
    ARBOREAL,
    FOLIVORE,
    MONOPHAGOUS,
    OPPORTUNISTIC,
    ROOT_EATING,
    SOCIAL,
    STALKING,
)
from src.nature_solo_bot.game.rules.preparation import PreparationRules


class SpeciesCardLifecycleTest(unittest.TestCase):
    def test_trait_card_returns_to_hand_when_species_goes_extinct(self):
        player = Player(name="Rani")
        species = Species(solo_card=SoloSpecies(), round_created=1)
        card = Card.init_trait_decks()[0]
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

    def test_extinct_species_discards_food_stored_on_trait_card(self):
        player = Player(name="Rani")
        species = Species(solo_card=SoloSpecies(), round_created=1)
        card = next(
            card
            for card in Card.init_trait_decks(promo=True, module=BAMBOO_GROVE)
            if card.trait.name == "Long Digestion"
        )
        card.stored_food[BAMBOO] = 3
        species.add_trait_card(card, max_traits=3)
        player.species.append(species)

        self.assertTrue(player.return_extinct_species(species))

        self.assertEqual(card.stored_food[BAMBOO], 0)
        self.assertIs(player.hand[-1], card)

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
        card = Card.init_trait_decks()[0]
        hunter_card = HunterCard()
        state = GameState()
        player.species.append(species)
        player.hand.append(card)
        player.play_trait_card(card, species, max_traits=3)

        replaced = player.replace_trait_card(
            species,
            card,
            hunter_card,
            state,
            max_traits=3,
        )

        self.assertTrue(replaced)
        self.assertNotIn(card, player.hand)
        self.assertIs(species.trait_cards[0], hunter_card)
        self.assertIs(state.nature_discard[0], card)
        self.assertTrue(species.is_hunter)

    def test_replaced_module_trait_card_goes_to_its_module_discard(self):
        player = Player(name="Rani")
        species = Species(solo_card=SoloSpecies(), round_created=1)
        card = Card.init_trait_decks(module=BAMBOO_GROVE)[0]
        state = GameState(modules=[BAMBOO_GROVE])
        player.species.append(species)
        player.hand.append(card)
        player.play_trait_card(card, species, max_traits=3)

        replaced = player.replace_trait_card(
            species,
            card,
            HunterCard(),
            state,
            max_traits=3,
        )

        self.assertTrue(replaced)
        self.assertEqual(state.nature_discard, [])
        self.assertEqual(state.module_decks[BAMBOO_GROVE].discard, [card])

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

    def test_removing_hunter_trait_turns_species_back_into_forager(self):
        species = Species(solo_card=SoloSpecies(), round_created=1)
        hunter_card = HunterCard()
        species.add_trait_card(hunter_card, max_traits=3)
        self.assertTrue(species.is_hunter)

        self.assertTrue(species.remove_trait_card(hunter_card))

        self.assertFalse(species.is_hunter)

    def test_replacing_hunter_trait_with_another_trait_turns_species_into_forager(self):
        species = Species(solo_card=SoloSpecies(), round_created=1)
        hunter_card = HunterCard()
        other_card = Card.init_trait_decks()[0]
        species.add_trait_card(hunter_card, max_traits=3)
        self.assertTrue(species.is_hunter)

        self.assertTrue(
            species.replace_trait_card(
                hunter_card,
                other_card,
                max_traits=3,
            )
        )

        self.assertFalse(species.is_hunter)

    def test_trait_without_effect_id_does_not_make_species_a_hunter(self):
        species = Species(solo_card=SoloSpecies(), round_created=1)

        self.assertTrue(species.add_trait_card(TraitCard(Trait(name="Unidentified")), max_traits=3))

        self.assertFalse(species.is_hunter)

    def test_hunter_effect_does_not_replace_traits_when_species_is_full(self):
        player = Player(name="Rani")
        species = Species(solo_card=SoloSpecies(), round_created=1)
        player.species.append(species)
        cards = Card.init_trait_decks()[:3]

        for card in cards:
            player.hand.append(card)
            self.assertTrue(player.play_trait_card(card, species, max_traits=3))

        nature_discard = []
        added = PreparationRules.add_hunter_card(
            species,
            player,
            max_traits=3,
            state=GameState(),
            rng=random.Random(42),
        )

        self.assertFalse(added)
        self.assertEqual(nature_discard, [])
        self.assertEqual(species.trait_cards, cards)
        self.assertEqual(len(species.trait_cards), 3)
        self.assertFalse(species.is_hunter)

    def test_chi_chi_draws_trait_from_its_deck_and_discards_other_draws(self):
        state = GameState(modules=[BAMBOO_GROVE])
        player = Player(name="Rani")
        species = Species(solo_card=CHI_CHI, round_created=1)
        bamboo_cards = Card.init_trait_decks(module=BAMBOO_GROVE)
        monophagous_cards = [
            card for card in bamboo_cards if card.trait is MONOPHAGOUS
        ]
        trait_card = monophagous_cards[0]
        unrelated_card = next(
            card for card in bamboo_cards if card.trait is not MONOPHAGOUS
        )
        card_in_wrong_deck = monophagous_cards[1]
        state.module_decks[BAMBOO_GROVE].deck[:] = [trait_card, unrelated_card]
        state.nature_deck[:] = [card_in_wrong_deck]

        PreparationRules.solo_species_effect_when_played(
            species,
            player,
            max_traits=state.max_traits,
            trait_discard=state.nature_discard,
            rng=random.Random(42),
            state=state,
        )

        self.assertEqual(species.trait_cards, [trait_card])
        self.assertEqual(state.module_decks[BAMBOO_GROVE].discard, [unrelated_card])
        self.assertEqual(state.nature_deck, [card_in_wrong_deck])
        self.assertEqual(species.size, 3)

    def test_bamboo_grove_solo_cards_attach_their_declared_traits(self):
        cases = (
            (CHOMPS, {ROOT_EATING, SOCIAL}),
            (FENG, {OPPORTUNISTIC, FOLIVORE}),
            (TRIM, {STALKING, ARBOREAL}),
        )

        for solo_card, expected_traits in cases:
            with self.subTest(solo_card=solo_card.name):
                state = GameState(modules=[BAMBOO_GROVE])
                player = Player(name="Rani")
                species = Species(solo_card=solo_card, round_created=1)

                bamboo_cards = Card.init_trait_decks(module=BAMBOO_GROVE)
                nature_cards = Card.init_trait_decks()
                state.module_decks[BAMBOO_GROVE].deck[:] = bamboo_cards
                state.nature_deck[:] = nature_cards

                PreparationRules.solo_species_effect_when_played(
                    species,
                    player,
                    max_traits=state.max_traits,
                    trait_discard=state.nature_discard,
                    rng=random.Random(42),
                    state=state,
                )

                actual_traits = set(species.traits)
                self.assertEqual(actual_traits, expected_traits)

    def test_add_trait_when_played_searches_matching_module_discard_after_deck(self):
        state = GameState(modules=[BAMBOO_GROVE])
        species = Species(
            solo_card=SoloSpecies(add_trait=[MONOPHAGOUS]),
            round_created=1,
        )
        bamboo_cards = Card.init_trait_decks(module=BAMBOO_GROVE)
        trait_card = next(
            card for card in bamboo_cards if card.trait is MONOPHAGOUS
        )
        unrelated_card = next(
            card for card in bamboo_cards if card.trait is not MONOPHAGOUS
        )
        card_in_wrong_discard = next(
            card
            for card in bamboo_cards
            if card.trait is MONOPHAGOUS and card is not trait_card
        )
        state.module_decks[BAMBOO_GROVE].deck[:] = [unrelated_card]
        state.module_decks[BAMBOO_GROVE].discard[:] = [trait_card]
        state.nature_discard[:] = [card_in_wrong_discard]

        PreparationRules.add_trait_when_played(state, species)

        self.assertEqual(species.trait_cards, [trait_card])
        self.assertEqual(state.module_decks[BAMBOO_GROVE].discard, [unrelated_card])
        self.assertEqual(state.nature_discard, [card_in_wrong_discard])

    def test_add_trait_when_played_skips_trait_missing_from_expected_piles(self):
        state = GameState(modules=[BAMBOO_GROVE])
        species = Species(
            solo_card=SoloSpecies(add_trait=[MONOPHAGOUS]),
            round_created=1,
        )
        bamboo_cards = Card.init_trait_decks(module=BAMBOO_GROVE)
        card_in_wrong_deck = next(
            card for card in bamboo_cards if card.trait is MONOPHAGOUS
        )
        card_in_wrong_discard = next(
            card
            for card in bamboo_cards
            if card.trait is MONOPHAGOUS and card is not card_in_wrong_deck
        )
        state.nature_deck[:] = [card_in_wrong_deck]
        state.nature_discard[:] = [card_in_wrong_discard]

        PreparationRules.add_trait_when_played(state, species)

        self.assertEqual(species.trait_cards, [])
        self.assertEqual(state.nature_deck, [card_in_wrong_deck])
        self.assertEqual(state.nature_discard, [card_in_wrong_discard])


if __name__ == "__main__":
    unittest.main()
