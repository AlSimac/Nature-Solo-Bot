from .trait import Trait

# Hunter trait
HUNTER = Trait(
    name="Hunter",
    effect_id="hunter",
)
# ----- Nature Traits -----
CLAWED = Trait(
    name="Clawed",
    effect_id="clawed",
    attack_modifier=2,
    defense_modifier=1,
)
FAST = Trait(
    name="Fast",
    effect_id="fast",
    is_evasive=True,
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
NATURE_TRAITS = [CLAWED, FAST, HORNED, OPPORTUNISTIC, PLATED, SCAVENGING, SOCIAL, TUSKED]
# ----- Bamboo Grove Traits -----
ARBOREAL = Trait(
    name="Arboreal",
    effect_id="arboreal",
    attack_modifier=1,
    is_evasive=True,
)
FOLIVORE = Trait(
    name="Folivore",
    effect_id="folivore",
    defense_modifier=1,
)
MONOPHAGOUS = Trait(
    name="Monophagous",
    effect_id="monophagous",
)
ROOT_EATING = Trait(
    name="Root Eating",
    effect_id="root_eating",
    defense_modifier=1,
)
STALKING = Trait(
    name="Stalking",
    effect_id="stalking",
    hidden_hunter=True,
)
# Promo traits
LONG_DIGESTION = Trait(
    name="Long Digestion",
    effect_id="long_digestion",
)
TERRITORIAL = Trait(
    name="Territorial",
    effect_id="territorial",
)
BAMBOO_GROVE_TRAITS = [ARBOREAL, FOLIVORE, MONOPHAGOUS, ROOT_EATING, STALKING]
