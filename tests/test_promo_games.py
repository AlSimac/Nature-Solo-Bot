"""Run several full games with the Promo cards and save only their final scores."""

from pathlib import Path
import unittest

from src.nature_solo_bot.engine.game_engine import GameEngine
from src.nature_solo_bot.game.model.trait_cards import AVID_FORAGER


class PromoGamesTest(unittest.TestCase):
    def test_five_promo_games_write_only_final_scores(self):
        score_lines = []

        for seed in range(1, 6):
            engine = GameEngine(seed=seed, promo=True)
            state = engine.setup_game()
            self.assertTrue(
                any(card.trait is AVID_FORAGER for card in state.nature_deck)
            )

            completed_state = engine.run_game()
            self.assertIs(completed_state, state)
            self.assertEqual(
                completed_state.current_round,
                completed_state.total_rounds + 1,
            )
            score_lines.append(
                f"Game {seed}: "
                + ", ".join(
                    f"{player.name}={player.score}" for player in completed_state.players
                )
            )

        log_path = Path(__file__).with_name("promo_game_scores.log")
        log_path.write_text("\n".join(score_lines) + "\n", encoding="utf-8")
        self.assertEqual(
            log_path.read_text(encoding="utf-8"),
            "\n".join(score_lines) + "\n",
        )
        self.assertEqual(len(score_lines), 5)


if __name__ == "__main__":
    unittest.main()
