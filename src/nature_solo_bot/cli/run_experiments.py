"""Command-line entry point for running simulation batches."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from ..experiments import BatchRunner
from ..game.model.state import Difficulty


class RunExperiments:
    """Parse command-line options and run a simulation batch."""

    @staticmethod
    def run(arguments: Sequence[str] | None = None) -> int:
        parser = argparse.ArgumentParser(
            description="Run a batch of Nature Solo games and log each game."
        )
        parser.add_argument(
            "--games",
            type=int,
            default=10000,
            help="number of games to run (default: 10000)",
        )
        parser.add_argument(
            "--start-seed",
            type=int,
            default=1,
            help="seed for the first game; subsequent games use consecutive seeds",
        )
        parser.add_argument(
            "--difficulty",
            choices=("easiest", "easy", "medium", "hard", "hardest"),
            default="medium",
            help="game difficulty (default: medium)",
        )
        parser.add_argument(
            "--promo",
            action="store_true",
            help="include Promo cards",
        )
        parser.add_argument(
            "--output-dir",
            help="directory for game logs (defaults to output/Nature/<difficulty>/<core-or-promo>)",
        )
        options = parser.parse_args(arguments)
        if options.games <= 0:
            parser.error("--games must be greater than zero")

        difficulties = {
            "easiest": Difficulty.EASIEST,
            "easy": Difficulty.EASY,
            "medium": Difficulty.MEDIUM,
            "hard": Difficulty.HARD,
            "hardest": Difficulty.HARDEST,
        }
        output_directory = options.output_dir or str(
            Path("output")
            / "Nature"
            / options.difficulty
            / ("promo" if options.promo else "core")
        )
        log_paths = BatchRunner(
            game_count=options.games,
            start_seed=options.start_seed,
            difficulty=difficulties[options.difficulty],
            promo=options.promo,
        ).run(output_directory)
        print(f"Saved {len(log_paths)} game logs to {output_directory}")
        return 0

    @staticmethod
    def run_loop() -> int:
        """Run batches for every difficulty, both with and without promo cards."""
        for difficulty in Difficulty:
            difficulty_name = difficulty.name.lower()

            for promo in (False, True):
                arguments = [
                    "--difficulty",
                    difficulty_name,
                    "--output-dir",
                    str(
                        Path("output")
                        / "Nature"
                        / difficulty_name
                        / ("promo" if promo else "core")
                    ),
                ]

                if promo:
                    arguments.append("--promo")

                exit_code = RunExperiments.run(arguments)

                if exit_code != 0:
                    return exit_code

        return 0


def main() -> int:
    """Run the CLI using the process command-line arguments."""
    return RunExperiments.run_loop()


if __name__ == "__main__":
    raise SystemExit(main())
