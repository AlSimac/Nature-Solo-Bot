from collections.abc import Collection
from random import Random

from ..model.card import Card
from ..model.state import GameState


class GameSetup:
    @staticmethod
    def shuffle_all_decks(
        state: GameState,
        rng: Random,
        *,
        promo_modules: Collection[str] | None = None,
        nature_promo: bool = False,
    ) -> None:
        """Shuffle all decks for the game."""
        selected_promo_modules = set(promo_modules or ())
        unsupported_promos = selected_promo_modules.difference(state.modules)
        if unsupported_promos:
            raise ValueError(
                "Promo cards requested for modules not in the game: "
                + ", ".join(sorted(unsupported_promos))
            )

        # Shuffle both players' solo decks
        for player in state.players:
            player.solo_deck = Card.init_solo_deck(state)
            rng.shuffle(player.solo_deck)

        # Prepare and shuffle the trait decks
        state.nature_deck[:] = Card.init_trait_decks(promo=nature_promo)

        for module in state.modules:
            state.module_decks[module].deck[:] = Card.init_trait_decks(
                promo=module in selected_promo_modules,
                module=module,
            )

        for deck in state.all_decks:
            rng.shuffle(deck)
