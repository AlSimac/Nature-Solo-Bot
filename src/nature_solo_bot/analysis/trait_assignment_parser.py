"""Count trait assignments by game outcome across detailed game logs."""

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

_ASSIGNMENT_PATTERN = re.compile(
    r"^\s*(?P<player>[^:]+): .* -> S\d+ trait '(?P<trait>[^']+)'$"
)


@dataclass(slots=True)
class TraitAssignmentCounts:
    """Number of times a trait was assigned by winners and by losers."""

    winner: int = 0
    loser: int = 0
    tied: int = 0


class TraitAssignmentParser:
    """Aggregate successful trait assignments across game log files."""

    def parse_folder(self, folder: str | Path) -> dict[str, TraitAssignmentCounts]:
        """Parse game logs under ``folder``, recursively, and count assignments.

        An assignment is counted when an adaptation log line shows a trait
        attached to a species. Merely having or triggering a trait is not
        counted as a new assignment.
        """
        directory = Path(folder)
        if not directory.is_dir():
            raise ValueError(f"Log folder does not exist or is not a directory: {directory}")

        log_paths = sorted(directory.rglob("gamelog_*.log"))
        if not log_paths:
            raise ValueError(f"No game log files found under: {directory}")

        totals: defaultdict[str, TraitAssignmentCounts] = defaultdict(
            TraitAssignmentCounts
        )
        for log_path in log_paths:
            self._parse_log(log_path, totals)

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
                    f"Unknown assigning player {player!r} on "
                    f"{log_path}:{line_number}"
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

        for line_number, line in enumerate(
            log_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if line.startswith("Players: "):
                players = [name.strip() for name in line.removeprefix("Players: ").split(",")]
            elif line.startswith("Winner: "):
                winner = line.removeprefix("Winner: ").strip()

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
