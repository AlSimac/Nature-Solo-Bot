import unittest

from src.nature_solo_bot.engine.game_engine import GameEngine


class GameEngineTest(unittest.TestCase):
    def test_initialize_game(self):
        engine = GameEngine(seed=42)

        state = engine.initialize_game()

        self.assertEqual(len(state.players), 2)
        self.assertEqual(len(state.deck), 87)
        self.assertIsNotNone(state.food_card)
        self.assertGreater(state.watering_hole_plant, 0)
        self.assertNotIn(state.food_card, state.deck)
        self.assertIn(state.first_player_index, range(state.number_players))
        print(f"Food card drawn: {state.food_card.name} with food value {state.food_card.food_value}")

if __name__ == "__main__":
    unittest.main()