from random import Random

from ..model.card import Card
from ..model.player import Player
from ..model.species import Species
from ..model.solo_species import SoloEffect
from ..model.hunter_card import HunterCard
from .trait_effects import TraitEffectRules
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
        nature_discard: list[Card],
        rng: Random,
        state: GameState,
    ) -> bool:
        is_full = len(species.trait_cards) >= max_traits
        if is_full and not species.trait_cards:
            return False

        hunter_card = HunterCard()
        if not is_full:
            attached = species.add_trait_card(hunter_card, max_traits=max_traits)
        else:
            replacement_card = rng.choice(species.trait_cards)
            attached = player.replace_trait_card(
                species,
                replacement_card,
                hunter_card,
                nature_discard,
                max_traits=max_traits,
            )

        if attached:
            TraitEffectRules.on_attach(species, hunter_card.trait, state)
        return attached
