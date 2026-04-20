"""
Matchmaking strategijos WoT matchmaking sistemai.

Dizaino šablonas: Fabrikinis metodas (Factory Method)
  - MatchmakingStrategy  — abstraktus produktas
  - RandomStrategy, TierStrategy, WeightStrategy, TierWeightStrategy — konkretūs produktai
  - StrategyFactory.create()  — fabrikinis metodas
"""

import random
from abc import ABC, abstractmethod
from collections import defaultdict

TEAM_SIZE = 15
REQUIRED_PLAYERS = TEAM_SIZE * 2  # 30
MAX_TIER_SPREAD = 2  # žaidėjas gali būti ne daugiau kaip 2 tieriais žemiau aukščiausio


# ---------------------------------------------------------------------------
# Tier atrankos pagalbinė funkcija
# ---------------------------------------------------------------------------

def _select_tier_pool(players: list, required: int = REQUIRED_PLAYERS) -> list | None:
    """
    Randa mažiausią galiojančią grupę iš `required` žaidėjų.

    Bando tier skirtumą 0, 1, 2 (eilės tvarka). Kiekvienam skirtumui tikrina
    kiekvieną galimą tier langą [min_tier, min_tier + spread] ir grąžina
    pirmą langą, kuriame yra pakankamai žaidėjų. Žaidėjai kiekviename tier
    segmente maišomi, kad niekas nebūtų sistemingai favorizuojamas.

    Grąžina sąrašą iš tiksliai `required` žaidėjų arba None, jei nė vienas
    langas su spread ≤ MAX_TIER_SPREAD neturi pakankamai žaidėjų.
    """
    by_tier: dict = defaultdict(list)
    for p in players:
        by_tier[p.tank.tier].append(p)

    available_tiers = sorted(by_tier.keys())

    for spread in range(MAX_TIER_SPREAD + 1):
        for min_tier in available_tiers:
            max_tier = min_tier + spread
            # Surenkame visus žaidėjus, kurių tier patenka į [min_tier, max_tier]
            group: list = []
            for t in range(min_tier, max_tier + 1):
                group.extend(by_tier.get(t, []))

            if len(group) < required:
                continue

            # Maišome kiekvieną tier segmentą atskirai, tada sulygname
            window: dict = defaultdict(list)
            for p in group:
                window[p.tank.tier].append(p)
            for bucket in window.values():
                random.shuffle(bucket)

            flat = [p for t in sorted(window) for p in window[t]]
            return flat[:required]

    return None  # nė vienas tier langas su spread ≤ MAX_TIER_SPREAD neturi pakankamai žaidėjų


# ---------------------------------------------------------------------------
# Abstraktus produktas
# ---------------------------------------------------------------------------

class MatchmakingStrategy(ABC):
    """Abstrakti bazinė klasė visoms matchmaking strategijoms."""

    @abstractmethod
    def match(self, players: list) -> tuple | None:
        """
        Padalija žaidėjus į dvi subalansuotas 15 žaidėjų komandas.

        Grąžina (team1, team2) jei yra bent 30 žaidėjų,
        arba None jei pool per mažas.
        """


# ---------------------------------------------------------------------------
# Konkretūs produktai
# ---------------------------------------------------------------------------

class RandomStrategy(MatchmakingStrategy):
    """Padalija žaidėjus į dvi 15 žaidėjų komandas atsitiktine tvarka."""

    def match(self, players: list) -> tuple | None:
        if len(players) < REQUIRED_PLAYERS:
            return None

        pool = players.copy()
        random.shuffle(pool)
        return pool[:TEAM_SIZE], pool[TEAM_SIZE:REQUIRED_PLAYERS]


class TierStrategy(MatchmakingStrategy):
    """Padalija žaidėjus į dvi komandas su vienodu tier pasiskirstymu."""

    def match(self, players: list) -> tuple | None:
        pool = _select_tier_pool(players)
        if pool is None:
            return None

        tier_groups: dict = defaultdict(list)
        for player in pool:
            tier_groups[player.tank.tier].append(player)

        team1: list = []
        team2: list = []
        # Kaitalioja, kuri komanda gauna likusį žaidėją, kai tier grupė nelyginė,
        # kad ilgainiui kiekviena komanda gautų vienodai "papildomų" žaidėjų.
        odd_toggle = True

        for tier in sorted(tier_groups.keys(), reverse=True):
            group = tier_groups[tier]
            random.shuffle(group)
            half = len(group) // 2
            team1.extend(group[:half])
            team2.extend(group[half: half * 2])  # half*2, ne half+half — praleisti nelyginį
            if len(group) % 2 == 1:
                (team1 if odd_toggle else team2).append(group[-1])
                odd_toggle = not odd_toggle

        return team1, team2


class WeightStrategy(MatchmakingStrategy):
    """Padalija žaidėjus į dvi komandas balansuojant pagal matchmaking svorį."""

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

        # Godžioji strategija: kiekvieną žaidėją priskiria lengvesnei komandai.
        # Veikia gerai kai pool surikiuotas mažėjančia tvarka — didžiausi svoriai
        # paskirstomi pirmiausia, kai paklaida dar maža.
        for player in pool:
            if weight1 <= weight2:
                team1.append(player)
                weight1 += player.matchmaking_weight()
            else:
                team2.append(player)
                weight2 += player.matchmaking_weight()

        return team1, team2


class TierWeightStrategy(MatchmakingStrategy):
    """Padalija žaidėjus balansuojant ir tier skirtumą, ir bendrą svorį."""

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
# Fabrika
# ---------------------------------------------------------------------------

class StrategyFactory:
    """
    Fabrikinis metodas MatchmakingStrategy objektams kurti.

    Naudojimas:
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
        """Sukuria ir grąžina strategiją pagal pavadinimą. Kelia ValueError jei nežinomas."""
        cls = StrategyFactory._registry.get(name)
        if cls is None:
            valid = ", ".join(sorted(StrategyFactory._registry))
            raise ValueError(
                f"Nežinoma matchmaking strategija '{name}'. Galimos: {valid}"
            )
        return cls()

    @staticmethod
    def available() -> list[str]:
        """Grąžina užregistruotų strategijų pavadinimų sąrašą."""
        return sorted(StrategyFactory._registry)


# ---------------------------------------------------------------------------
# Patogus apvalkalas (išsaugo suderinamumą su esamais iškvietimais)
# ---------------------------------------------------------------------------

def run_matchmaking(players: list, strategy: str) -> tuple | None:
    """
    Paleidžia matchmaking naudodamas nurodytą strategiją.

    strategy: 'random' | 'tier' | 'weight' | 'tier_weight'
    Grąžina (team1, team2) arba None jei žaidėjų pool per mažas.
    """
    return StrategyFactory.create(strategy).match(players)
