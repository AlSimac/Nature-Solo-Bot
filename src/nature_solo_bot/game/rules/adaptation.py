from ..model.player import Player
from ..model.species import Species
from ..model.symbol import SymbolName


class AdaptationRules:
    """Rules for selecting species during the adaptation phase."""

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