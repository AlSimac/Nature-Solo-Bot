"""Count trait assignments and feeding outcomes across game logs."""

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

_ASSIGNMENT_PATTERN = re.compile(r"^\s*(?P<player>[^:]+): .* -> S\d+ trait '(?P<trait>[^']+)'$")
_ROUND_PATTERN = re.compile(r"^ROUND (?P<round>\d+) - (?P<phase>[A-Z]+)$")
_SPECIES_BOARD_PATTERN = re.compile(
    r"^\s+(?P<species>S\d+) .+ population=(?P<population>\d+), " r"traits=\[(?P<traits>[^]]*)\]"
)
_SOLO_SPECIES_BOARD_PATTERN = re.compile(
    r"^\s+(?P<species>S\d+) (?P<solo_species>.+?) \(.*?population="
    r"(?P<population>\d+), traits=\["
)
_FOOD_EATEN_PATTERN = re.compile(
    r"\b(?P<species>S\d+) ate (?P<amount>\d+) "
    r"(?P<food_type>plant|meat|bamboo) food\b"
)
_FEEDING_SUMMARY_PATTERN = re.compile(
    r"^\s+[^:]+:\s+(?P<species>S\d+) (?P<solo_species>.+?) ate "
    r"(?P<amount>\d+) food \((?P<plant>\d+) plant, (?P<meat>\d+) meat"
    r"(?:, (?P<bamboo>\d+) bamboo)?\); population "
    r"\d+ to (?P<population>\d+|extinct)$"
)


@dataclass(slots=True)
class TraitAssignmentCounts:
    """Number of times a trait was assigned by winners and by losers."""

    winner: int = 0
    loser: int = 0
    tied: int = 0


@dataclass(slots=True)
class TraitRoundFoodStats:
    """Species count and cumulative food types for one trait in one round."""

    species_count: int = 0
    total_food: int = 0
    total_plant_food: int = 0
    total_meat_food: int = 0
    total_bamboo_food: int = 0

    @property
    def average_food(self) -> float:
        """Average food eaten per species carrying the trait that round."""
        if self.species_count == 0:
            return 0.0
        return self.total_food / self.species_count


@dataclass(slots=True)
class TraitCombinationStats:
    """Round, feeding, extinction, and population totals for one combination."""

    species_rounds_present: int = 0
    times_extinct: int = 0
    total_food: int = 0
    total_plant_food: int = 0
    total_meat_food: int = 0
    total_bamboo_food: int = 0
    total_population_at_start_of_feeding: int = 0
    total_lost_population: int = 0

    @property
    def average_food_per_round(self) -> float:
        """Average food eaten by a species carrying this combination per round."""
        if self.species_rounds_present == 0:
            return 0.0
        return self.total_food / self.species_rounds_present

    @property
    def average_lost_population(self) -> float:
        """Average lost population by a species carrying this combination per round."""
        if self.species_rounds_present == 0:
            return 0.0

        return self.total_lost_population / self.species_rounds_present

    @property
    def extinction_rate(self) -> float:
        """Extinction rate of a species carrying this combination per round."""
        if self.species_rounds_present == 0:
            return 0.0

        return self.times_extinct / self.species_rounds_present


@dataclass(slots=True)
class SoloSpeciesStats:
    """Round, feeding, extinction, and population totals for one Solo species."""

    species_rounds_present: int = 0
    times_extinct: int = 0
    total_food: int = 0
    total_plant_food: int = 0
    total_meat_food: int = 0
    total_bamboo_food: int = 0
    total_population_at_start_of_feeding: int = 0
    total_lost_population: int = 0

    @property
    def average_food_per_round(self) -> float:
        """Average food eaten by a species per round it was present."""
        if self.species_rounds_present == 0:
            return 0.0
        return self.total_food / self.species_rounds_present

    @property
    def average_lost_population(self) -> float:
        """Average lost population by a species carrying this combination per round."""
        if self.species_rounds_present == 0:
            return 0.0

        return self.total_lost_population / self.species_rounds_present

    @property
    def extinction_rate(self) -> float:
        """Extinction rate of a species carrying this combination per round."""
        if self.species_rounds_present == 0:
            return 0.0

        return self.times_extinct / self.species_rounds_present


@dataclass(slots=True)
class _FoodTotals:
    plant: int = 0
    meat: int = 0
    bamboo: int = 0

    @property
    def total(self) -> int:
        return self.plant + self.meat + self.bamboo

    def add(self, food_type: str, amount: int) -> None:
        setattr(self, food_type, getattr(self, food_type) + amount)


class TraitAssignmentParser:
    """Aggregate successful trait assignments across game log files."""

    def parse_folder(self, folder: str | Path) -> dict[str, TraitAssignmentCounts]:
        """Parse game logs under ``folder``, recursively, and count assignments.

        Counts traits attached during adaptation and traits granted by solo
        species during the first preparation. Merely having or triggering a
        trait is not counted as a new assignment.
        """
        directory = Path(folder)
        if not directory.is_dir():
            raise ValueError(f"Log folder does not exist or is not a directory: {directory}")

        log_paths = sorted(directory.rglob("gamelog_*.log"))
        if not log_paths:
            raise ValueError(f"No game log files found under: {directory}")

        totals: defaultdict[str, TraitAssignmentCounts] = defaultdict(TraitAssignmentCounts)
        for log_path in log_paths:
            self._parse_log(log_path, totals)

        return dict(sorted(totals.items()))

    def parse_food_by_trait(
        self,
        folder: str | Path,
    ) -> dict[str, dict[int, TraitRoundFoodStats]]:
        """Aggregate trait-bearing species and their food eaten, by round.

        A species qualifies if it has one or more copies of a trait on its
        board at the end of adaptation.         Food is summed across that species' plant, meat, and bamboo food actions
        in the same round. Qualifying species that
        eat no food are included in the average with a food total of zero.
        """
        directory = Path(folder)
        if not directory.is_dir():
            raise ValueError(f"Log folder does not exist or is not a directory: {directory}")

        log_paths = sorted(directory.rglob("gamelog_*.log"))
        if not log_paths:
            raise ValueError(f"No game log files found under: {directory}")

        totals: defaultdict[str, defaultdict[int, TraitRoundFoodStats]] = defaultdict(
            lambda: defaultdict(TraitRoundFoodStats)
        )
        round_numbers: set[int] = set()
        for log_path in log_paths:
            round_numbers.update(self._parse_food_log(log_path, totals))

        return {
            trait: {round_number: rounds[round_number] for round_number in sorted(round_numbers)}
            for trait, rounds in sorted(totals.items())
        }

    def parse_trait_combinations(
        self,
        folder: str | Path,
    ) -> dict[tuple[str, ...], TraitCombinationStats]:
        """Aggregate exact trait combinations across all logged species-rounds.

        Each species-round counts once, including species with no traits (the
        empty tuple). Repeated copies of a trait are preserved as part of the
        combination (for example, ``("Fast", "Fast")`` is distinct from
        ``("Fast",)``). Population loss is the difference between population
        after adaptation and the surviving population after feeding; an extinct
        species has zero surviving population.
        """
        directory = Path(folder)
        if not directory.is_dir():
            raise ValueError(f"Log folder does not exist or is not a directory: {directory}")

        log_paths = sorted(directory.rglob("gamelog_*.log"))
        if not log_paths:
            raise ValueError(f"No game log files found under: {directory}")

        totals: defaultdict[tuple[str, ...], TraitCombinationStats] = defaultdict(
            TraitCombinationStats
        )
        for log_path in log_paths:
            self._parse_combination_log(log_path, totals)
        return dict(sorted(totals.items()))

    def parse_solo_species(
        self,
        folder: str | Path,
    ) -> dict[str, SoloSpeciesStats]:
        """Aggregate round, food, extinction, and population stats per Solo card."""
        directory = Path(folder)
        if not directory.is_dir():
            raise ValueError(f"Log folder does not exist or is not a directory: {directory}")

        log_paths = sorted(directory.rglob("gamelog_*.log"))
        if not log_paths:
            raise ValueError(f"No game log files found under: {directory}")

        totals: defaultdict[str, SoloSpeciesStats] = defaultdict(SoloSpeciesStats)
        for log_path in log_paths:
            self._parse_solo_species_log(log_path, totals)
        return dict(sorted(totals.items()))

    @staticmethod
    def _parse_log(
        log_path: Path,
        totals: defaultdict[str, TraitAssignmentCounts],
    ) -> None:
        players, winner, assignment_lines = TraitAssignmentParser._read_log(log_path)
        if len(players) != 2 or len(set(players)) != 2 or not all(players):
            raise ValueError(f"Expected two player names in {log_path}")
        if winner != "None" and winner not in players:
            raise ValueError(f"Winner is missing or does not match Players in {log_path}")

        loser = next((player for player in players if player != winner), None)
        for line_number, player, trait in assignment_lines:
            if player not in players:
                raise ValueError(
                    f"Unknown assigning player {player!r} on " f"{log_path}:{line_number}"
                )
            if winner == "None":
                totals[trait].tied += 1
            elif player == winner:
                totals[trait].winner += 1
            elif player == loser:
                totals[trait].loser += 1

    @staticmethod
    def _read_log(
        log_path: Path,
    ) -> tuple[list[str], str, list[tuple[int, str, str]]]:
        players: list[str] | None = None
        winner: str | None = None
        assignment_lines: list[tuple[int, str, str]] = []
        reading_initial_preparation = False
        initial_preparation_read = False
        current_player: str | None = None

        for line_number, line in enumerate(
            log_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            round_match = _ROUND_PATTERN.match(line)
            if round_match is not None:
                reading_initial_preparation = (
                    not initial_preparation_read
                    and round_match.group("round") == "1"
                    and round_match.group("phase") == "PREPARATION"
                )
                if reading_initial_preparation:
                    initial_preparation_read = True
                current_player = None

            if line.startswith("Players: "):
                players = [name.strip() for name in line.removeprefix("Players: ").split(",")]
            elif line.startswith("Winner: "):
                winner = line.removeprefix("Winner: ").strip()

            if reading_initial_preparation:
                player_match = re.match(r"^\s*(?P<player>[^:]+) hand:", line)
                if player_match is not None:
                    current_player = player_match.group("player").strip()
                else:
                    species_match = _SPECIES_BOARD_PATTERN.match(line)
                    if species_match is not None and current_player is not None:
                        assignment_lines.extend(
                            (line_number, current_player, trait.strip())
                            for trait in species_match.group("traits").split(",")
                            if trait.strip() and trait.strip().lower() != "none"
                        )

            match = _ASSIGNMENT_PATTERN.match(line)
            if match is not None:
                assignment_lines.append(
                    (
                        line_number,
                        match.group("player").strip(),
                        match.group("trait"),
                    )
                )

        if players is None:
            raise ValueError(f"Expected two player names in {log_path}")
        if winner is None:
            raise ValueError(f"Winner is missing or does not match Players in {log_path}")
        return players, winner, assignment_lines

    @staticmethod
    def _parse_food_log(
        log_path: Path,
        totals: defaultdict[str, defaultdict[int, TraitRoundFoodStats]],
    ) -> set[int]:
        sections = TraitAssignmentParser._read_round_sections(log_path)
        round_numbers = set(sections)
        if any(
            "ADAPTATION" not in round_sections or "FEEDING" not in round_sections
            for round_sections in sections.values()
        ):
            raise ValueError(f"Incomplete adaptation or feeding data in {log_path}")

        for round_number, round_sections in sections.items():
            traits_by_species = TraitAssignmentParser._read_adaptation_traits(
                round_sections["ADAPTATION"]
            )
            food_by_species = TraitAssignmentParser._read_food_totals(round_sections["FEEDING"])
            for species_id, trait_names in traits_by_species.items():
                for trait in trait_names:
                    stats = totals[trait][round_number]
                    stats.species_count += 1
                    species_food = food_by_species[species_id]
                    stats.total_food += species_food.total
                    stats.total_plant_food += species_food.plant
                    stats.total_meat_food += species_food.meat
                    stats.total_bamboo_food += species_food.bamboo

        if not round_numbers:
            raise ValueError(f"No round data found in {log_path}")
        return round_numbers

    @staticmethod
    def _read_round_sections(log_path: Path) -> dict[int, dict[str, list[str]]]:
        lines = log_path.read_text(encoding="utf-8").splitlines()
        sections: defaultdict[int, dict[str, list[str]]] = defaultdict(dict)
        current_round: int | None = None
        phase: str | None = None
        for line in lines:
            round_match = _ROUND_PATTERN.match(line)
            if round_match is not None:
                current_round = int(round_match.group("round"))
                phase = round_match.group("phase")
            elif current_round is not None and phase is not None:
                sections[current_round].setdefault(phase, []).append(line)
        return dict(sections)

    @staticmethod
    def _read_adaptation_traits(lines: list[str]) -> dict[str, set[str]]:
        traits_by_species: dict[str, set[str]] = {}
        reading_board = False
        for line in lines:
            if line == "Species at the end of adaptation:":
                reading_board = True
                continue
            if not reading_board:
                continue

            match = _SPECIES_BOARD_PATTERN.match(line)
            if match is not None:
                traits_by_species[match.group("species")] = {
                    trait.strip()
                    for trait in match.group("traits").split(",")
                    if trait.strip() and trait.strip().lower() != "none"
                }
        return traits_by_species

    @staticmethod
    def _read_food_totals(lines: list[str]) -> defaultdict[str, _FoodTotals]:
        food_by_species: defaultdict[str, _FoodTotals] = defaultdict(_FoodTotals)
        for line in lines:
            match = _FEEDING_SUMMARY_PATTERN.match(line)
            if match is not None:
                food_totals = food_by_species[match.group("species")]
                food_totals.plant += int(match.group("plant"))
                food_totals.meat += int(match.group("meat"))
                food_totals.bamboo += int(match.group("bamboo") or 0)
                continue
            for match in _FOOD_EATEN_PATTERN.finditer(line):
                food_by_species[match.group("species")].add(
                    match.group("food_type"),
                    int(match.group("amount")),
                )
        return food_by_species

    @staticmethod
    def _read_species_states(
        lines: list[str],
    ) -> dict[str, tuple[tuple[str, ...], int]]:
        states: dict[str, tuple[tuple[str, ...], int]] = {}
        for line in lines:
            summary_match = _FEEDING_SUMMARY_PATTERN.match(line)
            if summary_match is not None:
                population = summary_match.group("population")
                if population != "extinct":
                    states[summary_match.group("species")] = ((), int(population))
                continue

            match = _SPECIES_BOARD_PATTERN.match(line)
            if match is None:
                continue
            traits = tuple(
                sorted(
                    trait.strip()
                    for trait in match.group("traits").split(",")
                    if trait.strip() and trait.strip().lower() != "none"
                )
            )
            states[match.group("species")] = (
                traits,
                int(match.group("population")),
            )
        return states

    @staticmethod
    def _parse_combination_log(
        log_path: Path,
        totals: defaultdict[tuple[str, ...], TraitCombinationStats],
    ) -> None:
        sections = TraitAssignmentParser._read_round_sections(log_path)
        if not sections:
            raise ValueError(f"No round data found in {log_path}")

        for round_number, round_sections in sections.items():
            if "ADAPTATION" not in round_sections or "FEEDING" not in round_sections:
                raise ValueError(
                    f"Incomplete adaptation or feeding data in {log_path} "
                    f"for round {round_number}"
                )
            if "Species at the end of adaptation:" not in round_sections["ADAPTATION"]:
                raise ValueError(
                    f"Missing post-adaptation species board in {log_path}, " f"round {round_number}"
                )
            if not any(
                line.startswith("Watering hole after feeding:")
                for line in round_sections["FEEDING"]
            ):
                raise ValueError(
                    f"Missing completed feeding phase in {log_path}, round {round_number}"
                )
            starting_species = TraitAssignmentParser._read_species_states(
                round_sections["ADAPTATION"]
            )
            surviving_species = TraitAssignmentParser._read_species_states(
                round_sections["FEEDING"]
            )
            food_by_species = TraitAssignmentParser._read_food_totals(round_sections["FEEDING"])

            for species_id, (combination, starting_population) in starting_species.items():
                surviving_state = surviving_species.get(species_id)
                surviving_population = surviving_state[1] if surviving_state is not None else 0
                stats = totals[combination]
                stats.species_rounds_present += 1
                species_food = food_by_species[species_id]
                stats.total_food += species_food.total
                stats.total_plant_food += species_food.plant
                stats.total_meat_food += species_food.meat
                stats.total_bamboo_food += species_food.bamboo
                stats.total_population_at_start_of_feeding += starting_population
                stats.total_lost_population += max(
                    0,
                    starting_population - surviving_population,
                )
                if surviving_state is None:
                    stats.times_extinct += 1

    @staticmethod
    def _read_solo_species_states(
        lines: list[str],
    ) -> dict[str, tuple[str, int]]:
        states: dict[str, tuple[str, int]] = {}
        for line in lines:
            summary_match = _FEEDING_SUMMARY_PATTERN.match(line)
            if summary_match is not None:
                population = summary_match.group("population")
                if population != "extinct":
                    states[summary_match.group("species")] = (
                        summary_match.group("solo_species"),
                        int(population),
                    )
                continue

            match = _SOLO_SPECIES_BOARD_PATTERN.match(line)
            if match is not None:
                states[match.group("species")] = (
                    match.group("solo_species"),
                    int(match.group("population")),
                )
        return states

    @staticmethod
    def _parse_solo_species_log(
        log_path: Path,
        totals: defaultdict[str, SoloSpeciesStats],
    ) -> None:
        sections = TraitAssignmentParser._read_round_sections(log_path)
        if not sections:
            raise ValueError(f"No round data found in {log_path}")

        for round_number, round_sections in sections.items():
            if "ADAPTATION" not in round_sections or "FEEDING" not in round_sections:
                raise ValueError(
                    f"Incomplete adaptation or feeding data in {log_path} "
                    f"for round {round_number}"
                )
            if "Species at the end of adaptation:" not in round_sections["ADAPTATION"]:
                raise ValueError(
                    f"Missing post-adaptation species board in {log_path}, " f"round {round_number}"
                )
            if not any(
                line.startswith("Watering hole after feeding:")
                for line in round_sections["FEEDING"]
            ):
                raise ValueError(
                    f"Missing completed feeding phase in {log_path}, round {round_number}"
                )

            starting_species = TraitAssignmentParser._read_solo_species_states(
                round_sections["ADAPTATION"]
            )
            surviving_species = TraitAssignmentParser._read_solo_species_states(
                round_sections["FEEDING"]
            )
            food_by_species = TraitAssignmentParser._read_food_totals(round_sections["FEEDING"])

            for species_id, (solo_species, starting_population) in starting_species.items():
                surviving_state = surviving_species.get(species_id)
                surviving_population = surviving_state[1] if surviving_state else 0
                stats = totals[solo_species]
                stats.species_rounds_present += 1
                species_food = food_by_species[species_id]
                stats.total_food += species_food.total
                stats.total_plant_food += species_food.plant
                stats.total_meat_food += species_food.meat
                stats.total_bamboo_food += species_food.bamboo
                stats.total_population_at_start_of_feeding += starting_population
                stats.total_lost_population += max(
                    0,
                    starting_population - surviving_population,
                )
                if surviving_state is None:
                    stats.times_extinct += 1
