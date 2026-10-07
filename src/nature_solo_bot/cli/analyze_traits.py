"""Command-line entry point for summarizing trait assignments in game logs."""

import argparse
import csv
from pathlib import Path

from ..analysis import TraitAssignmentParser


def main() -> int:
    """Parse game logs and print or export trait assignment counts."""
    parser = argparse.ArgumentParser(
        description="Count trait assignments by winner and loser across game logs."
    )
    parser.add_argument(
        "log_directory",
        type=Path,
        help="folder containing game logs; subfolders are searched recursively",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="also save the count table as a CSV file",
    )
    options = parser.parse_args()

    try:
        counts = TraitAssignmentParser().parse_folder(options.log_directory)
    except ValueError as error:
        parser.error(str(error))

    if options.output is not None:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        with options.output.open("w", encoding="utf-8", newline="") as output_file:
            writer = csv.writer(output_file)
            writer.writerow(
                ("trait", "winner_assignments", "loser_assignments", "tied_assignments")
            )
            for trait, trait_counts in counts.items():
                writer.writerow(
                    (
                        trait,
                        trait_counts.winner,
                        trait_counts.loser,
                        trait_counts.tied,
                    )
                )

    print("Trait | Winner assignments | Loser assignments | Tied-game assignments")
    for trait, trait_counts in counts.items():
        print(
            f"{trait} | {trait_counts.winner} | {trait_counts.loser} | "
            f"{trait_counts.tied}"
        )

    if options.output is not None:
        print(f"CSV saved to {options.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
