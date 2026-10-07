# Nature-Solo-Bot
Nature board game Solo mode automa

## Running game experiments

Run this command from the repository root to simulate 1,000 games with the
medium difficulty and no Promo cards. It writes one detailed `.log` file per
game in the `output` directory, including the seed, settings, phase actions,
trait triggers, round scores, and winner:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.run_experiments
```

You can change the run settings and output directory with options:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.run_experiments --games 1000 --start-seed 1 --difficulty hard --promo --output-dir output
```

Available difficulties are `easiest`, `easy`, `medium`, `hard`, and `hardest`.
Log files are named `gamelog_{difficulty_id}_difficulty_{unique_id}.log`
(difficulty IDs 0-4 in the order listed above). Each log also records the
game number, unique ID, seed, and settings. For use from Python code,
`BatchRunner` is available from `src.nature_solo_bot.experiments`.

## Analyzing trait assignments

Count how many times each trait was assigned by the winner and loser across
all logs in a folder (including subfolders). Assignments from tied games are
reported separately:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.analyze_traits output\core\hardest
```

Add `--output output\core\hardest\trait_assignment_counts.csv` to save the
summary as CSV. Only successful trait assignments during adaptation are
counted; a trait appearing on a species board or triggering during feeding
does not count as a new assignment.
