import unittest

from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.model.solo_species import SoloSpecies
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.symbol import Symbol, SymbolName
from src.nature_solo_bot.game.rules.adaptation import AdaptationRules


class AdaptationRulesTest(unittest.TestCase):
    def test_candidates_are_sorted_by_symbol_position_before_species_age(self):
        player = Player(name="Rani")
        older_species = Species(
            solo_card=SoloSpecies(
                pink_symbols=[Symbol(SymbolName.GEAR), Symbol(SymbolName.CAT)]
            ),
            round_created=1,
        )
        earlier_symbol_species = Species(
            solo_card=SoloSpecies(pink_symbols=[Symbol(SymbolName.CAT)]),
            round_created=2,
        )
        player.species.extend([older_species, earlier_symbol_species])

        candidates = AdaptationRules.select_species_for_symbol(player, SymbolName.CAT)

        self.assertEqual(candidates, [earlier_symbol_species, older_species])

    def test_oldest_species_wins_when_symbol_positions_tie(self):
        player = Player(name="Rani")
        oldest_species = Species(
            solo_card=SoloSpecies(pink_symbols=[Symbol(SymbolName.CAT)]),
            round_created=1,
        )
        younger_species = Species(
            solo_card=SoloSpecies(pink_symbols=[Symbol(SymbolName.CAT)]),
            round_created=2,
        )
        player.species.extend([younger_species, oldest_species])

        candidates = AdaptationRules.select_species_for_symbol(player, SymbolName.CAT)

        self.assertEqual(candidates, [oldest_species, younger_species])

    def test_returns_empty_list_if_no_species_has_the_symbol(self):
        player = Player(name="Rani")
        player.species.append(
            Species(
                solo_card=SoloSpecies(pink_symbols=[Symbol(SymbolName.GEAR)]),
                round_created=1,
            )
        )

        candidates = AdaptationRules.select_species_for_symbol(player, SymbolName.CAT)

        self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main()
