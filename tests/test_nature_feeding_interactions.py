import unittest
from itertools import combinations
from random import Random

from src.nature_solo_bot.game.model.hunter_card import HunterCard
from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.model.solo_species import SoloSpecies
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.state import GameState
from src.nature_solo_bot.game.model.trait_card import TraitCard
from src.nature_solo_bot.game.model.trait_cards import (
    AVID_FORAGER,
    CLAWED,
    NATURE_TRAITS,
    OPPORTUNISTIC,
    PLATED,
    SCAVENGING,
    SOCIAL,
    TUSKED,
)
from src.nature_solo_bot.game.rules.feeding import FeedingRules


class NatureFeedingInteractionTest(unittest.TestCase):
    def test_all_nature_trait_pairs_attach_and_count_independently(self):
        nature_pair_traits = [*NATURE_TRAITS, AVID_FORAGER]

        for first_trait, second_trait in combinations(nature_pair_traits, 2):
            with self.subTest(first=first_trait.name, second=second_trait.name):
                species = Species(solo_card=SoloSpecies(), round_created=1)
                species.size = 1

                self.assertTrue(
                    species.add_trait_card(TraitCard(first_trait), max_traits=3)
                )
                self.assertTrue(
                    species.add_trait_card(TraitCard(second_trait), max_traits=3)
                )
                self.assertEqual(len(species.trait_cards), 2)
                self.assertEqual(species.count_trait_instance(first_trait), 1)
                self.assertEqual(species.count_trait_instance(second_trait), 1)

    def test_nature_trait_pairs_compose_foraging_modifiers(self):
        nature_pair_traits = [*NATURE_TRAITS, AVID_FORAGER]

        for first_trait, second_trait in combinations(nature_pair_traits, 2):
            with self.subTest(first=first_trait.name, second=second_trait.name):
                species = Species(solo_card=SoloSpecies(), round_created=1)
                species.size = 2
                species.population = 10
                species.add_trait_card(TraitCard(first_trait), max_traits=3)
                species.add_trait_card(TraitCard(second_trait), max_traits=3)

                clawed_bonus = 2 * species.count_trait_instance(CLAWED)
                social_bonus = 2 * species.count_trait_instance(SOCIAL)

                self.assertEqual(
                    FeedingRules.food_taken_in_one_forage(species, 20),
                    2 + clawed_bonus + social_bonus,
                )

    def test_nature_trait_pairs_compose_hunt_modifiers(self):
        nature_pair_traits = [*NATURE_TRAITS, AVID_FORAGER]

        for first_trait, second_trait in combinations(nature_pair_traits, 2):
            with self.subTest(first=first_trait.name, second=second_trait.name):
                species = Species(solo_card=SoloSpecies(), round_created=1)
                species.size = 2
                species.population = 10
                species.add_trait_card(TraitCard(first_trait), max_traits=3)
                species.add_trait_card(TraitCard(second_trait), max_traits=3)

                expected_defense = (
                    2
                    + species.count_trait_instance(CLAWED)
                    + species.count_trait_instance(OPPORTUNISTIC)
                    + 4 * species.count_trait_instance(PLATED)
                    + 2 * species.count_trait_instance(TUSKED)
                )

                self.assertEqual(species.defense_value, expected_defense)
                self.assertEqual(
                    species.attack_value,
                    2 + 2 * species.count_trait_instance(CLAWED),
                )

    def test_scavenging_social_pair_stacks_after_hunt(self):
        scavenger_owner = Player(name="Scavenger")
        scavenger = Species(solo_card=SoloSpecies(), round_created=1)
        scavenger.population = 10
        scavenger.add_trait_card(TraitCard(SCAVENGING), max_traits=3)
        scavenger.add_trait_card(TraitCard(SOCIAL), max_traits=3)
        scavenger_owner.species.append(scavenger)

        prey_owner = Player(name="Prey")
        prey = Species(solo_card=SoloSpecies(), round_created=1)
        prey.population = 2
        prey_owner.species.append(prey)

        hunter_owner = Player(name="Hunter")
        hunter = Species(solo_card=SoloSpecies(), round_created=1)
        hunter.population = 3
        hunter.add_trait_card(HunterCard(), max_traits=3)
        hunter_owner.species.append(hunter)

        state = GameState()
        state.players = [hunter_owner, prey_owner, scavenger_owner]

        FeedingRules.take_feeding_turn(state, hunter_owner, Random(1))

        self.assertEqual(scavenger.meat_food, 4)

    def test_tusked_social_pair_stacks_when_watering_hole_empties(self):
        tusked_owner = Player(name="Tusked")
        tusked = Species(solo_card=SoloSpecies(), round_created=1)
        tusked.population = 10
        tusked.add_trait_card(TraitCard(TUSKED), max_traits=3)
        tusked.add_trait_card(TraitCard(SOCIAL), max_traits=3)
        tusked_owner.species.append(tusked)

        state = GameState()
        state.players = [tusked_owner]
        state.watering_hole_plant = 1

        FeedingRules.remove_watering_hole_food(state, 1, "plant_food")

        self.assertEqual(tusked.meat_food, 3)

    def test_avid_forager_social_pair_combines_bonus_and_eating(self):
        forager_owner = Player(name="Avid Social")
        forager = Species(solo_card=SoloSpecies(), round_created=1)
        forager.size = 2
        forager.population = 10
        forager.add_trait_card(TraitCard(AVID_FORAGER), max_traits=3)
        forager.add_trait_card(TraitCard(SOCIAL), max_traits=3)
        forager_owner.species.append(forager)

        state = GameState()
        state.players = [forager_owner]
        state.watering_hole_plant = 10

        FeedingRules.take_feeding_turn(state, forager_owner, Random(1))

        self.assertEqual(forager.plant_food, 8)


if __name__ == "__main__":
    unittest.main()
