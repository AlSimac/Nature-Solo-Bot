"""Action application stub."""


from nature_solo_bot.game.model.player import Player
from nature_solo_bot.game.model.state import GameState
from nature_solo_bot.game.model.trait_card import TraitCard


class ActionApplier:
    """Applies a selected action to the current game state."""

    def discard_card_for_watering_hole(state: GameState, player: Player):
        """ Discard a card to add food to the watering hole"""
        discarded_card = player.hand.pop()
        state.nature_discard.append(discarded_card)
        state.watering_hole_plants += discarded_card.food_value