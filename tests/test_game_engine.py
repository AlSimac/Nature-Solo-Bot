import unittest

from src.nature_solo_bot.engine.game_engine import GameEngine
from src.nature_solo_bot.game.model.state import DIFFICULTY_EASIEST


class GameEngineTest(unittest.TestCase):
    def test_initialize_game(self):
        engine = GameEngine(seed=42)

        state = engine.setup_game()

        self.assertEqual(len(state.players), 2)
        self.assertEqual(len(state.nature_deck), 87)
        self.assertIsNotNone(state.food_card)
        self.assertGreater(state.plant_per_round, 0)
        self.assertNotIn(state.food_card, state.nature_deck)
        self.assertIn(state.first_player_index, range(state.number_players))
        print(f"Food card drawn: {state.food_card.name} with food value {state.food_card.food_value}")

import unittest

from src.nature_solo_bot.engine.game_engine import GameEngine
from src.nature_solo_bot.game.model.state import GamePhase


class GameEnginePreparationTest(unittest.TestCase):
    def test_difficulty_controls_round_one_population_and_hand_size(self):
        engine = GameEngine(seed=42, difficulty=DIFFICULTY_EASIEST)
        state = engine.setup_game()

        engine.run_preparation_phase()

        self.assertIs(state.difficulty, DIFFICULTY_EASIEST)
        self.assertEqual(len(state.players[0].hand), 5)
        self.assertEqual(len(state.players[1].hand), 5)
        self.assertEqual(state.players[0].species[1].population, 1)
        self.assertEqual(state.players[1].species[1].population, 1)

    def test_initial_preparation(self):
        engine = GameEngine(seed=42)
        state = engine.setup_game()
        engine.run_preparation_phase()
        print(f"Plant per round: {state.plant_per_round}")
        self.assertEqual(state.current_round, 1)
        self.assertEqual(state.current_phase, GamePhase.PREPARATION)
        self.assertEqual(len(state.players), 2)
        self.assertEqual(len(state.players[0].hand), 7)
        self.assertEqual(len(state.players[1].hand), 7)
        self.assertEqual(len(state.players[0].species), 2)
        self.assertEqual(len(state.players[1].species), 2)
        self.assertEqual(state.players[0].species[0].population, 1)
        self.assertEqual(state.players[1].species[0].population, 1)
        self.assertEqual(state.players[0].species[1].population, 3)
        self.assertEqual(state.players[1].species[1].population, 3)
        self.assertEqual(state.watering_hole_plant, state.plant_per_round)

        print("\nCards in each player's hand:")
        for player in state.players:
            print(f"{player.name}:")
            for card in player.hand:
                print(f"  {card.name}: food value {card.food_value}")

        print("\nFirst 10 cards remaining in the Nature deck:")
        for card in state.nature_deck[-10:]:
            print(f"  {card.name}: food value {card.food_value}")

if __name__ == "__main__":
    unittest.main()