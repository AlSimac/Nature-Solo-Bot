from random import Random

from ..model.trait_cards import CLAWED, FAST, HORNED, OPPORTUNISTIC, SCAVENGING

from ...engine.action_applier import ActionApplier
from ..model.player import Player
from ..model.species import Species
from ..model.state import GameState

PLANT = "plant_food"
MEAT = "meat_food"


class FeedingRules:

    @staticmethod
    def take_feeding_turn(
        state: GameState,
        active_player: Player,
        rng: Random,
    ) -> None:
        """Feed or starve one species according to the solo feeding priority."""
        ordered_species = FeedingRules.choose_species_to_feed(state, active_player)
        if not ordered_species:
            active_player.passing = True
            return

        successful_feeding = False

        for species in ordered_species:
            if not species.is_hunter:
                available_food = FeedingRules.get_available_food(state, active_player)

                if available_food <= 0:
                    continue

                while (
                    state.watering_hole_plant
                    < FeedingRules.plant_food_taken_in_one_forage(species, available_food)
                    and active_player.hand
                ):
                    ActionApplier.discard_card_for_watering_hole(state, active_player, rng)

                FeedingRules.forage(state, species)
                successful_feeding = True
                break

            if FeedingRules.hunt(state, active_player, species):
                successful_feeding = True

                # Triggering Scavenging
                for player in state.players:
                    for species in player.species:
                        scavenging_count = sum(
                            trait.effect_id == SCAVENGING.effect_id for trait in species.traits
                        )

                        for _ in range(scavenging_count):
                            extra_food = min(
                                2,
                                max(0, species.population - species.total_food),
                            )
                            FeedingRules.eat(species, MEAT, extra_food)

                break

        if successful_feeding:
            if state.watering_hole_plant > 0:
                for species in active_player.species:
                    opportunistic_count = sum(
                        trait.effect_id == OPPORTUNISTIC.effect_id for trait in species.traits
                    )
                    for _ in range(opportunistic_count):
                        extra_food = min(
                            2,
                            max(0, species.population - species.total_food),
                        )
                        FeedingRules.eat(species, MEAT, extra_food)

        else:
            starving_species = FeedingRules.choose_species_to_starve(active_player)[0]
            FeedingRules.starve(state, starving_species, active_player)

    @staticmethod
    def choose_species_to_feed(
        state: GameState,
        active_player: Player,
    ) -> list[Species]:
        """Return hungry foragers by food yield, followed by hunters oldest-first."""
        available_food = FeedingRules.get_available_food(state, active_player)
        hungry_species = [species for species in active_player.species if species.is_hungry]
        foragers = [
            (
                index,
                species,
                FeedingRules.plant_food_taken_in_one_forage(species, available_food),
            )
            for index, species in enumerate(hungry_species)
            if not species.is_hunter
        ]
        foragers.sort(key=lambda candidate: (-candidate[2], candidate[0]))
        hunters = [species for species in hungry_species if species.is_hunter]
        return [species for _, species, _ in foragers] + hunters

    @staticmethod
    def get_available_food(state: GameState, active_player: Player) -> int:
        """Calculate watering-hole food plus potential food from cards in hand."""
        return state.watering_hole_plant + 3 * len(active_player.hand)

    @staticmethod
    def choose_species_to_starve(active_player: Player) -> list[Species]:
        """Choose the oldest hungry hunter, then unfed and remaining foragers."""
        hunters = [
            species for species in active_player.species if species.is_hungry and species.is_hunter
        ]
        unfed_foragers = sorted(
            [
                species
                for species in active_player.species
                if species.total_food == 0 and not species.is_hunter
            ],
            key=lambda species: (species.population, species.round_created),
        )
        foragers = [
            species
            for species in active_player.species
            if species.is_hungry and not species.is_hunter and species not in unfed_foragers
        ]
        return hunters + unfed_foragers + foragers

    def forage(state: GameState, forager: Species):
        """Forage feeding action"""
        plant_food_taken = FeedingRules.plant_food_taken_in_one_forage(
            forager, state.watering_hole_plant
        )
        state.watering_hole_plant -= plant_food_taken
        FeedingRules.eat(forager, PLANT, plant_food_taken)

    def hunt(state: GameState, player: Player, hunter: Species):
        """Hunt feeding action"""
        # Find valid targets and calculate losses
        possible_preys = FeedingRules.find_valid_targets(state, hunter)

        if not possible_preys:
            return False

        least_dangerous_preys = FeedingRules.count_own_losses(
            hunter,
            possible_preys,
            player,
        )
        chosen_prey, _ = FeedingRules.sort_preys(player, least_dangerous_preys)[0]
        prey_owner = next(
            (candidate for candidate in state.players if chosen_prey in candidate.species),
            None,
        )
        if prey_owner is None:
            raise ValueError("The selected prey does not belong to a player in the game state.")

        hunter_loss = FeedingRules.hunter_loss_caused_by_prey(chosen_prey, hunter)

        # Actual hunt action
        FeedingRules.eat(
            hunter, MEAT, min(chosen_prey.size, (hunter.population - hunter.total_food))
        )
        ActionApplier.kill_one_population(state, chosen_prey, prey_owner)

        if hunter_loss > 0:
            ActionApplier.kill_populations(state, hunter_loss, hunter, player)

        return True

    @staticmethod
    def hunter_loss_caused_by_prey(prey: Species, hunting_species: Species) -> int:
        """Return hunter populations lost to the prey's Horned traits."""
        return min(
            sum(prey.size for trait in prey.traits if trait.effect_id == HORNED.effect_id),
            hunting_species.population,
        )

    def eat(species: Species, food_type: str, food_taken: int):
        """Define the eat action"""
        if food_type == PLANT:
            species.plant_food += food_taken

        elif food_type == MEAT:
            species.meat_food += food_taken

    def starve(state: GameState, species: Species, player: Player):
        """Define the starve action"""
        ActionApplier.kill_one_population(state, species, player)

    @staticmethod
    def plant_food_taken_in_one_forage(species: Species, available_food: int) -> int:
        clawed_count = sum(1 for trait in species.traits if trait.effect_id == CLAWED.effect_id)

        return min(
            species.forage_value + 2 * clawed_count,
            max(0, species.population - species.total_food),
            available_food,
        )

    @staticmethod
    def find_valid_targets(state: GameState, hunting_species: Species) -> list[Species]:
        """Find all possible prey for this hunter"""
        valid_targets = []

        for player in state.players:
            for species in player.species:
                if FeedingRules.is_valid_target(species, hunting_species):
                    valid_targets.append(species)

        return valid_targets

    @staticmethod
    def is_valid_target(possible_prey: Species, hunting_species: Species) -> bool:
        """Check if the species is a valid target for hunting"""
        is_valid = True

        # Cannot hunt itself
        if possible_prey is hunting_species:
            is_valid = False

        # Cannot hunt a species with a defense value strictly greater than its attack value
        if possible_prey.defense_value > hunting_species.attack_value:
            is_valid = False

        # Cannot hunt a species with more Fast traits than itself
        if sum(1 for trait in possible_prey.traits if trait.effect_id == FAST.effect_id) > sum(
            1 for trait in hunting_species.traits if trait.effect_id == FAST.effect_id
        ):
            is_valid = False

        return is_valid

    @staticmethod
    def count_own_losses(
        hunter: Species,
        possible_preys: list[Species],
        player: Player,
    ) -> list[tuple[Species, int]]:
        """Sort the species by number of hunter's population losses"""
        loss_per_prey = {}

        for prey in possible_preys:
            own_prey_loss = int(prey in player.species)
            hunter_loss = FeedingRules.hunter_loss_caused_by_prey(prey, hunter)
            loss_per_prey[prey] = own_prey_loss + hunter_loss

        if not loss_per_prey:
            return []

        minimum_losses = min(loss_per_prey.values())
        least_dangerous_preys = [
            (prey, losses) for prey, losses in loss_per_prey.items() if losses == minimum_losses
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
