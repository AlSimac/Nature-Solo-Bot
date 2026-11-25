"""Run reproducible batches of games and save a detailed log for each game."""

from collections.abc import Callable, Collection
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
        modules: list[str] | None = None,
        promo_modules: Collection[str] | None = None,
        nature_promo: bool = False,
    ) -> None:
        if game_count <= 0:
            raise ValueError("game_count must be greater than zero.")

        self.game_count = game_count
        self.start_seed = start_seed
        self.difficulty = difficulty
        self.modules = list(modules or [])
        self.promo_modules = set(promo_modules or ())
        unsupported_promos = self.promo_modules.difference(self.modules)
        if unsupported_promos:
            raise ValueError(
                "Promo cards requested for modules not in the game: "
                + ", ".join(sorted(unsupported_promos))
            )
        self.nature_promo = nature_promo

    def run(
        self,
        output_directory: str | Path = "output",
        *,
        progress_callback: Callable[[int, int], None] | None = None,
        numbered_logs: bool = False,
    ) -> list[Path]:
        """Run games, save logs, and optionally report progress or number filenames."""
        directory = Path(output_directory)
        directory.mkdir(parents=True, exist_ok=True)
        difficulty_id = _DIFFICULTY_IDS.get(self.difficulty)
        difficulty_label = (
            str(difficulty_id) if difficulty_id is not None else "custom"
        )
        log_paths: list[Path] = []
        for game_number in range(1, self.game_count + 1):
            seed = self.start_seed + game_number - 1
            engine = GameEngine(
                seed=seed,
                difficulty=self.difficulty,
                modules=self.modules,
                promo_modules=self.promo_modules,
                nature_promo=self.nature_promo,
            )
            filename_id = str(game_number) if numbered_logs else uuid4().hex
            log_path = directory / f"gamelog_{difficulty_label}_difficulty_{filename_id}.log"
            GameLogger().run_game(
                engine,
                log_path,
                game_number=game_number,
            )
            log_paths.append(log_path)
            if progress_callback is not None:
                progress_callback(game_number, self.game_count)

        return log_paths
