"""Game engine stub."""

import random
from typing import TypeVar

from ..game.model.modules import BAMBOO_GROVE
from ..game.model.player import Player
from ..game.model.species import Species
from ..game.model.state import (
    Difficulty,
    GamePhase,
    GameState,
)
from ..game.model.symbol import SymbolIncrease
from ..game.model.trait_card import TraitCard
from ..game.rules.adaptation import AdaptationRules
from ..game.rules.feeding import FeedingRules
from ..game.rules.preparation import PreparationRules
from ..game.rules.scoring import ScoringRules
from ..game.rules.setup import GameSetup
from .action_applier import ActionApplier

T = TypeVar("T")


class GameEngine:
    """Runs a complete game from initialization through resolution."""

    def __init__(
        self,
        seed: int | None = None,
        difficulty: Difficulty = Difficulty.MEDIUM,
        modules: list[str] | None = None,
        promo: bool = False,
    ):
        self.seed = seed
        self.difficulty = difficulty
        self.modules = list(modules or [])
        self.promo = promo
        self.rng = random.Random(seed)
        self.state: GameState | None = None

    def setup_game(self) -> GameState:
        """Set up the initial game state."""
        state = GameState(difficulty=self.difficulty, modules=self.modules)
        state.seed = self.seed
        # Instantiate two players for the game
        state.players = Player.init_two_players()
        state.active_player_index = 1
        # Decks preparation
        GameSetup.shuffle_all_decks(state, self.rng, self.promo)
        self.state = state
        # Drawing a card from the deck for the watering hole plant
        state.food_card = self.draw_card(state.nature_deck, state.nature_discard)

        if BAMBOO_GROVE in state.modules:
            state.plant_per_round = 0
            state.bamboo_per_round = state.food_card.food_value * state.number_players

        else:
            state.plant_per_round = state.food_card.food_value * state.number_players

        state.first_player_index = self.rng.randrange(state.number_players)
        # Adding a new species for each player at the start of the game
        # this is before setting the current round to 1,
        # so that the species are created with round_created = 0
        # because Solo automa starts with 2 species.
        PreparationRules.add_new_species(state, self.rng)
        state.current_round = 1
        return state

    def run_game(self) -> GameState:
        """Set up and run the entire game, returning its final state."""
        state = self.state if self.state is not None else self.setup_game()

        while state.current_round <= state.total_rounds:
            self.run_preparation_phase()
            self.run_adaptation_phase()
            self.run_feeding_phase()
            self.run_scoring_phase()
            state.current_round += 1

        state.winner = self.define_winner()
        state.game_over = True
        return state

    def run_preparation_phase(self):
        """Run the preparation phase of the game."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        self.state.current_phase = GamePhase.PREPARATION

        # Keep the setup-selected starter for round one, then alternate each round.
        if self.state.current_round > 1:
            self.state.first_player_index = (
                self.state.first_player_index + 1
            ) % self.state.number_players

        # Add plant food equal to the food value of the drawn card to the watering hole
        if BAMBOO_GROVE in self.state.modules:
            self.state.watering_hole_bamboo += self.state.bamboo_per_round

        else:
            self.state.watering_hole_plant += self.state.plant_per_round

        # Getting a new species for each player
        self.add_new_species()

        # Starting by first player, each player draws cards based on difficulty.
        for player_offset in range(self.state.number_players):
            player_index = (
                self.state.first_player_index + player_offset
            ) % self.state.number_players
            player = self.state.players[player_index]

            if not self.state.modules:
                for _ in range(self.state.difficulty.cards_to_draw):
                    player.hand.append(
                        self.draw_card(self.state.nature_deck, self.state.nature_discard)
                    )

            else:
                for _ in range(self.state.difficulty.cards_to_draw_modules):
                    player.hand.append(
                        self.draw_card(self.state.nature_deck, self.state.nature_discard)
                    )

                module_count = len(self.state.modules)
                cards_per_module = {1: 3, 2: 2}.get(module_count, 1)

                for module in self.state.modules:
                    module_deck = self.state.module_decks[module]

                    for _ in range(cards_per_module):
                        player.hand.append(self.draw_card(module_deck.deck, module_deck.discard))

    def run_adaptation_phase(self):
        """Run the adaptation phase."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        self.state.current_phase = GamePhase.ADAPTATION

        for offset in range(self.state.number_players):
            player_index = (self.state.first_player_index + offset) % self.state.number_players
            player: Player = self.state.players[player_index]
            AdaptationRules.adapt_player(self.state, player, self.rng)

    def run_feeding_phase(self):
        """Run the feeding phase."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        self.state.current_phase = GamePhase.FEEDING
        # Starting with first player, players will alternate feeding turns.
        # The feeding phase continues until no species is hungry.
        hungry_populations_left = any(
            species.is_hungry for player in self.state.players for species in player.species
        )

        while hungry_populations_left and any(not player.passing for player in self.state.players):
            for player_offset in range(self.state.number_players):
                player_index = (
                    self.state.first_player_index + player_offset
                ) % self.state.number_players
                active_player = self.state.players[player_index]

                if not active_player.passing:
                    self.take_feeding_turn(active_player)

    def run_scoring_phase(self):
        """Run the scoring phase of the game."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        self.state.current_phase = GamePhase.SCORING
        ScoringRules.score_round(self.state, self.rng)

    def draw_card(self, deck: list[T], discard: list[T] | None = None) -> T:
        """Draw a card, reshuffling its discard pile when needed."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        return ActionApplier.draw_card(deck, self.rng, discard)

    def add_new_species(self) -> None:
        """Add a new species to each player's list of species."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        PreparationRules.add_new_species(self.state, self.rng)

    def assign_card_to_correct_candidate(
        self,
        player: Player,
        temporary_hand: list[TraitCard],
    ) -> None:
        """Compatibility entry point for assigning one adaptation card."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        AdaptationRules.assign_card_to_correct_candidate(
            self.state,
            player,
            temporary_hand,
            self.rng,
        )

    def assign_leftover_cards_to_hunters(
        self,
        player: Player,
        temporary_hand: list[TraitCard],
        increase: SymbolIncrease,
    ) -> None:
        """Compatibility entry point for using leftover adaptation cards."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        AdaptationRules.assign_leftover_cards_to_hunters(
            self.state,
            player,
            temporary_hand,
            increase,
        )

    def take_feeding_turn(self, active_player: Player) -> None:
        """Delegate one player's feeding turn to the feeding rules."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        FeedingRules.take_feeding_turn(self.state, active_player, self.rng)

    def choose_species_to_feed(self, active_player: Player) -> list[Species]:
        """Return hungry species in the order selected by the feeding rules."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        return FeedingRules.choose_species_to_feed(self.state, active_player)

    def define_winner(self) -> Player | None:
        """Determine the winner. Score decides first, then trait count; a remaining tie is a draw."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        if not self.state.players:
            return None

        highest_score = max(player.score for player in self.state.players)
        score_leaders = [player for player in self.state.players if player.score == highest_score]

        if len(score_leaders) == 1:
            return score_leaders[0]

        highest_trait_count = max(
            sum(len(species.trait_cards) for species in player.species) for player in score_leaders
        )
        trait_leaders = [
            player
            for player in score_leaders
            if sum(len(species.trait_cards) for species in player.species) == highest_trait_count
        ]

        if len(trait_leaders) == 1:
            return trait_leaders[0]

        return None
