import unittest
from unittest.mock import patch

from src.nature_solo_bot.engine.game_engine import GameEngine
from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.hunter_card import HunterCard
from src.nature_solo_bot.game.model.state import DIFFICULTY_EASIEST
from src.nature_solo_bot.game.model.trait_cards import HUNTER


class GameEngineTest(unittest.TestCase):
    @staticmethod
    def _remove_hunter_trait(species):
        for card in list(species.trait_cards):
            if card.trait is HUNTER:
                species.remove_trait_card(card)

    def test_initialize_game(self):
        engine = GameEngine(seed=42)

        state = engine.setup_game()

        self.assertEqual(len(state.players), 2)
        self.assertEqual(len(state.nature_deck), 87)
        self.assertIsNotNone(state.food_card)
        self.assertGreater(state.plant_per_round, 0)
        self.assertNotIn(state.food_card, state.nature_deck)
        self.assertIn(state.first_player_index, range(state.number_players))
        print(
            f"Food card drawn: {state.food_card.name} with food value {state.food_card.food_value}"
        )

    def test_run_game_sets_up_and_returns_completed_state(self):
        engine = GameEngine(seed=42)

        state = engine.run_game()

        self.assertIs(engine.state, state)
        self.assertEqual(state.current_round, state.total_rounds + 1)

    def test_define_winner_uses_total_species_traits_to_break_score_tie(self):
        engine = GameEngine(seed=42)
        state = engine.setup_game()
        first_player, second_player = state.players
        first_player.score = second_player.score = 10

        cards = Card.init_nature_deck()
        first_player.species[0].add_trait_card(cards[0], max_traits=state.max_traits)
        second_player.species[0].add_trait_card(cards[1], max_traits=state.max_traits)
        second_player.species[0].add_trait_card(cards[2], max_traits=state.max_traits)

        self.assertIs(engine.define_winner(), second_player)

    def test_choose_species_to_feed_excludes_fully_fed_species(self):
        engine = GameEngine(seed=42)
        state = engine.setup_game()
        engine.add_new_species()
        engine.add_new_species()
        player = state.players[0]
        for species in player.species:
            species.plant_food = species.population
            self._remove_hunter_trait(species)

        hungry_forager = player.species[0]
        hungry_forager.plant_food = 0
        hungry_forager.meat_food = 0
        fully_fed_hunter = player.species[1]
        fully_fed_hunter.add_trait_card(HunterCard(), max_traits=state.max_traits)

        self.assertEqual(
            engine.choose_species_to_feed(player),
            [hungry_forager],
        )

    def test_feeding_candidates_prioritize_food_yield_for_both_players(self):
        engine = GameEngine(seed=42)
        state = engine.setup_game()
        engine.add_new_species()
        engine.add_new_species()
        state.watering_hole_plant = 2

        for player in state.players:
            state.watering_hole_plant = 2
            player.hand = [state.nature_deck[0]]
            species = player.species
            for candidate in species:
                self._remove_hunter_trait(candidate)

            species[0].size = 5
            species[0].population = 4
            species[0].plant_food = 1
            species[0].meat_food = 0
            species[1].size = 3
            species[1].population = 5
            species[1].plant_food = 0
            species[1].meat_food = 0
            species[2].size = 4
            species[2].population = 4
            species[2].plant_food = 0
            species[2].meat_food = 0

            self.assertEqual(
                engine.choose_species_to_feed(player),
                [species[2], species[0], species[1]],
            )

            state.watering_hole_plant = 0
            species[0].size = 2
            species[0].population = 2
            species[0].plant_food = 0
            species[0].meat_food = 0
            species[1].size = 4
            species[1].population = 5
            species[1].plant_food = 0
            species[1].meat_food = 0
            species[2].size = 1
            species[2].population = 2
            species[2].plant_food = 0
            species[2].meat_food = 0
            self.assertEqual(
                engine.choose_species_to_feed(player),
                [species[1], species[0], species[2]],
            )

            species[0].add_trait_card(HunterCard(), max_traits=state.max_traits)
            species[1].add_trait_card(HunterCard(), max_traits=state.max_traits)
            species[1].plant_food = species[1].population
            self.assertEqual(
                engine.choose_species_to_feed(player),
                [species[2], species[0]],
            )


import unittest

from src.nature_solo_bot.engine.game_engine import GameEngine
from src.nature_solo_bot.game.model.state import GamePhase


class GameEnginePreparationTest(unittest.TestCase):
    def test_first_player_stays_for_round_and_switches_for_next_round(self):
        engine = GameEngine(seed=42)
        state = engine.setup_game()
        round_one_first_player = state.first_player_index

        engine.run_preparation_phase()
        self.assertEqual(state.first_player_index, round_one_first_player)

        with patch.object(engine.rng, "shuffle", lambda cards: None):
            engine.run_adaptation_phase()
        self.assertEqual(state.first_player_index, round_one_first_player)

        state.current_round = 2
        engine.run_preparation_phase()
        self.assertEqual(
            state.first_player_index,
            (round_one_first_player + 1) % state.number_players,
        )

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
