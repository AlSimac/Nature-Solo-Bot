import unittest
from itertools import combinations
from random import Random

from src.nature_solo_bot.const import BAMBOO, BAMBOO_GROVE, PLANT
from src.nature_solo_bot.game.model.hunter_card import HunterCard
from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.model.solo_species import SoloSpecies
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.state import GameState
from src.nature_solo_bot.game.model.trait_card import TraitCard
from src.nature_solo_bot.game.model.trait_cards import (
    ARBOREAL,
    AVID_FORAGER,
    BAMBOO_GROVE_TRAITS,
    CLAWED,
    FOLIVORE,
    FAST,
    MONOPHAGOUS,
    NATURE_TRAITS,
    OPPORTUNISTIC,
    PLATED,
    ROOT_EATING,
    SOCIAL,
    STALKING,
    TERRITORIAL,
    TUSKED,
)
from src.nature_solo_bot.game.rules.feeding import FeedingRules


class BambooFeedingInteractionTest(unittest.TestCase):
    def test_all_bamboo_trait_pairs_attach_and_count_independently(self):
        for first_trait, second_trait in combinations(BAMBOO_GROVE_TRAITS, 2):
            with self.subTest(first=first_trait.name, second=second_trait.name):
                species = Species(solo_card=SoloSpecies(), round_created=1)

                self.assertTrue(
                    species.add_trait_card(TraitCard(first_trait), max_traits=3)
                )
                self.assertTrue(
                    species.add_trait_card(TraitCard(second_trait), max_traits=3)
                )
                self.assertEqual(len(species.trait_cards), 2)
                self.assertEqual(species.count_trait_instance(first_trait), 1)
                self.assertEqual(species.count_trait_instance(second_trait), 1)

    def test_bamboo_nature_trait_pairs_attach_and_count_independently(self):
        nature_traits = [*NATURE_TRAITS, AVID_FORAGER, TERRITORIAL]

        for bamboo_trait in BAMBOO_GROVE_TRAITS:
            for nature_trait in nature_traits:
                with self.subTest(
                    bamboo=bamboo_trait.name,
                    nature=nature_trait.name,
                ):
                    species = Species(solo_card=SoloSpecies(), round_created=1)
                    self.assertTrue(
                        species.add_trait_card(
                            TraitCard(bamboo_trait),
                            max_traits=3,
                        )
                    )
                    self.assertTrue(
                        species.add_trait_card(
                            TraitCard(nature_trait),
                            max_traits=3,
                        )
                    )
                    self.assertEqual(species.count_trait_instance(bamboo_trait), 1)
                    self.assertEqual(species.count_trait_instance(nature_trait), 1)

    def test_arboreal_and_social_stack_for_foraging(self):
        forager = Species(solo_card=SoloSpecies(), round_created=1)
        forager.size = 2
        forager.population = 10
        forager.add_trait_card(TraitCard(ARBOREAL), max_traits=3)
        forager.add_trait_card(TraitCard(SOCIAL), max_traits=3)

        state = GameState(modules=[BAMBOO_GROVE])
        state.watering_hole_bamboo = 10

        actual_food = FeedingRules.eat(
            forager,
            BAMBOO,
            forager.forage_value,
            available_from_source=10,
        )

        self.assertEqual(actual_food, 5)
        self.assertEqual(forager.bamboo_food, 5)

    def test_arboreal_and_clawed_stack_for_plant_foraging(self):
        forager = Species(solo_card=SoloSpecies(), round_created=1)
        forager.size = 2
        forager.population = 10
        forager.add_trait_card(TraitCard(ARBOREAL), max_traits=3)
        forager.add_trait_card(TraitCard(CLAWED), max_traits=3)

        actual_food = FeedingRules.eat(
            forager,
            PLANT,
            forager.forage_value,
            available_from_source=10,
        )

        self.assertEqual(actual_food, 5)
        self.assertEqual(forager.plant_food, 5)

    def test_arboreal_and_clawed_stack_in_hunt_values(self):
        hunter = Species(solo_card=SoloSpecies(), round_created=1)
        hunter.size = 2
        hunter.population = 3
        hunter.add_trait_card(HunterCard(), max_traits=3)
        hunter.add_trait_card(TraitCard(ARBOREAL), max_traits=3)
        hunter.add_trait_card(TraitCard(CLAWED), max_traits=3)

        self.assertEqual(hunter.attack_value, 5)

    def test_folivore_and_social_stack_on_trigger(self):
        folivore = Species(solo_card=SoloSpecies(), round_created=1)
        folivore.population = 10
        folivore.add_trait_card(TraitCard(FOLIVORE), max_traits=3)
        folivore.add_trait_card(TraitCard(SOCIAL), max_traits=3)

        FeedingRules._trigger_trait_feeding(
            [folivore],
            FOLIVORE.effect_id,
            1,
            PLANT,
        )

        self.assertEqual(folivore.plant_food, 3)

    def test_folivore_and_defense_traits_stack(self):
        for defense_trait, defense_bonus in (
            (OPPORTUNISTIC, 1),
            (PLATED, 4),
            (TUSKED, 2),
            (ROOT_EATING, 1),
        ):
            with self.subTest(defense_trait=defense_trait.name):
                prey = Species(solo_card=SoloSpecies(), round_created=1)
                prey.size = 1
                prey.add_trait_card(TraitCard(FOLIVORE), max_traits=3)
                prey.add_trait_card(TraitCard(defense_trait), max_traits=3)

                self.assertEqual(prey.defense_value, 1 + 1 + defense_bonus)

    def test_monophagous_and_avid_forager_recheck_bamboo_first(self):
        player = Player(name="Monophagous forager")
        forager = Species(solo_card=SoloSpecies(), round_created=1)
        forager.size = 2
        forager.population = 10
        forager.add_trait_card(TraitCard(MONOPHAGOUS), max_traits=3)
        forager.add_trait_card(TraitCard(AVID_FORAGER), max_traits=3)
        player.species.append(forager)

        state = GameState(modules=[BAMBOO_GROVE])
        state.players = [player]
        state.watering_hole_bamboo = 2
        state.watering_hole_plant = 10

        projected_gain = FeedingRules._projected_food_gain_from_forage(
            state,
            player,
            forager,
            FeedingRules.get_available_food(state, player, BAMBOO),
            BAMBOO,
        )

        FeedingRules.take_feeding_turn(state, player, Random(1))

        self.assertEqual(projected_gain, 4)
        self.assertEqual(forager.bamboo_food, 2)
        self.assertEqual(forager.plant_food, 2)

    def test_monophagous_and_territorial_prefer_stored_bamboo(self):
        player = Player(name="Territorial forager")
        forager = Species(solo_card=SoloSpecies(), round_created=1)
        forager.size = 1
        forager.population = 2
        territorial_card = TraitCard(TERRITORIAL)
        territorial_card.stored_food[BAMBOO] = 2
        territorial_card.stored_food[PLANT] = 2
        forager.add_trait_card(TraitCard(MONOPHAGOUS), max_traits=3)
        forager.add_trait_card(territorial_card, max_traits=3)
        player.species.append(forager)

        state = GameState(modules=[BAMBOO_GROVE])
        state.players = [player]

        FeedingRules.take_feeding_turn(state, player, Random(1))

        self.assertEqual(forager.bamboo_food, 1)
        self.assertEqual(territorial_card.stored_food[BAMBOO], 1)
        self.assertEqual(territorial_card.stored_food[PLANT], 2)

    def test_root_eating_and_social_can_use_both_bamboo_and_plant(self):
        forager = Species(solo_card=SoloSpecies(), round_created=1)
        forager.size = 2
        forager.population = 10
        forager.add_trait_card(TraitCard(ROOT_EATING), max_traits=3)
        forager.add_trait_card(TraitCard(SOCIAL), max_traits=3)

        state = GameState(modules=[BAMBOO_GROVE])
        state.players = [Player(name="Root eater")]
        state.players[0].species.append(forager)
        state.watering_hole_bamboo = 1
        state.watering_hole_plant = 1

        FeedingRules.forage(state, forager, BAMBOO)
        FeedingRules._apply_root_eating(
            forager,
            state.watering_hole_food,
            state.players[0].species,
        )

        self.assertEqual(forager.bamboo_food, 1)
        self.assertEqual(forager.plant_food, 1)
        self.assertEqual(state.total_watering_hole_food, 0)

    def test_stalking_ignores_arboreal_only_for_fully_fed_prey(self):
        stalking_hunter = Species(solo_card=SoloSpecies(), round_created=1)
        stalking_hunter.size = 2
        stalking_hunter.population = 2
        stalking_hunter.add_trait_card(TraitCard(STALKING), max_traits=3)

        arboreal_prey = Species(solo_card=SoloSpecies(), round_created=1)
        arboreal_prey.size = 1
        arboreal_prey.population = 2
        arboreal_prey.plant_food = 2
        arboreal_prey.add_trait_card(TraitCard(ARBOREAL), max_traits=3)

        state = GameState(modules=[BAMBOO_GROVE])
        state.players = [Player(name="Hunter"), Player(name="Prey")]
        state.players[0].species.append(stalking_hunter)
        state.players[1].species.append(arboreal_prey)

        self.assertTrue(
            FeedingRules.is_valid_target(arboreal_prey, stalking_hunter)
        )

        arboreal_prey.plant_food = 0
        self.assertFalse(
            FeedingRules.is_valid_target(arboreal_prey, stalking_hunter)
        )

    def test_stalking_ignores_fast_only_when_prey_is_fully_fed(self):
        stalking_hunter = Species(solo_card=SoloSpecies(), round_created=1)
        stalking_hunter.add_trait_card(TraitCard(STALKING), max_traits=3)
        stalking_hunter.add_trait_card(TraitCard(FAST), max_traits=3)

        fast_prey = Species(solo_card=SoloSpecies(), round_created=1)
        fast_prey.population = 2
        fast_prey.plant_food = 2
        fast_prey.add_trait_card(TraitCard(FAST), max_traits=3)
        fast_prey.add_trait_card(TraitCard(FAST), max_traits=3)

        self.assertTrue(
            FeedingRules.is_valid_target(fast_prey, stalking_hunter)
        )

        fast_prey.plant_food = 0
        self.assertFalse(
            FeedingRules.is_valid_target(fast_prey, stalking_hunter)
        )


if __name__ == "__main__":
    unittest.main()
