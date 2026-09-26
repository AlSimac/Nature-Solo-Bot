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


