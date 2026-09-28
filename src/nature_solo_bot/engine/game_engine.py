"""Game engine stub."""


import random

from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.hunter_card import HunterCard
from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.rules.adaptation import AdaptationRules
from src.nature_solo_bot.game.model.symbol import SymbolIncrease
from src.nature_solo_bot.game.model.trait_card import TraitCard
from src.nature_solo_bot.game.rules.preparation import PreparationRules
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.state import (
    DIFFICULTY_MEDIUM,
    Difficulty,
    GamePhase,
    GameState,
)
from typing import TypeVar

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

    def run_preparation_phase(self):
        """Run the preparation phase of the game."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        self.state.current_phase = GamePhase.PREPARATION
        # Switch the first player to the new one
        self.state.first_player_index = (self.state.first_player_index + 1) % self.state.number_players
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
                player.hand.append(self.draw_card(self.state.nature_deck, self.state.nature_discard))

    def add_new_species(self):
        """Add a new species to the player's list of species."""
        for player in self.state.players:
            solo_card = self.draw_card(player.solo_deck, player.solo_discard)
            new_species = Species(solo_card=solo_card, round_created=self.state.current_round)
            
            if self.state.current_round == 1:
                new_species.population = self.state.difficulty.round_one_population
                
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
        """Run the adaptation phase"""
        self.state.current_phase = GamePhase.ADAPTATION

        for offset in range(self.state.number_players):
            player_index = (
                self.state.first_player_index + offset
            ) % self.state.number_players
            player: Player = self.state.players[player_index]
            # First, shuffle the player's hand
            self.rng.shuffle(player.hand)
            temporary_hand: list[TraitCard] = []

            # Draw cards one by one, and check the symbol
            while player.hand:
                self.assign_card_to_correct_candidate(player, temporary_hand)

            player.hand.extend(temporary_hand)
            self.rng.shuffle(player.hand)

            # If the player only has hunters, run again through the cards in hand
            # to increase size then population
            if player.species and all(species.is_hunter for species in player.species):
                # TODO
                pass

    def assign_card_to_correct_candidate(self, player: Player, temporary_hand: list[TraitCard]):
        picked_card: TraitCard = player.hand.pop(0)
        is_assigned = False
        drawn_symbol = picked_card.solo_symbol
        # Compare the symbol trough all species
        candidate_species: list[Species] = AdaptationRules.select_species_for_symbol(player, drawn_symbol)

        for candidate in candidate_species:
            candidate_symbol = next(
                        (
                            symbol
                            for symbol in candidate.solo_symbols
                            if symbol.symbol == drawn_symbol
                        ),
                        None,
                    )  
                    
            if candidate_symbol is None:
                continue

            candidate_assigned = False
            match candidate_symbol.increase:
                case SymbolIncrease.SIZE:
                    # Go to next candidate species if this one is at max size
                    if candidate.size >= self.state.max_size:
                        continue

                    # Discard the card and increase size by 1
                    candidate.size += 1
                    self.state.nature_discard.append(picked_card)
                    candidate_assigned = True

                case SymbolIncrease.POPULATION:
                    # Discard the card and increase population by 1
                    candidate.population += 1
                    self.state.nature_discard.append(picked_card)
                    candidate_assigned = True

                case None:
                    # Go to next candidate if this one is at max traits
                    if len(candidate.trait_cards) >= self.state.max_traits:
                        continue

                    # Give the card as a trait if there is a free trait slot.
                    candidate_assigned = candidate.add_trait_card(
                        picked_card,
                        max_traits=self.state.max_traits,
                    )

            if not candidate_assigned:
                continue

            if candidate_symbol.is_hunter:
                PreparationRules.add_hunter_card(
                    candidate,
                    player,
                    max_traits=self.state.max_traits,
                    nature_discard=self.state.nature_discard,
                    rng=self.rng,
                    state=self.state,
                )

            is_assigned = True
            break

        # if the card couldn't be assigned to a species,
        # set it in a temporary hand.
        if not is_assigned:
            temporary_hand.append(picked_card)