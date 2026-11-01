# Feeding Phase Flow and Decisions

This chart documents the plant-and-meat feeding behavior implemented by the solo engine, including the Promo Avid Forager trait. Bamboo Grove is configurable elsewhere in the engine, but `FeedingRules` does not yet resolve bamboo food or its module-specific feeding effects; those rules are outside this chart.

## Image files

- [Phase and turn flow (PNG)](./docs/images/feeding-phase/phase-and-turn-flow.png) | [SVG](./docs/images/feeding-phase/phase-and-turn-flow.svg)
- [Feeding candidate order (PNG)](./docs/images/feeding-phase/feeding-candidate-order.png) | [SVG](./docs/images/feeding-phase/feeding-candidate-order.svg)
- [Forage and plant-food resolution (PNG)](./docs/images/feeding-phase/forage-and-plant-food.png) | [SVG](./docs/images/feeding-phase/forage-and-plant-food.svg)
- [Hunt and prey selection (PNG)](./docs/images/feeding-phase/hunt-and-prey-selection.png) | [SVG](./docs/images/feeding-phase/hunt-and-prey-selection.svg)

## Phase and turn flow

```mermaid
flowchart TD
    A["Enter feeding phase"] --> B["Set current phase to FEEDING"]
    B --> C{"Any hungry species and any player not passing?"}
    C -- No --> Z["Leave feeding phase; proceed to scoring"]
    C -- Yes --> D["Visit players in order, starting at first_player_index and wrapping"]
    D --> E{"Has this player already passed?"}
    E -- Yes --> G["Continue to next player"]
    E -- No --> H{"Does this player have a hungry species?"}
    H -- No --> I["Mark player as passing"]
    I --> G
    H -- Yes --> J["Build feeding candidate order"]
    J --> K{"Any untried candidate species?"}
    K -- Yes --> L{"Is candidate a hunter?"}
    L -- No --> M{"Available food estimate > 0?"}
    M -- No --> K
    M -- Yes --> N["Try one forage, refilling watering hole if needed"]
    N --> O{"Forage succeeded?"}
    O -- No --> K
    O -- Yes --> P["Attempt one extra forage per Avid Forager copy"]
    P --> Q["Apply end-of-turn Opportunistic trigger if watering hole still has plants"]
    Q --> G
    L -- Yes --> R["Try to hunt a valid prey"]
    R --> S{"Hunt succeeded?"}
    S -- No --> K
    S -- Yes --> T["Resolve prey death, Horned losses, then all Scavenging triggers"]
    T --> U["Apply end-of-turn Opportunistic trigger if watering hole still has plants"]
    U --> G
    K -- No --> V["Starve the highest-priority hungry species by killing one population"]
    V --> G
    G --> W{"End of player rotation"}
    W -- No --> E
    W -- Yes --> C
```

The engine repeats complete player rotations while any species is hungry and at least one player has not passed. A player with no hungry species passes when their turn is reached. A player who still has hungry species but cannot complete a feeding action starves one population instead of passing.

The candidate order is built once, before the turn's first discard. Refilling does not recalculate that order: the selected forager continues its forage attempt. The implementation can move to the next candidate if an attempt returns failure, but with the normal Nature deck's positive food values (1–4), a refill begun with cards produces at least one plant and that initial forage succeeds.

## Feeding candidate order

```mermaid
flowchart TD
    A["Collect this player's hungry species"] --> B["Separate foragers and hunters"]
    B --> C["Rank foragers by projected total food gain, highest first"]
    C --> D["Keep original species order for ties"]
    D --> E["Append hungry hunters in original species order"]
    E --> F["Try candidates in order; take the first successful action"]
```

Forager projections simulate the base forage and each Avid Forager bonus forage, refills, Tusked triggers, and the player's Opportunistic triggers. The estimate values each card in hand at three plants. During an actual refill, a random card is discarded and its printed food value is added to the watering hole. Hunters are considered only after all foragers, regardless of how much food a hunt might provide.

## Forage and plant-food resolution

```mermaid
flowchart TD
    A["Begin initial forage"] --> B["Estimate amount: size + 2 per Clawed + 2 per Social"]
    B --> C["Cap estimate by hungry population and available food estimate"]
    C --> D{"Watering hole has enough plants for estimate?"}
    D -- No, hand has cards --> E["Discard a random card; add its printed food value"]
    E -- "same forager; recalculate" --> B
    D -- Yes --> F{"Any plant remains in watering hole?"}
    D -- No, hand empty --> F
    F -- No --> G["Initial forage fails; try next candidate"]
    F -- Yes --> H["Eat plants, capped by hunger and actual plants present"]
    H --> I{"Did this remove the last plant?"}
    I -- Yes --> J["Every Tusked copy in the game triggers: eat 1 meat each"]
    I -- No --> K["Continue"]
    J --> K
    K --> L{"More Avid Forager copies to attempt?"}
    L -- No --> M{"Watering hole still has plants?"}
    L -- Yes --> N["Attempt bonus forage using the same refill and eating rules"]
    N --> O{"Bonus forage succeeded?"}
    O -- No --> M
    O -- Yes --> P{"Did this remove the last plant?"}
    P -- Yes --> J
    P -- No --> L
    M -- Yes --> Q["Every Opportunistic copy on active player's species triggers: eat 2 meat each"]
    M -- No --> R["Finish feeding turn"]
    Q --> R
```

The `E --> B` loop recalculates the capped amount for the same already-selected forager; it does not choose another species. All eating effects are capped by the species' hungry population. Each Social copy adds two food from the same source as the triggering food; each Clawed copy adds two only when eating plants. If a refill leaves no plants after the hand is exhausted, that forage attempt fails. Avid Forager stops at its first failed bonus forage.

Tusked triggers for every species belonging to either player, once per copy, whenever removing plants changes the watering hole from nonempty to empty. A refill can make it trigger again later in the same round.

## Hunt and prey selection

```mermaid
flowchart TD
    A["Try a hungry hunter"] --> B["Inspect next species as a possible prey"]
    B --> C{"Any species left to inspect?"}
    C -- No --> D{"Any valid prey found?"}
    C -- Yes --> E{"Not the hunter itself, defense <= attack, and prey Fast copies <= hunter Fast copies?"}
    E -- Yes --> F["Add species to valid prey"]
    E -- No --> B
    F --> B
    D -- No --> G["Hunt fails; try next candidate"]
    D -- Yes --> H["Rank targets by hunter's expected population losses"]
    H --> I["Minimize own prey killed + hunter losses from prey's Horned copies"]
    I --> J["Tie-break: opponent prey, smaller size, older species"]
    J --> K["Hunter eats meat equal to prey size, capped by hunger"]
    K --> L["Kill one prey population"]
    L --> M["If prey had Horned, kill up to prey size per Horned copy from hunter"]
    M --> N["Every Scavenging copy on every species triggers: eat 2 meat each"]
    N --> O{"Watering hole still has plants?"}
    O -- Yes --> P["Every Opportunistic copy on active player's species triggers: eat 2 meat each"]
    O -- No --> Q["Finish feeding turn"]
    P --> Q
```

Attack and defense values start at species size. Clawed adds two attack and one defense per copy; Opportunistic adds one defense; Plated adds four defense; Tusked adds two defense. Each Horned copy causes hunter losses equal to prey size, capped by the hunter's current population. These losses are included in prey ranking and applied after the prey is killed.

When a population is killed, its owner is credited with the loss. If the species was fully fed just before the loss, one food is removed (plant food first, otherwise meat). Killing its last population removes the species, banks its size, and returns its trait cards according to the extinction rules.

## Starvation fallback

When no candidate can feed, one population is killed from the first available group:

1. Hungry hunters, in species order.
2. Foragers with no food at all, lowest population first and then oldest first.
3. Other hungry foragers, in species order.

The same population-loss and extinction handling used for a hunt applies. Feeding ends once no species is hungry, or the engine's turn loop has no non-passing players left. The following scoring phase counts remaining food, clears it from species, and applies end-of-round population-loss effects.
