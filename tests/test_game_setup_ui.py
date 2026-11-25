"""Tests for persisted desktop UI preferences."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.nature_solo_bot.cli.analyze_traits import run_analysis
from src.nature_solo_bot.cli.game_setup_ui import (
    _DEFAULT_OUTPUT_FOLDER,
    _analysis_directories,
    _load_last_output_folder,
    _save_last_output_folder,
)


class GameSetupUiTest(unittest.TestCase):
    def test_output_folder_defaults_when_no_preference_exists(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings_file = Path(temporary_directory) / "settings" / "output.txt"

            output_folder = _load_last_output_folder(settings_file)

        self.assertEqual(output_folder, str(_DEFAULT_OUTPUT_FOLDER))

    def test_output_folder_is_remembered_between_launches(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings_file = Path(temporary_directory) / "settings" / "output.txt"
            selected_folder = Path(temporary_directory) / "game-logs"

            _save_last_output_folder(str(selected_folder), settings_file)
            output_folder = _load_last_output_folder(settings_file)

        self.assertEqual(output_folder, str(selected_folder.resolve()))

    def test_analysis_uses_timestamped_run_analysis_folder(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_folder = Path(temporary_directory) / "2026-11-25_19-58-41_222664"
            simulations_folder = run_folder / "simulations"
            simulations_folder.mkdir(parents=True)

            logs, analysis = _analysis_directories(str(run_folder))
            logs_from_simulations, analysis_from_simulations = _analysis_directories(
                str(simulations_folder)
            )

        self.assertEqual(logs, simulations_folder.resolve())
        self.assertEqual(logs_from_simulations, simulations_folder.resolve())
        self.assertEqual(analysis, (run_folder / "analysis").resolve())
        self.assertEqual(analysis_from_simulations, (run_folder / "analysis").resolve())

    def test_run_analysis_creates_each_selected_report(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            output_directory = folder / "analysis"
            (folder / "gamelog_2_test.log").write_text("", encoding="utf-8")
            analyses = (
                "trait_assignments",
                "food_by_trait",
                "trait_combinations",
                "solo_species",
            )

            with patch(
                "src.nature_solo_bot.cli.analyze_traits._parse_counts",
                return_value={},
            ):
                progress = []
                reports = run_analysis(
                    folder,
                    output_directory,
                    analyses,
                    progress_callback=lambda completed, total: progress.append(
                        (completed, total)
                    ),
                )

            self.assertEqual(
                [report.name for report in reports],
                [
                    "trait_assignment_counts.csv",
                    "trait_food_by_round.csv",
                    "trait_combinations.csv",
                    "solo_species_stats.csv",
                ],
            )
            self.assertTrue(all(report.is_file() for report in reports))
            self.assertEqual(progress, [(1, 4), (2, 4), (3, 4), (4, 4)])


if __name__ == "__main__":
    unittest.main()
