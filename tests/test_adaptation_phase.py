import unittest
from unittest.mock import patch

from src.nature_solo_bot.engine.game_engine import GameEngine
from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.hunter_card import HunterCard
from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.model.solo_cards import (
    EVADER,
    GLUTTON,
    NATURE_SOLO_CARDS,
    PREDATOR,
    PROPAGATOR,
    SCAMP,
    SCAVENGER,
)
from src.nature_solo_bot.game.model.solo_species import SoloSpecies
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.state import GameState
from src.nature_solo_bot.game.model.symbol import Symbol, SymbolIncrease, SymbolName
from src.nature_solo_bot.game.model.trait_cards import FAST


class AdaptationPhaseTest(unittest.TestCase):
    def test_seeded_random_species_and_sizes_print_initial_and_final_state(self):
        engine = GameEngine(seed=73)
        state = GameState()
        state.current_round = 2
        state.first_player_index = 0
        state.players = [Player(name="Rani"), Player(name="Radwin")]
        engine.state = state

        solo_cards = engine.rng.sample(NATURE_SOLO_CARDS, 4)
        nature_deck = Card.init_nature_deck()
        engine.rng.shuffle(nature_deck)
        for player_index, player in enumerate(state.players):
            for species_index in range(2):
                solo_card = solo_cards[player_index * 2 + species_index]
                species = Species(
                    solo_card=solo_card,
                    round_created=species_index,
                )
                species.size = engine.rng.randint(1, state.max_size)
                species.population = 3
                player.species.append(species)
            player.hand.extend(nature_deck[player_index * 7 : (player_index + 1) * 7])

        def print_species(player):
            print(f"{player.name} species:")
            for species in player.species:
                traits = ", ".join(trait.name for trait in species.traits) or "none"
                print(
                    f"  {species.solo_species.name}: traits=[{traits}], "
                    f"size={species.size}, population={species.population}, "
                    f"is_hunter={species.is_hunter}"
                )

        print("\nSeeded random setup before adaptation (seed=73):")
        for player in state.players:
            print_species(player)
            cards = ", ".join(
                f"{card.name} ({card.solo_symbol.value}, food {card.food_value})"
                for card in player.hand
            )
            print(f"  Hand: {cards}")
            self.assertEqual(len(player.species), 2)
            self.assertEqual(len(player.hand), 7)

        engine.run_adaptation_phase()

        print("\nState after adaptation:")
        for player in state.players:
            print_species(player)

        self.assertEqual(state.current_round, 2)
        self.assertTrue(all(len(player.species) == 2 for player in state.players))

    def _create_two_species_hunter_scenario(
        self,
        rani_sizes: tuple[int, int],
        *,
        non_hunter_index: int | None = None,
    ) -> tuple[GameEngine, GameState, Player]:
        engine = GameEngine(seed=42)
        state = GameState()
        state.first_player_index = 0
        rani = Player(name="Rani")
        radwin = Player(name="Radwin")
        state.players = [rani, radwin]
        engine.state = state

        cards = [Card("Fast", 1, FAST, SymbolName.GEAR, "Nature") for _ in range(13)]
        card_index = 0
        for player in state.players:
            for species_index in range(2):
                species = Species(
                    solo_card=SoloSpecies(
                        name=f"{player.name} species {species_index + 1}",
                        pink_symbols=[Symbol(SymbolName.GEAR)],
                    ),
                    round_created=species_index,
                )
                species.population = 3
                if player is rani:
                    species.size = rani_sizes[species_index]

                if player is rani:
                    is_hunter = species_index != non_hunter_index
                    trait_count = 2 if is_hunter else 3
                    for card in cards[card_index : card_index + trait_count]:
                        self.assertTrue(
                            species.add_trait_card(card, max_traits=state.max_traits)
                        )
                    card_index += trait_count
                    if is_hunter:
                        self.assertTrue(
                            species.add_trait_card(
                                HunterCard(),
                                max_traits=state.max_traits,
                            )
                        )
                player.species.append(species)

        rani.hand.extend(cards[card_index : card_index + 7])
        self.assertEqual(len(rani.hand), 7)
        self.assertEqual(len(rani.species), 2)
        self.assertEqual(len(radwin.species), 2)
        return engine, state, rani

    def test_all_rani_species_start_as_hunters_and_size_increases_precede_population(
        self,
    ):
        engine, state, rani = self._create_two_species_hunter_scenario((1, 4))

        self.assertTrue(all(species.is_hunter for species in rani.species))
        with patch.object(engine.rng, "shuffle", lambda cards: None):
            engine.run_adaptation_phase()

        first_species, second_species = rani.species
        self.assertEqual((first_species.size, first_species.population), (4, 7))
        self.assertEqual((second_species.size, second_species.population), (4, 3))
        self.assertEqual(rani.hand, [])
        self.assertEqual(len(state.nature_discard), 7)

    def test_all_max_size_hunter_species_increase_population(self):
        engine, _, rani = self._create_two_species_hunter_scenario((4, 4))

        self.assertTrue(all(species.is_hunter for species in rani.species))
        with patch.object(engine.rng, "shuffle", lambda cards: None):
            engine.run_adaptation_phase()

        first_species, second_species = rani.species
        self.assertEqual((first_species.size, first_species.population), (4, 10))
        self.assertEqual((second_species.size, second_species.population), (4, 3))
        self.assertEqual(rani.hand, [])

    def test_hunter_fallback_does_not_run_when_one_species_is_not_a_hunter(self):
        engine, state, rani = self._create_two_species_hunter_scenario(
            (1, 1),
            non_hunter_index=1,
        )
        original_cards = list(rani.hand)

        self.assertTrue(rani.species[0].is_hunter)
        self.assertFalse(rani.species[1].is_hunter)
        with patch.object(engine.rng, "shuffle", lambda cards: None):
            engine.run_adaptation_phase()

        self.assertEqual(rani.hand, original_cards)
        self.assertEqual([species.size for species in rani.species], [1, 1])
        self.assertEqual([species.population for species in rani.species], [3, 3])
        self.assertEqual(state.nature_discard, [])

    def test_round_two_adaptation_scenario_prints_hands_and_species(self):
        engine = GameEngine(seed=42)
        state = GameState()
        state.current_round = 2
        state.first_player_index = 0
        state.players = [Player(name="Rani"), Player(name="Radwin")]
        state.nature_deck = Card.init_nature_deck()
        engine.rng.shuffle(state.nature_deck)
        engine.state = state

        solo_cards = [
            (EVADER, GLUTTON, SCAMP),
            (PREDATOR, PROPAGATOR, SCAVENGER),
        ]
        for player, player_solo_cards in zip(state.players, solo_cards):
            for round_created, (solo_card, size) in enumerate(
                zip(player_solo_cards, (1, 3, 4))
            ):
                species = Species(solo_card=solo_card, round_created=round_created)
                species.size = size
                species.population = 3
                player.species.append(species)
            player.hand.extend(engine.draw_card(state.nature_deck) for _ in range(7))

        radwin = state.players[1]
        trait_order = {
            ("Plated", SymbolName.GEAR): 0,
            ("Clawed", SymbolName.GEAR): 1,
            ("Fast", SymbolName.CAT): 2,
            ("Fast", SymbolName.GEAR): 3,
        }
        radwin.hand.sort(
            key=lambda card: trait_order.get(
                (card.name, card.solo_symbol),
                len(trait_order),
            )
        )
        self.assertEqual(
            [(card.name, card.solo_symbol) for card in radwin.hand[:4]],
            [
                ("Plated", SymbolName.GEAR),
                ("Clawed", SymbolName.GEAR),
                ("Fast", SymbolName.CAT),
                ("Fast", SymbolName.GEAR),
            ],
        )

        for player in state.players:
            self.assertEqual(len(player.hand), 7)
            self.assertEqual([species.size for species in player.species], [1, 3, 4])
            self.assertEqual(
                [species.population for species in player.species], [3, 3, 3]
            )

        print("\nHands at the beginning of round-two adaptation:")
        for player in state.players:
            cards = ", ".join(
                f"{card.name} ({card.solo_symbol.value}, food {card.food_value})"
                for card in player.hand
            )
            print(f"{player.name}: {cards}")

        assign_card = engine.assign_card_to_correct_candidate

        def trace_assignment(player, temporary_hand):
            card = player.hand[0]
            discarded_before = list(state.nature_discard)
            before = {
                species: (
                    species.size,
                    species.population,
                    list(species.trait_cards),
                    species.is_hunter,
                )
                for species in player.species
            }
            assign_card(player, temporary_hand)

            target = next(
                (species for species in player.species if card in species.trait_cards),
                None,
            )
            if target is not None:
                removed = [
                    old_card
                    for old_card in before[target][2]
                    if old_card not in target.trait_cards
                ]
                outcome = f"trait -> {target.solo_species.name}"
                if removed:
                    removed_names = []
                    for old_card in removed:
                        old_name = getattr(old_card, "name", old_card.trait.name)
                        old_symbol = getattr(old_card, "solo_symbol", None)
                        if old_symbol is not None:
                            old_name += f" ({old_symbol.value})"
                        removed_names.append(old_name)
                    outcome += f" (replaced {', '.join(removed_names)})"
                if not before[target][3] and target.is_hunter:
                    outcome += " + Hunter"
            else:
                changes = []
                for species, (size, population, _, was_hunter) in before.items():
                    if species.size != size:
                        changes.append(
                            f"{species.solo_species.name} size {size}->{species.size}"
                        )
                    if species.population != population:
                        changes.append(
                            f"{species.solo_species.name} population {population}->{species.population}"
                        )
                    if not was_hunter and species.is_hunter:
                        changes.append(f"{species.solo_species.name} gained Hunter")
                hunter_target = next(
                    (
                        species
                        for species, (_, _, _, was_hunter) in before.items()
                        if not was_hunter and species.is_hunter
                    ),
                    None,
                )
                if (
                    card not in discarded_before
                    and card in state.nature_discard
                    and hunter_target
                ):
                    outcome = (
                        f"trait -> {hunter_target.solo_species.name} "
                        "(replaced by Hunter)"
                    )
                else:
                    outcome = "; ".join(changes) or "unassigned; returned to hand"

            print(f"  {player.name}: {card.name} ({card.solo_symbol.value}) -> {outcome}")

        engine.assign_card_to_correct_candidate = trace_assignment
        print("\nCard-by-card adaptation assignments:")
        with patch.object(engine.rng, "shuffle", lambda cards: None):
            engine.run_adaptation_phase()

        print("\nSpecies after round-two adaptation:")
        for player in state.players:
            print(f"{player.name}:")
            for species in player.species:
                traits = ", ".join(trait.name for trait in species.traits) or "none"
                print(
                    f"  {species.solo_species.name}: traits=[{traits}], "
                    f"size={species.size}, population={species.population}, "
                    f"is_hunter={species.is_hunter}"
                )

        self.assertEqual(state.current_round, 2)
        self.assertTrue(all(len(player.species) == 3 for player in state.players))
        predator = state.players[1].species[0]
        self.assertTrue(predator.is_hunter)
        self.assertEqual(len(predator.trait_cards), state.max_traits)

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
            card for card in Card.init_nature_deck() if card.solo_symbol == SymbolName.CAT
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

    def test_regular_trait_does_not_replace_traits_when_species_is_full(self):
        engine = GameEngine(seed=42)
        state = GameState()
        engine.state = state
        player = Player(name="Rani")
        species = Species(
            solo_card=SoloSpecies(pink_symbols=[Symbol(SymbolName.GEAR)]),
            round_created=1,
        )
        nature_cards = Card.init_nature_deck()
        incoming_card = next(
            card for card in nature_cards if card.solo_symbol == SymbolName.GEAR
        )
        existing_cards = [card for card in nature_cards if card is not incoming_card][
            : state.max_traits
        ]
        for card in existing_cards:
            self.assertTrue(species.add_trait_card(card, max_traits=state.max_traits))
        player.species.append(species)
        player.hand.append(incoming_card)
        temporary_hand: list = []

        engine.assign_card_to_correct_candidate(player, temporary_hand)

        self.assertEqual(species.trait_cards, existing_cards)
        self.assertEqual(temporary_hand, [incoming_card])
        self.assertEqual(state.nature_discard, [])

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
            card for card in Card.init_nature_deck() if card.solo_symbol == SymbolName.CAT
        )
        player.hand.append(card)

        engine.assign_card_to_correct_candidate(player, [])

        self.assertEqual(species.size, 2)
        self.assertIn(card, state.nature_discard)
        self.assertTrue(species.is_hunter)
        self.assertEqual(len(species.trait_cards), 1)
        self.assertIs(species.trait_cards[0].trait, species.traits[0])

    def test_red_population_symbol_replaces_full_species_trait_with_hunter(self):
        engine = GameEngine(seed=42)
        state = GameState()
        engine.state = state
        player = Player(name="Rani")
        species = Species(
            solo_card=SoloSpecies(
                pink_symbols=[
                    Symbol(
                        SymbolName.CAT,
                        increase=SymbolIncrease.POPULATION,
                        make_hunter=True,
                    )
                ]
            ),
            round_created=1,
        )
        existing_cards = Card.init_nature_deck()[: state.max_traits]
        for existing_card in existing_cards:
            self.assertTrue(
                species.add_trait_card(existing_card, max_traits=state.max_traits)
            )
        player.species.append(species)

        incoming_card = next(
            card
            for card in Card.init_nature_deck()
            if card.solo_symbol == SymbolName.CAT
        )
        player.hand.append(incoming_card)

        with patch.object(engine.rng, "choice", return_value=existing_cards[1]):
            engine.assign_card_to_correct_candidate(player, [])

        self.assertEqual(species.population, 2)
        self.assertEqual(species.size, 1)
        self.assertTrue(species.is_hunter)
        self.assertEqual(len(species.trait_cards), state.max_traits)
        self.assertEqual(
            sum(trait.name == "Hunter" for trait in species.traits),
            1,
        )
        self.assertIn(existing_cards[0], species.trait_cards)
        self.assertNotIn(existing_cards[1], species.trait_cards)
        self.assertIn(existing_cards[2], species.trait_cards)
        self.assertIn(existing_cards[1], state.nature_discard)
        self.assertIn(incoming_card, state.nature_discard)
        self.assertEqual(player.hand, [])

    def test_red_size_symbol_replaces_full_species_trait_with_hunter(self):
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
        existing_cards = Card.init_nature_deck()[: state.max_traits]
        for existing_card in existing_cards:
            self.assertTrue(
                species.add_trait_card(existing_card, max_traits=state.max_traits)
            )
        player.species.append(species)

        incoming_card = next(
            card
            for card in Card.init_nature_deck()
            if card.solo_symbol == SymbolName.CAT
        )
        player.hand.append(incoming_card)

        with patch.object(engine.rng, "choice", return_value=existing_cards[1]):
            engine.assign_card_to_correct_candidate(player, [])

        self.assertEqual(species.population, 1)
        self.assertEqual(species.size, 2)
        self.assertTrue(species.is_hunter)
        self.assertEqual(len(species.trait_cards), state.max_traits)
        self.assertEqual(
            sum(trait.name == "Hunter" for trait in species.traits),
            1,
        )
        self.assertIn(existing_cards[0], species.trait_cards)
        self.assertNotIn(existing_cards[1], species.trait_cards)
        self.assertIn(existing_cards[2], species.trait_cards)
        self.assertIn(existing_cards[1], state.nature_discard)
        self.assertIn(incoming_card, state.nature_discard)
        self.assertEqual(player.hand, [])


if __name__ == "__main__":
    unittest.main()
