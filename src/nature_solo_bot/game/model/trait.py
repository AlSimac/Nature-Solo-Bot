from dataclasses import dataclass
from enum import Enum


class EffectTiming(Enum):
    ON_ATTACH = "on_attach"
    ADAPTATION = "adaptation"
    FEEDING = "feeding"
    SCORING = "scoring"


@dataclass(frozen=True)
class TraitEffect:
    effect_id: str
    timing: EffectTiming


class Trait:
    def __init__(
        self,
        name: str,
        effect_id: str | None = None,
        attack_modifier: int = 0,
        defense_modifier: int = 0,
        effects: tuple[TraitEffect, ...] = (),
    ):
        self.name = name
        self.effect_id = effect_id
        self.attack_modifier = attack_modifier
        self.defense_modifier = defense_modifier
        self.effects = effects
