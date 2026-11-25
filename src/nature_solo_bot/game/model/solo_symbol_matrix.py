from __future__ import annotations

import csv
from collections import defaultdict
from importlib.resources import files

from .symbol import SymbolName


MatrixEntry = tuple[int, SymbolName]


def _normalize(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def _load_matrix() -> dict[str, dict[str, dict[int, tuple[SymbolName, ...]]]]:
    matrix: dict[str, dict[str, dict[int, tuple[SymbolName, ...]]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    resource = files("nature_solo_bot").joinpath("data/solo_symbol_matrix.csv")

    with resource.open("r", newline="", encoding="utf-8") as matrix_file:
        reader = csv.DictReader(matrix_file, delimiter=";", restkey="__rest")

        for row in reader:
            deck = _normalize(row["Deck"])
            trait = _normalize(row["Trait"])
            food_value = int(row["Food value"])
            symbols: list[SymbolName] = []

            for column in ("Gear", "Armadillo", "Vulture", "Leaf", "Seedling", "Cat"):
                count = int(row[column] or 0)
                symbols.extend([SymbolName(column.lower())] * count)

            matrix[deck][trait][food_value] = tuple(symbols)

    return matrix


MATRIX = _load_matrix()


def card_entries_for(
    deck: str,
    trait: str,
    fallback_food_values: list[int],
    default_symbol: SymbolName = SymbolName.SEEDLING,
) -> list[MatrixEntry]:
    trait_matrix = MATRIX.get(_normalize(deck), {}).get(_normalize(trait), {})

    if not trait_matrix:
        return [(food_value, default_symbol) for food_value in fallback_food_values]

    entries: list[MatrixEntry] = []

    for food_value in sorted(trait_matrix):
        entries.extend(
            (food_value, symbol)
            for symbol in trait_matrix[food_value]
        )
        
    return entries
