"""Game engine stub."""

import random
from typing import TypeVar

from ..game.model.card import Card
from ..game.model.player import Player
from ..game.model.species import Species
from ..game.model.state import (
    DIFFICULTY_MEDIUM,
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

T = TypeVar("T")


class GameEngine:
    """Runs a complete game from initialization through resolution."""

    def __init__(
        self,
        seed: int | None = None,
        difficulty: Difficulty = DIFFICULTY_MEDIUM,
    ):
        self.seed = seed
        self.difficulty = difficulty
        self.rng = random.Random(seed)
        self.state: GameState | None = None

    def setup_game(self) -> GameState:
        """Set up the initial game state."""
        state = GameState(difficulty=self.difficulty)
        state.seed = self.seed
        # Instantiate two players for the game
        state.players = Player.init_two_players()
        state.active_player_index = 1
        # Decks preparation
        self.shuffle_all_decks(state)
        self.state = state
        # Drawing a card from the deck for the watering hole plant
        state.food_card = self.draw_card(state.nature_deck, state.nature_discard)
        state.plant_per_round = state.food_card.food_value * state.number_players
        state.first_player_index = self.rng.randrange(state.number_players)
        # Adding a new species for each player at the start of the game
        # this is before setting the current round to 1,
        # so that the species are created with round_created = 0
        # because Solo automa starts with 2 species.
        self.add_new_species()
        state.current_round = 1
        return state

    def shuffle_all_decks(self, state):
        """Shuffle all decks for the game."""
        # Shuffle both players' solo decks
        state.players[0].solo_deck = Card.init_solo_deck()
        self.rng.shuffle(state.players[0].solo_deck)
        state.players[1].solo_deck = Card.init_solo_deck()
        self.rng.shuffle(state.players[1].solo_deck)
        # Shuffle the Nature trait decks
        state.nature_deck = Card.init_nature_deck()
        self.rng.shuffle(state.nature_deck)

    def draw_card(self, deck: list[T], discard: list[T] | None = None) -> T:
        """Remove and return the top card from the deck."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        # Reshuffle the discard pile into the deck if the deck is empty
        if not deck and discard:
            deck.extend(discard)
            discard.clear()
            self.rng.shuffle(deck)

        return deck.pop()

    def run_game(self) -> GameState:
        """Set up and run the entire game, returning its final state."""
        state = self.state if self.state is not None else self.setup_game()

        while state.current_round <= state.total_rounds:
            self.run_preparation_phase()
            self.run_adaptation_phase()
            self.run_feeding_phase()
            self.run_scoring_phase()
            state.current_round += 1

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

        # Add plant food equal tothe food value of the drawn card to the watering hole
        self.state.watering_hole_plant += self.state.plant_per_round
        # Getting a new species for each player
        self.add_new_species()

        # Starting by first player, each player draws cards based on difficulty.
        for player_offset in range(self.state.number_players):
            player_index = (
                self.state.first_player_index + player_offset
            ) % self.state.number_players
            player = self.state.players[player_index]

            for _ in range(self.state.difficulty.cards_to_draw):
                player.hand.append(
                    self.draw_card(self.state.nature_deck, self.state.nature_discard)
                )

    def add_new_species(self):
        """Add a new species to the player's list of species."""
        for player in self.state.players:
            solo_card = self.draw_card(player.solo_deck, player.solo_discard)
            new_species = Species(solo_card=solo_card, round_created=self.state.current_round)

            if self.state.current_round == 1:
                new_species.population = self.state.difficulty.round_one_population

            new_species.population += player.lost_population
            player.lost_population = 0
            player.species.append(new_species)

            if solo_card.effect_id:
                PreparationRules.solo_species_effect_when_played(
                    new_species,
                    player,
                    max_traits=self.state.max_traits,
                    nature_discard=self.state.nature_discard,
                    rng=self.rng,
                    state=self.state,
                )

    def run_adaptation_phase(self):
        """Run the adaptation phase."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        self.state.current_phase = GamePhase.ADAPTATION

        for offset in range(self.state.number_players):
            player_index = (self.state.first_player_index + offset) % self.state.number_players
            player: Player = self.state.players[player_index]
            AdaptationRules.adapt_player(self.state, player, self.rng)

    def assign_card_to_correct_candidate(self, player: Player, temporary_hand: list[TraitCard]):
        """Compatibility entry point for assigning one adaptation card."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        AdaptationRules.assign_card_to_correct_candidate(
            self.state, player, temporary_hand, self.rng
        )

    def assign_leftover_cards_to_hunters(
        self, player: Player, temporary_hand: list[TraitCard], increase: SymbolIncrease
    ):
        """Compatibility entry point for using leftover adaptation cards."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        AdaptationRules.assign_leftover_cards_to_hunters(
            self.state, player, temporary_hand, increase
        )

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

    def run_scoring_phase(self):
        """Run the scoring phase of the game."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        self.state.current_phase = GamePhase.SCORING
        ScoringRules.score_round(self.state, self.rng)
