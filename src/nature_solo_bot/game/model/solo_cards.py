from .symbol import Symbol
from .solo_species import SoloSpecies

EVADER = SoloSpecies(
    name="Evader",
    pink_symbols=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="population", is_hunter=True),
        Symbol("gear"),
        Symbol("leaf", increase="size"),
        Symbol("armadillo", increase="population"),        
    ],
    pink_symbols_last_round=[
        Symbol("cat"),
        Symbol("vulture", increase="population"),
        Symbol("armadillo", increase="size"),
        Symbol("gear"),
    ],
    blue_symbols=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="population", is_hunter=True),
        Symbol("gear", is_hunter=True),
        Symbol("leaf", increase="population"),
        Symbol("armadillo", increase="size"),
    ],
    blue_symbols_last_round=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="size"),
        Symbol("gear"),
        Symbol("armadillo", increase="population"),
    ],
)
GLUTTON = SoloSpecies(
    name="Glutton",
    pink_symbols=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="population", is_hunter=True),
        Symbol("gear"),
        Symbol("leaf", increase="size"),
        Symbol("armadillo", increase="population"),        
    ],
    pink_symbols_last_round=[
        Symbol("cat"),
        Symbol("vulture", increase="population"),
        Symbol("armadillo", increase="size"),
        Symbol("gear"),
    ],
    blue_symbols=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="population", is_hunter=True),
        Symbol("gear", is_hunter=True),
        Symbol("leaf", increase="population"),
        Symbol("armadillo", increase="size"),
    ],
    blue_symbols_last_round=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="size"),
        Symbol("gear"),
        Symbol("armadillo", increase="population"),
    ],
)
PREDATOR = SoloSpecies(
    name="Predator",
    pink_symbols=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="population", is_hunter=True),
        Symbol("gear"),
        Symbol("leaf", increase="size"),
        Symbol("armadillo", increase="population"),        
    ],
    pink_symbols_last_round=[
        Symbol("cat"),
        Symbol("vulture", increase="population"),
        Symbol("armadillo", increase="size"),
        Symbol("gear"),
    ],
    blue_symbols=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="population", is_hunter=True),
        Symbol("gear", is_hunter=True),
        Symbol("leaf", increase="population"),
        Symbol("armadillo", increase="size"),
    ],
    blue_symbols_last_round=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="size"),
        Symbol("gear"),
        Symbol("armadillo", increase="population"),
    ],
)
SCAMP = SoloSpecies(
    name="Scamp",
    pink_symbols=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="population", is_hunter=True),
        Symbol("gear"),
        Symbol("leaf", increase="size"),
        Symbol("armadillo", increase="population"),        
    ],
    pink_symbols_last_round=[
        Symbol("cat"),
        Symbol("vulture", increase="population"),
        Symbol("armadillo", increase="size"),
        Symbol("gear"),
    ],
    blue_symbols=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="population", is_hunter=True),
        Symbol("gear", is_hunter=True),
        Symbol("leaf", increase="population"),
        Symbol("armadillo", increase="size"),
    ],
    blue_symbols_last_round=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="size"),
        Symbol("gear"),
        Symbol("armadillo", increase="population"),
    ],
)
SCAVENGER = SoloSpecies(
    name="Scavenger",
    pink_symbols=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="population", is_hunter=True),
        Symbol("gear"),
        Symbol("leaf", increase="size"),
        Symbol("armadillo", increase="population"),        
    ],
    pink_symbols_last_round=[
        Symbol("cat"),
        Symbol("vulture", increase="population"),
        Symbol("armadillo", increase="size"),
        Symbol("gear"),
    ],
    blue_symbols=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="population", is_hunter=True),
        Symbol("gear", is_hunter=True),
        Symbol("leaf", increase="population"),
        Symbol("armadillo", increase="size"),
    ],
    blue_symbols_last_round=[
        Symbol("cat", is_hunter=True),
        Symbol("vulture", increase="size"),
        Symbol("gear"),
        Symbol("armadillo", increase="population"),
    ],
)
NATURE_SOLO_CARDS = [
    EVADER,
    GLUTTON,
    PREDATOR,
    SCAMP,
    SCAVENGER,
]