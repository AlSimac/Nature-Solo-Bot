from collections.abc import Iterable
from copy import copy
from random import Random

from nature_solo_bot.game.model.modules import BAMBOO_GROVE

from ...engine.action_applier import ActionApplier
from ..model.player import Player
from ..model.species import Species
from ..model.state import GameState
from ..model.trait_cards import (
    AVID_FORAGER,
    CLAWED,
    FAST,
    HORNED,
    MONOPHAGOUS,
    OPPORTUNISTIC,
    SCAVENGING,
    SOCIAL,
    TUSKED,
)

PLANT = "plant_food"
MEAT = "meat_food"
BAMBOO = "bamboo_food"


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
            available_food = 0

            if not species.is_hunter:
                # foragers check each available food type in order of priority
                available_food, food_type = FeedingRules.food_type_eating_priorities(
                    state, active_player, species
                )

                # if the species can't forage, go to the next one
                if available_food <= 0:
                    continue

                # if the watering hole has enough food, forage without discarding cards
                if not FeedingRules._forage_with_refill(
                    state, active_player, species, food_type, rng
                ):
                    continue

                for _ in range(species.trait_count(AVID_FORAGER.effect_id)):
                    if not FeedingRules._forage_with_refill(
                        state, active_player, species, food_type, rng
                    ):
                        break

                successful_feeding = True
                break

            if FeedingRules.hunt(state, active_player, species):
                successful_feeding = True

                # Triggering Scavenging
                FeedingRules._trigger_trait_feeding(
                    (species for player in state.players for species in player.species),
                    SCAVENGING.effect_id,
                    2,
                    MEAT,
                )

                break

        if successful_feeding:
            if state.watering_hole_food[PLANT] > 0:
                FeedingRules._trigger_trait_feeding(
                    active_player.species,
                    OPPORTUNISTIC.effect_id,
                    2,
                    MEAT,
                )

        else:
            starving_species = FeedingRules.choose_species_to_starve(active_player)[0]
            FeedingRules.starve(state, starving_species, active_player)

    @staticmethod
    def food_type_eating_priorities(
        state: GameState, active_player: Player, species: Species
    ) -> tuple[int, str]:
        """Return the amount of food available for the species to eat, by food type priorities."""
        priorities = [PLANT]
        available_food = 0
        food_type_to_eat = PLANT

        if BAMBOO_GROVE in state.modules:
            if MONOPHAGOUS in [trait.effect_id for trait in species.traits]:
                priorities.insert(0, BAMBOO)

            else:
                priorities.append(BAMBOO)

        for food_type in priorities:
            available_food = FeedingRules.get_available_food(state, active_player, food_type)

            if available_food > 0:
                food_type_to_eat = food_type
                break

        return available_food, food_type_to_eat

    @staticmethod
    def _forage_with_refill(
        state: GameState,
        player: Player,
        species: Species,
        food_type: str,
        rng: Random,
    ) -> bool:
        """Forage once, discarding cards first when the watering hole needs food."""
        while player.hand:
            available_food = FeedingRules.get_available_food(state, player, food_type)
            forage_amount = FeedingRules.food_taken_in_one_forage(
                species,
                available_food,
                food_type,
            )

            if state.watering_hole_food[food_type] >= forage_amount:
                break

            ActionApplier.discard_card_for_watering_hole(state, player, rng, food_type)

        can_forage = state.watering_hole_food[food_type] > 0

        FeedingRules.forage(state, species, food_type)
        return can_forage

    @staticmethod
    def choose_species_to_feed(
        state: GameState,
        active_player: Player,
    ) -> list[Species]:
        """Return foragers by projected total food gain, followed by hunters oldest-first."""
        hungry_species = [species for species in active_player.species if species.is_hungry]
        # for each forager, count the projected food gain from foraging,
        # including any triggered effects, and sort by that value
        foragers = []
        for index, species in enumerate(hungry_species):
            if species.is_hunter:
                continue

            available_food, food_type = FeedingRules.food_type_eating_priorities(
                state, active_player, species
            )
            foragers.append(
                (
                    index,
                    species,
                    FeedingRules._projected_food_gain_from_forage(
                        state, active_player, species, available_food, food_type
                    ),
                )
            )
        foragers.sort(key=lambda candidate: (-candidate[2], candidate[0]))
        hunters = [species for species in hungry_species if species.is_hunter]
        return [species for _, species, _ in foragers] + hunters

    @staticmethod
    def _projected_food_gain_from_forage(
        state: GameState,
        active_player: Player,
        forager: Species,
        available_food: int,
        food_type: str = PLANT,
    ) -> int:
        """Project all forages and triggers, valuing each discarded card at three food."""
        all_species = [species for player in state.players for species in player.species]
        simulated_species = {id(species): copy(species) for species in all_species}
        simulated_forager = simulated_species[id(forager)]
        simulated_active_species = [
            simulated_species[id(species)] for species in active_player.species
        ]
        simulated_watering_hole_food = state.watering_hole_food[food_type]
        simulated_plant_food = state.watering_hole_food[PLANT]
        simulated_total_watering_hole_food = state.total_watering_hole_food

        if food_type == BAMBOO:
            remaining_cards = sum(card.deck == BAMBOO_GROVE for card in active_player.hand)

        else:
            remaining_cards = sum(card.deck != BAMBOO_GROVE for card in active_player.hand)

        simulated_available_food = available_food
        successful_forage = False

        for _ in range(1 + forager.trait_count(AVID_FORAGER.effect_id)):
            while remaining_cards:
                forage_amount = FeedingRules.food_taken_in_one_forage(
                    simulated_forager,
                    simulated_available_food,
                    food_type,
                )
                if simulated_watering_hole_food >= forage_amount:
                    break

                simulated_watering_hole_food += 3
                simulated_total_watering_hole_food += 3

                if food_type == PLANT:
                    simulated_plant_food += 3

                remaining_cards -= 1

            if simulated_watering_hole_food <= 0:
                break

            food_eaten = FeedingRules.eat(
                simulated_forager,
                food_type,
                simulated_forager.forage_value,
                available_from_source=simulated_watering_hole_food,
            )
            simulated_watering_hole_food -= food_eaten
            simulated_total_watering_hole_food -= food_eaten

            if food_type == PLANT:
                simulated_plant_food -= food_eaten

            simulated_available_food = simulated_watering_hole_food + 3 * remaining_cards
            successful_forage = True

            if food_eaten > 0 and simulated_total_watering_hole_food == 0:
                FeedingRules._trigger_trait_feeding(
                    simulated_species.values(),
                    TUSKED.effect_id,
                    1,
                    MEAT,
                )

        if successful_forage and simulated_plant_food > 0:
            FeedingRules._trigger_trait_feeding(
                simulated_active_species,
                OPPORTUNISTIC.effect_id,
                2,
                MEAT,
            )

        return sum(
            simulated.total_food - original.total_food
            for original, simulated in zip(active_player.species, simulated_active_species)
        )

    @staticmethod
    def get_available_food(state: GameState, active_player: Player, food_type: str = PLANT) -> int:
        """Calculate watering-hole food plus potential food from cards in hand."""
        bamboo_grove_cards = sum(card.deck == BAMBOO_GROVE for card in active_player.hand)
        non_bg_cards = len(active_player.hand) - bamboo_grove_cards

        if food_type == BAMBOO:
            return state.watering_hole_food[BAMBOO] + 3 * bamboo_grove_cards

        return state.watering_hole_food[food_type] + 3 * non_bg_cards

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

    def forage(state: GameState, forager: Species, food_type: str = PLANT):
        """Forage feeding action"""
        food_eaten = FeedingRules.eat(
            forager,
            food_type,
            forager.forage_value,
            available_from_source=state.watering_hole_food[food_type],
        )
        FeedingRules.remove_watering_hole_food(state, food_eaten, food_type)

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
        FeedingRules.eat(hunter, MEAT, chosen_prey.size)
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

    @staticmethod
    def remove_watering_hole_food(
        state: GameState,
        amount: int,
        food_type: str,
    ) -> None:
        """Remove food from the watering hole."""
        food_to_remove = min(max(0, amount), state.watering_hole_food[food_type])

        if food_to_remove == 0:
            return

        state.watering_hole_food[food_type] -= food_to_remove

        if state.total_watering_hole_food == 0:
            FeedingRules._trigger_trait_feeding(
                (species for player in state.players for species in player.species),
                TUSKED.effect_id,
                1,
                MEAT,
            )

    @staticmethod
    def _trigger_trait_feeding(
        species_list: Iterable[Species], trait_id: str, food_per_trigger: int, food_type: str
    ) -> None:
        """Managed the triggered effects that make a species eat."""
        for species in species_list:
            for _ in range(species.trait_count(trait_id)):
                food_to_eat = min(
                    food_per_trigger,
                    max(0, species.population - species.total_food),
                )
                FeedingRules.eat(species, food_type, food_to_eat)

    @staticmethod
    def _food_amount_to_eat(
        species: Species,
        food_type: str,
        base_amount: int,
        available_from_source: int | None = None,
    ) -> int:
        social_count = sum(trait.effect_id == SOCIAL.effect_id for trait in species.traits)
        bonus = 2 * social_count

        if food_type == PLANT:
            clawed_count = sum(trait.effect_id == CLAWED.effect_id for trait in species.traits)
            bonus += 2 * clawed_count

        limits = [
            base_amount + bonus,
            max(0, species.population - species.total_food),
        ]

        if available_from_source is not None:
            limits.append(max(0, available_from_source))

        return min(limits)

    @staticmethod
    def eat(
        species: Species,
        food_type: str,
        base_amount: int,
        available_from_source: int | None = None,
    ) -> int:
        amount = FeedingRules._food_amount_to_eat(
            species, food_type, base_amount, available_from_source
        )

        if food_type == PLANT:
            species.plant_food += amount

        elif food_type == BAMBOO:
            species.bamboo_food += amount

        else:
            species.meat_food += amount

        return amount

    def starve(state: GameState, species: Species, player: Player):
        """Define the starve action"""
        ActionApplier.kill_one_population(state, species, player)

    @staticmethod
    def food_taken_in_one_forage(
        species: Species, available_food: int, food_type: str = PLANT
    ) -> int:
        return FeedingRules._food_amount_to_eat(
            species,
            food_type,
            species.forage_value,
            available_from_source=available_food,
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
