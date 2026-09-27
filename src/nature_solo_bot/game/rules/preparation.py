from nature_solo_bot.game.model.player import Player
from nature_solo_bot.game.model.species import Species
from nature_solo_bot.game.model.solo_species import SoloEffect
from nature_solo_bot.game.model.trait_cards import HUNTER


class PreparationRules:
    """Rules applied during preparation"""

    @staticmethod
    def solo_species_effect_when_played(
        species: Species, player: Player,
    ) -> None:
        """Calls the correct Solo card effect"""
        if species.solo_species.effect_id == SoloEffect.PREDATOR:
            PreparationRules.predator_effect(species)

        if species.solo_species.effect_id == SoloEffect.PROPAGATOR:
            PreparationRules.propagator_effect(player)

    @staticmethod
    def predator_effect(species: Species) -> None:
        """When Played: Add the Hunter trait if the species is size 2 or less."""
        if species.size <= 2:
            species.add_trait(HUNTER)

    @staticmethod
    def propagator_effect(player: Player) -> None:
        """When played: If Rani has no hunter, add the Hunter trait to her largest species (oldest breeaks ties)."""
        if not any(existing_species.is_hunter for existing_species in player.species):
            largest_species = max(
                player.species,
                key=lambda item: (item.size, -item.round_created),
            )
            largest_species.add_trait(HUNTER)
