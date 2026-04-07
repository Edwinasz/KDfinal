# Player model for the World of Tanks inspired matchmaking system.
from .tank import Tank, HeavyTank, MediumTank, LightTank, TankDestroyer, SPG

# Maps tank_class string (from JSON) back to the correct subclass.
_TANK_CLASS_MAP: dict[str, type[Tank]] = {
    "Heavy": HeavyTank,
    "Medium": MediumTank,
    "Light": LightTank,
    "TD": TankDestroyer,
    "SPG": SPG,
}


# Represents a player in the matchmaking system.
# Each player owns exactly one tank at a time. Stats (wins, battles_played)
class Player:
    def __init__(
        self,
        username: str,
        player_id: str,
        tank: Tank,
        wins: int = 0,
        battles_played: int = 0,
    ) -> None:
        if not username.strip():
            raise ValueError("Username cannot be empty.")
        if not player_id.strip():
            raise ValueError("Player ID cannot be empty.")
        if wins < 0 or battles_played < 0:
            raise ValueError("Stats cannot be negative.")
        if wins > battles_played:
            raise ValueError("Wins cannot exceed battles played.")

        self._username = username
        self._player_id = player_id
        self._tank = tank
        self._wins = wins
        self._battles_played = battles_played

    # --- Properties ---

    @property
    def username(self) -> str:
        return self._username
    
    @property
    def player_id(self) -> str:
        return self._player_id
    
    @property
    def tank(self) -> Tank:
        return self._tank
    
    @property
    def wins(self) -> int:
        return self._wins
    
    @property
    def battles_played(self) -> int:
        return self._battles_played
    
    @property
    def win_rate(self) -> float:
        if self._battles_played == 0:
            return 0.0
        return self._wins / self._battles_played
    
    # --- Game logic ---

    def matchmaking_weight(self) -> float:
        return self._tank.matchmaking_weight()
    
    def record_battle(self, won: bool) -> None:
        self._battles_played += 1
        if won:
            self._wins += 1
    
    # --- Serialization ---

    def to_dict(self) -> dict:
        return {
            "username": self._username,
            "player_id": self._player_id,
            "tank": self._tank.to_dict(),
            "wins": self._wins,
            "battles_played": self._battles_played,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """Deserialize a Player from a dictionary (e.g. from JSON)."""
        tank_data = data["tank"]
        tank_cls = _TANK_CLASS_MAP.get(tank_data["tank_class"])
        if tank_cls is None:
            raise ValueError(f"Unknown tank class: '{tank_data['tank_class']}'")

        tank = tank_cls(
            name=tank_data["name"],
            tier=tank_data["tier"],
            nation=tank_data["nation"],
        )

        return cls(
            username=data["username"],
            player_id=data["player_id"],
            tank=tank,
            wins=data.get("wins", 0),
            battles_played=data.get("battles_played", 0),
        )

    def __str__(self) -> str:
        return f"Username: {self._username}, (ID: {self._player_id}, Tank: {self._tank}, Win Rate: {self.win_rate:.2%})"    

    def __repr__(self) -> str:
        return (
            f"Player(username='{self._username}', player_id='{self._player_id}', "
            f"tank={self._tank}, wins={self._wins}, battles_played={self._battles_played})"
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Player):
            return NotImplemented
        return self._player_id == other._player_id
    
    def __hash__(self) -> int:
        return hash(self._player_id)