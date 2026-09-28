import unittest

from src.nature_solo_bot.engine.game_engine import GameEngine
from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.model.solo_species import SoloSpecies
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.state import GameState
from src.nature_solo_bot.game.model.symbol import Symbol, SymbolIncrease, SymbolName


class AdaptationPhaseTest(unittest.TestCase):
    def test_leftover_size_card_uses_next_candidate_when_priority_species_is_full(self):
        engine = GameEngine(seed=42)
        state = GameState()
        engine.state = state
        player = Player(name="Rani")
        full_species = Species(
            solo_card=SoloSpecies(pink_symbols=[Symbol(SymbolName.CAT)]),
            round_created=1,
        )
        full_species.size = state.max_size
        next_species = Species(
            solo_card=SoloSpecies(pink_symbols=[Symbol(SymbolName.CAT)]),
            round_created=2,
        )
        player.species.extend([full_species, next_species])
        card = next(
            card for card in Card.init_nature_deck()
            if card.solo_symbol == SymbolName.CAT
        )
        player.hand.append(card)
        temporary_hand: list = []

        engine.assign_leftover_cards_to_hunters(
            player,
            temporary_hand,
            SymbolIncrease.SIZE,
        )

        self.assertEqual(full_species.size, state.max_size)
        self.assertEqual(next_species.size, 2)
        self.assertIn(card, state.nature_discard)
        self.assertEqual(temporary_hand, [])

    def test_size_symbol_that_makes_hunter_applies_both_effects(self):
        engine = GameEngine(seed=42)
        state = GameState()
        engine.state = state
        player = Player(name="Rani")
        species = Species(
            solo_card=SoloSpecies(
                pink_symbols=[
                    Symbol(
                        SymbolName.CAT,
                        increase=SymbolIncrease.SIZE,
                        make_hunter=True,
                    )
                ]
            ),
            round_created=1,
        )
        player.species.append(species)
        card = next(
            card for card in Card.init_nature_deck()
            if card.solo_symbol == SymbolName.CAT
        )
        player.hand.append(card)

        engine.assign_card_to_correct_candidate(player, [])

        self.assertEqual(species.size, 2)
        self.assertIn(card, state.nature_discard)
        self.assertTrue(species.is_hunter)
        self.assertEqual(len(species.trait_cards), 1)
        self.assertIs(species.trait_cards[0].trait, species.traits[0])


if __name__ == "__main__":
    unittest.main()