"""Command-line entry point for summarizing trait assignments in game logs."""

import argparse
import csv
from pathlib import Path
from typing import TypeAlias

from ..analysis import (
    SoloSpeciesStats,
    TraitAssignmentCounts,
    TraitAssignmentParser,
    TraitCombinationStats,
    TraitRoundFoodStats,
)

AnalysisCounts: TypeAlias = (
    dict[str, TraitAssignmentCounts]
    | dict[str, dict[int, TraitRoundFoodStats]]
    | dict[tuple[str, ...], TraitCombinationStats]
    | dict[str, SoloSpeciesStats]
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
        combination_name = "No traits" if not combination else " + ".join(combination)
        writer.writerow(
            (
                combination_name,
                stats.species_rounds_present,
                stats.times_extinct,
                stats.total_food,
                f"{stats.average_food_per_round:.2f}",
                stats.total_population_at_start_of_feeding,
                stats.total_lost_population,
            )
        )


def _write_solo_species_csv(
    writer,
    counts: dict[str, SoloSpeciesStats],
) -> None:
    writer.writerow(
        (
            "solo_species",
            "species_rounds_present",
            "times_extinct",
            "total_food",
            "average_food_per_species_round",
            "total_population_at_start_of_feeding",
            "total_lost_population",
        )
    )
    for solo_species, stats in counts.items():
        writer.writerow(
            (
                solo_species,
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
        combination_name = "No traits" if not combination else " + ".join(combination)
        print(
            f"{combination_name} | {stats.species_rounds_present} | "
            f"{stats.times_extinct} | {stats.total_food} | "
            f"{stats.average_food_per_round:.2f} | "
            f"{stats.total_population_at_start_of_feeding} | "
            f"{stats.total_lost_population}"
        )


def _print_solo_species_counts(counts: dict[str, SoloSpeciesStats]) -> None:
    print(
        "Solo species | Species-rounds present | Extinctions | Total food | "
        "Average food/species-round | Starting population | Population lost"
    )
    for solo_species, stats in counts.items():
        print(
            f"{solo_species} | {stats.species_rounds_present} | "
            f"{stats.times_extinct} | {stats.total_food} | "
            f"{stats.average_food_per_round:.2f} | "
            f"{stats.total_population_at_start_of_feeding} | "
            f"{stats.total_lost_population}"
        )


def _parse_counts(options: argparse.Namespace) -> AnalysisCounts:
    trait_parser = TraitAssignmentParser()
    if options.solo_species:
        return trait_parser.parse_solo_species(options.log_directory)
    if options.trait_combinations:
        return trait_parser.parse_trait_combinations(options.log_directory)
    if options.food_by_trait:
        return trait_parser.parse_food_by_trait(options.log_directory)
    return trait_parser.parse_folder(options.log_directory)


def _save_counts(options: argparse.Namespace, counts: AnalysisCounts) -> None:
    if options.output is None:
        return

    options.output.parent.mkdir(parents=True, exist_ok=True)
    with options.output.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file)
        if options.solo_species:
            _write_solo_species_csv(writer, counts)
        elif options.trait_combinations:
            _write_combination_csv(writer, counts)
        elif options.food_by_trait:
            _write_food_csv(writer, counts)
        else:
            _write_assignment_csv(writer, counts)


def _display_counts(options: argparse.Namespace, counts: AnalysisCounts) -> None:
    if options.solo_species:
        _print_solo_species_counts(counts)
    elif options.trait_combinations:
        _print_combination_counts(counts)
    elif options.food_by_trait:
        _print_food_counts(counts)
    else:
        _print_assignment_counts(counts)


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
    analysis_group.add_argument(
        "--solo-species",
        action="store_true",
        help="report round, extinction, food, and population stats by Solo species card",
    )
    options = parser.parse_args()

    try:
        counts = _parse_counts(options)
    except ValueError as error:
        parser.error(str(error))

    _save_counts(options, counts)
    _display_counts(options, counts)

    if options.output is not None:
        print(f"CSV saved to {options.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
