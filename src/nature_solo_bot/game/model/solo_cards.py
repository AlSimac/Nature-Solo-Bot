from .symbol import Symbol, SymbolIncrease, SymbolName
from .solo_species import SoloEffect, SoloSpecies

EVADER = SoloSpecies(
    name="Evader",
    pink_symbols=[
        Symbol(SymbolName.GEAR),
        Symbol(SymbolName.LEAF, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.VULTURE, increase=SymbolIncrease.SIZE),
        Symbol(SymbolName.SEEDLING),
        Symbol(SymbolName.CAT, increase=SymbolIncrease.POPULATION, make_hunter=True),
    ],
    pink_symbols_last_round=[
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.SEEDLING),
        Symbol(SymbolName.GEAR),
        Symbol(SymbolName.VULTURE, increase=SymbolIncrease.SIZE),
    ],
    blue_symbols=[
        Symbol(SymbolName.GEAR),
        Symbol(SymbolName.LEAF, make_hunter=True),
        Symbol(SymbolName.VULTURE),
        Symbol(SymbolName.SEEDLING),
        Symbol(SymbolName.CAT, increase=SymbolIncrease.POPULATION, make_hunter=True),
    ],
    blue_symbols_last_round=[
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.SEEDLING),
        Symbol(SymbolName.GEAR),
        Symbol(SymbolName.VULTURE),
        Symbol(SymbolName.LEAF, increase=SymbolIncrease.SIZE, make_hunter=True),
    ],
)
GLUTTON = SoloSpecies(
    name="Glutton",
    pink_symbols=[
        Symbol(SymbolName.LEAF),
        Symbol(SymbolName.SEEDLING, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.CAT, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.ARMADILLO),
        Symbol(SymbolName.GEAR, increase=SymbolIncrease.SIZE),
    ],
    pink_symbols_last_round=[
        Symbol(SymbolName.LEAF),
        Symbol(SymbolName.GEAR, increase=SymbolIncrease.SIZE),
    ],
    blue_symbols=[
        Symbol(SymbolName.LEAF, increase=SymbolIncrease.SIZE),
        Symbol(SymbolName.SEEDLING, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.CAT),
        Symbol(SymbolName.ARMADILLO, make_hunter=True),
        Symbol(SymbolName.GEAR, increase=SymbolIncrease.POPULATION),
    ],
    blue_symbols_last_round=[
        Symbol(SymbolName.LEAF, increase=SymbolIncrease.SIZE),
        Symbol(SymbolName.GEAR),
        Symbol(SymbolName.CAT, increase=SymbolIncrease.POPULATION, make_hunter=True),
    ],
)
PROPAGATOR = SoloSpecies(
    name="Propagator",
    effect_id=SoloEffect.PROPAGATOR,
    pink_symbols=[
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.CAT, increase=SymbolIncrease.SIZE),
        Symbol(SymbolName.SEEDLING, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.VULTURE, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.LEAF),
    ],
    pink_symbols_last_round=[
        Symbol(SymbolName.GEAR),
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.LEAF, increase=SymbolIncrease.SIZE),
    ],
    blue_symbols=[
        Symbol(SymbolName.ARMADILLO),
        Symbol(SymbolName.CAT, increase=SymbolIncrease.SIZE),
        Symbol(SymbolName.LEAF, increase=SymbolIncrease.SIZE),
        Symbol(SymbolName.VULTURE, make_hunter=True),
        Symbol(SymbolName.SEEDLING),
    ],
    blue_symbols_last_round=[
        Symbol(SymbolName.GEAR),
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.SIZE),
        Symbol(SymbolName.LEAF, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.CAT, make_hunter=True),
    ],
)
PREDATOR = SoloSpecies(
    name="Predator",
    effect_id=SoloEffect.PREDATOR,
    pink_symbols=[
        Symbol(SymbolName.CAT, make_hunter=True),
        Symbol(SymbolName.VULTURE, increase=SymbolIncrease.POPULATION, make_hunter=True),
        Symbol(SymbolName.GEAR),
        Symbol(SymbolName.LEAF, increase=SymbolIncrease.SIZE),
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.POPULATION),
    ],
    pink_symbols_last_round=[
        Symbol(SymbolName.CAT),
        Symbol(SymbolName.VULTURE, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.SIZE),
        Symbol(SymbolName.GEAR),
    ],
    blue_symbols=[
        Symbol(SymbolName.CAT, make_hunter=True),
        Symbol(SymbolName.VULTURE, increase=SymbolIncrease.POPULATION, make_hunter=True),
        Symbol(SymbolName.GEAR, make_hunter=True),
        Symbol(SymbolName.LEAF, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.SIZE),
    ],
    blue_symbols_last_round=[
        Symbol(SymbolName.CAT, make_hunter=True),
        Symbol(SymbolName.VULTURE, increase=SymbolIncrease.SIZE),
        Symbol(SymbolName.GEAR),
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.POPULATION),
    ],
)
SCAMP = SoloSpecies(
    name="Scamp",
    pink_symbols=[
        Symbol(SymbolName.SEEDLING),
        Symbol(SymbolName.GEAR),
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.CAT, increase=SymbolIncrease.SIZE),
        Symbol(SymbolName.VULTURE, increase=SymbolIncrease.POPULATION),
    ],
    pink_symbols_last_round=[
        Symbol(SymbolName.SEEDLING),
        Symbol(SymbolName.LEAF),
    ],
    blue_symbols=[
        Symbol(SymbolName.SEEDLING),
        Symbol(SymbolName.GEAR, make_hunter=True),
        Symbol(SymbolName.ARMADILLO),
        Symbol(SymbolName.CAT, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.VULTURE, make_hunter=True),
    ],
    blue_symbols_last_round=[
        Symbol(SymbolName.SEEDLING),
        Symbol(SymbolName.LEAF),
    ],
)
SCAVENGER = SoloSpecies(
    name="Scavenger",
    pink_symbols=[
        Symbol(SymbolName.VULTURE),
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.LEAF),
        Symbol(SymbolName.GEAR),
        Symbol(SymbolName.SEEDLING, increase=SymbolIncrease.SIZE, make_hunter=True),
    ],
    pink_symbols_last_round=[
        Symbol(SymbolName.VULTURE),
        Symbol(SymbolName.CAT, increase=SymbolIncrease.SIZE),
    ],
    blue_symbols=[
        Symbol(SymbolName.VULTURE),
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.SEEDLING),
        Symbol(SymbolName.GEAR, make_hunter=True),
        Symbol(SymbolName.LEAF, increase=SymbolIncrease.SIZE),
    ],
    blue_symbols_last_round=[
        Symbol(SymbolName.VULTURE),
        Symbol(SymbolName.CAT),
        Symbol(SymbolName.ARMADILLO, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.LEAF, increase=SymbolIncrease.POPULATION),
        Symbol(SymbolName.SEEDLING, make_hunter=True),
    ],
)
NATURE_SOLO_CARDS = [
    EVADER,
    GLUTTON,
    PREDATOR,
    PROPAGATOR,
    SCAMP,
    SCAVENGER,
]