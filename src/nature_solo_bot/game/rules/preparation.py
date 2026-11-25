from random import Random

from nature_solo_bot.const import PLANT
from nature_solo_bot.game.model.trait import Trait
from nature_solo_bot.game.model.trait_cards import AVID_FORAGER, MONOPHAGOUS, TERRITORIAL

from ...engine.action_applier import ActionApplier
from ..model.card import Card
from ..model.hunter_card import HunterCard
from ..model.modules import MODULE_DEFINITIONS
from ..model.player import Player
from ..model.solo_species import SoloEffect
from ..model.species import Species
from ..model.state import GameState
from ..model.trait_cards import NATURE_TRAITS


class PreparationRules:
    """Rules applied during preparation"""

    @staticmethod
    def solo_species_effect_when_played(
        species: Species,
        player: Player,
        *,
        max_traits: int,
        trait_discard: list[Card],
        rng: Random,
        state: GameState,
    ) -> None:
        """Calls the correct Solo card effect"""
        # Adding traits when played
        if species.solo_species.add_trait:
            PreparationRules.add_trait_when_played(state, species)

        if species.solo_species.effect_id == SoloEffect.PREDATOR:
            PreparationRules.predator_effect(
                species,
                player,
                max_traits=max_traits,
                trait_discard=trait_discard,
                rng=rng,
                state=state,
            )

        if species.solo_species.effect_id == SoloEffect.PROPAGATOR:
            PreparationRules.propagator_effect(
                player,
                max_traits=max_traits,
                trait_discard=trait_discard,
                rng=rng,
                state=state,
            )

        # BAMBOO_GROVE
        if species.solo_species.effect_id == SoloEffect.CHI_CHI:
            PreparationRules.chi_chi_effect(
                species,
                state=state,
            )

    @staticmethod
    def predator_effect(
        species: Species,
        player: Player,
        *,
        max_traits: int,
        trait_discard: list[Card],
        rng: Random,
        state: GameState,
    ) -> None:
        """When Played: Add the Hunter trait if the species is size 2 or less."""
        if species.size <= 2:
            PreparationRules.add_hunter_card(
                species,
                player,
                max_traits=max_traits,
                trait_discard=trait_discard,
                rng=rng,
                state=state,
            )

    @staticmethod
    def propagator_effect(
        player: Player,
        *,
        max_traits: int,
        trait_discard: list[Card],
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
                trait_discard=trait_discard,
                rng=rng,
                state=state,
            )

    # BAMBOO_GROVE
    @staticmethod
    def chi_chi_effect(
        species: Species,
        *,
        state: GameState,
    ) -> None:
        """When Played: Add the Monophagous trait,
        and increse Chi Chi's size twice."""
        for _ in range(2):
            species_max_size = min(
                state.max_size,
                (2 if species.count_trait_instance(AVID_FORAGER) > 0 else state.max_size),
            )

            if species.size < species_max_size:
                species.size += 1

    @staticmethod
    def add_hunter_card(
        species: Species,
        player: Player,
        *,
        max_traits: int,
        state: GameState,
        rng: Random,
        trait_discard: list[Card] | None = None,
        replace_random_trait: bool = False,
    ) -> bool:
        attached = True
        is_full = len(species.trait_cards) >= max_traits

        if is_full and not species.trait_cards:
            attached = False

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
            attached = False

        # BAMBOO_GROVE: If a species with Monophagous becomes hunter,
        # Monophagous is removed
        if species.is_hunter:
            for card in species.trait_cards:
                if card.trait.effect_id == MONOPHAGOUS.effect_id:
                    species.remove_trait_card(card)
                    player._return_trait_card(card, state.trait_discard_pile(card))

        return attached

    @staticmethod
    def add_trait_when_played(state: GameState, species: Species) -> None:
        """Add a specific trait to a species when played"""
        traits_to_find: list[Trait] = species.solo_species.add_trait or []

        for trait in traits_to_find:

            def matches_trait(candidate: Trait) -> bool:
                return candidate is trait or (
                    trait.effect_id is not None and candidate.effect_id == trait.effect_id
                )

            deck_to_search: list[Card] | None = None
            discard_pile: list[Card] | None = None
            is_nature_trait = any(
                matches_trait(nature_trait) for nature_trait in NATURE_TRAITS
            ) or matches_trait(AVID_FORAGER)

            # Finding the correct deck to search for the specified trait
            if is_nature_trait:
                deck_to_search = state.nature_deck
                discard_pile = state.nature_discard

            else:
                matching_modules = [
                    module
                    for module in state.modules
                    if any(
                        matches_trait(module_trait)
                        for module_trait in MODULE_DEFINITIONS[module].traits_for_deck(promo=True)
                    )
                ]

                if len(matching_modules) > 1:
                    raise ValueError(f"Trait {trait.name!r} belongs to multiple active decks.")

                if matching_modules:
                    module_deck = state.module_decks[matching_modules[0]]
                    deck_to_search = module_deck.deck
                    discard_pile = module_deck.discard

                else:
                    raise ValueError(f"No active trait deck is configured for {trait.name!r}.")

            if discard_pile is None:
                raise RuntimeError(f"The discard pile for trait {trait.name!r} is not initialized.")

            if deck_to_search is None:
                raise RuntimeError(f"The draw deck for trait {trait.name!r} is not initialized.")

            trait_card = None

            # goes through the draw pile and discard all cards until the trait is found
            while deck_to_search:
                drawn_card = deck_to_search.pop()

                if matches_trait(drawn_card.trait):
                    trait_card = drawn_card
                    break

                discard_pile.insert(0, drawn_card)

            # if not found, go through the discard pile
            if trait_card is None:
                trait_card = next(
                    (card for card in discard_pile if matches_trait(card.trait)),
                    None,
                )

                if trait_card is not None:
                    discard_pile.remove(trait_card)

            if trait_card is not None and not species.add_trait_card(
                trait_card,
                max_traits=state.max_traits,
            ):
                discard_pile.insert(0, trait_card)

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
                    trait_discard=state.nature_discard,
                    rng=rng,
                    state=state,
                )

    # BAMBOO_GROVE
    @staticmethod
    def store_food_on_territorial(state: GameState) -> None:
        territorial_cards = (
            card
            for player in state.players
            for species in player.species
            for card in species.trait_cards
            if card.trait.effect_id == TERRITORIAL.effect_id
        )

        for card in territorial_cards:
            card.stored_food[PLANT] += 2
