"""Write concise, parser-friendly logs for complete games."""

from collections.abc import Callable, Iterable
from pathlib import Path
from unittest.mock import patch

from ..const import BAMBOO, BAMBOO_GROVE, MEAT, NATURE, PLANT
from ..engine.action_applier import ActionApplier
from ..engine.game_engine import GameEngine
from ..game.model.player import Player
from ..game.model.species import Species, TreeColor
from ..game.model.state import GameState
from ..game.model.trait_card import TraitCard
from ..game.model.trait_cards import (
    AVID_FORAGER,
    LONG_DIGESTION,
    MONOPHAGOUS,
    OPPORTUNISTIC,
    SCAVENGING,
    SOCIAL,
    TUSKED,
)
from ..game.rules.adaptation import AdaptationRules
from ..game.rules.feeding import FeedingRules


class GameLogger:
    """Capture a game's setup, phase actions, and final results."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.species_ids: dict[Species, str] = {}
        self._state: GameState | None = None
        self._feeding_actions: list[str] | None = None
        self._original_assign: Callable[..., None] | None = None
        self._original_assign_leftover: Callable[..., None] | None = None
        self._original_preparation: Callable[[], None] | None = None
        self._original_adaptation: Callable[[], None] | None = None
        self._original_feeding: Callable[[], None] | None = None
        self._original_scoring: Callable[[], None] | None = None
        self._original_feeding_turn: Callable[..., None] | None = None
        self._original_forage: Callable[..., None] | None = None
        self._original_hunt: Callable[..., bool] | None = None
        self._original_starve: Callable[..., None] | None = None
        self._original_trigger_trait_feeding: Callable[..., None] | None = None
        self._original_discard: Callable[..., None] | None = None

    @property
    def state(self) -> GameState:
        assert self._state is not None
        return self._state

    def write(self, line: str = "") -> None:
        self.lines.append(line)

    def species_id(self, species: Species) -> str:
        if species not in self.species_ids:
            self.species_ids[species] = f"S{len(self.species_ids) + 1}"
        return self.species_ids[species]

    @staticmethod
    def card_name(card: TraitCard) -> str:
        name = getattr(card, "name", card.trait.name)
        details = []
        food_value = getattr(card, "food_value", None)
        symbol = getattr(card, "solo_symbol", None)
        if food_value is not None:
            details.append(str(food_value))
        if symbol is not None:
            details.append(symbol.value)
        card_description = f"{name}[{'/'.join(details)}]" if details else str(name)
        if getattr(card, "deck", NATURE) == BAMBOO_GROVE:
            return f"{card_description} (Bamboo Grove)"
        return card_description

    @staticmethod
    def discard_pile_name(state: GameState, card: TraitCard) -> str | None:
        if state.nature_discard is not None and card in state.nature_discard:
            return "Nature discard"
        for module, module_deck in state.module_decks.items():
            if card in module_deck.discard:
                return f"{module.replace('_', ' ').title()} discard"
        return None

    def watering_hole_description(self) -> str:
        return (
            f"{self.state.watering_hole_plant} plant, "
            f"{self.state.watering_hole_bamboo} bamboo"
        )

    def species_description(self, species: Species) -> str:
        traits = ", ".join(card.trait.name for card in species.trait_cards) or "none"
        return (
            f"{self.species_id(species)} {species.solo_species.name} "
            f"(tree={species.tree_color.name}, size={species.size}, "
            f"attack={species.attack_value}, defense={species.defense_value}, "
            f"population={species.population}, traits=[{traits}], "
            f"food (plant/meat/bamboo)="
            f"{species.plant_food}/{species.meat_food}/{species.bamboo_food})"
        )

    def player_board(self, player: Player) -> None:
        hand = ", ".join(self.card_name(card) for card in player.hand) or "empty"
        self.write(f"{player.name} hand: {hand}")
        for species in player.species:
            self.write(f"  {self.species_description(species)}")

    def adaptation_event(
        self,
        state: GameState,
        player: Player,
        card: TraitCard,
        before: dict[Species, tuple[int, int, list[TraitCard]]],
    ) -> None:
        for species in player.species:
            old_size, old_population, old_traits = before[species]
            if card not in old_traits and card in species.trait_cards:
                self.write(
                    f"  {player.name}: {self.card_name(card)} -> "
                    f"{self.species_id(species)} trait '{card.trait.name}'"
                )
                return
            if species.size != old_size:
                discard_pile_name = self.discard_pile_name(state, card)
                if discard_pile_name is None:
                    raise RuntimeError("Adaptation increase card was not found in a discard pile.")
                self.write(
                    f"  {player.name}: {self.card_name(card)} -> "
                    f"{self.species_id(species)} size {old_size} to {species.size}; "
                    f"card discarded to the {discard_pile_name}"
                )
                return
            if species.population != old_population:
                discard_pile_name = self.discard_pile_name(state, card)
                if discard_pile_name is None:
                    raise RuntimeError("Adaptation increase card was not found in a discard pile.")
                self.write(
                    f"  {player.name}: {self.card_name(card)} -> "
                    f"{self.species_id(species)} population "
                    f"{old_population} to {species.population}; "
                    f"card discarded to the {discard_pile_name}"
                )
                return

        discard_pile_name = self.discard_pile_name(state, card)
        if discard_pile_name is not None:
            self.write(
                f"  {player.name}: {self.card_name(card)} -> "
                f"discarded to the {discard_pile_name}"
            )
        else:
            self.write(f"  {player.name}: {self.card_name(card)} -> returned to hand")

    def _trace_assign(
        self,
        state: GameState,
        player: Player,
        temporary_hand: list[TraitCard],
        rng,
    ) -> None:
        assert self._original_assign is not None
        card = player.hand[0]
        before = {
            species: (species.size, species.population, list(species.trait_cards))
            for species in player.species
        }
        self._original_assign(state, player, temporary_hand, rng)
        self.adaptation_event(state, player, card, before)

    def _trace_assign_leftover(
        self,
        state: GameState,
        player: Player,
        temporary_hand: list[TraitCard],
        increase,
    ) -> None:
        assert self._original_assign_leftover is not None
        card = player.hand[0]
        before = {
            species: (species.size, species.population, list(species.trait_cards))
            for species in player.species
        }
        self._original_assign_leftover(state, player, temporary_hand, increase)
        self.adaptation_event(state, player, card, before)

    def _trace_preparation(self) -> None:
        assert self._original_preparation is not None
        self._original_preparation()
        self.write(f"\nROUND {self.state.current_round} - PREPARATION")
        self.write(
            f"First player: {self.state.players[self.state.first_player_index].name}; "
            f"watering hole: {self.watering_hole_description()}"
        )
        for player in self.state.players:
            self.player_board(player)

    def _trace_adaptation(self) -> None:
        assert self._original_adaptation is not None
        self.write(f"\nROUND {self.state.current_round} - ADAPTATION")
        self._original_adaptation()
        self.write("Species at the end of adaptation:")
        for player in self.state.players:
            self.player_board(player)

    def _record_feeding_action(self, action: str) -> None:
        if self._feeding_actions is not None:
            self._feeding_actions.append(action)

    def _trace_feeding_turn(self, state: GameState, player: Player, rng) -> None:
        assert self._original_feeding_turn is not None
        self._feeding_actions = []
        self._original_feeding_turn(state, player, rng)
        if self._feeding_actions:
            self.write(f"  {player.name} turn: " + "; ".join(self._feeding_actions))
        elif player.passing:
            self.write(f"  {player.name} turn: passes")
        else:
            self.write(f"  {player.name} turn: no action")
        self._feeding_actions = None

    def _trace_forage(self, state: GameState, species: Species, food_type: str) -> None:
        assert self._original_forage is not None
        before_food = species.eaten_food[food_type]
        self._original_forage(state, species, food_type)
        amount = species.eaten_food[food_type] - before_food
        food_name = {PLANT: "plant", MEAT: "meat", BAMBOO: "bamboo"}[food_type]
        self._record_feeding_action(
            f"{self.species_id(species)} ate {amount} {food_name} food"
        )

    def _trace_hunt(self, state: GameState, player: Player, species: Species) -> bool:
        assert self._original_hunt is not None
        before_meat = species.meat_food
        before_populations = {
            candidate: candidate.population
            for owner in state.players
            for candidate in owner.species
        }
        hunted = self._original_hunt(state, player, species)
        if hunted:
            prey_losses = [
                f"{self.species_id(candidate)} -{before_population - candidate.population} pop"
                for candidate, before_population in before_populations.items()
                if candidate.population < before_population
            ]
            prey_details = ", ".join(prey_losses) or "prey unchanged"
            self._record_feeding_action(
                f"{self.species_id(species)} ate "
                f"{species.meat_food - before_meat} meat food (hunt; {prey_details})"
            )
        return hunted

    def _trace_trait_trigger(
        self,
        species_list: Iterable[Species],
        trait_id: str,
        food_per_trigger: int,
        food_type: str,
    ) -> None:
        assert self._original_trigger_trait_feeding is not None
        affected_species = list(species_list)
        active_species = {species for player in self.state.players for species in player.species}
        before_food = {
            species: species.total_food for species in affected_species if species in active_species
        }
        trigger_counts = {species: species.trait_count(trait_id) for species in before_food}
        self._original_trigger_trait_feeding(
            affected_species,
            trait_id,
            food_per_trigger,
            food_type,
        )
        if self._feeding_actions is None:
            return

        trigger_details = {
            TUSKED.effect_id: ("Tusked", "hole emptied"),
            SCAVENGING.effect_id: ("Scavenging", "successful hunt"),
            OPPORTUNISTIC.effect_id: ("Opportunistic", "plants remained"),
        }
        trait_name, trigger_reason = trigger_details.get(trait_id, (trait_id, "triggered"))
        for species, previous_food in before_food.items():
            food_eaten = species.total_food - previous_food
            if food_eaten > 0:
                copies = trigger_counts[species]
                social_copies = species.trait_count(SOCIAL.effect_id)
                social_note = f", Social x{social_copies}" if social_copies else ""
                self._record_feeding_action(
                    f"{self.species_id(species)} ate {food_eaten} "
                    f"{food_type.removesuffix('_food')} food "
                    f"({trait_name} x{copies} trigger{social_note}; {trigger_reason})"
                )

    def _trace_starve(self, state: GameState, species: Species, player: Player) -> None:
        assert self._original_starve is not None
        before_population = species.population
        self._original_starve(state, species, player)
        status = "extinct" if species not in player.species else str(species.population)
        self._record_feeding_action(
            f"{self.species_id(species)} starved ({before_population} -> {status})"
        )

    def _trace_discard(self, state: GameState, player: Player, rng, food_type: str) -> None:
        assert self._original_discard is not None
        previous_hand = list(player.hand)
        self._original_discard(state, player, rng, food_type)
        remaining_ids = {id(card) for card in player.hand}
        discarded_cards = [card for card in previous_hand if id(card) not in remaining_ids]
        food_name = {PLANT: "plant", MEAT: "meat", BAMBOO: "bamboo"}[food_type]
        for card in discarded_cards:
            discard_pile_name = self.discard_pile_name(state, card)
            if discard_pile_name is None:
                raise RuntimeError("Watering-hole discard card was not found in a discard pile.")
            self._record_feeding_action(
                f"discarded {self.card_name(card)} (+{card.food_value} {food_name}; "
                f"{discard_pile_name})"
            )

    def _trace_feeding(self) -> None:
        assert self._original_feeding is not None
        self.write(f"\nROUND {self.state.current_round} - FEEDING")
        self.write(f"Watering hole before feeding: {self.watering_hole_description()}")
        self._original_feeding()
        self.write(f"Watering hole after feeding: {self.watering_hole_description()}")
        for player in self.state.players:
            self.write(f"  {player.name} after feeding:")
            for species in player.species:
                self.write(
                    f"    {self.species_description(species)}; "
                    f"fed={species.total_food}/{species.population}"
                )

    def _trace_scoring(self) -> None:
        assert self._original_scoring is not None
        before_scores = {player: player.score for player in self.state.players}
        before_species = {
            species: (species.tree_color, list(species.trait_cards))
            for player in self.state.players
            for species in player.species
        }
        before_food = {
            species: species.eaten_food.copy()
            for player in self.state.players
            for species in player.species
        }
        self.write(f"\nROUND {self.state.current_round} - SCORING")
        self._original_scoring()
        for player in self.state.players:
            points_gained = player.score - before_scores[player]
            end_game_bonus = (
                2 * len(player.species)
                if self.state.current_round == self.state.total_rounds
                else 0
            )
            food_points = points_gained - end_game_bonus
            self.write(
                f"  {player.name} scored {food_points} food points "
                f"(total points gained: {points_gained}"
                + (f", surviving-species bonus: {end_game_bonus}" if end_game_bonus else "")
                + f"); score={player.score}"
            )
            for species in player.species:
                bamboo_food = before_food[species][BAMBOO]
                if bamboo_food:
                    trait_ids = {
                        card.trait.effect_id for card in before_species[species][1]
                    }
                    if MONOPHAGOUS.effect_id in trait_ids:
                        bamboo_outcome = "scored"
                    elif LONG_DIGESTION.effect_id in trait_ids:
                        bamboo_outcome = "stored"
                    else:
                        bamboo_outcome = "discarded"
                    self.write(
                        f"    {self.species_id(species)} bamboo food: "
                        f"{bamboo_food} {bamboo_outcome}"
                    )
                self._write_scoring_changes(species, before_species[species])

    def _write_scoring_changes(
        self,
        species: Species,
        before: tuple[TreeColor, list[TraitCard]],
    ) -> None:
        old_tree, old_traits = before
        if old_tree != species.tree_color:
            self.write(
                f"    {self.species_id(species)} tree changed "
                f"{old_tree.name} to {species.tree_color.name}"
            )
        for card in old_traits:
            if card not in species.trait_cards:
                self.write(f"    {self.species_id(species)} lost trait '{card.trait.name}'")

    def _remember_originals(self, engine: GameEngine) -> None:
        self._original_preparation = engine.run_preparation_phase
        self._original_adaptation = engine.run_adaptation_phase
        self._original_feeding = engine.run_feeding_phase
        self._original_scoring = engine.run_scoring_phase
        self._original_assign = AdaptationRules.assign_card_to_correct_candidate
        self._original_assign_leftover = AdaptationRules.assign_leftover_cards_to_hunters
        self._original_feeding_turn = FeedingRules.take_feeding_turn
        self._original_forage = FeedingRules.forage
        self._original_hunt = FeedingRules.hunt
        self._original_starve = FeedingRules.starve
        self._original_trigger_trait_feeding = FeedingRules._trigger_trait_feeding
        self._original_discard = ActionApplier.discard_card_for_watering_hole

    def _patch_game(self, engine: GameEngine) -> None:
        with (
            patch.object(engine, "run_preparation_phase", side_effect=self._trace_preparation),
            patch.object(engine, "run_adaptation_phase", side_effect=self._trace_adaptation),
            patch.object(engine, "run_feeding_phase", side_effect=self._trace_feeding),
            patch.object(engine, "run_scoring_phase", side_effect=self._trace_scoring),
            patch.object(
                AdaptationRules,
                "assign_card_to_correct_candidate",
                side_effect=self._trace_assign,
            ),
            patch.object(
                AdaptationRules,
                "assign_leftover_cards_to_hunters",
                side_effect=self._trace_assign_leftover,
            ),
            patch.object(
                FeedingRules,
                "take_feeding_turn",
                side_effect=self._trace_feeding_turn,
            ),
            patch.object(FeedingRules, "forage", side_effect=self._trace_forage),
            patch.object(FeedingRules, "hunt", side_effect=self._trace_hunt),
            patch.object(FeedingRules, "starve", side_effect=self._trace_starve),
            patch.object(
                FeedingRules,
                "_trigger_trait_feeding",
                side_effect=self._trace_trait_trigger,
            ),
            patch.object(
                ActionApplier,
                "discard_card_for_watering_hole",
                side_effect=self._trace_discard,
            ),
        ):
            engine.run_game()

    def _write_setup(self, engine: GameEngine, game_number: int) -> None:
        self.write("FULL GAME SETUP")
        self.write(f"Game number: {game_number}")
        self.write(f"Seed: {engine.seed}")
        self.write(
            "Difficulty: "
            f"round_one_population={self.state.difficulty.round_one_population}, "
            f"cards_to_draw={self.state.difficulty.cards_to_draw}"
        )
        self.write(f"Nature promo cards: {engine.nature_promo}")
        self.write(
            "Module promo cards: "
            + (", ".join(sorted(engine.promo_modules)) if engine.promo_modules else "none")
        )
        self.write(f"Modules: {', '.join(engine.modules) if engine.modules else 'none'}")
        self.write(f"Players: {', '.join(player.name for player in self.state.players)}")
        self.write(f"Rounds: {self.state.total_rounds}")
        self.write(f"First player: {self.state.players[self.state.first_player_index].name}")
        self.write(
            f"Watering hole: {self.state.watering_hole_plant}; "
            f"plant added per round: {self.state.plant_per_round}; "
            f"bamboo: {self.state.watering_hole_bamboo}; "
            f"bamboo added per round: {getattr(self.state, 'bamboo_per_round', 0)}"
        )
        if self.state.food_card is not None:
            self.write(f"Setup food card: {self.card_name(self.state.food_card)}")
        self.write(
            f"Nature deck: {len(self.state.nature_deck)} cards; "
            f"Nature discard: {len(self.state.nature_discard)} cards"
        )
        for module, module_deck in self.state.module_decks.items():
            module_name = module.replace("_", " ").title()
            self.write(
                f"{module_name} deck: {len(module_deck.deck)} cards; "
                f"{module_name} discard: {len(module_deck.discard)} cards"
            )
        nature_cards = [*self.state.nature_deck, *self.state.nature_discard]
        if self.state.food_card is not None:
            nature_cards.append(self.state.food_card)
        avid_forager_count = sum(
            card.trait is AVID_FORAGER for card in nature_cards
        )
        self.write(
            "Avid Forager cards in Nature deck "
            f"(including setup food card): {avid_forager_count}"
        )
        for player in self.state.players:
            self.player_board(player)

    def run_game(
        self,
        engine: GameEngine,
        output_path: str | Path,
        *,
        game_number: int,
    ) -> GameState:
        """Run and log one game, writing a concise trace to ``output_path``."""
        self.lines.clear()
        self.species_ids.clear()
        self._state = engine.setup_game()
        self._feeding_actions = None
        self._write_setup(engine, game_number)
        self._remember_originals(engine)
        self._patch_game(engine)

        self.write("\nGAME COMPLETE")
        self.write(
            f"Completed rounds: {self.state.current_round - 1}; "
            "final scores: "
            + ", ".join(f"{player.name}={player.score}" for player in self.state.players)
        )
        winner = engine.define_winner()
        self.write(f"Winner: {winner.name if winner is not None else 'None'}")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        return self.state
