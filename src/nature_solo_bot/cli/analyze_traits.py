"""Command-line entry point for summarizing trait assignments in game logs."""

import argparse
import csv
from pathlib import Path

from ..analysis import (
    TraitAssignmentCounts,
    TraitAssignmentParser,
    TraitCombinationStats,
    TraitRoundFoodStats,
)


def _write_assignment_csv(writer, counts: dict[str, TraitAssignmentCounts]) -> None:
    writer.writerow(("trait", "winner_assignments", "loser_assignments", "tied_assignments"))
    for trait, trait_counts in counts.items():
        writer.writerow(
            (
                trait,
                trait_counts.winner,
                trait_counts.loser,
                trait_counts.tied,
            )
        )


def _write_food_csv(
    writer,
    counts: dict[str, dict[int, TraitRoundFoodStats]],
) -> None:
    writer.writerow(("trait", "round", "species_count", "total_food", "average_food"))
    for trait, rounds in counts.items():
        for round_number, stats in rounds.items():
            writer.writerow(
                (
                    trait,
                    round_number,
                    stats.species_count,
                    stats.total_food,
                    f"{stats.average_food:.2f}",
                )
            )


def _write_combination_csv(
    writer,
    counts: dict[tuple[str, ...], TraitCombinationStats],
) -> None:
    writer.writerow(
        (
            "trait_combination",
            "species_rounds_present",
            "times_extinct",
            "total_food",
            "average_food_per_species_round",
            "total_population_at_start_of_feeding",
            "total_lost_population",
        )
    )
    for combination, stats in counts.items():
        writer.writerow(
            (
                " + ".join(combination),
                stats.species_rounds_present,
                stats.times_extinct,
                stats.total_food,
                f"{stats.average_food_per_round:.2f}",
                stats.total_population_at_start_of_feeding,
                stats.total_lost_population,
            )
        )


def _print_assignment_counts(counts: dict[str, TraitAssignmentCounts]) -> None:
    print("Trait | Winner assignments | Loser assignments | Tied-game assignments")
    for trait, trait_counts in counts.items():
        print(
            f"{trait} | {trait_counts.winner} | {trait_counts.loser} | "
            f"{trait_counts.tied}"
        )


def _print_food_counts(
    counts: dict[str, dict[int, TraitRoundFoodStats]],
) -> None:
    print("Trait | Round | Species with trait | Total food | Average food")
    for trait, rounds in counts.items():
        for round_number, stats in rounds.items():
            print(
                f"{trait} | {round_number} | {stats.species_count} | "
                f"{stats.total_food} | {stats.average_food:.2f}"
            )


def _print_combination_counts(
    counts: dict[tuple[str, ...], TraitCombinationStats],
) -> None:
    print(
        "Trait combination | Species-rounds present | Extinctions | Total food | "
        "Average food/species-round | Starting population | Population lost"
    )
    for combination, stats in counts.items():
        print(
            f"{' + '.join(combination)} | {stats.species_rounds_present} | "
            f"{stats.times_extinct} | {stats.total_food} | "
            f"{stats.average_food_per_round:.2f} | "
            f"{stats.total_population_at_start_of_feeding} | "
            f"{stats.total_lost_population}"
        )


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
        help="also save the summary as a CSV file",
    )
    analysis_group = parser.add_mutually_exclusive_group()
    analysis_group.add_argument(
        "--food-by-trait",
        action="store_true",
        help="report trait-bearing species counts and their average food by round",
    )
    analysis_group.add_argument(
        "--trait-combinations",
        action="store_true",
        help="report round, extinction, food, and population stats by trait combination",
    )
    options = parser.parse_args()

    try:
        trait_parser = TraitAssignmentParser()
        if options.trait_combinations:
            counts = trait_parser.parse_trait_combinations(options.log_directory)
        elif options.food_by_trait:
            counts = trait_parser.parse_food_by_trait(options.log_directory)
        else:
            counts = trait_parser.parse_folder(options.log_directory)
    except ValueError as error:
        parser.error(str(error))

    if options.output is not None:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        with options.output.open("w", encoding="utf-8", newline="") as output_file:
            writer = csv.writer(output_file)
            if options.trait_combinations:
                _write_combination_csv(writer, counts)
            elif options.food_by_trait:
                _write_food_csv(writer, counts)
            else:
                _write_assignment_csv(writer, counts)

    if options.trait_combinations:
        _print_combination_counts(counts)
    elif options.food_by_trait:
        _print_food_counts(counts)
    else:
        _print_assignment_counts(counts)

    if options.output is not None:
        print(f"CSV saved to {options.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
