from nature_solo_bot.game.model.player import Player
from nature_solo_bot.game.model.species import Species
from nature_solo_bot.game.model.state import GameState


class FeedingRules:

    def forage(state: GameState, player: Player, forager: Species):
        """ Forage feeding action"""
        plant_food_taken = FeedingRules.plant_food_taken_in_one_forage(forager, state.watering_hole_plant)
        state.watering_hole_plant -= plant_food_taken
        FeedingRules.eat(forager, plant_food_taken)
    
    def hunt(state: GameState, player: Player, hunter: Species, prey: Species):
        """ Hunt feeding action"""
        # Find valid targets
        possible_preys = FeedingRules.find_valid_targets(state, hunter)
        least_dangerous_preys = FeedingRules.count_own_losses(state, hunter, possible_preys, player)
        sorted_preys = FeedingRules.sort_preys(player, least_dangerous_preys)
        

    def eat(species: Species, food_taken: int):
        species.food += food_taken
        species.is_hungry = species.food < species.population
    
    @staticmethod
    def plant_food_taken_in_one_forage(species: Species, available_food: int) -> int:
        return min(
            species.forage_value,
            max(0, species.population - species.food),
            available_food,
        )

    @staticmethod
    def find_valid_targets(state: GameState, hunter: Species) -> list[Species]:
        """ Find all possible prey for this hunter"""
        valid_targets = []

        for player in state.players:
            for species in player.species:
                if species is not hunter and species.defense_value <= hunter.attack_value:
                    valid_targets.append(species)

            return valid_targets

    @staticmethod
    def count_own_losses(state: GameState, hunter: Species, possible_preys: list[Species], player: Player) -> list[Species]:
        """ Sort the species by number of hunter's population losses"""
        loss_per_prey = {}

        for prey in possible_preys:
            if prey in player.species:
                loss_per_prey[prey] = 1

            else:
                loss_per_prey[prey] = 0

        if not loss_per_prey:
            return []

        minimum_losses = min(loss_per_prey.values())
        least_dangerous_preys = [
            prey
            for prey, losses in loss_per_prey.items()
            if losses == minimum_losses
        ]
        return least_dangerous_preys

    @staticmethod
    def sort_preys(player: Player, preys: list[Species]) -> list[Species]:
        """Sort opponent-owned prey first, then by size and age."""
        return sorted(
            preys,
            key=lambda prey: (
                prey in player.species,
                prey.size,
                prey.round_created,
            ),
        )
        
