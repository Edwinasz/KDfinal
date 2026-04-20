"""
JSON duomenų saugojimo sluoksnis matchmaking sistemai.

Teikia dvi funkcijas kiekvienam objektui:
  load_players / save_players   — skaito/rašo žaidėjų sąrašą
  load_matches  / save_match    — skaito mačų istoriją / prideda vieną mačo įrašą
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .player import Player

# ---------------------------------------------------------------------------
# Keliai
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"
PLAYERS_FILE = DATA_DIR / "players.json"
MATCHES_FILE = DATA_DIR / "match_output.json"


# ---------------------------------------------------------------------------
# Žaidėjai
# ---------------------------------------------------------------------------

def load_players(path: Path = PLAYERS_FILE) -> list[Player]:
    """
    Įkelia visus žaidėjus iš JSON failo.

    Tikėtinas failo formatas:
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

    Grąžina tuščią sąrašą jei failas neegzistuoja arba yra tuščias.
    Kelia ValueError jei bet kuris žaidėjo įrašas yra klaidingas.
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
            raise ValueError(f"Klaidingas žaidėjo įrašas indekse {i}: {exc}") from exc

    return players


def save_players(players: list[Player], path: Path = PLAYERS_FILE) -> None:
    """
    Perrašo žaidėjų sąrašo failą pateiktu sąrašu.

    Sukuria tėvinį katalogą jei jo nėra.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in players], f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Mačų istorija
# ---------------------------------------------------------------------------

def load_matches(path: Path = MATCHES_FILE) -> list[dict]:
    """
    Įkelia visą mačų istoriją iš JSON failo.

    Kiekvienas sąrašo elementas yra mačo įrašas, kurį parašė save_match().
    Grąžina tuščią sąrašą jei failas neegzistuoja arba yra tuščias.
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
    Prideda vieną mačo rezultatą prie mačų istorijos failo.

    Automatiškai generuoja unikalų match_id ir ISO-8601 UTC laiko žymę.
    Grąžina match_id, kad kviečiantysis galėtų nuorodą į išsaugotą įrašą.

    Išsaugomo įrašo formatas:
        {
            "match_id": "a3f1...",
            "timestamp": "2026-04-01T12:00:00+00:00",
            "strategy": "tier_weight",
            "Team1": [ { žaidėjo žodynas }, ... ],
            "Team2": [ { žaidėjo žodynas }, ... ]
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
