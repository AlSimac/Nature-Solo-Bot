"""Action application stub."""

from random import Random

from ..game.model.player import Player
from ..game.model.species import Species
from ..game.model.state import GameState
from ..game.model.minimodules import Minimodules


class ActionApplier:
    """Applies a selected action to the current game state."""

    def discard_card_for_watering_hole(
        state: GameState,
        player: Player,
        rng: Random,
    ):
        """Discard a card to add food to the watering hole"""
        rng.shuffle(player.hand)
        discarded_card = player.hand.pop()
        state.nature_discard.append(discarded_card)
        state.watering_hole_plant += discarded_card.food_value

    def kill_populations(state: GameState, loss: int, species: Species, player: Player):
        """Kill populations of a species"""
        for _ in range(min(loss, species.population)):
            ActionApplier.kill_one_population(state, species, player)

    def kill_one_population(state: GameState, species: Species, player: Player):
        """Kill one population of a species"""
        # If the species is fully-fed, the killed population was carrying 1 food
        if species.total_food == species.population:
            if species.plant_food > 0:
                species.plant_food -= 1

            elif species.meat_food > 0:
                species.meat_food -= 1

        species.population -= 1
        species.lost_population += 1
        player.lost_population += 1

        if Minimodules.ELEPHANT_GRAVEYARD in state.minimodules:
            state.elephant_graveyard_meat += 1

        # Killing the last species triggers extinction
        if species.population == 0:
            player.return_extinct_species(species)
