"""Player model for a Nature-like board game."""


from .solo_species import SoloSpecies
from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.species import Species


class Player:
    """Represents one player in the game, controlled by a deterministic automaton."""

    def __init__(self, name: str, player_id: int | None = None):
        """Initialize a player with a name and identity."""
        self.name: str = name
        self.player_id: int | None = player_id
        self.score: int = 0
        self.species: list[Species] = []
        self.hand: list[Card] = []
        self.solo_deck: list[SoloSpecies] = []
        self.solo_discard: list[SoloSpecies] | None = []
        self.automaton: None = None
        self.winner: bool = False
        self.is_first_player: bool = False
        self.is_active: bool = False
        self.metadata: dict = {}
        

    def init_two_players() -> list["Player"]:
        """Initialize two players for the game."""
        player1 = Player(name="Rani", player_id=1)
        player2 = Player(name="Radwin", player_id=2)
        return [player1, player2]