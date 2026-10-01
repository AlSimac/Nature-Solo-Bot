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
            [own_old_large, own_new_small, opponent_old_large, opponent_young_small],
        )

        self.assertEqual(
            sorted_preys,
            [opponent_young_small, opponent_old_large, own_new_small, own_old_large],
        )


if __name__ == "__main__":
    unittest.main()