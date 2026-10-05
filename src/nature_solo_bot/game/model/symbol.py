from enum import Enum


class SymbolName(str, Enum):
    ARMADILLO = "armadillo"
    CAT = "cat"
    GEAR = "gear"
    LEAF = "leaf"
    SEEDLING = "seedling"
    VULTURE = "vulture"


class SymbolIncrease(str, Enum):
    POPULATION = "population"
    SIZE = "size"


class Symbol:
    """A symbol on a species card."""

    def __init__(
        self,
        name: SymbolName,
        increase: SymbolIncrease | None = None,
        make_hunter: bool = False,
    ):
        """Initialize a symbol with a name."""
        self.symbol = name
        self.increase = increase
        self.is_hunter: bool = make_hunter
