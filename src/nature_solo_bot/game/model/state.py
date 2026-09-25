"""Game state snapshot for the Nature-like solo board game."""


from enum import Enum

from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.player import Player

class GamePhase(Enum):
    PREPARATION = "preparation"
    ADAPTATION = "adaptation"
    FEEDING = "feeding"
    SCORING = "scoring"

class GameState:
    """Stores a complete snapshot of a game at any moment in time."""

    def __init__(self):
        """Initialize a fresh game state."""
        self.current_round: int = 0
        self.current_phase: GamePhase = GamePhase.PREPARATION
        self.number_players: int = 2
        self.players: list[Player] = []
        self.active_player_index: int = 0
        self.deck: list[Card] = []
        self.discard: list[Card] | None = []
        self.turn_history: list = []
        self.food_card : Card | None = None
        self.plant_per_round: int = 0
        self.watering_hole_plant: int = 0
        self.game_over: bool = False
        self.winner: None = None
        self.seed: None = None
        self.scenario_id: None = None
        self.metadata: dict = {}

