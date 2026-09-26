class PreparationRules:
    """Rules"""
    @staticmethod
    def apply_solo_effects(state: GameState) -> None:
        for player in state.players:
            for species in player.species:
                apply_species_effect(state, player, species)