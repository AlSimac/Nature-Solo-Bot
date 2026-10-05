"""Player model for a Nature-like board game."""

from .solo_species import SoloSpecies
from src.nature_solo_bot.game.model.card import Card
from src.nature_solo_bot.game.model.hunter_card import HunterCard
from src.nature_solo_bot.game.model.species import Species
from src.nature_solo_bot.game.model.trait_card import TraitCard


class Player:
    """Represents one player in the game, controlled by a deterministic automaton."""

    def __init__(self, name: str, player_id: int | None = None):
        """Initialize a player with a name and identity."""
        self.name: str = name
        self.player_id: int | None = player_id
        self.score: int = 0
        self.species: list[Species] = []
        self.hand: list[Card] = []
        self.solo_deck: list[SoloSpecies] = []
        self.solo_discard: list[SoloSpecies] = []
        self.automaton: None = None
        self.winner: bool = False
        self.is_first_player: bool = False
        self.is_active: bool = False
        self.metadata: dict = {}
        self.lost_population: int = 0
        self.extinct_size: int = 0
        self.passing: bool = False

    def init_two_players() -> list["Player"]:
        """Initialize two players for the game."""
        player1 = Player(name="Rani", player_id=1)
        player2 = Player(name="Radwin", player_id=2)
        return [player1, player2]

    def play_trait_card(
        self,
        card: Card,
        species: Species,
        *,
        max_traits: int,
    ) -> bool:
        """Move a card from this player's hand onto one of their species."""
        if species not in self.species:
            raise ValueError("Cannot attach a trait card to another player's species.")
        if card not in self.hand:
            raise ValueError("The trait card must be in this player's hand.")
        if not species.add_trait_card(card, max_traits=max_traits):
            return False

        self.hand.remove(card)
        return True

    def replace_trait_card(
        self,
        species: Species,
        old_card: TraitCard,
        new_card: TraitCard,
        nature_discard: list[Card],
        *,
        max_traits: int,
    ) -> bool:
        """Replace an attached card and return it to its proper supply."""
        if species not in self.species:
            raise ValueError("Cannot replace a trait on another player's species.")
        if not species.replace_trait_card(old_card, new_card, max_traits=max_traits):
            return False

        self._return_trait_card(old_card, nature_discard)
        return True

    @staticmethod
    def _return_trait_card(
        card: TraitCard,
        nature_discard: list[Card],
    ) -> None:
        if isinstance(card, HunterCard):
            return

        elif isinstance(card, Card):
            nature_discard.append(card)

        else:
            raise TypeError(f"Unsupported trait card type: {type(card).__name__}")

    def return_extinct_species(
        self,
        species: Species,
    ) -> bool:
        """Remove an extinct species and return its trait cards to the hand."""
        if species not in self.species:
            return False

        self.extinct_size += species.size
        self.species.remove(species)
        self.solo_discard.append(species.solo_species)

        for card in list(species.trait_cards):
            if isinstance(card, Card):
                self.hand.append(card)

            else:
                self._return_trait_card(card, [])

            species.remove_trait_card(card)

        return True
