"""Run reproducible batches of games and export their settings and results."""

import csv
import json
from pathlib import Path
from typing import Literal

from ..engine.game_engine import GameEngine
from ..game.model.state import DIFFICULTY_MEDIUM, Difficulty


class BatchRunner:
    """Run multiple seeded games with shared settings and save each result."""

    def __init__(
        self,
        game_count: int = 1000,
        *,
        start_seed: int = 1,
        difficulty: Difficulty = DIFFICULTY_MEDIUM,
        promo: bool = False,
    ) -> None:
        if game_count <= 0:
            raise ValueError("game_count must be greater than zero.")

        self.game_count = game_count
        self.start_seed = start_seed
        self.difficulty = difficulty
        self.promo = promo

    def run(
        self,
        output_path: str | Path,
        *,
        output_format: Literal["csv", "json"] | None = None,
    ) -> list[dict[str, object]]:
        """Run the configured games and write one record per game.

        When output_format is omitted, the format is inferred from the file
        extension. The records are returned after they have been written.
        """
        path = Path(output_path)
        selected_format = (
            output_format
            if output_format is not None
            else path.suffix.lower().lstrip(".")
        )
        if selected_format not in ("csv", "json"):
            raise ValueError(
                "output_format must be 'csv' or 'json', or the output path "
                "must have a .csv or .json extension."
            )

        records: list[dict[str, object]] = []
        for game_number in range(1, self.game_count + 1):
            seed = self.start_seed + game_number - 1
            engine = GameEngine(
                seed=seed,
                difficulty=self.difficulty,
                promo=self.promo,
            )
            state = engine.run_game()
            winner = engine.define_winner()

            record: dict[str, object] = {
                "game_number": game_number,
                "game_count": self.game_count,
                "seed": seed,
                "difficulty_round_one_population": (
                    self.difficulty.round_one_population
                ),
                "difficulty_cards_to_draw": self.difficulty.cards_to_draw,
                "promo": self.promo,
            }
            record.update(
                {f"score_{player.name}": player.score for player in state.players}
            )
            record["winner"] = winner.name if winner is not None else None
            records.append(record)

        path.parent.mkdir(parents=True, exist_ok=True)
        if selected_format == "csv":
            with path.open("w", encoding="utf-8", newline="") as output_file:
                writer = csv.DictWriter(
                    output_file,
                    fieldnames=list(records[0]),
                )
                writer.writeheader()
                writer.writerows(records)
        else:
            with path.open("w", encoding="utf-8") as output_file:
                json.dump(records, output_file, indent=2)
                output_file.write("\n")

        return records
