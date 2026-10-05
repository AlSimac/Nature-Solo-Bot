import unittest

from src.nature_solo_bot.game.model.solo_species import SoloSpecies
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.trait_card import TraitCard
from src.nature_solo_bot.game.model.trait_cards import CLAWED, PLATED


class SpeciesTest(unittest.TestCase):
    def test_hunger_status_tracks_food_and_population_changes(self):
        species = Species(solo_card=SoloSpecies(), round_created=1)
        self.assertTrue(species.is_hungry)

        species.plant_food = 1
        self.assertFalse(species.is_hungry)

        species.population += 1
        self.assertTrue(species.is_hungry)

        species.meat_food = 1
        self.assertFalse(species.is_hungry)

    def test_size_values_follow_size(self):
        species = Species(solo_card=SoloSpecies(), round_created=1)

        species.size = 4

        self.assertEqual(species.attack_value, 4)
        self.assertEqual(species.defense_value, 4)
        self.assertEqual(species.forage_value, 4)

    def test_combat_values_include_attached_trait_modifiers(self):
        species = Species(solo_card=SoloSpecies(), round_created=1)
        species.size = 3
        clawed = TraitCard(CLAWED)
        second_clawed = TraitCard(CLAWED)

        self.assertTrue(species.add_trait_card(clawed, max_traits=3))
        self.assertEqual(species.attack_value, 5)
        self.assertEqual(species.defense_value, 4)

        self.assertTrue(species.add_trait_card(second_clawed, max_traits=3))
        self.assertEqual(species.attack_value, 7)
        self.assertEqual(species.defense_value, 5)

        self.assertTrue(species.remove_trait_card(clawed))
        self.assertEqual(species.attack_value, 5)
        self.assertEqual(species.defense_value, 4)

        plated = TraitCard(PLATED)
        self.assertTrue(
            species.replace_trait_card(
                second_clawed,
                plated,
                max_traits=3,
            )
        )
        self.assertEqual(species.attack_value, 3)
        self.assertEqual(species.defense_value, 7)

    def test_total_food_is_sum_of_plant_and_meat_food(self):
        species = Species(solo_card=SoloSpecies(), round_created=1)

        species.plant_food = 2
        species.meat_food = 3

        self.assertEqual(species.total_food, 5)


if __name__ == "__main__":
    unittest.main()
