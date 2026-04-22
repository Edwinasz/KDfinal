import json
import tempfile
import unittest
from pathlib import Path

from ..tank import HeavyTank
from ..player import Player
from ..data_loader import load_players, save_players, load_matches, save_match


# Pagalbinė funkcija

def _make_player(player_id: str = "p001", tier: int = 7) -> Player:
    tank = HeavyTank(name="Tiger I", tier=tier, nation="Germany")
    return Player(
        username=f"Player_{player_id}",
        player_id=player_id,
        tank=tank,
        wins=10,
        battles_played=20,
    )


# load_players / save_players

class TestLoadPlayers(unittest.TestCase):

    def test_returns_empty_list_for_missing_file(self):
        path = Path(tempfile.mkdtemp()) / "nonexistent.json"
        self.assertEqual(load_players(path), [])

    def test_returns_empty_list_for_empty_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("")
            path = Path(f.name)
        self.assertEqual(load_players(path), [])

    def test_loads_single_player(self):
        player = _make_player()
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False
        ) as f:
            json.dump([player.to_dict()], f)
            path = Path(f.name)
        loaded = load_players(path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].player_id, "p001")

    def test_raises_on_malformed_entry(self):
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False
        ) as f:
            json.dump([{"username": "Ghost"}], f)   # trūksta privalomų laukų
            path = Path(f.name)
        with self.assertRaises(ValueError):
            load_players(path)


class TestSavePlayers(unittest.TestCase):

    def test_round_trip_single_player(self):
        player = _make_player("p001", tier=8)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "players.json"
            save_players([player], path)
            loaded = load_players(path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].player_id, "p001")
        self.assertEqual(loaded[0].tank.tier, 8)

    def test_round_trip_multiple_players(self):
        players = [_make_player(f"p{i:03}") for i in range(5)]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "players.json"
            save_players(players, path)
            loaded = load_players(path)
        self.assertEqual(len(loaded), 5)
        self.assertEqual(
            {p.player_id for p in loaded},
            {p.player_id for p in players},
        )

    def test_save_overwrites_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "players.json"
            save_players([_make_player("p001")], path)
            save_players([_make_player("p002")], path)
            loaded = load_players(path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].player_id, "p002")

    def test_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "players.json"
            save_players([_make_player()], path)
            self.assertTrue(path.exists())


# load_matches / save_match

class TestLoadMatches(unittest.TestCase):

    def test_returns_empty_list_for_missing_file(self):
        path = Path(tempfile.mkdtemp()) / "nonexistent.json"
        self.assertEqual(load_matches(path), [])

    def test_returns_empty_list_for_empty_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("")
            path = Path(f.name)
        self.assertEqual(load_matches(path), [])


class TestSaveMatch(unittest.TestCase):

    def _two_teams(self):
        team1 = [_make_player(f"t1p{i}") for i in range(15)]
        team2 = [_make_player(f"t2p{i}") for i in range(15)]
        return team1, team2

    def test_returns_match_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "matches.json"
            t1, t2 = self._two_teams()
            match_id = save_match(t1, t2, "random", path)
        self.assertIsInstance(match_id, str)
        self.assertGreater(len(match_id), 0)

    def test_match_record_has_required_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "matches.json"
            t1, t2 = self._two_teams()
            save_match(t1, t2, "tier_weight", path)
            matches = load_matches(path)
        record = matches[0]
        for key in ("match_id", "timestamp", "strategy", "Team1", "Team2"):
            self.assertIn(key, record)

    def test_strategy_stored_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "matches.json"
            t1, t2 = self._two_teams()
            save_match(t1, t2, "tier", path)
            matches = load_matches(path)
        self.assertEqual(matches[0]["strategy"], "tier")

    def test_team_sizes_stored_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "matches.json"
            t1, t2 = self._two_teams()
            save_match(t1, t2, "weight", path)
            matches = load_matches(path)
        self.assertEqual(len(matches[0]["Team1"]), 15)
        self.assertEqual(len(matches[0]["Team2"]), 15)

    def test_appends_multiple_matches(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "matches.json"
            t1, t2 = self._two_teams()
            save_match(t1, t2, "random", path)
            save_match(t1, t2, "tier", path)
            matches = load_matches(path)
        self.assertEqual(len(matches), 2)

    def test_match_ids_are_unique(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "matches.json"
            t1, t2 = self._two_teams()
            id1 = save_match(t1, t2, "random", path)
            id2 = save_match(t1, t2, "random", path)
        self.assertNotEqual(id1, id2)


if __name__ == "__main__":
    unittest.main()
