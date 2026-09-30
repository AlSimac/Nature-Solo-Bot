"""Action resolution rules stub."""


from nature_solo_bot.game.model.player import Player
from nature_solo_bot.game.model.species import Species
from nature_solo_bot.game.model.state import GameState


class Resolution:
    """Applies actions and resolves their effects."""

    def forage(state: GameState, player: Player, forager: Species):
        pass

    def hunt(state: GameState, player: Player, hunter: Species, prey: Species):
        pass
        
