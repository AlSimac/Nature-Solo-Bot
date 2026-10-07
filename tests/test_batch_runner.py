"""Tests for running and exporting game batches."""

import csv
import json
from pathlib import Path
import tempfile
import unittest

from src.nature_solo_bot.experiments import BatchRunner
from src.nature_solo_bot.game.model.state import DIFFICULTY_EASY


class BatchRunnerTest(unittest.TestCase):
    def test_run_writes_each_game_and_setting_to_csv(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "nested" / "results.csv"
            runner = BatchRunner(
                game_count=3,
                start_seed=10,
                difficulty=DIFFICULTY_EASY,
                promo=True,
            )

            records = runner.run(output_path)

            with output_path.open(encoding="utf-8", newline="") as output_file:
                rows = list(csv.DictReader(output_file))

        self.assertEqual(len(records), 3)
        self.assertEqual([row["seed"] for row in rows], ["10", "11", "12"])
        self.assertEqual([row["game_number"] for row in rows], ["1", "2", "3"])
        self.assertEqual(rows[0]["game_count"], "3")
        self.assertEqual(rows[0]["difficulty_round_one_population"], "2")
        self.assertEqual(rows[0]["difficulty_cards_to_draw"], "6")
        self.assertEqual(rows[0]["promo"], "True")
        self.assertIn("score_Rani", rows[0])
        self.assertIn("score_Radwin", rows[0])
        self.assertIn(rows[0]["winner"], ("Rani", "Radwin"))

    def test_run_writes_json_results(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "results.json"
            records = BatchRunner(game_count=2).run(output_path)
            saved_records = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved_records, records)
        self.assertEqual([record["seed"] for record in saved_records], [1, 2])
        self.assertEqual([record["game_number"] for record in saved_records], [1, 2])
        self.assertTrue(all("score_Rani" in record for record in saved_records))
        self.assertTrue(all("score_Radwin" in record for record in saved_records))

    def test_run_rejects_unsupported_output_format(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "results.txt"

            with self.assertRaisesRegex(ValueError, "output_format"):
                BatchRunner(game_count=1).run(output_path)

    def test_constructor_rejects_nonpositive_game_count(self):
        with self.assertRaisesRegex(ValueError, "game_count"):
            BatchRunner(game_count=0)


if __name__ == "__main__":
    unittest.main()
