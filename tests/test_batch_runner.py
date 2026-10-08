"""Tests for running and exporting game batches."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.nature_solo_bot.analysis import GameLogger
from src.nature_solo_bot.cli.run_experiments import RunExperiments
from src.nature_solo_bot.engine.game_engine import GameEngine
from src.nature_solo_bot.experiments import BatchRunner
from src.nature_solo_bot.game.model.state import Difficulty


class BatchRunnerTest(unittest.TestCase):
    def test_run_writes_a_unique_full_log_for_each_game(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "nested"
            runner = BatchRunner(
                game_count=3,
                start_seed=10,
                difficulty=Difficulty.EASY,
                promo=True,
            )

            log_paths = runner.run(output_directory)
            log_contents = [log_path.read_text(encoding="utf-8") for log_path in log_paths]
            self.assertTrue(all(path.is_file() for path in log_paths))

        self.assertEqual(len(log_paths), 3)
        self.assertEqual(len({path.name for path in log_paths}), 3)
        for index, (log_path, log_text) in enumerate(zip(log_paths, log_contents), start=1):
            self.assertRegex(
                log_path.name,
                r"gamelog_1_difficulty_[0-9a-f]{32}\.log",
            )
            self.assertIn(f"Game number: {index}", log_text)
            self.assertIn(f"Seed: {index + 9}", log_text)
            self.assertIn("Promo cards: True", log_text)
            self.assertIn(
                "Avid Forager cards in Nature deck (including setup food card): 11",
                log_text,
            )
            self.assertIn("ROUND 1 - PREPARATION", log_text)
            self.assertIn("ROUND 1 - ADAPTATION", log_text)
            self.assertIn("ROUND 1 - FEEDING", log_text)
            self.assertIn("ROUND 1 - SCORING", log_text)
            self.assertIn("final scores:", log_text)
            self.assertRegex(log_text, r"Winner: (Rani|Radwin)")

    def test_log_captures_trait_trigger_details(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "gamelog.log"
            baseline_state = GameEngine(
                seed=0,
                difficulty=Difficulty.MEDIUM,
            ).run_game()
            engine = GameEngine(seed=0, difficulty=Difficulty.MEDIUM)

            completed_state = GameLogger().run_game(
                engine,
                log_path,
                game_number=1,
            )
            log_text = log_path.read_text(encoding="utf-8")

        self.assertEqual(completed_state.current_round, completed_state.total_rounds + 1)
        self.assertEqual(
            [player.score for player in completed_state.players],
            [player.score for player in baseline_state.players],
        )
        self.assertIn("Tusked trigger", log_text)
        self.assertIn("Scavenging trigger", log_text)
        self.assertIn("Opportunistic trigger", log_text)
        self.assertIn("the watering hole emptied", log_text)
        self.assertIn("after a successful hunt", log_text)
        self.assertIn("after feeding while plants remained", log_text)

    def test_constructor_rejects_nonpositive_game_count(self):
        with self.assertRaisesRegex(ValueError, "game_count"):
            BatchRunner(game_count=0)

    def test_cli_runs_with_selected_options(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "logs"

            exit_code = RunExperiments.run(
                [
                    "--games",
                    "2",
                    "--start-seed",
                    "20",
                    "--difficulty",
                    "easy",
                    "--promo",
                    "--output-dir",
                    str(output_directory),
                ]
            )
            log_paths = list(output_directory.glob("*.log"))
            contents = [path.read_text(encoding="utf-8") for path in log_paths]

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(log_paths), 2)
        self.assertTrue(any("Seed: 20" in content for content in contents))
        self.assertTrue(any("Seed: 21" in content for content in contents))
        self.assertTrue(all("Promo cards: True" in content for content in contents))
        self.assertTrue(
            all(
                "Avid Forager cards in Nature deck "
                "(including setup food card): 11" in content
                for content in contents
            )
        )

    def test_cli_run_loop_runs_each_difficulty_with_separate_promo_outputs(self):
        with patch.object(RunExperiments, "run", return_value=0) as run:
            exit_code = RunExperiments.run_loop()

        self.assertEqual(exit_code, 0)
        self.assertEqual(run.call_count, 10)
        arguments = [call.args[0] for call in run.call_args_list]
        output_directories = [
            args[args.index("--output-dir") + 1] for args in arguments
        ]
        self.assertEqual(len(set(output_directories)), 10)
        for args in arguments:
            difficulty = args[args.index("--difficulty") + 1]
            self.assertIn(difficulty, {"easiest", "easy", "medium", "hard", "hardest"})
            output_path = Path(args[args.index("--output-dir") + 1])
            self.assertEqual(output_path.parts[:2], ("output", "Nature"))
            self.assertEqual(output_path.parts[2], difficulty)
            self.assertEqual(
                output_path.parts[3],
                "promo" if "--promo" in args else "core",
            )


if __name__ == "__main__":
    unittest.main()
