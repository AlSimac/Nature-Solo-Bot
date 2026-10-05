"""Run a complete deterministic game and write a human-readable trace."""

from pathlib import Path
import unittest
from unittest.mock import patch

from src.nature_solo_bot.engine.action_applier import ActionApplier
from src.nature_solo_bot.engine.game_engine import GameEngine
from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.state import DIFFICULTY_MEDIUM, GameState
from src.nature_solo_bot.game.model.trait_card import TraitCard
from src.nature_solo_bot.game.rules.adaptation import AdaptationRules
from src.nature_solo_bot.game.rules.feeding import FeedingRules


class FullGameLog:
    """Collect a readable trace while the real game rules run."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.species_ids: dict[Species, str] = {}

    def write(self, line: str = "") -> None:
        self.lines.append(line)

    def species_id(self, species: Species) -> str:
        if species not in self.species_ids:
            self.species_ids[species] = f"S{len(self.species_ids) + 1}"
        return self.species_ids[species]

    @staticmethod
    def card_name(card: TraitCard) -> str:
        name = getattr(card, "name", card.trait.name)
        food_value = getattr(card, "food_value", None)
        symbol = getattr(card, "solo_symbol", None)
        details = []
        if food_value is not None:
            details.append(f"food={food_value}")
        if symbol is not None:
            details.append(f"symbol={symbol.value}")
        return f"{name} ({', '.join(details)})" if details else str(name)

    def species_description(self, species: Species) -> str:
        traits = ", ".join(card.trait.name for card in species.trait_cards) or "none"
        return (
            f"{self.species_id(species)} {species.solo_species.name} "
            f"(tree={species.tree_color.name}, size={species.size}, "
            f"attack={species.attack_value}, defense={species.defense_value}, "
            f"population={species.population}, traits=[{traits}], "
            f"plant food={species.plant_food}, meat food={species.meat_food})"
        )

    def player_board(self, player: Player) -> None:
        self.write(f"{player.name}: hand=[{'; '.join(self.card_name(c) for c in player.hand)}]")
        for species in player.species:
            self.write(f"  {self.species_description(species)}")

    def adaptation_event(self, state: GameState, player, card: TraitCard, before) -> None:
        for species in player.species:
            old_size, old_population, old_traits = before[species]
            if card not in old_traits and card in species.trait_cards:
                self.write(
                    f"  {player.name}: {self.card_name(card)} -> "
                    f"{self.species_id(species)} trait '{card.trait.name}'"
                )
                return
            if species.size != old_size:
                self.write(
                    f"  {player.name}: {self.card_name(card)} -> "
                    f"{self.species_id(species)} size {old_size} to {species.size}; "
                    "card discarded to the Nature discard"
                )
                return
            if species.population != old_population:
                self.write(
                    f"  {player.name}: {self.card_name(card)} -> "
                    f"{self.species_id(species)} population "
                    f"{old_population} to {species.population}; "
                    "card discarded to the Nature discard"
                )
                return

        if card in state.nature_discard:
            self.write(
                f"  {player.name}: {self.card_name(card)} -> discarded to the Nature discard"
            )
        else:
            self.write(f"  {player.name}: {self.card_name(card)} -> returned to hand")


class FullGameTest(unittest.TestCase):
    def test_complete_game_writes_detailed_log(self):
        seed = 0
        engine = GameEngine(seed=seed, difficulty=DIFFICULTY_MEDIUM)
        state = engine.setup_game()
        trace = FullGameLog()
        for player in state.players:
            self.assertEqual(
                len({species.solo_species.name for species in player.species}),
                len(player.species),
            )

        first_player = state.players[state.first_player_index].name
        trace.write("FULL GAME SETUP")
        trace.write(f"Seed: {seed}")
        trace.write(f"Difficulty: {state.difficulty}")
        trace.write(f"Players: {', '.join(player.name for player in state.players)}")
        trace.write(f"Rounds: {state.total_rounds}")
        trace.write(f"First player: {first_player}")
        trace.write(
            f"Watering hole: {state.watering_hole_plant}; "
            f"plant added per round: {state.plant_per_round}"
        )
        if state.food_card is not None:
            trace.write(f"Setup food card: {trace.card_name(state.food_card)}")
        trace.write(
            f"Nature deck: {len(state.nature_deck)} cards; "
            f"Nature discard: {len(state.nature_discard)} cards"
        )
        for player in state.players:
            trace.player_board(player)

        original_preparation = engine.run_preparation_phase
        original_adaptation = engine.run_adaptation_phase
        original_feeding = engine.run_feeding_phase
        original_scoring = engine.run_scoring_phase
        original_assign = AdaptationRules.assign_card_to_correct_candidate
        original_assign_leftover = AdaptationRules.assign_leftover_cards_to_hunters
        original_feeding_turn = FeedingRules.take_feeding_turn
        original_forage = FeedingRules.forage
        original_hunt = FeedingRules.hunt
        original_starve = FeedingRules.starve
        original_discard = ActionApplier.discard_card_for_watering_hole
        feeding_actions: list[str] | None = None

        def trace_assign(state, player, temporary_hand, rng) -> None:
            card = player.hand[0]
            before = {
                species: (species.size, species.population, list(species.trait_cards))
                for species in player.species
            }
            original_assign(state, player, temporary_hand, rng)
            trace.adaptation_event(state, player, card, before)

        def trace_assign_leftover(state, player, temporary_hand, increase) -> None:
            card = player.hand[0]
            before = {
                species: (species.size, species.population, list(species.trait_cards))
                for species in player.species
            }
            original_assign_leftover(state, player, temporary_hand, increase)
            trace.adaptation_event(state, player, card, before)

        def trace_preparation() -> None:
            carryover = {
                player: (player.lost_population, player.extinct_size) for player in state.players
            }
            original_preparation()
            for player in state.players:
                if state.current_round > 1:
                    lost_population, extinct_size = carryover[player]
                    new_species = player.species[-1]
                    self.assertEqual(
                        new_species.population,
                        lost_population + 1,
                    )
                    self.assertEqual(
                        new_species.size,
                        min(1 + extinct_size, state.max_size),
                    )
                    self.assertEqual(player.extinct_size, 0)
                solo_species_seen = [species.solo_species.name for species in player.species] + [
                    solo_species.name for solo_species in player.solo_discard
                ]
                self.assertEqual(len(solo_species_seen), len(set(solo_species_seen)))
            trace.write(f"\nROUND {state.current_round} - PREPARATION")
            trace.write(
                f"First player: {state.players[state.first_player_index].name}; "
                f"watering hole: {state.watering_hole_plant}"
            )
            for player in state.players:
                trace.player_board(player)

        def trace_adaptation() -> None:
            trace.write(f"\nROUND {state.current_round} - ADAPTATION")
            original_adaptation()
            trace.write("Species at the end of adaptation:")
            for player in state.players:
                trace.player_board(player)

        def record_feeding_action(action: str) -> None:
            if feeding_actions is not None:
                feeding_actions.append(action)

        def trace_feeding_turn(state, player, rng) -> None:
            nonlocal feeding_actions
            feeding_actions = []
            original_feeding_turn(state, player, rng)
            trace.write(f"  {player.name} feeding turn:")
            if feeding_actions:
                for action in feeding_actions:
                    trace.write(f"    {action}")
            elif player.passing:
                trace.write("    passes (no hungry species)")
            else:
                trace.write("    no feeding action")
            feeding_actions = None

        def trace_forage(state, species) -> None:
            before_food = species.plant_food
            original_forage(state, species)
            amount = species.plant_food - before_food
            record_feeding_action(f"{trace.species_id(species)} ate {amount} plant food")

        def trace_hunt(state, player, species) -> bool:
            before_meat = species.meat_food
            before_populations = {
                candidate: candidate.population
                for owner in state.players
                for candidate in owner.species
            }
            hunted = original_hunt(state, player, species)
            if hunted:
                prey_losses = [
                    f"{trace.species_id(candidate)} lost "
                    f"{before_population - candidate.population} population"
                    for candidate, before_population in before_populations.items()
                    if candidate.population < before_population
                ]
                details = ", ".join(prey_losses) or "prey population unchanged"
                record_feeding_action(
                    f"{trace.species_id(species)} ate "
                    f"{species.meat_food - before_meat} meat food by hunting; {details}"
                )
            return hunted

        def trace_starve(state, species, player) -> None:
            before_population = species.population
            original_starve(state, species, player)
            status = (
                "extinct" if species not in player.species else f"population {species.population}"
            )
            record_feeding_action(
                f"{trace.species_id(species)} starved "
                f"(population {before_population} to {status})"
            )

        def trace_discard(state, player, rng) -> None:
            previous_discard_size = len(state.nature_discard)
            original_discard(state, player, rng)
            for card in state.nature_discard[previous_discard_size:]:
                record_feeding_action(
                    f"{player.name} discarded {trace.card_name(card)} for "
                    f"{card.food_value} plant food"
                )

        def trace_feeding() -> None:
            trace.write(f"\nROUND {state.current_round} - FEEDING")
            trace.write(f"Watering hole before feeding: {state.watering_hole_plant}")
            original_feeding()
            trace.write(f"Watering hole after feeding: {state.watering_hole_plant}")
            for player in state.players:
                trace.write(f"  {player.name} species after feeding:")
                for species in player.species:
                    trace.write(
                        f"    {trace.species_description(species)}; "
                        f"fed={species.total_food}/{species.population}"
                    )

        def trace_scoring() -> None:
            round_number = state.current_round
            before_scores = {player: player.score for player in state.players}
            before_species = {
                species: (
                    species.tree_color,
                    list(species.trait_cards),
                    species.total_food,
                )
                for player in state.players
                for species in player.species
            }
            food_scores = {
                player: sum(species.total_food for species in player.species)
                for player in state.players
            }
            trace.write(f"\nROUND {round_number} - SCORING")
            original_scoring()
            for player in state.players:
                points_gained = player.score - before_scores[player]
                end_game_bonus = points_gained - food_scores[player]
                trace.write(
                    f"  {player.name} scored {food_scores[player]} food points "
                    f"(total points gained: {points_gained}"
                    + (f", surviving-species bonus: {end_game_bonus}" if end_game_bonus else "")
                    + f"); score={player.score}"
                )
                for species in player.species:
                    old_tree, old_traits, _ = before_species[species]
                    lost_traits = [card for card in old_traits if card not in species.trait_cards]
                    if old_tree != species.tree_color:
                        trace.write(
                            f"    {trace.species_id(species)} tree changed "
                            f"{old_tree.name} to {species.tree_color.name}"
                        )
                    for card in lost_traits:
                        trace.write(
                            f"    {trace.species_id(species)} lost trait " f"'{card.trait.name}'"
                        )

        with (
            patch.object(engine, "run_preparation_phase", side_effect=trace_preparation),
            patch.object(engine, "run_adaptation_phase", side_effect=trace_adaptation),
            patch.object(engine, "run_feeding_phase", side_effect=trace_feeding),
            patch.object(engine, "run_scoring_phase", side_effect=trace_scoring),
            patch.object(
                AdaptationRules,
                "assign_card_to_correct_candidate",
                side_effect=trace_assign,
            ),
            patch.object(
                AdaptationRules,
                "assign_leftover_cards_to_hunters",
                side_effect=trace_assign_leftover,
            ),
            patch.object(FeedingRules, "take_feeding_turn", side_effect=trace_feeding_turn),
            patch.object(FeedingRules, "forage", side_effect=trace_forage),
            patch.object(FeedingRules, "hunt", side_effect=trace_hunt),
            patch.object(FeedingRules, "starve", side_effect=trace_starve),
            patch.object(
                ActionApplier,
                "discard_card_for_watering_hole",
                side_effect=trace_discard,
            ),
        ):
            completed_state = engine.run_game()

        trace.write("\nGAME COMPLETE")
        trace.write(
            f"Completed rounds: {completed_state.current_round - 1}; "
            f"final scores: "
            + ", ".join(f"{player.name}={player.score}" for player in completed_state.players)
        )
        winner = engine.define_winner()
        self.assertIsNotNone(winner)
        trace.write(f"Winner: {winner.name}")

        log_path = Path(__file__).with_name("full_game.log")
        log_path.write_text("\n".join(trace.lines) + "\n", encoding="utf-8")
        log_text = log_path.read_text(encoding="utf-8")

        self.assertIs(completed_state, engine.state)
        self.assertEqual(
            winner,
            max(
                completed_state.players,
                key=lambda player: (
                    player.score,
                    sum(len(species.trait_cards) for species in player.species),
                ),
            ),
        )
        self.assertEqual(completed_state.current_round, completed_state.total_rounds + 1)
        self.assertTrue(log_path.is_file())
        self.assertIn("FULL GAME SETUP", log_text)
        self.assertIn("Difficulty:", log_text)
        self.assertIn("First player:", log_text)
        self.assertIn("hand=[", log_text)
        self.assertIn("size=", log_text)
        self.assertIn("attack=", log_text)
        self.assertIn("defense=", log_text)
        self.assertIn("population=", log_text)
        self.assertNotIn("Solo Species", log_text)
        self.assertIn("Species at the end of adaptation:", log_text)
        self.assertRegex(log_text, r"-> S\d+ (?:trait|size|population)")
        self.assertIn("feeding turn:", log_text)
        self.assertRegex(log_text, r"ate \d+ (?:plant|meat) food")
        self.assertRegex(log_text, r"discarded .+ for \d+ plant food")
        self.assertRegex(log_text, r"scored \d+ food points")
        self.assertIn("tree changed", log_text)
        self.assertIn("lost trait", log_text)
        self.assertIn(f"Winner: {winner.name}", log_text)
        self.assertEqual(log_text.count(" - PREPARATION"), completed_state.total_rounds)
        self.assertEqual(log_text.count(" - ADAPTATION"), completed_state.total_rounds)
        self.assertEqual(log_text.count(" - FEEDING"), completed_state.total_rounds)
        self.assertEqual(log_text.count(" - SCORING"), completed_state.total_rounds)


if __name__ == "__main__":
    unittest.main()
