from random import Random

from ..model.card import Card
from ..model.player import Player
from ..model.species import Species
from ..model.solo_species import SoloEffect
from ..model.hunter_card import HunterCard


class PreparationRules:
    """Rules applied during preparation"""

    @staticmethod
    def solo_species_effect_when_played(
        species: Species,
        player: Player,
        *,
        max_traits: int,
        nature_discard: list[Card],
        hunter_deck: list[HunterCard],
        rng: Random,
    ) -> None:
        """Calls the correct Solo card effect"""
        if species.solo_species.effect_id == SoloEffect.PREDATOR:
            PreparationRules.predator_effect(
                species,
                player,
                max_traits=max_traits,
                nature_discard=nature_discard,
                hunter_deck=hunter_deck,
                rng=rng,
            )

        if species.solo_species.effect_id == SoloEffect.PROPAGATOR:
            PreparationRules.propagator_effect(
                player,
                max_traits=max_traits,
                nature_discard=nature_discard,
                hunter_deck=hunter_deck,
                rng=rng,
            )

    @staticmethod
    def predator_effect(
        species: Species,
        player: Player,
        *,
        max_traits: int,
        nature_discard: list[Card],
        hunter_deck: list[HunterCard],
        rng: Random,
    ) -> None:
        """When Played: Add the Hunter trait if the species is size 2 or less."""
        if species.size <= 2:
            PreparationRules.add_hunter_card(
                species,
                player,
                max_traits=max_traits,
                nature_discard=nature_discard,
                hunter_deck=hunter_deck,
                rng=rng,
            )

    @staticmethod
    def propagator_effect(
        player: Player,
        *,
        max_traits: int,
        nature_discard: list[Card],
        hunter_deck: list[HunterCard],
        rng: Random,
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
                hunter_deck=hunter_deck,
                rng=rng,
            )

    @staticmethod
    def add_hunter_card(
        species: Species,
        player: Player,
        *,
        max_traits: int,
        nature_discard: list[Card],
        hunter_deck: list[HunterCard],
        rng: Random,
    ) -> bool:
        is_full = len(species.trait_cards) >= max_traits
        if is_full and not species.trait_cards:
            return False

        hunter_card = hunter_deck.pop() if hunter_deck else HunterCard()
        if not is_full:
            return species.add_trait_card(hunter_card, max_traits=max_traits)

        replacement_card = rng.choice(species.trait_cards)
        replaced = player.replace_trait_card(
            species,
            replacement_card,
            hunter_card,
            nature_discard,
            hunter_deck,
            max_traits=max_traits,
        )
        if not replaced:
            hunter_deck.append(hunter_card)
        return replaced
