"""Game state snapshot for the Nature-like solo board game."""


from dataclasses import dataclass
from enum import Enum

from .solo_species import SoloSpecies
from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.player import Player

class GamePhase(Enum):
    PREPARATION = "preparation"
    ADAPTATION = "adaptation"
    FEEDING = "feeding"
    SCORING = "scoring"


@dataclass(frozen=True, slots=True)
class Difficulty:
    """Starting-game settings controlled by the selected difficulty."""

    round_one_population: int
    cards_to_draw: int


DIFFICULTY_EASIEST = Difficulty(round_one_population=1, cards_to_draw=5)
DIFFICULTY_EASY = Difficulty(round_one_population=2, cards_to_draw=6)
DIFFICULTY_MEDIUM = Difficulty(round_one_population=3, cards_to_draw=7)
DIFFICULTY_HARD = Difficulty(round_one_population=4, cards_to_draw=8)
DIFFICULTY_HARDEST = Difficulty(round_one_population=5, cards_to_draw=9)


class GameState:
    """Stores a complete snapshot of a game at any moment in time."""

    def __init__(self, difficulty: Difficulty = DIFFICULTY_MEDIUM):
        """Initialize a fresh game state."""
        self.current_round: int = 0
        self.total_rounds: int = 4
        self.current_phase: GamePhase = GamePhase.PREPARATION
        self.number_players: int = 2
        self.players: list[Player] = []
        self.active_player_index: int = 0
        self.nature_deck: list[Card] = []
        self.nature_discard: list[Card] | None = []
        self.turn_history: list = []
        self.food_card : Card | None = None
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
