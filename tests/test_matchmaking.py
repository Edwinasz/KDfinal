import unittest
from ..tank import HeavyTank, MediumTank, LightTank
from ..player import Player
from ..matchmaking import (
    REQUIRED_PLAYERS,
    RandomStrategy,
    TierStrategy,
    WeightStrategy,
    TierWeightStrategy,
    StrategyFactory,
    run_matchmaking,
    _select_tier_pool,
)


# ---------------------------------------------------------------------------
# Pagalbinės funkcijos
# ---------------------------------------------------------------------------

def _make_player(player_id: str, tier: int, tank_class="Heavy") -> Player:
    classes = {"Heavy": HeavyTank, "Medium": MediumTank, "Light": LightTank}
    tank = classes[tank_class](name="Test", tier=tier, nation="USSR")
    return Player(
        username=f"Player_{player_id}",
        player_id=player_id,
        tank=tank,
        wins=10,
        battles_played=20,
    )


def _pool(n: int, tier: int = 7) -> list[Player]:
    """Create n players all at the given tier."""
    return [_make_player(f"p{i:03}", tier) for i in range(n)]


def _mixed_pool(counts: dict[int, int]) -> list[Player]:
    """Create players from a {tier: count} mapping."""
    players = []
    pid = 0
    for tier, count in counts.items():
        for _ in range(count):
            players.append(_make_player(f"p{pid:03}", tier))
            pid += 1
    return players


# ---------------------------------------------------------------------------
# _select_tier_pool
# ---------------------------------------------------------------------------

class TestSelectTierPool(unittest.TestCase):

    def test_returns_none_when_not_enough_players(self):
        pool = _pool(29, tier=7)
        self.assertIsNone(_select_tier_pool(pool))

    def test_returns_30_players_exact(self):
        pool = _pool(30, tier=7)
        result = _select_tier_pool(pool)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 30)

    def test_prefers_spread_0_over_spread_1(self):
        # 30 T7 + 10 T8 — turėtų pasirinkti tik T7 langą (skirtumas 0)
        pool = _pool(30, tier=7) + _pool(10, tier=8)
        result = _select_tier_pool(pool)
        tiers = {p.tank.tier for p in result}
        self.assertEqual(tiers, {7})

    def test_falls_back_to_spread_1(self):
        # 15 T7 + 15 T8 — reikia abiejų lygių
        pool = _pool(15, tier=7) + _pool(15, tier=8)
        result = _select_tier_pool(pool)
        self.assertIsNotNone(result)
        spread = max(p.tank.tier for p in result) - min(p.tank.tier for p in result)
        self.assertEqual(spread, 1)

    def test_falls_back_to_spread_2(self):
        # po 10 T6, T7, T8 — reikia visų trijų (skirtumas 2)
        pool = _pool(10, tier=6) + _pool(10, tier=7) + _pool(10, tier=8)
        result = _select_tier_pool(pool)
        self.assertIsNotNone(result)
        spread = max(p.tank.tier for p in result) - min(p.tank.tier for p in result)
        self.assertEqual(spread, 2)

    def test_returns_none_when_spread_exceeds_2(self):
        # 15 T5 + 15 T8 — skirtumas 3, nėra tinkamo lango
        pool = _pool(15, tier=5) + _pool(15, tier=8)
        self.assertIsNone(_select_tier_pool(pool))

    def test_all_selected_within_window(self):
        pool = _mixed_pool({6: 20, 7: 20, 9: 20})
        result = _select_tier_pool(pool)
        self.assertIsNotNone(result)
        tiers = [p.tank.tier for p in result]
        self.assertLessEqual(max(tiers) - min(tiers), 2)


# ---------------------------------------------------------------------------
# RandomStrategy
# ---------------------------------------------------------------------------

class TestRandomStrategy(unittest.TestCase):

    def setUp(self):
        self.strategy = RandomStrategy()

    def test_returns_none_when_too_few(self):
        self.assertIsNone(self.strategy.match(_pool(29)))

    def test_returns_two_teams(self):
        result = self.strategy.match(_pool(30))
        self.assertIsNotNone(result)
        team1, team2 = result
        self.assertEqual(len(team1), 15)
        self.assertEqual(len(team2), 15)

    def test_no_duplicate_players(self):
        team1, team2 = self.strategy.match(_pool(30))
        ids = [p.player_id for p in team1 + team2]
        self.assertEqual(len(ids), len(set(ids)))

    def test_works_with_more_than_30(self):
        result = self.strategy.match(_pool(50))
        self.assertIsNotNone(result)
        team1, team2 = result
        self.assertEqual(len(team1) + len(team2), 30)


# ---------------------------------------------------------------------------
# TierStrategy
# ---------------------------------------------------------------------------

class TestTierStrategy(unittest.TestCase):

    def setUp(self):
        self.strategy = TierStrategy()

    def test_returns_none_when_too_few(self):
        self.assertIsNone(self.strategy.match(_pool(29)))

    def test_returns_none_when_spread_too_large(self):
        pool = _pool(15, tier=5) + _pool(15, tier=8)
        self.assertIsNone(self.strategy.match(pool))

    def test_team_sizes(self):
        team1, team2 = self.strategy.match(_pool(30))
        self.assertEqual(len(team1), 15)
        self.assertEqual(len(team2), 15)

    def test_tier_spread_at_most_2(self):
        pool = _mixed_pool({6: 15, 7: 15})
        team1, team2 = self.strategy.match(pool)
        all_tiers = [p.tank.tier for p in team1 + team2]
        self.assertLessEqual(max(all_tiers) - min(all_tiers), 2)

    def test_no_duplicate_players(self):
        team1, team2 = self.strategy.match(_pool(30))
        ids = [p.player_id for p in team1 + team2]
        self.assertEqual(len(ids), len(set(ids)))

    def test_tier_counts_roughly_equal(self):
        # Su 15 T6 + 15 T7, kiekviena komanda turėtų gauti ~7–8 kiekvieno lygio
        pool = _mixed_pool({6: 15, 7: 15})
        team1, team2 = self.strategy.match(pool)
        t1_tiers = [p.tank.tier for p in team1]
        t2_tiers = [p.tank.tier for p in team2]
        # Kiekvienoje komandoje turi būti abu lygiai
        self.assertIn(6, t1_tiers)
        self.assertIn(7, t1_tiers)
        self.assertIn(6, t2_tiers)
        self.assertIn(7, t2_tiers)


# ---------------------------------------------------------------------------
# WeightStrategy
# ---------------------------------------------------------------------------

class TestWeightStrategy(unittest.TestCase):

    def setUp(self):
        self.strategy = WeightStrategy()

    def test_returns_none_when_too_few(self):
        self.assertIsNone(self.strategy.match(_pool(29)))

    def test_team_sizes(self):
        team1, team2 = self.strategy.match(_pool(30))
        self.assertEqual(len(team1), 15)
        self.assertEqual(len(team2), 15)

    def test_weight_is_balanced(self):
        # Mišrūs lygiai sukuria nevienodus svorius; godžioji strategija turėtų sumažinti skirtumą
        pool = _mixed_pool({5: 10, 7: 10, 9: 10})
        team1, team2 = self.strategy.match(pool)
        w1 = sum(p.matchmaking_weight() for p in team1)
        w2 = sum(p.matchmaking_weight() for p in team2)
        # Skirtumas turi būti mažesnis nei vieno žaidėjo svoris aukščiausiame lygyje
        max_single_weight = max(p.matchmaking_weight() for p in pool)
        self.assertLess(abs(w1 - w2), max_single_weight)

    def test_no_duplicate_players(self):
        team1, team2 = self.strategy.match(_pool(30))
        ids = [p.player_id for p in team1 + team2]
        self.assertEqual(len(ids), len(set(ids)))


# ---------------------------------------------------------------------------
# TierWeightStrategy
# ---------------------------------------------------------------------------

class TestTierWeightStrategy(unittest.TestCase):

    def setUp(self):
        self.strategy = TierWeightStrategy()

    def test_returns_none_when_too_few(self):
        self.assertIsNone(self.strategy.match(_pool(29)))

    def test_returns_none_when_spread_too_large(self):
        pool = _pool(15, tier=5) + _pool(15, tier=8)
        self.assertIsNone(self.strategy.match(pool))

    def test_team_sizes(self):
        team1, team2 = self.strategy.match(_pool(30))
        self.assertEqual(len(team1), 15)
        self.assertEqual(len(team2), 15)

    def test_tier_spread_at_most_2(self):
        pool = _mixed_pool({6: 15, 7: 15})
        team1, team2 = self.strategy.match(pool)
        all_tiers = [p.tank.tier for p in team1 + team2]
        self.assertLessEqual(max(all_tiers) - min(all_tiers), 2)

    def test_weight_more_balanced_than_tier_only(self):
        # TierWeight turėtų duoti mažesnį svorio skirtumą nei vien Tier strategija
        pool = _mixed_pool({6: 15, 7: 15})
        t1, t2 = TierStrategy().match(pool)
        tw1, tw2 = self.strategy.match(pool)
        tier_gap = abs(
            sum(p.matchmaking_weight() for p in t1) -
            sum(p.matchmaking_weight() for p in t2)
        )
        tw_gap = abs(
            sum(p.matchmaking_weight() for p in tw1) -
            sum(p.matchmaking_weight() for p in tw2)
        )
        self.assertLessEqual(tw_gap, tier_gap)

    def test_no_duplicate_players(self):
        team1, team2 = self.strategy.match(_pool(30))
        ids = [p.player_id for p in team1 + team2]
        self.assertEqual(len(ids), len(set(ids)))


# ---------------------------------------------------------------------------
# StrategyFactory
# ---------------------------------------------------------------------------

class TestStrategyFactory(unittest.TestCase):

    def test_create_random(self):
        self.assertIsInstance(StrategyFactory.create("random"), RandomStrategy)

    def test_create_tier(self):
        self.assertIsInstance(StrategyFactory.create("tier"), TierStrategy)

    def test_create_weight(self):
        self.assertIsInstance(StrategyFactory.create("weight"), WeightStrategy)

    def test_create_tier_weight(self):
        self.assertIsInstance(StrategyFactory.create("tier_weight"), TierWeightStrategy)

    def test_unknown_strategy_raises(self):
        with self.assertRaises(ValueError):
            StrategyFactory.create("nonexistent")

    def test_available_returns_all_four(self):
        names = StrategyFactory.available()
        self.assertEqual(set(names), {"random", "tier", "weight", "tier_weight"})

    def test_available_is_sorted(self):
        names = StrategyFactory.available()
        self.assertEqual(names, sorted(names))

    def test_each_create_returns_new_instance(self):
        a = StrategyFactory.create("random")
        b = StrategyFactory.create("random")
        self.assertIsNot(a, b)


# ---------------------------------------------------------------------------
# run_matchmaking – pagalbinis apvalkalas
# ---------------------------------------------------------------------------

class TestRunMatchmaking(unittest.TestCase):

    def test_delegates_correctly(self):
        pool = _pool(30)
        result = run_matchmaking(pool, "random")
        self.assertIsNotNone(result)
        team1, team2 = result
        self.assertEqual(len(team1) + len(team2), 30)

    def test_unknown_strategy_raises(self):
        with self.assertRaises(ValueError):
            run_matchmaking(_pool(30), "unknown")

    def test_returns_none_when_too_few(self):
        self.assertIsNone(run_matchmaking(_pool(10), "weight"))


if __name__ == "__main__":
    unittest.main()
