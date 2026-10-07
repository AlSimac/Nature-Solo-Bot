# Nature-Solo-Bot
Nature board game Solo mode automa

## Running game experiments

`BatchRunner` runs 1,000 games by default, using consecutive seeds starting at
1, the medium difficulty, and no Promo cards. Each output record includes the
game's seed and settings, each player's final score, and the winner. The file
format is inferred from the `.csv` or `.json` extension.

```python
from src.nature_solo_bot.experiments import BatchRunner
from src.nature_solo_bot.game.model.state import DIFFICULTY_HARD

runner = BatchRunner(
    game_count=1000,
    start_seed=1,
    difficulty=DIFFICULTY_HARD,
    promo=True,
)
runner.run("output/experiment_results.csv")
```
