from abc import ABC, abstractmethod

VALID_NATIONS = frozenset({
    "USSR", "Germany", "USA", "France", "UK",
    "China", "Japan", "Czech", "Sweden", "Poland", "Italy",
})

# Svoriai pagal oficialų WoT matchmaking modelį — eksponentinis augimas užtikrina,
# kad aukšto tier žaidėjai nepatektų į žemo tier mačus dėl svorio disbalanso.
WEIGHT_BY_TIER = {
    1: 2, 2: 3, 3: 5, 4: 8, 5: 12,
    6: 18, 7: 27, 8: 40, 9: 60, 10: 100
}

class Tank(ABC):
    def __init__(self, name: str, tier: int, nation: str) -> None:
        if not (1 <= tier <= 10):
            raise ValueError(f"Invalid tier {tier}. Must be between 1 and 10.")
        if nation not in VALID_NATIONS:
            raise ValueError(f"Invalid nation '{nation}'. Must be one of {VALID_NATIONS}.")
        
        self._name = name
        self._tier = tier
        self._nation = nation

    @property
    def name(self) -> str:
        return self._name

    @property
    def tier(self) -> int:
        return self._tier

    @property
    def nation(self) -> str:
        return self._nation
    
    @property
    @abstractmethod
    def tank_class(self) -> str:
        """Grąžina tanko klasės identifikatorių (pvz. 'Heavy', 'SPG')."""

    @property
    @abstractmethod
    def _weight_multiplier(self) -> float:
        """Klasei būdingas svorio daugiklis matchmaking skaičiavimams."""

    def matchmaking_weight(self) -> float:
        base = WEIGHT_BY_TIER[self._tier]
        return base * self._weight_multiplier
    
    def to_dict(self) -> dict:
        return {
            "name": self._name,
            "tier": self._tier,
            "nation": self._nation,
            "tank_class": self.tank_class,
        }
    
    def __str__(self) -> str:
        return f"{self._name} (Tier {self._tier} {self.tank_class}, {self._nation})"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self._name}', tier={self._tier}, "
            f"nation='{self._nation}')"
        )

class HeavyTank(Tank):
    @property
    def tank_class(self) -> str:
        return "Heavy"

    @property
    def _weight_multiplier(self) -> float:
        return 1.2

class MediumTank(Tank):
    @property
    def tank_class(self) -> str:
        return "Medium"

    @property
    def _weight_multiplier(self) -> float:
        return 1.2 if self._tier >= 9 else 1.0
    
class LightTank(Tank):
    @property
    def tank_class(self) -> str:
        return "Light"

    @property
    def _weight_multiplier(self) -> float:
        return 1.2 if 5 <= self._tier <= 8 else 1.0
    
class TankDestroyer(Tank):
    @property
    def tank_class(self) -> str:
        return "TD"

    @property
    def _weight_multiplier(self) -> float:
        return 1.2 if self._tier >= 8 else 1.0

class SPG(Tank):
    @property
    def tank_class(self) -> str:
        return "SPG"

    @property
    def _weight_multiplier(self) -> float:
        return 1.08
