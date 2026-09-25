"""Game engine stub."""


import random

from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.player import Player
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.state import GamePhase, GameState


class GameEngine:
    """Runs a complete game from initialization through resolution."""

    def __init__(self, seed: int | None = None):
        self.seed = seed
        self.rng = random.Random(seed)
        self.state: GameState | None = None
        

    def initialize_game(self) -> GameState:
        """Set up the initial game state."""
        state = GameState()
        state.seed = self.seed
        state.players = Player.init_two_players()
        state.active_player_index = 1
        state.deck = Card.init_deck()
        self.rng.shuffle(state.deck)
        self.state = state
        # Drawing a card from the deck for the watering hole plant
        state.food_card = self.draw_card()
        state.plant_per_round = state.food_card.food_value * state.number_players
        state.first_player_index = self.rng.randrange(state.number_players)
        # Adding a new species for each player at the start of the game
        self.add_new_species()
        state.current_round = 1
        return state

    def draw_card(self) -> Card:
        """Remove and return the top card from the deck."""
        if self.state is None:
            raise RuntimeError("The game has not been initialized.")

        # Reshuffle the discard pile into the deck if the deck is empty
        if not self.state.deck and self.state.discard:
            self.state.deck = self.state.discard
            self.rng.shuffle(self.state.deck)
            self.state.discard = []

        return self.state.deck.pop()

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
        # Starting by first player, each player draws 7 cards from the deck
        for i in range(self.state.number_players):
            for _ in range(7):
                player_index = (self.state.first_player_index + i) % self.state.number_players
                player = self.state.players[player_index]
                player.hand.append(self.draw_card())

    def add_new_species(self):
        """Add a new species to the player's list of species."""
        for player in self.state.players:
            new_species = Species(traits=[], round_created=self.state.current_round)

            if self.state.current_round == 1:
                new_species.population = 3
            player.species.append(new_species)