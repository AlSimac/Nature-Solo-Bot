from enum import Enum

from .symbol import Symbol


class SoloEffect(str, Enum):
    PREDATOR = "predator"
    PROPAGATOR = "propagator"


class SoloSpecies:
    """A Solo species card."""

    def __init__(
        self,
        name: str = "Solo Species",
        effect_id: SoloEffect = None,
        pink_symbols: list[Symbol] | None = None,
        pink_symbols_last_round: list[Symbol] | None = None,
        blue_symbols: list[Symbol] | None = None,
        blue_symbols_last_round: list[Symbol] | None = None,
    ):
        """Initialize a solo species with a name and traits."""
        self.name = name
        self.effect_id = effect_id
        self.pink_symbols = pink_symbols or []
        self.pink_symbols_last_round = pink_symbols_last_round or []
        self.blue_symbols = blue_symbols or []
        self.blue_symbols_last_round = blue_symbols_last_round or []

    

    