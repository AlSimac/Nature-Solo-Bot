"""Action resolution rules stub."""

from ..model.player import Player
from ..model.species import Species
from ..model.state import GameState
from .feeding import FeedingRules


class Resolution:
    """Applies actions and resolves their effects."""
