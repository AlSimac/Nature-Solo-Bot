from enum import Enum


class Trait:
    def __init__(
        self,
        name: str,
        effect_id: str,
        attack_modifier: int = 0,
        defense_modifier: int = 0,
    ):
        self.name = name
        self.effect_id = effect_id
        self.attack_modifier = attack_modifier
        self.defense_modifier = defense_modifier


class NatureTrait(Enum):
    CLAWED = Trait(
        name="Clawed",
        effect_id="clawed",
        attack_modifier=2,
        defense_modifier=1,
    )
    FAST = Trait(
        name="Fast",
        effect_id="fast",
    )
    HORNED = Trait(
        name="Horned",
        effect_id="horned",
    )
    OPPORTUNISTIC = Trait(
        name="Opportunistic",
        effect_id="opportunistic",
        defense_modifier=1,
    )
    PLATED = Trait(
        name="Plated",
        effect_id="plated",
        defense_modifier=4,
    )
    SCAVENGING = Trait(
        name="Scavenging",
        effect_id="scavenging",
    )
    SOCIAL = Trait(
        name="Social",
        effect_id="social",
    )
    TUSKED = Trait(
        name="Tusked",
        effect_id="tusked",
        defense_modifier=2,
    )