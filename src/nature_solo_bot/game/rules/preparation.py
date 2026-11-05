from random import Random

from ...engine.action_applier import ActionApplier
from ..model.card import Card
from ..model.hunter_card import HunterCard
from ..model.player import Player
from ..model.solo_species import SoloEffect
from ..model.species import Species
from ..model.state import GameState


class PreparationRules:
    """Rules applied during preparation"""

    @staticmethod
    def solo_species_effect_when_played(
        species: Species,
        player: Player,
        *,
        max_traits: int,
        nature_discard: list[Card],
        rng: Random,
        state: GameState,
    ) -> None:
        """Calls the correct Solo card effect"""
        if species.solo_species.effect_id == SoloEffect.PREDATOR:
            PreparationRules.predator_effect(
                species,
                player,
                max_traits=max_traits,
                nature_discard=nature_discard,
                rng=rng,
                state=state,
            )

        if species.solo_species.effect_id == SoloEffect.PROPAGATOR:
            PreparationRules.propagator_effect(
                player,
                max_traits=max_traits,
                nature_discard=nature_discard,
                rng=rng,
                state=state,
            )

    @staticmethod
    def predator_effect(
        species: Species,
        player: Player,
        *,
        max_traits: int,
        nature_discard: list[Card],
        rng: Random,
        state: GameState,
    ) -> None:
        """When Played: Add the Hunter trait if the species is size 2 or less."""
        if species.size <= 2:
            PreparationRules.add_hunter_card(
                species,
                player,
                max_traits=max_traits,
                nature_discard=nature_discard,
                rng=rng,
                state=state,
            )

    @staticmethod
    def propagator_effect(
        player: Player,
        *,
        max_traits: int,
        nature_discard: list[Card],
        rng: Random,
        state: GameState,
    ) -> None:
        """When played: If Rani has no hunter, add the Hunter trait to her largest species (oldest breeaks ties)."""
        if not any(existing_species.is_hunter for existing_species in player.species):
            largest_species = max(
                player.species,
                key=lambda item: (item.size, -item.round_created),
            )
            PreparationRules.add_hunter_card(
                largest_species,
                player,
                max_traits=max_traits,
                nature_discard=nature_discard,
                rng=rng,
                state=state,
            )

    @staticmethod
    def add_hunter_card(
        species: Species,
        player: Player,
        *,
        max_traits: int,
        state: GameState,
        rng: Random,
        replace_random_trait: bool = False,
    ) -> bool:
        is_full = len(species.trait_cards) >= max_traits

        if is_full and not species.trait_cards:
            return False

        hunter_card = HunterCard()

        if not is_full:
            attached = species.add_trait_card(hunter_card, max_traits=max_traits)

        elif replace_random_trait and species.trait_cards:
            replacement_card = rng.choice(species.trait_cards)
            attached = player.replace_trait_card(
                species,
                replacement_card,
                hunter_card,
                state,
                max_traits=max_traits,
            )

        else:
            return False

        return attached

    @staticmethod
    @staticmethod
    def add_new_species(state: GameState, rng: Random) -> None:
        """Add a new species to the player's list of species."""
        for player in state.players:
            solo_card = ActionApplier.draw_card(player.solo_deck, rng, player.solo_discard)
            new_species = Species(solo_card=solo_card, round_created=state.current_round)

            if state.current_round == 1:
                new_species.population = state.difficulty.round_one_population

            new_species.population += player.lost_population
            player.lost_population = 0
            new_species.size = min(
                new_species.size + player.extinct_size,
                state.max_size,
            )
            player.extinct_size = 0
            player.species.append(new_species)

            if solo_card.effect_id:
                PreparationRules.solo_species_effect_when_played(
                    new_species,
                    player,
                    max_traits=state.max_traits,
                    nature_discard=state.nature_discard,
                    rng=rng,
                    state=state,
                )
