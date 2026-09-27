from ..model.species import Species
from ..model.trait import EffectTiming, Trait
from ..model.state import GameState


class TraitEffectRules:
    """Resolve trait effects at attachment or game-phase timing points."""

    @staticmethod
    def on_attach(species: Species, trait: Trait, state: GameState) -> None:
        """Apply effects that trigger once when this trait is attached."""
        for effect in trait.effects:
            if effect.timing is EffectTiming.ON_ATTACH:
                if effect.effect_id == "make_hunter":
                    species.is_hunter = True

    @staticmethod
    def on_timing(
        timing: EffectTiming,
        species: Species,
        state: GameState,
    ) -> None:
        """Apply this species' trait effects that trigger at the given timing."""
        pass