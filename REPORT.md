# World of Tanks Matchmaking System — Coursework Report

---

## 1. Introduction

### What is this application?

This project is a **World of Tanks-inspired matchmaking simulation** built in Python 3.12.
The goal of the coursework is to demonstrate all four pillars of Object-Oriented Programming
through a realistic, domain-driven problem: grouping tank-driving players into two balanced
teams of 15 before a battle begins.

The application models:
- A **tank hierarchy** (Heavy, Medium, Light, Tank Destroyer, SPG) where each type carries
  a different matchmaking weight.
- A **player** who owns exactly one tank and has a tracked win/loss record.
- Four interchangeable **matchmaking strategies** that split a 30-player pool into two teams
  using different balancing rules (random, tier-based, weight-based, or both combined).
- A **JSON persistence layer** that loads the player roster and saves every completed match
  to a history file.
- An **interactive CLI** for exploring and using the system.

### How to run the program

Python 3.12+ is required. No third-party packages are needed.

```bash
# From the directory that CONTAINS the KDfinal/ folder:
python -m KDfinal
```

### How to use the program

Once the shell starts, type any of the following commands:

| Command | Description |
|---|---|
| `players` | List all 70 players in the roster |
| `strategies` | Show all available matchmaking strategies |
| `match <strategy>` | Form two teams using the chosen strategy |
| `history [n]` | Show last n saved matches (default 5) |
| `help` | Print the command reference |
| `quit` | Exit the program |

Example session:

```
mm> match tier_weight
============================================================
  Strategy : tier_weight
  Tier spread : 2  (+/-2)
  Weight balance : 756.0 vs 754.8  (diff 1.2)
============================================================
  TEAM 1  (total weight: 756.0)
  ...
  Save this match? [y/N] y
  Saved — match id: 3a7f1c2d
```

---

## 2. Body / Analysis

### 2.1 OOP Pillar 1 — Encapsulation

**What it is:** Encapsulation bundles data (attributes) and the methods that operate on it
inside a single class, and controls external access using access modifiers. In Python this is
done by prefixing attributes with `_` (protected) and exposing them through read-only
`@property` descriptors.

**How it is used in this project:**

Every attribute in `Tank` and `Player` is private and exposed only through properties.
Direct assignment from outside the class is prevented.

```python
# tank.py
class Tank(ABC):
    def __init__(self, name: str, tier: int, nation: str) -> None:
        if not (1 <= tier <= 10):
            raise ValueError(f"Invalid tier {tier}. Must be between 1 and 10.")
        if nation not in VALID_NATIONS:
            raise ValueError(f"Invalid nation '{nation}'.")

        self._name = name      # private — cannot be set from outside
        self._tier = tier
        self._nation = nation

    @property
    def tier(self) -> int:     # safe read-only access
        return self._tier
```

```python
# player.py
class Player:
    def __init__(self, username, player_id, tank, wins=0, battles_played=0):
        if wins > battles_played:
            raise ValueError("Wins cannot exceed battles played.")
        self._wins = wins
        self._battles_played = battles_played

    @property
    def win_rate(self) -> float:          # computed, not stored
        if self._battles_played == 0:
            return 0.0
        return self._wins / self._battles_played
```

Validation is enforced at construction time — once a `Tank` or `Player` object exists, its
core identity fields cannot be corrupted from outside.

---

### 2.2 OOP Pillar 2 — Abstraction

**What it is:** Abstraction hides implementation details and exposes only the interface that
callers need. In Python, `abc.ABC` with `@abstractmethod` enforces that subclasses implement
a required interface without revealing how.

**How it is used in this project:**

`Tank` is an abstract base class. Callers work with `Tank` references and call
`matchmaking_weight()` without knowing which concrete subclass they have.

```python
# tank.py
from abc import ABC, abstractmethod

class Tank(ABC):

    @property
    @abstractmethod
    def tank_class(self) -> str:
        """Return the tank class identifier (e.g. 'Heavy', 'SPG')."""

    @property
    @abstractmethod
    def _weight_multiplier(self) -> float:
        """Class-specific weight multiplier for matchmaking calculations."""

    def matchmaking_weight(self) -> float:   # concrete — uses the abstract multiplier
        return WEIGHT_BY_TIER[self._tier] * self._weight_multiplier
```

`MatchmakingStrategy` applies the same idea to strategies:

```python
# matchmaking.py
class MatchmakingStrategy(ABC):

    @abstractmethod
    def match(self, players: list) -> tuple | None:
        """Split players into two balanced teams of 15."""
```

The CLI and tests only call `strategy.match(players)` — they never need to know whether
the strategy is `RandomStrategy` or `TierWeightStrategy`.

---

### 2.3 OOP Pillar 3 — Inheritance

**What it is:** Inheritance allows a subclass to reuse the code of a parent class and extend
or override its behaviour. It creates an "is-a" relationship.

**How it is used in this project:**

All five tank types inherit from `Tank`. They only override the two abstract properties;
everything else (validation, `to_dict`, `__str__`, `__repr__`) is inherited for free.

```python
# tank.py
class HeavyTank(Tank):
    @property
    def tank_class(self) -> str:
        return "Heavy"

    @property
    def _weight_multiplier(self) -> float:
        return 1.2          # always 20% heavier — strongest classification


class LightTank(Tank):
    @property
    def tank_class(self) -> str:
        return "Light"

    @property
    def _weight_multiplier(self) -> float:
        return 1.2 if 5 <= self._tier <= 8 else 1.0   # bonus only in active scout range
```

All four matchmaking strategies inherit from `MatchmakingStrategy`:

```python
# matchmaking.py
class TierWeightStrategy(MatchmakingStrategy):
    def match(self, players: list) -> tuple | None:
        pool = _select_tier_pool(players)   # inherited helper
        ...
```

Inheritance here removes duplication: each concrete tank class is roughly 6 lines; without
inheritance it would need to repeat 40+ lines of validation, serialization, and dunder methods.

---

### 2.4 OOP Pillar 4 — Polymorphism

**What it is:** Polymorphism allows different objects to respond to the same method call in
their own way. Code that calls `obj.method()` does not need to know the concrete type of
`obj` — the correct implementation is selected at runtime.

**How it is used in this project:**

The CLI calls `strategy.match(players)` on whatever `MatchmakingStrategy` instance was
selected. The same line of code produces four completely different behaviours:

```python
# main.py
strategy = StrategyFactory.create(strategy_name)  # returns one of 4 types
result = strategy.match(players)                  # polymorphic dispatch
```

The same applies to `matchmaking_weight()`. The code below works identically for every
tank type without any `isinstance` checks:

```python
# works for HeavyTank, MediumTank, LightTank, TankDestroyer, SPG — all transparently
total_weight = sum(p.matchmaking_weight() for p in team)
```

`Player.__eq__` is also polymorphic — it returns `NotImplemented` when compared against
a non-`Player` object, letting Python fall back to its default behaviour gracefully:

```python
# player.py
def __eq__(self, other: object) -> bool:
    if not isinstance(other, Player):
        return NotImplemented
    return self._player_id == other._player_id
```

---

### 2.5 Design Pattern — Factory Method

**What it is:** The Factory Method pattern defines an interface for creating objects, but
lets a factory class decide which concrete class to instantiate. The caller asks for an
object by name and receives a fully constructed instance without knowing the class.

**How it is used in this project:**

`StrategyFactory` holds a registry dict and a `create()` method that maps string names to
concrete strategy classes:

```python
# matchmaking.py
class StrategyFactory:
    _registry: dict[str, type[MatchmakingStrategy]] = {
        "random":      RandomStrategy,
        "tier":        TierStrategy,
        "weight":      WeightStrategy,
        "tier_weight": TierWeightStrategy,
    }

    @staticmethod
    def create(name: str) -> MatchmakingStrategy:
        cls = StrategyFactory._registry.get(name)
        if cls is None:
            valid = ", ".join(sorted(StrategyFactory._registry))
            raise ValueError(f"Unknown strategy '{name}'. Valid: {valid}")
        return cls()

    @staticmethod
    def available() -> list[str]:
        return sorted(StrategyFactory._registry)
```

**Why Factory Method and not other patterns?**

- **Singleton** — would be wrong here: we need many independent strategy instances, not one
  shared instance.
- **Builder** — strategies have no complex multi-step construction, so a builder would be
  over-engineering.
- **Abstract Factory** — would make sense if we were creating *families* of related objects
  (e.g. strategy + scorer + logger together). Here we only create one kind of object.
- **Factory Method** — fits exactly: the caller supplies a name string (from user input or a
  test), the factory selects and constructs the right class, and the caller only ever holds
  a `MatchmakingStrategy` reference. Adding a new strategy requires only one new line in the
  registry dict — zero changes to callers.

---

### 2.6 Composition and Aggregation

**Composition** is a "has-a" relationship where the owned object's lifetime is controlled
by the owner. **Aggregation** is also "has-a" but the owned object can exist independently.

**Composition in this project — `Player` owns a `Tank`:**

A `Player` is constructed with a `Tank` instance and holds it exclusively. There is no
shared `Tank` between players, and the `Tank` has no meaning outside the context of a
`Player` in the game domain. This is **composition**.

```python
# player.py
class Player:
    def __init__(self, username, player_id, tank: Tank, wins=0, battles_played=0):
        self._tank = tank        # Player OWNS this Tank

    def matchmaking_weight(self) -> float:
        return self._tank.matchmaking_weight()   # delegates to composed object
```

The `Player` also **composes** its behaviour from the `Tank`: `matchmaking_weight()` is
not duplicated — it is delegated to `self._tank`, so the player's weight automatically
changes if the tank type changes.

**Aggregation in this project — strategies work with player lists:**

`MatchmakingStrategy.match()` receives a list of `Player` objects it did not create and
does not own. The players exist before the strategy is called and continue to exist after.
This is **aggregation**.

```python
# matchmaking.py
class WeightStrategy(MatchmakingStrategy):
    def match(self, players: list) -> tuple | None:
        # players are owned by main.py — this strategy only reads them
        pool = sorted(players[:REQUIRED_PLAYERS], key=lambda p: p.matchmaking_weight(), reverse=True)
        ...
```

---

### 2.7 Reading from File and Writing to File

The `data_loader.py` module handles all JSON persistence using the standard library only.

**Reading players from file:**

```python
# data_loader.py
def load_players(path: Path = PLAYERS_FILE) -> list[Player]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8") as f:
        raw: list[dict] = json.load(f)
    return [Player.from_dict(entry) for entry in raw]
```

**Appending a match result to the history file:**

```python
# data_loader.py
def save_match(team1, team2, strategy, path=MATCHES_FILE) -> str:
    match_id = uuid.uuid4().hex[:8]
    record = {
        "match_id": match_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy,
        "Team1": [p.to_dict() for p in team1],
        "Team2": [p.to_dict() for p in team2],
    }
    history = load_matches(path)
    history.append(record)
    with path.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    return match_id
```

Two files are used:

| File | Purpose | Operations |
|---|---|---|
| `data/players.json` | Player roster (70 players, tiers 5–10) | Read on startup |
| `data/match_output.json` | Match history (append per confirmed match) | Read + write |

---

### 2.8 Testing

All core logic is covered by unit tests using Python's built-in `unittest` framework,
organised into four test modules that mirror the source modules.

**Running the tests:**

```bash
# From the parent directory of KDfinal/:
python -m unittest discover -s KDfinal/tests -p "test_*.py" --top-level-directory .
```

**Example — testing weight multiplier boundaries in `TankDestroyer`:**

```python
# tests/test_tank.py
def test_td_weight_below_8(self):
    for tier in range(1, 8):
        expected = WEIGHT_BY_TIER[tier] * 1.0
        self.assertAlmostEqual(
            TankDestroyer("X", tier, "USSR").matchmaking_weight(), expected
        )

def test_td_weight_from_8(self):
    for tier in (8, 9, 10):
        expected = WEIGHT_BY_TIER[tier] * 1.2
        self.assertAlmostEqual(
            TankDestroyer("X", tier, "USSR").matchmaking_weight(), expected
        )
```

**Example — testing that `WeightStrategy` balances team weights:**

```python
# tests/test_matchmaking.py
def test_weight_is_balanced(self):
    pool = _mixed_pool({5: 10, 7: 10, 9: 10})
    team1, team2 = self.strategy.match(pool)
    w1 = sum(p.matchmaking_weight() for p in team1)
    w2 = sum(p.matchmaking_weight() for p in team2)
    max_single_weight = max(p.matchmaking_weight() for p in pool)
    self.assertLess(abs(w1 - w2), max_single_weight)
```

**Test coverage summary:**

| Module | Test classes | Scenarios |
|---|---|---|
| `tank.py` | `TestTankValidation`, `TestTankClass`, `TestTankWeights`, `TestTankSerialization` | Tier/nation guards, all multiplier boundaries, serialization round-trip |
| `player.py` | `TestPlayerValidation`, `TestPlayerStats`, `TestPlayerEquality`, `TestPlayerSerialization` | Stat guards, win-rate edge cases, `record_battle`, equality/hashing, `from_dict` defaults |
| `matchmaking.py` | `TestSelectTierPool`, `TestRandom/Tier/Weight/TierWeightStrategy`, `TestStrategyFactory`, `TestRunMatchmaking` | Spread 0/1/2 fall-through, spread > 2 rejection, team sizes, no duplicates, weight gap, factory registry |
| `data_loader.py` | `TestLoadPlayers`, `TestSavePlayers`, `TestLoadMatches`, `TestSaveMatch` | Missing/empty file, round-trip, overwrite, parent-dir creation, unique match IDs |

---

## 3. Results and Conclusions

### Results

- The application successfully implements a working matchmaking CLI that groups 70 players
  into balanced teams using four distinct strategies, all of which produce teams with no
  duplicate players and correct sizes.
- The most challenging part of the implementation was the `_select_tier_pool` helper: it
  must find the tightest tier window (spread 0 → 1 → 2) across an arbitrary player pool
  while shuffling within buckets to prevent the same players always being selected.
- Applying the Strategy pattern made it straightforward to add new balancing algorithms
  without touching the CLI or persistence layers — only the `_registry` dict needed a new entry.
- Using composition (`Player` owns a `Tank`) kept `matchmaking_weight()` a single
  one-line delegation rather than duplicated logic in two classes.
- Writing tests before finalising the multiplier boundary rules (e.g. `LightTank` bonuses
  at tiers 5–8, `TankDestroyer` bonuses at tier 8+) caught two off-by-one errors during
  development.

### Conclusions

This coursework demonstrates that OOP principles are not abstract theory — they solve
concrete engineering problems. Encapsulation kept tank and player state consistent;
abstraction let the CLI drive four strategies through one interface; inheritance reduced
the five tank classes to ~6 lines each; polymorphism let a single `strategy.match()` call
select the right algorithm at runtime. The Factory Method pattern cleanly decoupled
user-supplied strategy names from class construction.

The result is a maintainable, testable matchmaking engine. Future prospects include:
incorporating `win_rate` into the weight formula for skill-based balancing, adding a live
`reload` command to refresh the player roster without restarting, and exposing a public
`StrategyFactory.register()` API so external modules can add strategies without editing
library code.

---

## 4. Resources

- [Python `abc` module — Abstract Base Classes](https://docs.python.org/3/library/abc.html)
- [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Python `unittest` framework](https://docs.python.org/3/library/unittest.html)
- [Refactoring Guru — Factory Method](https://refactoring.guru/design-patterns/factory-method)
- [Refactoring Guru — Strategy Pattern](https://refactoring.guru/design-patterns/strategy)
- [Python `json` module](https://docs.python.org/3/library/json.html)
- [Markdown syntax guide](https://www.markdownguide.org/basic-syntax/)
