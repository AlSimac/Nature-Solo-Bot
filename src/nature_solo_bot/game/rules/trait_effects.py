from ..model.species import Species
from ..model.trait import EffectTiming
from ..model.state import GameState


class TraitEffectRules:
    """Resolve trait effects at attachment or game-phase timing points."""

    @staticmethod
    def on_timing(
        timing: EffectTiming,
        species: Species,
        state: GameState,
    ) -> None:
        """Apply this species' trait effects that trigger at the given timing."""
        pass
