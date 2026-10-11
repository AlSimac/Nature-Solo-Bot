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

    def test_counts_trait_species_and_average_food_for_each_round(self):
        log_lines = (
            "FULL GAME SETUP",
            "Players: Rani, Radwin",
            "ROUND 1 - ADAPTATION",
            "Species at the end of adaptation:",
            "Rani: hand=[]",
            "  S1 SpeciesA (tree=PINK, size=1, attack=1, defense=1, "
            "population=3, traits=[Fast, Fast, Social], plant food=0, meat food=0)",
            "  S2 SpeciesB (tree=PINK, size=1, attack=1, defense=1, "
            "population=2, traits=[Fast], plant food=0, meat food=0)",
            "ROUND 1 - FEEDING",
            "  S1 ate 2 plant food",
            "  S1 ate 1 meat food by hunting",
            "Watering hole after feeding: 0",
            "ROUND 1 - SCORING",
            "ROUND 2 - ADAPTATION",
            "Species at the end of adaptation:",
            "Rani: hand=[]",
            "  S1 SpeciesA (tree=PINK, size=1, attack=1, defense=1, "
            "population=3, traits=[Social], plant food=0, meat food=0)",
            "  S2 SpeciesB (tree=PINK, size=1, attack=1, defense=1, "
            "population=2, traits=[Social], plant food=0, meat food=0)",
            "ROUND 2 - FEEDING",
            "  S1 ate 2 plant food",
            "Watering hole after feeding: 0",
            "ROUND 2 - SCORING",
            "GAME COMPLETE",
            "Winner: Rani",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "gamelog_2_test.log"
            log_path.write_text("\n".join(log_lines), encoding="utf-8")

            stats = TraitAssignmentParser().parse_food_by_trait(temporary_directory)

        self.assertEqual(stats["Fast"][1].species_count, 2)
        self.assertEqual(stats["Fast"][1].total_food, 3)
        self.assertEqual(stats["Fast"][1].average_food, 1.5)
        self.assertEqual(stats["Social"][1].species_count, 1)
        self.assertEqual(stats["Social"][1].total_food, 3)
        self.assertEqual(stats["Social"][2].species_count, 2)
        self.assertEqual(stats["Social"][2].total_food, 2)
        self.assertEqual(stats["Social"][2].average_food, 1)
        self.assertEqual(stats["Fast"][2].species_count, 0)
        self.assertEqual(stats["Fast"][2].total_food, 0)
        self.assertEqual(stats["Fast"][2].average_food, 0)

    def test_aggregates_exact_trait_combinations_and_population_outcomes(self):
        log_lines = (
            "FULL GAME SETUP",
            "Players: Rani, Radwin",
            "ROUND 1 - ADAPTATION",
            "Species at the end of adaptation:",
            "Rani: hand=[]",
            "  S1 SpeciesA (tree=PINK, size=1, attack=1, defense=1, "
            "population=4, traits=[Social, Fast, Social], plant food=0, meat food=0)",
            "  S2 SpeciesB (tree=PINK, size=1, attack=1, defense=1, "
            "population=2, traits=[Fast, Social, Social], plant food=0, meat food=0)",
            "  S3 SpeciesC (tree=PINK, size=1, attack=1, defense=1, "
            "population=2, traits=[Fast], plant food=0, meat food=0)",
            "  S4 SpeciesD (tree=PINK, size=1, attack=1, defense=1, "
            "population=1, traits=[none], plant food=0, meat food=0)",
            "ROUND 1 - FEEDING",
            "  S1 ate 2 plant food",
            "  S1 ate 1 meat food by hunting",
            "  S2 ate 1 plant food",
            "  S3 ate 2 plant food",
            "Watering hole after feeding: 0",
            "  Rani species after feeding:",
            "    S1 SpeciesA (tree=PINK, size=1, attack=1, defense=1, "
            "population=3, traits=[Fast, Social, Social], plant food=0, meat food=0); fed=3/3",
            "    S3 SpeciesC (tree=PINK, size=1, attack=1, defense=1, "
            "population=2, traits=[Fast], plant food=0, meat food=0); fed=2/2",
            "ROUND 1 - SCORING",
            "GAME COMPLETE",
            "Winner: Rani",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "gamelog_2_test.log"
            log_path.write_text("\n".join(log_lines), encoding="utf-8")

            stats = TraitAssignmentParser().parse_trait_combinations(temporary_directory)

        duplicate_combo = ("Fast", "Social", "Social")
        self.assertEqual(stats[duplicate_combo].species_rounds_present, 2)
        self.assertEqual(stats[duplicate_combo].times_extinct, 1)
        self.assertEqual(stats[duplicate_combo].total_food, 4)
        self.assertEqual(stats[duplicate_combo].average_food_per_round, 2)
        self.assertEqual(stats[duplicate_combo].total_population_at_start_of_feeding, 6)
        self.assertEqual(stats[duplicate_combo].total_lost_population, 3)
        self.assertEqual(stats[("Fast",)].species_rounds_present, 1)
        self.assertEqual(stats[("Fast",)].total_lost_population, 0)
        self.assertEqual(stats[()].species_rounds_present, 1)
        self.assertEqual(stats[()].times_extinct, 1)
        self.assertEqual(stats[()].total_food, 0)
        self.assertEqual(stats[()].total_population_at_start_of_feeding, 1)
        self.assertEqual(stats[()].total_lost_population, 1)

    def test_aggregates_food_extinctions_and_population_by_solo_species(self):
        log_lines = (
            "FULL GAME SETUP",
            "Players: Rani, Radwin",
            "ROUND 1 - ADAPTATION",
            "Species at the end of adaptation:",
            "Rani: hand=[]",
            "  S1 Evader (tree=PINK, size=1, attack=1, defense=1, "
            "population=4, traits=[Fast], plant food=0, meat food=0)",
            "  S2 Glutton (tree=PINK, size=1, attack=1, defense=1, "
            "population=3, traits=[none], plant food=0, meat food=0)",
            "  S3 Evader (tree=PINK, size=1, attack=1, defense=1, "
            "population=2, traits=[Social], plant food=0, meat food=0)",
            "ROUND 1 - FEEDING",
            "  S1 ate 2 plant food",
            "  S3 ate 1 meat food by hunting",
            "Watering hole after feeding: 0",
            "  Rani species after feeding:",
            "    S1 Evader (tree=PINK, size=1, attack=1, defense=1, "
            "population=3, traits=[Fast], plant food=2, meat food=0); fed=2/3",
            "ROUND 1 - SCORING",
            "ROUND 2 - ADAPTATION",
            "Species at the end of adaptation:",
            "Rani: hand=[]",
            "  S1 Evader (tree=PINK, size=1, attack=1, defense=1, "
            "population=3, traits=[Fast], plant food=0, meat food=0)",
            "ROUND 2 - FEEDING",
            "Watering hole after feeding: 0",
            "  Rani species after feeding:",
            "    S1 Evader (tree=PINK, size=1, attack=1, defense=1, "
            "population=3, traits=[Fast], plant food=0, meat food=0); fed=0/3",
            "ROUND 2 - SCORING",
            "GAME COMPLETE",
            "Winner: Rani",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "gamelog_2_test.log"
            log_path.write_text("\n".join(log_lines), encoding="utf-8")

            stats = TraitAssignmentParser().parse_solo_species(temporary_directory)

        self.assertEqual(stats["Evader"].species_rounds_present, 3)
        self.assertEqual(stats["Evader"].times_extinct, 1)
        self.assertEqual(stats["Evader"].total_food, 3)
        self.assertEqual(stats["Evader"].average_food_per_round, 1)
        self.assertEqual(stats["Evader"].total_population_at_start_of_feeding, 9)
        self.assertEqual(stats["Evader"].total_lost_population, 3)
        self.assertEqual(stats["Glutton"].species_rounds_present, 1)
        self.assertEqual(stats["Glutton"].times_extinct, 1)
        self.assertEqual(stats["Glutton"].total_lost_population, 3)


if __name__ == "__main__":
    unittest.main()
