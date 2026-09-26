class Symbol:
    """A symbol on a species card."""

    def __init__(self, name: str, increase: str = "default", is_hunter: bool = False):
        """Initialize a symbol with a name."""
        self.symbol: str = name
        self.increase: str = increase
        self.is_hunter: bool = is_hunter