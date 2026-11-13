"""Rules for scoring and end-of-round species changes."""

from random import Random

from nature_solo_bot.game.model.modules import BAMBOO_GROVE
from nature_solo_bot.game.model.trait_cards import MONOPHAGOUS
from nature_solo_bot.game.rules.feeding import BAMBOO

from ..model.card import Card
from ..model.player import Player
from ..model.species import Species
from ..model.state import GameState


class ScoringRules:
    """Apply the scoring and cleanup rules at the end of a round."""

    @staticmethod
    def score_round(state: GameState, rng: Random) -> None:
        for player_offset in range(state.number_players):
            # Resetting the players' status
            player_index = (state.first_player_index + player_offset) % state.number_players
            active_player: Player = state.players[player_index]
            active_player.passing = False

            # adding food to score bags
            for species in active_player.species:
                # In the case of Bamboo Grove, discard the unscorable food
                if BAMBOO_GROVE in state.modules:
                    if MONOPHAGOUS in species.traits:
                        species.eaten_food[food_type] = (
                            0 for food_type in species.eaten_food if food_type != BAMBOO
                        )

                    else:
                        species.eaten_food[BAMBOO] = 0

                active_player.score += species.total_food

                # reset species' eaten food
                for food_type in species.eaten_food:
                    species.eaten_food[food_type] = 0

                # Apply population loss effects
                if species.lost_population > 0:
                    ScoringRules._apply_population_loss_effects(state, species, rng)
                    species.lost_population = 0

                # Switch tree if the species lost population
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
        """Apply the effects of population loss for a species."""
        species.switch_tree_color()

        # Discarding a trait card if the species lost population
        if species.trait_cards:
            removed_trait = rng.choice(species.trait_cards)
            species.remove_trait_card(removed_trait)

            if isinstance(removed_trait, Card):
                state.trait_discard_pile(removed_trait).insert(0, removed_trait)
