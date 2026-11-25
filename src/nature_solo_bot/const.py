"""Constants shared across the Nature Solo Bot codebase."""

__all__ = [
    "NATURE",
    "BAMBOO_GROVE",
    "PLANT",
    "MEAT",
    "BAMBOO",
    "FOOD_VALUES",
    "NATURE_FOOD_VALUES",
    "BAMBOO_GROVE_FOOD_VALUES",
    "FOOD_DISCARD_PRIORITIES",
]

NATURE = "nature"
BAMBOO_GROVE = "bamboo_grove"

PLANT = "plant_food"
MEAT = "meat_food"
BAMBOO = "bamboo_food"

FOOD_VALUES = [1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4]
NATURE_FOOD_VALUES = FOOD_VALUES
BAMBOO_GROVE_FOOD_VALUES = [2, 2, 2, 3, 3, 3, 4, 4]

FOOD_DISCARD_PRIORITIES = {
    True: (PLANT, MEAT, BAMBOO),
    False: (BAMBOO, PLANT, MEAT),
}
