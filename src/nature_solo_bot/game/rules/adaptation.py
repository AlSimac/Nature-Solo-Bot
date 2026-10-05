from collections.abc import Iterator
from random import Random

from ..model.player import Player
from ..model.species import Species
from ..model.state import GameState
from ..model.symbol import Symbol, SymbolIncrease, SymbolName
from ..model.trait_card import TraitCard
from .preparation import PreparationRules


class AdaptationRules:
    """Rules and automaton decisions for the adaptation phase."""

    @staticmethod
    def select_species_for_symbol(
        player: Player,
        drawn_symbol: SymbolName,
    ) -> list[Species]:
        candidates: list[tuple[int, int, Species]] = []

        for species in player.species:
            for symbol_index, symbol in enumerate(species.solo_symbols):
                if symbol.symbol == drawn_symbol:
                    candidates.append((symbol_index, species.round_created, species))
                    break

        candidates.sort(key=lambda candidate: (candidate[0], candidate[1]))
        return [species for _, _, species in candidates]

    @staticmethod
    def adapt_player(state: GameState, player: Player, rng: Random) -> None:
        """Apply the complete solo adaptation procedure to one player's hand."""
        rng.shuffle(player.hand)
        temporary_hand: list[TraitCard] = []

        if state.current_round == state.total_rounds:
            num_foragers = sum(1 for species in player.species if not species.is_hunter)

            for _ in range(num_foragers):
                temporary_hand.append(player.hand.pop(0))

        while player.hand:
            AdaptationRules.assign_card_to_correct_candidate(
                state, player, temporary_hand, rng
            )

        AdaptationRules._refresh_player_hand(player, temporary_hand, rng)

        if player.species and all(species.is_hunter for species in player.species):
            for increase in (SymbolIncrease.SIZE, SymbolIncrease.POPULATION):
                while player.hand:
                    AdaptationRules.assign_leftover_cards_to_hunters(
                        state, player, temporary_hand, increase
                    )

                AdaptationRules._refresh_player_hand(player, temporary_hand, rng)

    @staticmethod
    def assign_card_to_correct_candidate(
        state: GameState,
        player: Player,
        temporary_hand: list[TraitCard],
        rng: Random,
    ) -> None:
        """Assign the next card to its highest-priority matching species."""
        picked_card = player.hand.pop(0)
        is_assigned = False

        for candidate, candidate_symbol in AdaptationRules._candidate_symbols_for(
            player, picked_card.solo_symbol
        ):
            if candidate_symbol.increase in (
                SymbolIncrease.SIZE,
                SymbolIncrease.POPULATION,
            ):
                candidate_assigned = AdaptationRules._apply_species_increase(
                    state, candidate, picked_card, candidate_symbol.increase
                )
            else:
                candidate_assigned = candidate.add_trait_card(
                    picked_card,
                    max_traits=state.max_traits,
                )

            if not candidate_assigned:
                continue

            if candidate_symbol.is_hunter and not candidate.is_hunter:
                PreparationRules.add_hunter_card(
                    candidate,
                    player,
                    max_traits=state.max_traits,
                    nature_discard=state.nature_discard,
                    rng=rng,
                    replace_random_trait=True,
                )

            is_assigned = True
            break

        if not is_assigned:
            temporary_hand.append(picked_card)

    @staticmethod
    def assign_leftover_cards_to_hunters(
        state: GameState,
        player: Player,
        temporary_hand: list[TraitCard],
        increase: SymbolIncrease,
    ) -> None:
        """Use the next leftover card to increase a matching hunter's size or population."""
        picked_card = player.hand.pop(0)

        for candidate, _ in AdaptationRules._candidate_symbols_for(
            player, picked_card.solo_symbol
        ):
            if AdaptationRules._apply_species_increase(
                state, candidate, picked_card, increase
            ):
                return

        temporary_hand.append(picked_card)

    @staticmethod
    def _refresh_player_hand(
        player: Player,
        temporary_hand: list[TraitCard],
        rng: Random,
    ) -> None:
        player.hand.extend(temporary_hand)
        temporary_hand.clear()
        rng.shuffle(player.hand)

    @staticmethod
    def _candidate_symbols_for(
        player: Player,
        drawn_symbol: SymbolName,
    ) -> Iterator[tuple[Species, Symbol]]:
        for candidate in AdaptationRules.select_species_for_symbol(player, drawn_symbol):
            candidate_symbol = next(
                (symbol for symbol in candidate.solo_symbols if symbol.symbol == drawn_symbol),
                None,
            )

            if candidate_symbol is not None:
                yield candidate, candidate_symbol

    @staticmethod
    def _apply_species_increase(
        state: GameState,
        candidate: Species,
        picked_card: TraitCard,
        increase: SymbolIncrease,
    ) -> bool:
        if increase == SymbolIncrease.SIZE:
            if candidate.size >= state.max_size:
                return False

            candidate.size += 1
        elif increase == SymbolIncrease.POPULATION:
            candidate.population += 1
        else:
            return False

        state.nature_discard.append(picked_card)
        return True
