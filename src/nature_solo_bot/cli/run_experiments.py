"""Command-line entry point for running simulation batches."""

import argparse
from collections.abc import Sequence

from ..experiments import BatchRunner
from ..game.model.state import (
    DIFFICULTY_EASIEST,
    DIFFICULTY_EASY,
    DIFFICULTY_HARD,
    DIFFICULTY_HARDEST,
    DIFFICULTY_MEDIUM,
)


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
            default=1000,
            help="number of games to run (default: 1000)",
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
            default="output/core",
            help="directory for game logs (default: output)",
        )
        options = parser.parse_args(arguments)
        if options.games <= 0:
            parser.error("--games must be greater than zero")

        difficulties = {
            "easiest": DIFFICULTY_EASIEST,
            "easy": DIFFICULTY_EASY,
            "medium": DIFFICULTY_MEDIUM,
            "hard": DIFFICULTY_HARD,
            "hardest": DIFFICULTY_HARDEST,
        }
        log_paths = BatchRunner(
            game_count=options.games,
            start_seed=options.start_seed,
            difficulty=difficulties[options.difficulty],
            promo=options.promo,
        ).run(options.output_dir)
        print(f"Saved {len(log_paths)} game logs to {options.output_dir}")
        return 0


def main() -> int:
    """Run the CLI using the process command-line arguments."""
    return RunExperiments.run()


if __name__ == "__main__":
    raise SystemExit(main())
