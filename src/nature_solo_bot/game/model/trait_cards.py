from .trait import Trait

# ----- Nature Traits -----
# Hunter trait
HUNTER = Trait(
    name="Hunter",
    effect_id="hunter",
)
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
# Promo trait
AVID_FORAGER = Trait(
    name="Avid Forager",
    effect_id="avid_forager",
)
NATURE_TRAITS = [
    CLAWED,
    FAST,
    HORNED,
    OPPORTUNISTIC,
    PLATED,
    SCAVENGING,
    SOCIAL,
    TUSKED
]