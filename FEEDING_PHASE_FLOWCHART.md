# Feeding Phase Flowcharts

The diagrams below document the solo engine's feeding behavior in two configurations: core Nature, and games that include Bamboo Grove. Each set has its own phase flow, candidate order, forage resolution, and hunt/prey selection.

## Core Nature

### Phase and turn flow

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
    L -- No --> M{"Available plant food estimate > 0?"}
    M -- No --> K
    M -- Yes --> N["Try one forage, refilling watering hole if needed"]
    N --> O{"Forage succeeded?"}
    O -- No --> K
    O -- Yes --> P["Resolve post-forage triggers and Avid Forager bonus forages"]
    P --> G
    L -- Yes --> R["Try to hunt a valid prey"]
    R --> S{"Hunt succeeded?"}
    S -- No --> K
    S -- Yes --> T["Resolve prey death, Horned losses, then all Scavenging triggers"]
    T --> U["Resolve Opportunistic triggers if plants remain"]
    U --> G
    K -- No --> V["Starve the highest-priority hungry species by killing one population"]
    V --> G
    G --> W{"End of player rotation?"}
    W -- No --> E
    W -- Yes --> C
```

### Feeding candidate order

```mermaid
flowchart TD
    A["Collect this player's hungry species"] --> B["Separate foragers and hunters"]
    B --> C["Rank foragers by projected total food gain, highest first"]
    C --> D["Keep original species order for ties"]
    D --> E["Append hungry hunters in original species order"]
    E --> F["Try candidates in order; take the first successful action"]
```

### Forage and plant-food resolution

```mermaid
flowchart TD
    A["Begin initial forage"] --> B["Estimate amount: size + 2 per Clawed + 2 per Social"]
    B --> C["Cap by hungry population and available plant-food estimate"]
    C --> D{"Watering hole has enough plants for estimate?"}
    D -- No, hand has cards --> E["Discard a random card; add its printed food value as plants"]
    E --> B
    D -- Yes --> F{"Any plant remains in watering hole?"}
    D -- No, hand empty --> F
    F -- No --> G["Initial forage fails; try next candidate"]
    F -- Yes --> H["Eat plants, capped by hunger and plants present"]
    H --> I{"Did this remove the last plant?"}
    I -- Yes --> J["Every Tusked copy in the game triggers: eat 1 meat each"]
    I -- No --> K{"Plants remain in watering hole?"}
    J --> K
    K -- Yes --> Q["Active player's Opportunistic copies trigger: eat 2 meat each"]
    K -- No --> L{"More Avid Forager copies to attempt?"}
    Q --> L
    L -- No --> R["Finish feeding turn"]
    L -- Yes --> N["Attempt bonus forage using the same refill and eating rules"]
    N --> O{"Bonus forage succeeded?"}
    O -- No --> R
    O -- Yes --> P{"Did this remove the last plant?"}
    P -- Yes --> J
    P -- No --> K
```

### Hunt and prey selection

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
    N --> O{"Plants remain in watering hole?"}
    O -- Yes --> P["Active player's Opportunistic copies trigger: eat 2 meat each"]
    O -- No --> Q["Finish feeding turn"]
    P --> Q
```

Foragers are ordered once at the start of the player's turn by projected total food gain, with original species order breaking ties; hunters follow in species order. Refilling does not rebuild that order or change the selected forager. Each successful forage resolves Opportunistic effects before the next Avid Forager attempt. Projections value each card in hand at three plants; an actual refill adds the discarded card's printed food value.

The forage amount is capped by hunger and available plants. Clawed adds two plants per copy and Social adds two food from the source per copy. Tusked triggers for every species belonging to either player, once per copy, when the last plant leaves the watering hole. Refilling can empty the watering hole again later in the round.

Attack and defense start at species size. Clawed adds two attack and one defense per copy; Opportunistic adds one defense; Plated adds four defense; Tusked adds two defense. Each Horned copy causes hunter losses equal to prey size, capped by the hunter's current population. These losses are included in prey ranking and applied after the prey is killed.

When no candidate can feed, one population is killed from the first available group:

1. Hungry hunters, in species order.
2. Foragers with no food at all, lowest population first and then oldest first.
3. Other hungry foragers, in species order.

The same population-loss and extinction handling used for a hunt applies. Feeding ends once no species is hungry, or the engine's turn loop has no non-passing players left. Scoring then counts remaining food, clears it from species, and applies end-of-round population-loss effects.

## Games with Bamboo Grove

### Phase and turn flow

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
    L -- No --> M{"Choose forage food: bamboo for Monophagous if available; otherwise best projected plant or bamboo gain"}
    M --> N["Try watering-hole forage with refills; discarded cards add food matching their deck"]
    N --> O{"Forage succeeded?"}
    O -- No --> K
    O -- Yes --> P["Resolve post-forage effects and Avid Forager bonus forages; stop on first failed bonus"]
    P --> G
    L -- Yes --> R["Try to hunt a valid prey, including Stalking hunters"]
    R --> S{"Hunt succeeded?"}
    S -- No --> K
    S -- Yes --> T["Resolve prey death, Horned losses, then all Scavenging triggers"]
    T --> U["Resolve Opportunistic triggers if plants remain"]
    U --> G
    K -- No --> V["Starve the highest-priority hungry species by killing one population"]
    V --> G
    G --> W{"End of player rotation?"}
    W -- No --> E
    W -- Yes --> C
```

### Feeding candidate order

```mermaid
flowchart TD
    A["Collect this player's hungry species"] --> B["Separate foragers and hunters"]
    B --> C["Choose each forager's food source and project total gain, including trait triggers"]
    C --> D["Rank foragers by projected total food gain, highest first"]
    D --> E["Keep original species order for ties"]
    E --> F["Append hungry hunters in original species order"]
    F --> G["Try candidates in order; take the first successful action"]
```

### Forage and plant-or-bamboo resolution

```mermaid
flowchart TD
    A["Begin forage"] --> B{"Is the forager Monophagous?"}
    B -- Yes --> C{"Bamboo available from watering hole or matching cards?"}
    C -- Yes --> D["Choose bamboo"]
    C -- No --> E["Choose plants"]
    B -- No --> F["Project plant and bamboo gains; choose bamboo only if its gain is greater, otherwise plants"]
    D --> G{"Foraging from watering hole?"}
    E --> G
    F --> G
    G -- Yes --> H["Estimate amount using forage traits; cap by hunger and chosen food availability"]
    H --> I{"Watering hole has enough chosen food?"}
    I -- No, hand has cards --> J["Discard a card; add food matching its deck"]
    J --> H
    I -- Yes --> K{"Any chosen food remains?"}
    I -- No, hand empty --> K
    K -- Yes --> L["Eat the chosen type only; a forage cannot mix plants and bamboo"]
    K -- No --> M["Try Territorial food"]
    G -- No --> M
    M --> N{"Territorial forage succeeded?"}
    N -- No --> O["Initial forage fails: try next candidate; a failed bonus forage ends this feeding turn"]
    L --> T{"Did the forage empty all watering-hole food?"}
    T -- Yes --> U["Every Tusked copy in the game triggers: eat 1 meat each"]
    T -- No --> Q
    U --> Q
    N -- Yes --> Q["Resolve Opportunistic if plants remain in watering hole"]
    Q --> R["Other active-player Folivore copies eat plants from supply"]
    R --> S["Resolve Root Eating for each copy while watering-hole food remains"]
    S --> V{"Did Root Eating empty all watering-hole food?"}
    V -- Yes --> W["Every Tusked copy in the game triggers: eat 1 meat each"]
    V -- No --> X["Continue"]
    W --> X
    X --> Y{"More Avid Forager copies to attempt?"}
    Y -- Yes --> Z{"Is the forager Monophagous?"}
    Z -- Yes --> B
    Z -- No --> G
    Y -- No --> AA["Finish feeding turn"]
```

### Hunt and prey selection

```mermaid
flowchart TD
    A["Try a hungry hunter, including a Stalking species"] --> B["Inspect next species as a possible prey"]
    B --> C{"Any species left to inspect?"}
    C -- No --> D{"Any valid prey found?"}
    C -- Yes --> E{"Not the hunter itself and defense <= attack?"}
    E -- No --> B
    E -- Yes --> F{"Does prey have any evasive trait?"}
    F -- No --> I["Add species to valid prey"]
    F -- Yes --> G{"Stalking hunter and prey fully fed?"}
    G -- Yes --> I
    G -- No --> H{"Fast copies matched and Arboreal prey has an Arboreal hunter?"}
    H -- No --> B
    H -- Yes --> I
    I --> B
    D -- No --> J["Hunt fails; try next candidate"]
    D -- Yes --> K["Rank targets by hunter's expected population losses"]
    K --> L["Minimize own prey killed + hunter losses from prey's Horned copies"]
    L --> M["Tie-break: opponent prey, smaller size, older species"]
    M --> N["Hunter eats meat equal to prey size, capped by hunger"]
    N --> O["Kill one prey population"]
    O --> P["If prey had Horned, kill up to prey size per Horned copy from hunter"]
    P --> Q["Every Scavenging copy on every species triggers: eat 2 meat each"]
    Q --> R{"Plants remain in watering hole?"}
    R -- Yes --> S["Active player's Opportunistic copies trigger: eat 2 meat each"]
    R -- No --> T["Finish feeding turn"]
    S --> T
```

In Bamboo Grove, a forage takes either plants or bamboo, never a mix. Monophagous selects bamboo when the watering-hole estimate includes bamboo (including potential Bamboo Grove card refills), and otherwise selects plants. If that forage cannot feed, the Territorial fallback checks bamboo first for Monophagous. Other foragers choose bamboo only when its projected gain is greater than the plant gain; ties favor plants. Avid Forager repeats the same food choice, with Monophagous rechecking its availability for each bonus forage.

The forage amount is capped by hunger and food at the selected source. Social adds two food per copy; Arboreal adds one food per copy from either forage type; Clawed adds two only when foraging for plants. Refills add the discarded card's printed value to the food type associated with that card's deck. Tusked triggers whenever a watering-hole food removal empties the entire supply, including ordinary foraging and Root Eating; a later refill and emptying triggers it again. After any successful forage, Opportunistic triggers if plants remain in the watering hole, Folivore triggers on the active player's other species, and then Root Eating resolves. Territorial food can be used as a fallback forage source.

Stalking makes a species a hunter. It can bypass evasive traits when the prey is fully fed; otherwise Fast must still be matched, and Arboreal prey still require an Arboreal hunter. A hunter that eats prey with Horned loses population as shown in the shared hunt flow. Scavenging and Opportunistic resolve after a successful hunt as shown above.

As in core Nature, candidates are ranked once per turn by projected gain and starvation removes one population using the same priority order. The Bamboo Grove forage projection also accounts for food-type availability, card decks, Territorial food, and module trait triggers.
