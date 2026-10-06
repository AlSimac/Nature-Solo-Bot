import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.nature_solo_bot.game.model.hunter_card import HunterCard
from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.model.solo_species import SoloSpecies
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.state import GameState
from src.nature_solo_bot.game.model.trait_card import TraitCard
from src.nature_solo_bot.game.model.trait_cards import CLAWED, FAST, PLATED
from src.nature_solo_bot.game.rules.feeding import FeedingRules


class FeedingRulesTest(unittest.TestCase):
    def test_clawed_increases_forage_yield_by_two_per_trait(self):
        for clawed_count, expected_food in ((0, 2), (1, 4), (2, 6)):
            with self.subTest(clawed_count=clawed_count):
                forager = Species(solo_card=SoloSpecies(), round_created=1)
                forager.size = 2
                forager.population = 10
                for _ in range(clawed_count):
                    forager.add_trait_card(TraitCard(CLAWED), max_traits=3)

                self.assertEqual(
                    FeedingRules.plant_food_taken_in_one_forage(forager, 10),
                    expected_food,
                )

    def test_clawed_forage_is_limited_by_hunger_and_available_food(self):
        forager = Species(solo_card=SoloSpecies(), round_created=1)
        forager.size = 2
        forager.population = 5
        forager.plant_food = 3
        forager.add_trait_card(TraitCard(CLAWED), max_traits=3)

        self.assertEqual(
            FeedingRules.plant_food_taken_in_one_forage(forager, 10),
            2,
        )
        forager.plant_food = 0
        self.assertEqual(
            FeedingRules.plant_food_taken_in_one_forage(forager, 3),
            3,
        )

    def test_fast_only_prevents_hunting_species_with_more_fast_traits(self):
        for fast_prey_count, expected_validity in ((0, True), (1, True), (2, False)):
            with self.subTest(fast_prey_count=fast_prey_count):
                hunter = Species(solo_card=SoloSpecies(), round_created=1)
                prey = Species(solo_card=SoloSpecies(), round_created=1)
                hunter.add_trait_card(TraitCard(FAST), max_traits=3)
                for _ in range(fast_prey_count):
                    prey.add_trait_card(TraitCard(FAST), max_traits=3)

                self.assertEqual(
                    FeedingRules.is_valid_target(prey, hunter),
                    expected_validity,
                )

    def test_hunt_targets_use_trait_adjusted_attack_and_defense_values(self):
        hunter = Species(solo_card=SoloSpecies(), round_created=1)
        prey = Species(solo_card=SoloSpecies(), round_created=1)
        hunter.size = 2
        prey.size = 3
        hunter.add_trait_card(TraitCard(CLAWED), max_traits=3)
        prey.add_trait_card(TraitCard(PLATED), max_traits=3)
        state = GameState()
        state.players = [Player(name="Hunter owner"), Player(name="Prey owner")]
        state.players[0].species.append(hunter)
        state.players[1].species.append(prey)

        self.assertEqual(FeedingRules.find_valid_targets(state, hunter), [])

        prey.remove_trait_card(prey.trait_cards[0])
        self.assertEqual(FeedingRules.find_valid_targets(state, hunter), [prey])

    def test_hunting_own_prey_does_not_kill_hunter_population(self):
        player = Player(name="Hunter owner")
        prey = Species(solo_card=SoloSpecies(), round_created=1)
        hunter = Species(solo_card=SoloSpecies(), round_created=1)
        hunter.size = 2
        hunter.population = 2
        hunter.add_trait_card(HunterCard(), max_traits=3)
        player.species.extend([prey, hunter])
        state = GameState()
        state.players = [player]

        result = FeedingRules.hunt(state, player, hunter)

        self.assertTrue(result)
        self.assertNotIn(prey, player.species)
        self.assertEqual(hunter.population, 2)
        self.assertEqual(player.lost_population, 1)

    def test_hunt_attributes_prey_death_and_extinction_to_prey_owner(self):
        prey_owner = Player(name="Prey owner")
        hunter_owner = Player(name="Hunter owner")
        prey = Species(solo_card=SoloSpecies(), round_created=1)
        prey.population = 1
        hunter = Species(solo_card=SoloSpecies(), round_created=1)
        hunter.size = 2
        hunter.population = 1
        hunter.add_trait_card(HunterCard(), max_traits=3)
        prey_owner.species.append(prey)
        hunter_owner.species.append(hunter)
        state = GameState()
        state.players = [prey_owner, hunter_owner]

        result = FeedingRules.hunt(state, hunter_owner, hunter)

        self.assertTrue(result)
        self.assertNotIn(prey, prey_owner.species)
        self.assertEqual(prey_owner.lost_population, 1)
        self.assertEqual(prey_owner.extinct_size, prey.size)
        self.assertEqual(hunter_owner.lost_population, 0)

    def test_sort_preys_prioritizes_opponents_size_then_age(self):
        own_old_large = SimpleNamespace(size=3, round_created=1)
        own_new_small = SimpleNamespace(size=1, round_created=2)
        opponent_young_small = SimpleNamespace(size=1, round_created=3)
        opponent_old_large = SimpleNamespace(size=2, round_created=1)
        player = SimpleNamespace(species=[own_old_large, own_new_small])

        sorted_preys = FeedingRules.sort_preys(
            player,
            [
                (own_old_large, 1),
                (own_new_small, 1),
                (opponent_old_large, 0),
                (opponent_young_small, 0),
            ],
        )

        self.assertEqual(
            sorted_preys,
            [
                (opponent_young_small, 0),
                (opponent_old_large, 0),
                (own_new_small, 1),
                (own_old_large, 1),
            ],
        )

    def test_count_own_losses_keeps_loss_with_selected_prey(self):
        own_prey = object()
        opponent_prey = object()
        player = SimpleNamespace(species=[own_prey])

        least_dangerous_preys = FeedingRules.count_own_losses(
            SimpleNamespace(),
            SimpleNamespace(),
            [own_prey, opponent_prey],
            player,
        )

        self.assertEqual(least_dangerous_preys, [(opponent_prey, 0)])

    def test_prey_selection_minimizes_own_prey_and_hunter_losses(self):
        player = Player(name="Hunter owner")
        hunter = Species(solo_card=SoloSpecies(), round_created=1)
        own_prey = Species(solo_card=SoloSpecies(), round_created=1)
        opponent_prey = Species(solo_card=SoloSpecies(), round_created=1)
        player.species.extend([hunter, own_prey])

        def hunter_loss_caused_by_prey(prey, hunter):
            return 2 if prey is opponent_prey else 0

        with patch.object(
            FeedingRules,
            "hunter_loss_caused_by_prey",
            side_effect=hunter_loss_caused_by_prey,
        ):
            least_dangerous_preys = FeedingRules.count_own_losses(
                GameState(),
                hunter,
                [opponent_prey, own_prey],
                player,
            )

        self.assertEqual(least_dangerous_preys, [(own_prey, 1)])


if __name__ == "__main__":
    unittest.main()
