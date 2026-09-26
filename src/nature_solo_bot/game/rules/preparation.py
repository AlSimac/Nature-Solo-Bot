from nature_solo_bot.game.model.player import Player
from nature_solo_bot.game.model.species import Species
from nature_solo_bot.game.model.trait_cards import HUNTER


class PreparationRules:
    """Rules applied during preparation"""

    @staticmethod
    def solo_species_effect_when_played(
        species: Species, player: Player,
    ) -> None:
        """Calls the correct Solo card effect"""
        if species.solo_species.effect_id == "predator":
            PreparationRules.predator_effect(species)

        if species.solo_species.effect_id == "propagator":
            PreparationRules.propagator_effect(species, player)

    @staticmethod
    def predator_effect(species: Species) -> None:
        """When Played: Add the Hunter trait if the species is size 2 or less."""
        if species.size <= 2:
            species.add_trait(HUNTER)

    @staticmethod
    def propagator_effect(species: Species, player: Player) -> None:
        """When played:"""
        if not any(existing_species.is_hunter for existing_species in player.species):
            
            species.add_trait(HUNTER)
