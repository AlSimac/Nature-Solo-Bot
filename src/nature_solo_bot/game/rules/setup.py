from random import Random

from ..model.card import Card
from ..model.state import GameState


class GameSetup:
    @staticmethod
    def shuffle_all_decks(state: GameState, rng: Random, promo: bool = False) -> None:
        """Shuffle all decks for the game."""
        # Shuffle both players' solo decks
        for player in state.players:
            player.solo_deck = Card.init_solo_deck(state)
            rng.shuffle(player.solo_deck)

        # Prepare and shuffle the trait decks
        state.nature_deck[:] = Card.init_trait_decks(promo=promo)

        for module in state.modules:
            state.module_decks[module].deck[:] = Card.init_trait_decks(promo=promo, module=module)

        for deck in state.all_decks:
            rng.shuffle(deck)
