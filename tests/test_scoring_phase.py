import unittest
from unittest.mock import patch

from src.nature_solo_bot.engine.game_engine import GameEngine
from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.hunter_card import HunterCard
from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.model.solo_species import SoloSpecies
from src.nature_solo_bot.game.model.species import Species, TreeColor
from src.nature_solo_bot.game.model.state import GamePhase, GameState


class ScoringPhaseTest(unittest.TestCase):
    def _create_engine_with_players(self, current_round: int = 1):
        engine = GameEngine(seed=42)
        state = GameState()
        state.current_round = current_round
        state.first_player_index = 0
        state.players = [Player(name="Rani"), Player(name="Radwin")]
        engine.state = state
        return engine, state

    def test_scores_food_for_both_players_and_clears_species_food(self):
        engine, state = self._create_engine_with_players()
        rani_species = Species(SoloSpecies(), round_created=1)
        rani_species.plant_food = 2
        rani_species.meat_food = 1
        radwin_species = Species(SoloSpecies(), round_created=1)
        radwin_species.plant_food = 1
        state.players[0].species.append(rani_species)
        state.players[1].species.append(radwin_species)
        state.players[0].passing = True
        state.players[1].passing = True
        state.watering_hole_plant = 4

        engine.run_scoring_phase()

        self.assertEqual([player.score for player in state.players], [3, 1])
        self.assertEqual(
            [
                (species.plant_food, species.meat_food)
                for player in state.players
                for species in player.species
            ],
            [(0, 0), (0, 0)],
        )
        self.assertTrue(all(not player.passing for player in state.players))
        self.assertEqual(state.watering_hole_plant, 4)
        self.assertIs(state.current_phase, GamePhase.SCORING)

    def test_lost_population_switches_tree_and_discards_selected_nature_trait(self):
        engine, state = self._create_engine_with_players(current_round=2)
        player = state.players[0]
        species = Species(SoloSpecies(), round_created=1)
        cards = Card.init_nature_deck()[:2]
        for card in cards:
            self.assertTrue(species.add_trait_card(card, max_traits=state.max_traits))
        species.lost_population = 1
        player.species.append(species)

        with patch.object(engine.rng, "choice", return_value=cards[1]):
            engine.run_scoring_phase()

        self.assertIs(species.tree_color, TreeColor.BLUE)
        self.assertEqual(species.trait_cards, [cards[0]])
        self.assertEqual(state.nature_discard, [cards[1]])
        self.assertEqual(species.lost_population, 0)

    def test_discarding_hunter_trait_turns_species_into_forager_without_nature_discard(self):
        engine, state = self._create_engine_with_players(current_round=2)
        player = state.players[0]
        species = Species(SoloSpecies(), round_created=1)
        nature_card = Card.init_nature_deck()[0]
        hunter_card = HunterCard()
        self.assertTrue(species.add_trait_card(nature_card, max_traits=state.max_traits))
        self.assertTrue(species.add_trait_card(hunter_card, max_traits=state.max_traits))
        species.lost_population = 1
        player.species.append(species)

        with patch.object(engine.rng, "choice", return_value=hunter_card):
            engine.run_scoring_phase()

        self.assertFalse(species.is_hunter)
        self.assertEqual(species.trait_cards, [nature_card])
        self.assertEqual(state.nature_discard, [])
        self.assertEqual(species.lost_population, 0)

    def test_lost_population_without_traits_does_not_fail(self):
        engine, state = self._create_engine_with_players(current_round=2)
        species = Species(SoloSpecies(), round_created=1)
        species.lost_population = 1
        state.players[0].species.append(species)

        engine.run_scoring_phase()

        self.assertIs(species.tree_color, TreeColor.BLUE)
        self.assertEqual(species.lost_population, 0)
        self.assertEqual(species.trait_cards, [])

    def test_final_round_awards_two_points_per_surviving_species(self):
        engine, state = self._create_engine_with_players(current_round=4)
        for player, species_count in zip(state.players, (2, 1)):
            for _ in range(species_count):
                player.species.append(Species(SoloSpecies(), round_created=1))

        engine.run_scoring_phase()

        self.assertEqual([player.score for player in state.players], [4, 2])


if __name__ == "__main__":
    unittest.main()
