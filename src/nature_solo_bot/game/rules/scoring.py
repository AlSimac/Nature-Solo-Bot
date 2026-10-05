"""Rules for scoring and end-of-round species changes."""

from random import Random

from ..model.card import Card
from ..model.player import Player
from ..model.species import Species
from ..model.state import GameState


class ScoringRules:
    """Apply the scoring and cleanup rules at the end of a round."""

    @staticmethod
    def score_round(state: GameState, rng: Random) -> None:
        for player_offset in range(state.number_players):
            player_index = (state.first_player_index + player_offset) % state.number_players
            active_player: Player = state.players[player_index]
            active_player.score += sum(species.total_food for species in active_player.species)
            active_player.passing = False

            for species in active_player.species:
                species.plant_food = 0
                species.meat_food = 0

                if species.lost_population > 0:
                    ScoringRules._apply_population_loss_effects(state, species, rng)
                    species.lost_population = 0

                if state.current_round == state.total_rounds - 1:
                    species.last_round_tree()

            if state.current_round == state.total_rounds:
                active_player.score += 2 * len(active_player.species)

    @staticmethod
    def _apply_population_loss_effects(
        state: GameState,
        species: Species,
        rng: Random,
    ) -> None:
        species.switch_tree_color()

        if species.trait_cards:
            removed_trait = rng.choice(species.trait_cards)
            species.remove_trait_card(removed_trait)

            if isinstance(removed_trait, Card):
                state.nature_discard.append(removed_trait)
