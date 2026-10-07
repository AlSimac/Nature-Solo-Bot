"""Tests for counting trait assignments in game logs."""

import tempfile
import unittest
from pathlib import Path

from src.nature_solo_bot.analysis import TraitAssignmentParser


class TraitAssignmentParserTest(unittest.TestCase):
    def test_counts_assignments_by_winner_and_loser_recursively(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            nested_folder = folder / "difficulty"
            nested_folder.mkdir()
            (folder / "gamelog_2_first.log").write_text(
                "\n".join(
                    (
                        "FULL GAME SETUP",
                        "Players: Rani, Radwin",
                        "ROUND 1 - ADAPTATION",
                        "  Rani: Card -> S1 trait 'Fast'",
                        "  Rani: Card -> S1 trait 'Fast'",
                        "  Radwin: Card -> S2 trait 'Clawed'",
                        "Winner: Rani",
                    )
                ),
                encoding="utf-8",
            )
            (nested_folder / "gamelog_2_second.log").write_text(
                "\n".join(
                    (
                        "Players: Rani, Radwin",
                        "  Rani: Card -> S1 trait 'Clawed'",
                        "  Radwin: Card -> S2 trait 'Fast'",
                        "Winner: Radwin",
                    )
                ),
                encoding="utf-8",
            )

            counts = TraitAssignmentParser().parse_folder(folder)

        self.assertEqual(counts["Fast"].winner, 3)
        self.assertEqual(counts["Fast"].loser, 0)
        self.assertEqual(counts["Clawed"].winner, 0)
        self.assertEqual(counts["Clawed"].loser, 2)

    def test_counts_assignments_in_a_tied_game_separately(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "gamelog_2_tied.log"
            log_path.write_text(
                "\n".join(
                    (
                        "Players: Rani, Radwin",
                        "  Rani: Card -> S1 trait 'Fast'",
                        "  Radwin: Card -> S2 trait 'Clawed'",
                        "Winner: None",
                    )
                ),
                encoding="utf-8",
            )

            counts = TraitAssignmentParser().parse_folder(temporary_directory)

        self.assertEqual(counts["Fast"].winner, 0)
        self.assertEqual(counts["Fast"].loser, 0)
        self.assertEqual(counts["Fast"].tied, 1)
        self.assertEqual(counts["Clawed"].tied, 1)

    def test_fails_for_log_without_a_valid_winner(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "gamelog_2_invalid.log"
            log_path.write_text(
                "Players: Rani, Radwin\nWinner: Nobody\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Winner"):
                TraitAssignmentParser().parse_folder(temporary_directory)

    def test_fails_when_folder_has_no_logs(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(ValueError, "No game log files"):
                TraitAssignmentParser().parse_folder(temporary_directory)


if __name__ == "__main__":
    unittest.main()
