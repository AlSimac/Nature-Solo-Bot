# Nature-Solo-Bot
Nature board game Solo mode automa

See [FEEDING_PHASE_FLOWCHART.md](./FEEDING_PHASE_FLOWCHART.md) for separate core Nature and Bamboo Grove feeding diagrams, including feeding priorities, trait triggers, hunting, and starvation.

## Disclaimer

This is an unofficial, fan-created software project that simulates the solo variant of Nature through bot-vs-bot gameplay for automated simulations and experimentation.

This project is not affiliated with, endorsed by, or sponsored by NorthStar Game Studio.

All trademarks and other intellectual property belonging to their respective owners remain their property. The game's original design and any third-party materials included in this repository are not claimed as my own.

The software is intended for research, experimentation, and automated simulation. It does not provide a human-playable version of the game.

For questions concerning the original game, please consult its official publisher.

## Running game experiments

To configure a batch with a desktop window, run:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.game_setup_ui
```

Select the game count and difficulty, then choose any modules and their Promo
cards. Nature Promo cards can be enabled separately. Use **Browse...** to
choose the folder where game logs will be saved; the default is `output\Nature`.
Each run creates a timestamped subfolder there, then saves game logs numbered
in order under its `simulations` subfolder. A `run_settings.md` file beside
that subfolder records the run configuration. The last chosen output folder is
remembered for the next launch.

Use the **Analysis** tab to select a timestamped run folder (or its
`simulations` subfolder), choose which reports to generate, and save the CSV
reports under that run's `analysis` subfolder.

Run this command from the repository root to simulate 1,000 games with the
medium difficulty and no Promo cards. It writes one detailed `.log` file per
game in the `output` directory, including the seed, settings, phase actions,
trait triggers, round scores, and winner:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.run_experiments
```

You can change the run settings and output directory with options:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.run_experiments --games 1000 --start-seed 1 --difficulty hard --nature-promo --output-dir output
```

Use `--module-promo` to include Promo cards for selected modules, for example:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.run_experiments --games 1000 --module bamboo_grove --module-promo bamboo_grove
```

Select one or more game modules with `--module`. The currently supported
module is `bamboo_grove`; module runs are saved in a module-specific output
subdirectory by default:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.run_experiments --games 1000 --module bamboo_grove
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
Game logs also record Bamboo Grove deck/discard counts, bamboo in the watering
hole, Bamboo Grove card origins, and bamboo scoring outcomes.

To see, for every trait and round, how many species carried it and how much
food those species ate on average, add `--food-by-trait`:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.analyze_traits output\core\hardest --food-by-trait --output output\core\hardest\trait_food_by_round.csv
```

A species qualifies once per trait per round even if it has multiple copies.
The trait is read from the post-adaptation board, and food includes both plant
and meat food as well as bamboo eaten during that round. The report breaks
food totals down by type. Qualifying species that ate no food remain in the
average as zero-food observations.

To aggregate exact trait combinations instead, run:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.analyze_traits output\core\hardest --trait-combinations --output output\core\hardest\trait_combinations.csv
```

Each species-round with at least one trait contributes one observation for its
exact trait combination, so the presence count is species-round appearances,
not unique game-rounds. Duplicate copies are preserved (for example,
`Fast + Fast` differs from `Fast`). The CSV reports species-round appearances,
extinctions during feeding, total food by type, average food eaten per
species-round, starting population at the start of feeding, and population
lost by the end of feeding. Extinct species count as losing their full
starting population. Species with no traits are included under `No traits`.
Game logs also report how many Avid Forager cards were present in the Nature
deck, including the setup food card, to make Promo deck contents easy to
verify.

To aggregate the same metrics by Solo species card instead of by trait
combination, run:

```powershell
.\.venv\Scripts\python.exe -m src.nature_solo_bot.cli.analyze_traits output\core\hardest --solo-species --output output\core\hardest\solo_species_stats.csv
```

Every species-round contributes one observation to its Solo species card's
totals. The report includes its number of species-round appearances,
extinctions during feeding, total food by type, average food eaten per
species-round, starting population, and population lost by the end of feeding.
