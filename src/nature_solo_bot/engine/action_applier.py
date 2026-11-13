"""Action application stub."""

from random import Random
from typing import TypeVar

from nature_solo_bot.game.model.card import Card
from nature_solo_bot.game.model.modules import BAMBOO_GROVE
from nature_solo_bot.game.model.trait_cards import MONOPHAGOUS
from nature_solo_bot.game.rules.feeding import BAMBOO

from ..game.model.player import Player
from ..game.model.species import Species
from ..game.model.state import GameState

T = TypeVar("T")

FOOD_DISCARD_PRIORITIES = {
    True: ("plant_food", "meat_food", "bamboo_food"),
    False: ("bamboo_food", "plant_food", "meat_food"),
}


class ActionApplier:
    """Applies a selected action to the current game state."""

    def discard_card_for_watering_hole(
        state: GameState,
        player: Player,
        rng: Random,
        food_type: str,
    ):
        """Discard a card to add food to the watering hole.

        The Nature discard pile is face-up, so the most recently discarded card sits at the
        front of the list while the draw deck keeps its top at the back of the list.
        """
        rng.shuffle(player.hand)

        # Bamboo Grove needs to be separated from the others
        if BAMBOO_GROVE in state.modules:
            bamboo_cards: list[Card] = (card for card in player.hand if card.deck == BAMBOO_GROVE)
            other_cards: list[Card] = (card for card in player.hand if card not in bamboo_cards)
            rng.shuffle(bamboo_cards)
            rng.shuffle(other_cards)

            if food_type == BAMBOO:
                discarded_card: Card = bamboo_cards.pop()

            else:
                discarded_card: Card = other_cards.pop()

        else:
            discarded_card: Card = player.hand.pop()

        discard_pile: list[Card] = state.trait_discard_pile(discarded_card)
        discard_pile.insert(0, discarded_card)

        if discarded_card.deck == BAMBOO_GROVE:
            state.watering_hole_bamboo += discarded_card.food_value

        else:
            state.watering_hole_plant += discarded_card.food_value

    def kill_populations(state: GameState, loss: int, species: Species, player: Player):
        """Kill populations of a species"""
        for _ in range(min(loss, species.population)):
            ActionApplier.kill_one_population(state, species, player)

    def kill_one_population(state: GameState, species: Species, player: Player):
        """Kill one population of a species"""
        # If the species is fully-fed, the killed population was carrying 1 food
        if species.total_food == species.population:
            priorities = FOOD_DISCARD_PRIORITIES[MONOPHAGOUS in species.traits]

            for food_type in priorities:
                food_count = getattr(species, food_type)

                if food_count > 0:
                    setattr(species, food_type, food_count - 1)
                    break

        species.population -= 1
        species.lost_population += 1
        player.lost_population += 1

        # Killing the last species triggers extinction
        if species.population == 0:
            player.return_extinct_species(species)

    @staticmethod
    def draw_card(
        deck: list[T],
        rng: Random,
        discard: list[T] | None = None,
    ) -> T:
        """Remove and return the top card from a face-down draw deck.

        Discard piles are face-up, so their most recent card sits at index 0. Rebuilding a deck
        from a discard therefore needs to reverse the pile before appending it to the deck: the
        discard pile's top becomes the deck's top when the deck is later drawn from its end.
        """
        # Reshuffle the discard pile into the draw deck if the deck is empty.
        if not deck and discard:
            deck.extend(reversed(discard))
            discard.clear()
            rng.shuffle(deck)

        if not deck:
            raise RuntimeError("Cannot draw a card: the deck and discard pile are empty.")

        return deck.pop()
