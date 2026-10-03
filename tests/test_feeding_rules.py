import unittest
from types import SimpleNamespace

from src.nature_solo_bot.game.rules.feeding import FeedingRules


class FeedingRulesTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()