"""
JSON persistence layer for the matchmaking system.

Provides two functions per entity:
  load_players / save_players   — read/write the player roster
  load_matches  / save_match    — read the match history / append one match result

All files default to the paths in DATA_DIR but callers may override them.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .player import Player

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"
PLAYERS_FILE = DATA_DIR / "players.json"
MATCHES_FILE = DATA_DIR / "match_output.json"


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------

def load_players(path: Path = PLAYERS_FILE) -> list[Player]:
    """
    Load all players from a JSON file.

    Expected file format:
        [
            {
                "username": "TankAce",
                "player_id": "p001",
                "tank": {
                    "name": "Tiger I",
                    "tier": 7,
                    "nation": "Germany",
                    "tank_class": "Heavy"
                },
                "wins": 120,
                "battles_played": 200
            },
            ...
        ]

    Returns an empty list if the file does not exist or is empty.
    Raises ValueError if any player entry is malformed.
    """
    if not path.exists() or path.stat().st_size == 0:
        return []

    with path.open(encoding="utf-8") as f:
        raw: list[dict] = json.load(f)

    players: list[Player] = []
    for i, entry in enumerate(raw):
        try:
            players.append(Player.from_dict(entry))
        except (KeyError, ValueError) as exc:
            raise ValueError(f"Malformed player entry at index {i}: {exc}") from exc

    return players


def save_players(players: list[Player], path: Path = PLAYERS_FILE) -> None:
    """
    Overwrite the player roster file with the given list.

    Creates the parent directory if it does not exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in players], f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Match history
# ---------------------------------------------------------------------------

def load_matches(path: Path = MATCHES_FILE) -> list[dict]:
    """
    Load the full match history from a JSON file.

    Each entry in the list is a match record as written by save_match().
    Returns an empty list if the file does not exist or is empty.
    """
    if not path.exists() or path.stat().st_size == 0:
        return []

    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_match(
    team1: list[Player],
    team2: list[Player],
    strategy: str,
    path: Path = MATCHES_FILE,
) -> str:
    """
    Append one match result to the match history file.

    Generates a unique match_id and an ISO-8601 UTC timestamp automatically.
    Returns the match_id so callers can reference the saved record.

    Saved record format:
        {
            "match_id": "a3f1...",
            "timestamp": "2026-04-01T12:00:00+00:00",
            "strategy": "tier_weight",
            "Team1": [ { player dict }, ... ],
            "Team2": [ { player dict }, ... ]
        }
    """
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

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    return match_id
