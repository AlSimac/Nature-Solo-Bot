"""Tests for running and exporting game batches."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.nature_solo_bot.analysis import GameLogger, TraitAssignmentParser
from src.nature_solo_bot.cli.run_experiments import RunExperiments, main
from src.nature_solo_bot.engine.game_engine import GameEngine
from src.nature_solo_bot.experiments import BatchRunner
from src.nature_solo_bot.game.model.modules import MODULE_DEFINITIONS
from src.nature_solo_bot.game.model.state import Difficulty


class BatchRunnerTest(unittest.TestCase):
    def test_run_writes_a_unique_full_log_for_each_game(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "nested"
            runner = BatchRunner(
                game_count=3,
                start_seed=10,
                difficulty=Difficulty.EASY,
                nature_promo=True,
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
            self.assertIn("Nature promo cards: True", log_text)
            self.assertIn("Module promo cards: none", log_text)
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

    def test_log_keeps_details_in_compact_form_and_preserves_game_behavior(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "gamelog_2_test.log"
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
            parser = TraitAssignmentParser()
            parsed_assignments = parser.parse_folder(log_path.parent)
            parsed_food = parser.parse_food_by_trait(log_path.parent)
            parsed_combinations = parser.parse_trait_combinations(log_path.parent)
            parsed_species = parser.parse_solo_species(log_path.parent)

        self.assertEqual(completed_state.current_round, completed_state.total_rounds + 1)
        self.assertEqual(
            [player.score for player in completed_state.players],
            [player.score for player in baseline_state.players],
        )
        self.assertIn("Rani hand:", log_text)
        self.assertRegex(log_text, r"Rani turn: .*S\d+ ate \d+ (?:plant|meat) food")
        self.assertRegex(log_text, r"Rani turn: .*discarded \w+\[\d+/[a-z]+\]")
        self.assertIn("hunt;", log_text)
        self.assertIn("starved (", log_text)
        self.assertIn("passes", log_text)
        self.assertIn("trigger", log_text)
        self.assertNotIn("symbol=", log_text)
        self.assertTrue(parsed_assignments)
        self.assertTrue(parsed_food)
        self.assertTrue(parsed_combinations)
        self.assertTrue(parsed_species)

    def test_bamboo_grove_log_records_bamboo_state_and_deck_origin(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "gamelog_1_bamboo.log"
            engine = GameEngine(
                seed=1,
                difficulty=Difficulty.EASY,
                modules=["bamboo_grove"],
            )
            GameLogger().run_game(engine, log_path, game_number=1)
            log_text = log_path.read_text(encoding="utf-8")
            parsed_food = TraitAssignmentParser().parse_food_by_trait(log_path.parent)

        self.assertIn("bamboo added per round:", log_text)
        self.assertIn("Bamboo Grove deck:", log_text)
        self.assertIn("watering hole: 0 plant,", log_text)
        self.assertIn("(Bamboo Grove)", log_text)
        self.assertTrue(parsed_food)
        self.assertTrue(
            any(stats.total_bamboo_food > 0 for rounds in parsed_food.values() for stats in rounds.values())
        )

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
                    "--nature-promo",
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
        self.assertTrue(
            all("Nature promo cards: True" in content for content in contents)
        )
        self.assertTrue(
            all(
                "Avid Forager cards in Nature deck "
                "(including setup food card): 11" in content
                for content in contents
            )
        )

    def test_cli_accepts_multiple_modules_and_passes_them_to_runner(self):
        extra_module = "test_module"
        with patch(
            "src.nature_solo_bot.cli.run_experiments.MODULE_DEFINITIONS",
            {**MODULE_DEFINITIONS, extra_module: next(iter(MODULE_DEFINITIONS.values()))},
        ):
            with patch(
                "src.nature_solo_bot.cli.run_experiments.BatchRunner"
            ) as runner:
                runner.return_value.run.return_value = []
                exit_code = RunExperiments.run(
                    [
                        "--module",
                        "bamboo_grove",
                        extra_module,
                        "--module-promo",
                        "bamboo_grove",
                        "--games",
                        "1",
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            runner.call_args.kwargs["modules"],
            ["bamboo_grove", extra_module],
        )
        self.assertEqual(runner.call_args.kwargs["promo_modules"], ["bamboo_grove"])
        runner.return_value.run.assert_called_once_with(
            str(
                Path("output")
                / "Nature"
                / "medium"
                / "promo"
                / "bamboo_grove+test_module"
            )
        )

    def test_batch_runner_passes_modules_to_each_engine(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch("src.nature_solo_bot.experiments.batch_runner.GameEngine") as engine:
                with patch("src.nature_solo_bot.experiments.batch_runner.GameLogger"):
                    BatchRunner(
                        game_count=1,
                        modules=["bamboo_grove"],
                        promo_modules=["bamboo_grove"],
                        nature_promo=False,
                    ).run(temporary_directory)

        engine.assert_called_once()
        self.assertEqual(
            engine.call_args.kwargs["modules"],
            ["bamboo_grove"],
        )
        self.assertEqual(
            engine.call_args.kwargs["promo_modules"],
            {"bamboo_grove"},
        )
        self.assertFalse(engine.call_args.kwargs["nature_promo"])

    def test_main_uses_supplied_cli_options_instead_of_run_loop(self):
        with patch(
            "src.nature_solo_bot.cli.run_experiments.sys.argv",
            ["run_experiments", "--games", "1"],
        ):
            with patch.object(RunExperiments, "run", return_value=0) as run:
                with patch.object(RunExperiments, "run_loop") as run_loop:
                    self.assertEqual(main(), 0)

        run.assert_called_once_with()
        run_loop.assert_not_called()

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
                "promo" if "--nature-promo" in args else "core",
            )


if __name__ == "__main__":
    unittest.main()
