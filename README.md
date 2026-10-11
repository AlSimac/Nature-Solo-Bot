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

To see, for every trait and round, how many species carried it and how much
food those species ate on average, add `--food-by-trait`:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.analyze_traits output\core\hardest --food-by-trait --output output\core\hardest\trait_food_by_round.csv
```

A species qualifies once per trait per round even if it has multiple copies.
The trait is read from the post-adaptation board, and food includes both plant
and meat food eaten during that round. Qualifying species that ate no food
remain in the average as zero-food observations.

To aggregate exact trait combinations instead, run:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.analyze_traits output\core\hardest --trait-combinations --output output\core\hardest\trait_combinations.csv
```

Each species-round with at least one trait contributes one observation for its
exact trait combination, so the presence count is species-round appearances,
not unique game-rounds. Duplicate copies are preserved (for example,
`Fast + Fast` differs from `Fast`). The CSV reports species-round appearances,
extinctions during feeding, total and average food eaten per species-round,
starting population at the start of feeding, and population lost by the end of
feeding. Extinct species count as losing their full starting population.
Species with no traits are included under `No traits`. Game logs also report
how many Avid Forager cards were present in the Nature deck, including the
setup food card, to make Promo deck contents easy to verify.

To aggregate the same metrics by Solo species card instead of by trait
combination, run:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.analyze_traits output\core\hardest --solo-species --output output\core\hardest\solo_species_stats.csv
```

Every species-round contributes one observation to its Solo species card's
totals. The report includes its number of species-round appearances,
extinctions during feeding, total and average food eaten per species-round,
starting population, and population lost by the end of feeding.
