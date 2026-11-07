"""Game state snapshot for the Nature-like solo board game."""

from dataclasses import dataclass, field
from enum import Enum

from nature_solo_bot.game.model.modules import BAMBOO_GROVE

from .card import NATURE, Card
from .player import Player


class GamePhase(Enum):
    PREPARATION = "preparation"
    ADAPTATION = "adaptation"
    FEEDING = "feeding"
    SCORING = "scoring"


class Difficulty(Enum):
    """Starting-game settings controlled by the selected difficulty."""

    EASIEST = (1, 5, 2)
    EASY = (2, 6, 3)
    MEDIUM = (3, 7, 4)
    HARD = (4, 8, 5)
    HARDEST = (5, 9, 6)

    def __init__(
        self, round_one_population: int, cards_to_draw: int, cards_to_draw_modules: int
    ) -> None:
        self.round_one_population = round_one_population
        self.cards_to_draw = cards_to_draw
        self.cards_to_draw_modules = cards_to_draw_modules


@dataclass
class ModuleDeck:
    """Draw and discard piles belonging to one game module."""

    deck: list[Card] = field(default_factory=list)
    discard: list[Card] = field(default_factory=list)


class GameState:
    """Stores a complete snapshot of a game at any moment in time."""

    def __init__(
        self, difficulty: Difficulty = Difficulty.MEDIUM, modules: list[str] | None = None
    ) -> None:
        """Initialize a fresh game state."""
        # global settings
        self.seed: None = None
        self.max_traits = 3
        self.max_size = 4
        self.difficulty = difficulty
        # rounds and phases
        self.current_round: int = 0
        self.total_rounds: int = 4
        self.current_phase: GamePhase = GamePhase.PREPARATION
        # players
        self.number_players: int = 2
        self.players: list[Player] = []
        self.active_player_index: int = 0
        # decks
        self.modules = list(modules or [])
        self.nature_deck: list[Card] = []
        self.nature_discard: list[Card] | None = []
        # watering hole
        self.food_card: Card | None = None
        self.plant_per_round: int = 0
        self.watering_hole_plant: int = 0
        self.watering_hole_bamboo: int = 0
        # Modules
        self.module_decks: dict[str, ModuleDeck] = {}

        for module in self.modules:
            if module == BAMBOO_GROVE:
                self.module_decks[module] = ModuleDeck()
                self.bamboo_per_round: int = 0
                self.bamboo_grove_deck = self.module_decks[module].deck
                self.bamboo_grove_discard = self.module_decks[module].discard

            else:
                raise ValueError(f"Unsupported game module: {module}")

        self.all_decks: list[list[Card]] = [
            self.nature_deck,
            *(module_deck.deck for module_deck in self.module_decks.values()),
        ]
        # endgame
        self.game_over: bool = False
        self.winner: None = None

    @property
    def total_food(self) -> int:
        return self.watering_hole_plant + self.watering_hole_bamboo

    def trait_discard_pile(self, card: Card) -> list[Card]:
        """Return the discard pile belonging to a trait card's deck."""
        if card.deck == NATURE:
            if self.nature_discard is None:
                raise RuntimeError("The Nature discard pile is not initialized.")
            
            return self.nature_discard

        try:
            return self.module_decks[card.deck].discard
        
        except KeyError as error:
            raise ValueError(
                f"No discard pile is configured for trait deck {card.deck!r}."
            ) from error
