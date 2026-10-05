"""Action resolution rules stub."""

from nature_solo_bot.engine.game_engine import GameEngine
from nature_solo_bot.game.model.player import Player
from nature_solo_bot.game.model.species import Species
from nature_solo_bot.game.model.state import GameState
from nature_solo_bot.game.rules.feeding import FeedingRules


class Resolution:
    """Applies actions and resolves their effects."""
