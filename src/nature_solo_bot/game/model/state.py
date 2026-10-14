"""Game state snapshot for the Nature-like solo board game."""

from dataclasses import dataclass
from enum import Enum

from nature_solo_bot.game.model.minimodules import Minimodules

from .card import Card
from .player import Player


class GamePhase(Enum):
    PREPARATION = "preparation"
    ADAPTATION = "adaptation"
    FEEDING = "feeding"
    SCORING = "scoring"


class Difficulty(Enum):
    """Starting-game settings controlled by the selected difficulty."""

    EASIEST = (1, 5)
    EASY = (2, 6)
    MEDIUM = (3, 7)
    HARD = (4, 8)
    HARDEST = (5, 9)

    def __init__(self, round_one_population: int, cards_to_draw: int) -> None:
        self.round_one_population = round_one_population
        self.cards_to_draw = cards_to_draw


class GameState:
    """Stores a complete snapshot of a game at any moment in time."""

    def __init__(
        self, minimodules: list[str] | None = None, difficulty: Difficulty = Difficulty.MEDIUM
    ):
        """Initialize a fresh game state."""
        self.minimodules: list[str] = minimodules
        self.current_round: int = 0
        self.total_rounds: int = 4
        self.current_phase: GamePhase = GamePhase.PREPARATION
        self.number_players: int = 2
        self.players: list[Player] = []
        self.active_player_index: int = 0
        self.nature_deck: list[Card] = []
        self.nature_discard: list[Card] | None = []
        self.turn_history: list = []
        self.food_card: Card | None = None
        self.plant_per_round: int = 0
        self.watering_hole_plant: int = 0
        self.game_over: bool = False
        self.winner: None = None
        self.seed: None = None
        self.scenario_id: None = None
        self.metadata: dict = {}
        self.max_traits = 3
        self.max_size = 4
        self.difficulty = difficulty

        if Minimodules.ELEPHANT_GRAVEYARD in self.minimodules:
            self.elephant_graveyard_meat = 0
