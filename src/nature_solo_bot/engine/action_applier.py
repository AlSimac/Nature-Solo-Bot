"""Action application stub."""


from nature_solo_bot.game.model.player import Player
from nature_solo_bot.game.model.species import Species
from nature_solo_bot.game.model.state import GameState
from nature_solo_bot.game.model.trait_card import TraitCard


class ActionApplier:
    """Applies a selected action to the current game state."""

    def discard_card_for_watering_hole(state: GameState, player: Player):
        """ Discard a card to add food to the watering hole"""
        discarded_card = player.hand.pop()
        state.nature_discard.append(discarded_card)
        state.watering_hole_plant += discarded_card.food_value

    def kill_populations(state: GameState, loss: int, species: Species, player: Player):
        """ Kill populations of a species"""
        for _ in range(loss):
            ActionApplier.kill_one_population(state, species, player)

    def kill_one_population(state: GameState, species: Species, player: Player):
        """ Kill one population of a species"""
        # If the species is fully-fed, the killed population was carrying 1 food
        if species.total_food == species.population:
            species.total_food -= 1

            if species.plant_food > 0:
                species.plant_food -= 1

            elif species.meat_food > 0:
                species.meat_food -= 1
        
        species.population -= 1
        player.lost_population += 1

        # Killing the last species triggers extinction
        if species.population == 0:
            player.return_extinct_species(species)
