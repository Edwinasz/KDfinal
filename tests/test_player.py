import unittest
from ..tank import HeavyTank
from ..player import Player


def _make_player(username="Ace", player_id="p001", tier=7,
                 wins=10, battles=20) -> Player:
    tank = HeavyTank(name="Tiger I", tier=tier, nation="Germany")
    return Player(username=username, player_id=player_id, tank=tank,
                  wins=wins, battles_played=battles)


class TestPlayerValidation(unittest.TestCase):

    def test_valid_creation(self):
        p = _make_player()
        self.assertEqual(p.username, "Ace")
        self.assertEqual(p.player_id, "p001")

    def test_empty_username(self):
        with self.assertRaises(ValueError):
            _make_player(username="   ")

    def test_empty_player_id(self):
        with self.assertRaises(ValueError):
            _make_player(player_id="  ")

    def test_negative_wins(self):
        with self.assertRaises(ValueError):
            _make_player(wins=-1, battles=0)

    def test_negative_battles(self):
        with self.assertRaises(ValueError):
            _make_player(wins=0, battles=-1)

    def test_wins_exceed_battles(self):
        with self.assertRaises(ValueError):
            _make_player(wins=10, battles=5)

    def test_wins_equal_battles_allowed(self):
        p = _make_player(wins=5, battles=5)
        self.assertEqual(p.wins, 5)


class TestPlayerStats(unittest.TestCase):

    def test_win_rate_normal(self):
        p = _make_player(wins=50, battles=100)
        self.assertAlmostEqual(p.win_rate, 0.5)

    def test_win_rate_zero_battles(self):
        p = _make_player(wins=0, battles=0)
        self.assertEqual(p.win_rate, 0.0)

    def test_win_rate_perfect(self):
        p = _make_player(wins=10, battles=10)
        self.assertAlmostEqual(p.win_rate, 1.0)

    def test_record_battle_win(self):
        p = _make_player(wins=10, battles=20)
        p.record_battle(won=True)
        self.assertEqual(p.wins, 11)
        self.assertEqual(p.battles_played, 21)

    def test_record_battle_loss(self):
        p = _make_player(wins=10, battles=20)
        p.record_battle(won=False)
        self.assertEqual(p.wins, 10)
        self.assertEqual(p.battles_played, 21)

    def test_matchmaking_weight_delegates_to_tank(self):
        p = _make_player(tier=7)
        self.assertAlmostEqual(p.matchmaking_weight(), p.tank.matchmaking_weight())


class TestPlayerEquality(unittest.TestCase):

    def test_equal_same_id(self):
        p1 = _make_player(player_id="p001")
        p2 = _make_player(player_id="p001")
        self.assertEqual(p1, p2)

    def test_not_equal_different_id(self):
        p1 = _make_player(player_id="p001")
        p2 = _make_player(player_id="p002")
        self.assertNotEqual(p1, p2)

    def test_hashable_in_set(self):
        p1 = _make_player(player_id="p001")
        p2 = _make_player(player_id="p001")
        self.assertEqual(len({p1, p2}), 1)

    def test_not_equal_to_non_player(self):
        p = _make_player()
        self.assertNotEqual(p, "not a player")


class TestPlayerSerialization(unittest.TestCase):

    def _round_trip(self, player: Player) -> Player:
        return Player.from_dict(player.to_dict())

    def test_round_trip_preserves_username(self):
        p = _make_player(username="TankAce")
        self.assertEqual(self._round_trip(p).username, "TankAce")

    def test_round_trip_preserves_stats(self):
        p = _make_player(wins=123, battles=456)
        rt = self._round_trip(p)
        self.assertEqual(rt.wins, 123)
        self.assertEqual(rt.battles_played, 456)

    def test_round_trip_preserves_tank(self):
        p = _make_player(tier=8)
        rt = self._round_trip(p)
        self.assertEqual(rt.tank.tier, 8)
        self.assertEqual(rt.tank.tank_class, "Heavy")

    def test_from_dict_defaults_stats(self):
        data = {
            "username": "Ghost",
            "player_id": "p999",
            "tank": {"name": "Tiger I", "tier": 7, "nation": "Germany", "tank_class": "Heavy"},
        }
        p = Player.from_dict(data)
        self.assertEqual(p.wins, 0)
        self.assertEqual(p.battles_played, 0)

    def test_from_dict_unknown_tank_class(self):
        data = {
            "username": "Ghost",
            "player_id": "p999",
            "tank": {"name": "X", "tier": 7, "nation": "Germany", "tank_class": "Submarine"},
        }
        with self.assertRaises(ValueError):
            Player.from_dict(data)

    def test_to_dict_has_required_keys(self):
        p = _make_player()
        d = p.to_dict()
        for key in ("username", "player_id", "wins", "battles_played", "tank"):
            self.assertIn(key, d)


if __name__ == "__main__":
    unittest.main()
