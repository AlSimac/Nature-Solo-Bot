from nature_solo_bot.engine.action_applier import ActionApplier
from nature_solo_bot.game.model.player import Player
from nature_solo_bot.game.model.species import Species
from nature_solo_bot.game.model.state import GameState


PLANT = "plant_food"
MEAT = "meat_food"


class FeedingRules:


    def forage(state: GameState, forager: Species):
        """ Forage feeding action"""
        plant_food_taken = FeedingRules.plant_food_taken_in_one_forage(forager, state.watering_hole_plant)
        state.watering_hole_plant -= plant_food_taken
        FeedingRules.eat(forager, PLANT, plant_food_taken)
    
    def hunt(state: GameState, player: Player, hunter: Species):
        """ Hunt feeding action"""
        # Find valid targets and calculate losses
        possible_preys = FeedingRules.find_valid_targets(state, hunter)

        if not possible_preys:
            return False
        
        least_dangerous_preys = FeedingRules.count_own_losses(state, hunter, possible_preys, player)
        chosen_prey, loss = FeedingRules.sort_preys(player, least_dangerous_preys)[0]
        # Actual hunt action
        FeedingRules.eat(hunter, MEAT, chosen_prey.size)        
        ActionApplier.kill_one_population(state, chosen_prey, player)

        if loss > 0:
            ActionApplier.kill_populations(state, loss, hunter, player)

        return True

    def eat(species: Species, food_type: str, food_taken: int):
        """ Define the eat action"""
        if food_type == PLANT:
            species.plant_food += food_taken

        elif food_type == MEAT:
            species.meat_food += food_taken
            
        species.total_food += food_taken
        species.is_hungry = species.total_food < species.population

    def starve(state: GameState, species: Species, player: Player):
        """ Define the starve action"""
        ActionApplier.kill_one_population(state, species, player)

    @staticmethod
    def plant_food_taken_in_one_forage(species: Species, available_food: int) -> int:
        return min(
            species.forage_value,
            max(0, species.population - species.total_food),
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
    def count_own_losses(
        state: GameState,
        hunter: Species,
        possible_preys: list[Species],
        player: Player,
    ) -> list[tuple[Species, int]]:
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
            (prey, losses)
            for prey, losses in loss_per_prey.items()
            if losses == minimum_losses
        ]
        return least_dangerous_preys

    @staticmethod
    def sort_preys(
        player: Player,
        preys: list[tuple[Species, int]],
    ) -> list[tuple[Species, int]]:
        """Sort opponent-owned prey first, then by size and age."""
        return sorted(
            preys,
            key=lambda prey_and_loss: (
                prey_and_loss[0] in player.species,
                prey_and_loss[0].size,
                prey_and_loss[0].round_created,
            ),
        )
        
