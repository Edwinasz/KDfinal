"""
Matchmaking strategies for the WoT-inspired matchmaking system.

Design pattern: Factory Method
  - MatchmakingStrategy  — abstract product
  - RandomStrategy, TierStrategy, WeightStrategy, TierWeightStrategy — concrete products
  - StrategyFactory.create()  — the factory method
"""

import random
from abc import ABC, abstractmethod
from collections import defaultdict

TEAM_SIZE = 15
REQUIRED_PLAYERS = TEAM_SIZE * 2  # 30
MAX_TIER_SPREAD = 2  # a player can be at most 2 tiers below the top tier in a battle


# ---------------------------------------------------------------------------
# Tier-pool helper
# ---------------------------------------------------------------------------

def _select_tier_pool(players: list, required: int = REQUIRED_PLAYERS) -> list | None:
    """
    Find the tightest valid group of `required` players from the pool.

    Tries tier spreads 0, 1, 2 (in that order).  For each spread it checks
    every possible tier window [min_tier, min_tier + spread] and returns the
    first window that contains at least `required` players.  Players within
    each tier bucket are shuffled before selection so no one is systematically
    favoured.

    Returns a list of exactly `required` players, or None if no window with
    spread ≤ MAX_TIER_SPREAD has enough players.
    """
    # Pre-bucket players by tier once — O(n)
    by_tier: dict = defaultdict(list)
    for p in players:
        by_tier[p.tank.tier].append(p)

    available_tiers = sorted(by_tier.keys())

    for spread in range(MAX_TIER_SPREAD + 1):       # 0, 1, 2
        for min_tier in available_tiers:
            max_tier = min_tier + spread
            # Collect all players whose tier falls in [min_tier, max_tier]
            group: list = []
            for t in range(min_tier, max_tier + 1):
                group.extend(by_tier.get(t, []))

            if len(group) < required:
                continue

            # Shuffle within each tier bucket for fairness, then flatten
            window: dict = defaultdict(list)
            for p in group:
                window[p.tank.tier].append(p)
            for bucket in window.values():
                random.shuffle(bucket)

            flat = [p for t in sorted(window) for p in window[t]]
            return flat[:required]

    return None  # no tier window with spread ≤ MAX_TIER_SPREAD has enough players


# ---------------------------------------------------------------------------
# Abstract product
# ---------------------------------------------------------------------------

class MatchmakingStrategy(ABC):
    """Abstract base class for all matchmaking strategies."""

    @abstractmethod
    def match(self, players: list) -> tuple | None:
        """
        Split players into two balanced teams of 15.

        Returns (team1, team2) if there are at least 30 players,
        or None if the pool is too small (caller should wait).
        """


# ---------------------------------------------------------------------------
# Concrete products
# ---------------------------------------------------------------------------

class RandomStrategy(MatchmakingStrategy):
    """Split players into two teams of 15 by random shuffle."""

    def match(self, players: list) -> tuple | None:
        if len(players) < REQUIRED_PLAYERS:
            return None

        pool = players.copy()
        random.shuffle(pool)
        return pool[:TEAM_SIZE], pool[TEAM_SIZE:REQUIRED_PLAYERS]


class TierStrategy(MatchmakingStrategy):
    """Split players into two teams with equal tier counts per team."""

    def match(self, players: list) -> tuple | None:
        pool = _select_tier_pool(players)
        if pool is None:
            return None

        tier_groups: dict = defaultdict(list)
        for player in pool:
            tier_groups[player.tank.tier].append(player)

        team1: list = []
        team2: list = []
        odd_toggle = True

        for tier in sorted(tier_groups.keys(), reverse=True):
            group = tier_groups[tier]
            random.shuffle(group)
            half = len(group) // 2
            team1.extend(group[:half])
            team2.extend(group[half: half * 2])
            if len(group) % 2 == 1:
                (team1 if odd_toggle else team2).append(group[-1])
                odd_toggle = not odd_toggle

        return team1, team2


class WeightStrategy(MatchmakingStrategy):
    """Split players into two teams balanced by matchmaking weight."""

    def match(self, players: list) -> tuple | None:
        if len(players) < REQUIRED_PLAYERS:
            return None

        pool = sorted(
            players[:REQUIRED_PLAYERS],
            key=lambda p: p.matchmaking_weight(),
            reverse=True,
        )

        team1: list = []
        team2: list = []
        weight1 = weight2 = 0.0

        for player in pool:
            if weight1 <= weight2:
                team1.append(player)
                weight1 += player.matchmaking_weight()
            else:
                team2.append(player)
                weight2 += player.matchmaking_weight()

        return team1, team2


class TierWeightStrategy(MatchmakingStrategy):
    """Split players into two teams balancing both tier spread and total weight."""

    def match(self, players: list) -> tuple | None:
        pool = _select_tier_pool(players)
        if pool is None:
            return None

        tier_groups: dict = defaultdict(list)
        for player in pool:
            tier_groups[player.tank.tier].append(player)

        team1: list = []
        team2: list = []
        weight1 = weight2 = 0.0

        for tier in sorted(tier_groups.keys(), reverse=True):
            group = sorted(
                tier_groups[tier],
                key=lambda p: p.matchmaking_weight(),
                reverse=True,
            )
            for player in group:
                if weight1 <= weight2:
                    team1.append(player)
                    weight1 += player.matchmaking_weight()
                else:
                    team2.append(player)
                    weight2 += player.matchmaking_weight()

        return team1, team2


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class StrategyFactory:
    """
    Factory Method for creating MatchmakingStrategy instances.

    Usage:
        strategy = StrategyFactory.create('tier_weight')
        result   = strategy.match(players)
    """

    _registry: dict[str, type[MatchmakingStrategy]] = {
        "random":      RandomStrategy,
        "tier":        TierStrategy,
        "weight":      WeightStrategy,
        "tier_weight": TierWeightStrategy,
    }

    @staticmethod
    def create(name: str) -> MatchmakingStrategy:
        """
        Instantiate and return a strategy by name.

        Raises ValueError for unknown strategy names.
        """
        cls = StrategyFactory._registry.get(name)
        if cls is None:
            valid = ", ".join(sorted(StrategyFactory._registry))
            raise ValueError(
                f"Unknown matchmaking strategy '{name}'. Valid options: {valid}"
            )
        return cls()

    @staticmethod
    def available() -> list[str]:
        """Return the list of registered strategy names."""
        return sorted(StrategyFactory._registry)


# ---------------------------------------------------------------------------
# Convenience wrapper (keeps existing callers working)
# ---------------------------------------------------------------------------

def run_matchmaking(players: list, strategy: str) -> tuple | None:
    """
    Run matchmaking using the named strategy.

    strategy: 'random' | 'tier' | 'weight' | 'tier_weight'
    Returns (team1, team2) or None if the player pool is too small.
    """
    return StrategyFactory.create(strategy).match(players)
