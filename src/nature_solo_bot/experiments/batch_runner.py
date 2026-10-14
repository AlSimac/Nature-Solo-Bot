"""Run reproducible batches of games and save a detailed log for each game."""

from pathlib import Path
from uuid import uuid4

from ..analysis.game_logger import GameLogger
from ..engine.game_engine import GameEngine
from ..game.model.state import Difficulty

_DIFFICULTY_IDS = {
    Difficulty.EASIEST: 0,
    Difficulty.EASY: 1,
    Difficulty.MEDIUM: 2,
    Difficulty.HARD: 3,
    Difficulty.HARDEST: 4,
}


class BatchRunner:
    """Run multiple seeded games with shared settings and save each result."""

    def __init__(
        self,
        game_count: int = 1000,
        *,
        start_seed: int = 1,
        difficulty: Difficulty = Difficulty.MEDIUM,
        promo: bool = False,
        minimodules: list[str],
    ) -> None:
        if game_count <= 0:
            raise ValueError("game_count must be greater than zero.")

        self.game_count = game_count
        self.start_seed = start_seed
        self.difficulty = difficulty
        self.promo = promo

    def run(
        self,
        output_directory: str | Path = "output",
    ) -> list[Path]:
        """Run the configured games and save a uniquely named log per game."""
        directory = Path(output_directory)
        directory.mkdir(parents=True, exist_ok=True)
        difficulty_id = _DIFFICULTY_IDS.get(self.difficulty)
        difficulty_label = str(difficulty_id) if difficulty_id is not None else "custom"
        log_paths: list[Path] = []
        for game_number in range(1, self.game_count + 1):
            seed = self.start_seed + game_number - 1
            engine = GameEngine(
                seed=seed,
                difficulty=self.difficulty,
                promo=self.promo,
            )
            log_path = directory / (f"gamelog_{difficulty_label}_{seed}.log")
            GameLogger().run_game(
                engine,
                log_path,
                game_number=game_number,
            )
            log_paths.append(log_path)

        return log_paths
