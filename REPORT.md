# World of Tanks Matchmaking Sistema — Kursinio Darbo Ataskaita

---

## 1. Įvadas

### Apie ką yra ši programa?

Šis projektas yra **World of Tanks žaidimo matchmaking simuliacija**, parašyta Python 3.12.  
Kursinio darbo tikslas — parodyti visus keturis objektinio programavimo (OOP) principus,
sprendžiant realų, dalykinės srities uždavinį: sugrupuoti tankų žaidėjus į dvi subalansuotas
15 žaidėjų komandas prieš mūšį.

Programa modeliuoja:

- **Tankų hierarchiją** (HeavyTank, MediumTank, LightTank, TankDestroyer, SPG) — kiekvienas
  tanko tipas turi skirtingą matchmaking svorį.
- **Žaidėją**, kuris valdo vieną tanką ir turi savo pergalių/mūšių statistiką.
- Keturias keičiamas **matchmaking strategijas**, kurios 30 žaidėjų baseiną padalija į dvi
  komandas pagal skirtingas balanso taisykles (atsitiktinis, pagal tier, pagal svorį arba abu).
- **JSON saugojimo sluoksnį**, kuris įkelia žaidėjų sąrašą ir išsaugo kiekvieną baigtą mačą į
  istorijos failą.
- **Interaktyvų CLI**, kuris leidžia tyrinėti ir naudoti sistemą.

### Kaip paleisti programą?

Reikalingas Python 3.12+. Jokių išorinių bibliotekų nereikia.

```bash
# Iš katalogo, kuriame YRA KDfinal/ aplankas:
python -m KDfinal
```

### Kaip naudotis programa?

Paleidus programą, galima rašyti šias komandas:

| Komanda | Aprašymas |
|---|---|
| `players` | Išvardinti visus 70 žaidėjų sąraše |
| `strategies` | Parodyti visas galimas matchmaking strategijas |
| `match <strategija>` | Sudaryti dvi komandas pasirinkta strategija |
| `history [n]` | Rodyti paskutinius n išsaugotų mačų (numatyta: 5) |
| `help` | Spausdinti komandų sąrašą |
| `quit` | Išeiti iš programos |

Naudojimo pavyzdys:

```
mm> match tier_weight
================================================================================
  Strategija : tier_weight
  Tier skirtumas : 2  (+/-2)
  Svorio balansas : 756.0 vs 754.8  (skirtumas 1.2)
================================================================================

  KOMANDA 1  (bendras svoris: 756.0)
  ...
  KOMANDA 2  (bendras svoris: 754.8)
  ...
  Išsaugoti šį mačą? [y/N] y
  Išsaugota — mačo id: 3a7f1c2d
```

---

## 2. Analizė

### 2.1 OOP Principas 1 — Inkapsuliacija (Encapsulation)

**Kas tai yra:**  
Inkapsuliacija sujungia duomenis (atributus) ir metodus, kurie su jais dirba, į vieną klasę,
ir kontroliuoja išorinę prieigą naudojant prieigos modifikatorius. Python kalboje tai daroma
prefiksu `_` (apsaugoti atributai), prie kurių prieiga suteikiama tik per tik skaitymo
`@property` deskriptorius.

**Kaip naudojama šiame projekte:**

Visi `Tank` ir `Player` klasių atributai yra privatūs ir pasiekiami tik per savybes.
Tiesioginis priskyrimas iš išorės yra draudžiamas. Tikrinimas atliekamas konstruktoriuje —
sukūrus objektą, jo pagrindiniai laukai negali būti sugadinti iš išorės.

```python
# tank.py
class Tank(ABC):
    def __init__(self, name: str, tier: int, nation: str) -> None:
        if not (1 <= tier <= 10):
            raise ValueError(f"Invalid tier {tier}. Must be between 1 and 10.")
        if nation not in VALID_NATIONS:
            raise ValueError(f"Invalid nation '{nation}'.")

        self._name = name      # privatus — negali būti pakeistas iš išorės
        self._tier = tier
        self._nation = nation

    @property
    def tier(self) -> int:     # saugi tik skaitoma prieiga
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
    def win_rate(self) -> float:       # apskaičiuojama, ne saugoma
        if self._battles_played == 0:
            return 0.0
        return self._wins / self._battles_played
```

---

### 2.2 OOP Principas 2 — Abstrakcija (Abstraction)

**Kas tai yra:**  
Abstrakcija paslepia įgyvendinimo detales ir atskleidžia tik tą sąsają, kurios reikia
iškvietėjams. Python kalboje `abc.ABC` su `@abstractmethod` užtikrina, kad poklasiai
įgyvendintų reikiamą sąsają, neatskleidžiant kaip.

**Kaip naudojama šiame projekte:**

`Tank` yra abstrakti bazinė klasė. Iškvietėjai dirba su `Tank` nuorodomis ir kviečia
`matchmaking_weight()` nežinodami, kokį konkretų poklasį turi.

```python
# tank.py
from abc import ABC, abstractmethod

class Tank(ABC):

    @property
    @abstractmethod
    def tank_class(self) -> str:
        """Grąžina tanko klasės identifikatorių (pvz. 'Heavy', 'SPG')."""

    @property
    @abstractmethod
    def _weight_multiplier(self) -> float:
        """Klasei būdingas svorio daugiklis matchmaking skaičiavimams."""

    def matchmaking_weight(self) -> float:   # konkretus — naudoja abstraktų daugiklį
        return WEIGHT_BY_TIER[self._tier] * self._weight_multiplier
```

`MatchmakingStrategy` taiko tą pačią idėją strategijoms:

```python
# matchmaking.py
class MatchmakingStrategy(ABC):

    @abstractmethod
    def match(self, players: list) -> tuple | None:
        """Padalija žaidėjus į dvi subalansuotas 15 žaidėjų komandas."""
```

CLI ir testai kviečia tik `strategy.match(players)` — jiems niekada nereikia žinoti, ar
strategija yra `RandomStrategy`, ar `TierWeightStrategy`.

---

### 2.3 OOP Principas 3 — Paveldėjimas (Inheritance)

**Kas tai yra:**  
Paveldėjimas leidžia poklasui pakartotinai naudoti tėvinės klasės kodą ir išplėsti ar
perrašyti jo elgesį. Jis sukuria „yra" (is-a) santykį.

**Kaip naudojama šiame projekte:**

Visi penki tankų tipai paveldi iš `Tank`. Jie perrašo tik dvi abstrakčias savybes —
viskas kita (tikrinimas, `to_dict`, `__str__`, `__repr__`) paveldima automatiškai.

```python
# tank.py
class HeavyTank(Tank):
    @property
    def tank_class(self) -> str:
        return "Heavy"

    @property
    def _weight_multiplier(self) -> float:
        return 1.2          # visada 20% sunkesnis — stipriausia klasifikacija


class LightTank(Tank):
    @property
    def tank_class(self) -> str:
        return "Light"

    @property
    def _weight_multiplier(self) -> float:
        return 1.2 if 5 <= self._tier <= 8 else 1.0   # bonusas tik aktyviame žvalgų diapazone
```

Visos keturios matchmaking strategijos paveldi iš `MatchmakingStrategy`:

```python
# matchmaking.py
class TierWeightStrategy(MatchmakingStrategy):
    def match(self, players: list) -> tuple | None:
        pool = _select_tier_pool(players)
        ...
```

Paveldėjimas pašalina kodo dubliavimą: kiekviena konkreti tanko klasė yra maždaug 6 eilutės;
be paveldėjimo reikėtų pakartoti 40+ eilučių tikrinimo, serializavimo ir `__dunder__` metodų.

---

### 2.4 OOP Principas 4 — Polimorfizmas (Polymorphism)

**Kas tai yra:**  
Polimorfizmas leidžia skirtingiems objektams reaguoti į tą patį metodo kvietimą savaip.
Kodas, kuris kviečia `obj.method()`, neprivalo žinoti konkretaus `obj` tipo — teisingas
įgyvendinimas parenkamas vykdymo metu.

**Kaip naudojama šiame projekte:**

CLI kviečia `strategy.match(players)` ant bet kurio pasirinkto `MatchmakingStrategy`
egzemplioriaus. Ta pati kodo eilutė gamina keturis visiškai skirtingus rezultatus:

```python
# main.py
strategy = StrategyFactory.create(strategy_name)  # grąžina vieną iš 4 tipų
result = strategy.match(players)                  # polimorfinis iškvietimas
```

Tas pat taikoma `matchmaking_weight()`. Žemiau esantis kodas veikia vienodai kiekvienam
tanko tipui be jokių `isinstance` tikrinimų:

```python
# veikia HeavyTank, MediumTank, LightTank, TankDestroyer, SPG — visiems skaidriai
total_weight = sum(p.matchmaking_weight() for p in team)
```

`Player.__eq__` taip pat yra polimorfinis — grąžina `NotImplemented` lyginant su ne-`Player`
objektu, leisdamas Python grįžti prie numatytojo elgesio:

```python
# player.py
def __eq__(self, other: object) -> bool:
    if not isinstance(other, Player):
        return NotImplemented
    return self._player_id == other._player_id
```

---

### 2.5 Projektavimo Šablonas — Fabrikinis Metodas (Factory Method)

**Kas tai yra:**  
Fabrikinio metodo šablonas apibrėžia sąsają objektų kūrimui, tačiau leidžia fabriko klasei
nuspręsti, kurį konkretų klasę instantizuoti. Iškvietėjas prašo objekto pagal pavadinimą
ir gauna pilnai sukonstruotą egzempliorių nežinodamas klasės.

**Kaip naudojama šiame projekte:**

`StrategyFactory` laiko registro žodyną ir `create()` metodą, kuris žemėlapina eilutės
pavadinimus į konkrečias strategijų klases:

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
            raise ValueError(
                f"Nežinoma matchmaking strategija '{name}'. Galimos: {valid}"
            )
        return cls()

    @staticmethod
    def available() -> list[str]:
        return sorted(StrategyFactory._registry)
```

**Kodėl Fabrikinis Metodas, o ne kiti šablonai?**

- **Singleton** — netinkamas: reikia daugelio nepriklausomų strategijų egzempliorių, ne vieno
  bendro.
- **Builder** — perteklinis: strategijos neturi sudėtingo daugiapakopės konstrukcijos proceso.
- **Abstract Factory** — tiktų, jei kurtume susijusių objektų *šeimas* (pvz. strategija +
  vertintojas + žurnalas kartu). Čia kuriamas tik vienas objekto tipas.
- **Fabrikinis Metodas** — tinka tiksliai: iškvietėjas pateikia pavadinimo eilutę (iš vartotojo
  įvesties ar testo), fabrikas parenka ir sukonstruoja tinkamą klasę, o iškvietėjas visada
  laiko tik `MatchmakingStrategy` nuorodą. Norint pridėti naują strategiją, reikia tik vienos
  naujos eilutės registro žodyne — jokie pokyčiai iškvietėjuose nereikalingi.

---

### 2.6 Kompozicija ir Agregacija

**Kompozicija** yra „turi" (has-a) santykis, kuriame valdomo objekto gyvavimo laikas
kontroliuojamas savininko. **Agregacija** taip pat yra „turi", bet valdomas objektas gali
egzistuoti savarankiškai.

**Kompozicija projekte — `Player` valdo `Tank`:**

`Player` sukonstruojamas su `Tank` egzemplioriumi ir laiko jį išimtinai. Tankų žaidėjai
nesidalina vienu tanku, o `Tank` neturi prasmės be `Player` konteksto. Tai yra **kompozicija**.

```python
# player.py
class Player:
    def __init__(self, username, player_id, tank: Tank, wins=0, battles_played=0):
        self._tank = tank        # Player VALDO šį Tank

    def matchmaking_weight(self) -> float:
        return self._tank.matchmaking_weight()   # deleguoja sudėtiniam objektui
```

`Player` taip pat **sudaro** savo elgesį iš `Tank`: `matchmaking_weight()` nėra dubliuojamas —
jis deleguojamas `self._tank`, todėl žaidėjo svoris automatiškai pasikeičia pasikeitus
tanko tipui.

**Agregacija projekte — strategijos dirba su žaidėjų sąrašais:**

`MatchmakingStrategy.match()` gauna `Player` objektų sąrašą, kurių ji nesukūrė ir nevaldo.
Žaidėjai egzistuoja prieš strategijos kvietimą ir po jo. Tai yra **agregacija**.

```python
# matchmaking.py
class WeightStrategy(MatchmakingStrategy):
    def match(self, players: list) -> tuple | None:
        # žaidėjai priklauso main.py — ši strategija juos tik skaito
        pool = sorted(
            players[:REQUIRED_PLAYERS],
            key=lambda p: p.matchmaking_weight(),
            reverse=True,
        )
        ...
```

---

### 2.7 Skaitymas iš Failo ir Rašymas į Failą

`data_loader.py` modulis tvarko visą JSON saugojimą naudodamas tik standartinę biblioteką.

**Žaidėjų įkėlimas iš failo:**

```python
# data_loader.py
def load_players(path: Path = PLAYERS_FILE) -> list[Player]:
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
```

**Mačo rezultato pridėjimas prie istorijos failo:**

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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    return match_id
```

Naudojami du failai:

| Failas | Paskirtis | Operacijos |
|---|---|---|
| `data/players.json` | Žaidėjų sąrašas (70 žaidėjų, tier 5–10) | Skaitoma paleidžiant |
| `data/match_output.json` | Mačų istorija (pridedama po kiekvieno patvirtinto mačo) | Skaitoma ir rašoma |

---

### 2.8 Testavimas

Visa pagrindinė logika padengta vienetiniais testais naudojant Python integruotą `unittest`
karkasą, suskirstytą į keturis testų modulius, atitinkančius šaltinio modulius.

**Testų paleidimas:**

```bash
# Iš KDfinal/ tėvinio katalogo:
python -m unittest discover -s KDfinal/tests -p "test_*.py" --top-level-directory .
```

**Pavyzdys — `TankDestroyer` svorio daugiklio ribų tikrinimas:**

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

**Pavyzdys — `WeightStrategy` komandų svorio balanso tikrinimas:**

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

**Testų aprėpties santrauka:**

| Modulis | Testų klasės | Scenarijai |
|---|---|---|
| `tank.py` | `TestTankValidation`, `TestTankClass`, `TestTankWeights`, `TestTankSerialization` | Tier/tautos tikrinimas, visi daugiklio ribų atvejai, serializavimo ciklas |
| `player.py` | `TestPlayerValidation`, `TestPlayerStats`, `TestPlayerEquality`, `TestPlayerSerialization` | Statistikos tikrinimas, laimėjimo normos kraštiniai atvejai, `record_battle`, lygybė ir maišymas, `from_dict` numatytosios reikšmės |
| `matchmaking.py` | `TestSelectTierPool`, `TestRandom/Tier/Weight/TierWeightStrategy`, `TestStrategyFactory`, `TestRunMatchmaking` | Skirtumas 0/1/2 rezervinis, skirtumas >2 atmetimas, komandų dydžiai, jokių dublikatų, svorio skirtumas, fabriko registras |
| `data_loader.py` | `TestLoadPlayers`, `TestSavePlayers`, `TestLoadMatches`, `TestSaveMatch` | Neegzistuojantis/tuščias failas, apykaitinis ciklas, perrašymas, tėvinio katalogo kūrimas, unikalūs mačų ID |

---

## 3. Rezultatai ir Išvados

### Rezultatai

- Programa sėkmingai įgyvendina veikiantį matchmaking CLI, kuris sugrupuoja 30 žaidėjų į
  subalansuotas komandas naudodamas keturias skirtingas strategijas — visos gamina komandas
  be dublikatų ir tinkamo dydžio iš galimų 150 žaidėjų.
- Sudėtingiausia įgyvendinimo dalis buvo `_select_tier_pool` pagalbinė funkcija: ji turi
  rasti siauriausią galiojantį tier langą (skirtumas 0 → 1 → 2) per atsitiktinį žaidėjų
  baseiną, o kiekviename segmente maišyti žaidėjus, kad tie patys žaidėjai nebūtų visada
  parenkami.
- Strategy šablono pritaikymas leido lengvai pridėti naujus balanso algoritmus neliečiant
  CLI ar saugojimo sluoksnių — reikėjo tik naujos eilutės registro žodyne.
- Kompozicijos naudojimas (`Player` valdo `Tank`) palaikė `matchmaking_weight()` vieną
  eilutės delegavimo, o ne dubliuotos logikos dviejose klasėse.
- Testų rašymas prieš galutinai nustatant daugiklio ribų taisykles (pvz. `LightTank` bonusai
  tier 5–8, `TankDestroyer` bonusai nuo tier 8) atskleidė du vienetu perskaičiavimo klaidas
  kūrimo metu.

### Išvados

Šis kursinis darbas parodo, kad OOP principai nėra abstrakti teorija — jie sprendžia
konkrečias inžinerines problemas. Inkapsuliacija palaikė tanko ir žaidėjo būseną nuoseklią;
abstrakcija leido CLI valdyti keturias strategijas per vieną sąsają; paveldėjimas sumažino
penkias tankų klases iki maždaug 6 eilučių kiekvieną; polimorfizmas leido vienam
`strategy.match()` kvietimui parinkti tinkamą algoritmą vykdymo metu. Fabrikinio metodo
šablonas švariai atskyrė vartotojo pateiktus strategijų pavadinimus nuo klasių konstrukcijos.

Rezultatas yra prižiūrima, testuojama matchmaking sistema. Ateities plėtros galimybės:
`win_rate` įtraukimas į svorio formulę įgūdžiais pagrįstam balansavimui; gyvas `reload`
komandos pridėjimas žaidėjų sąrašo atnaujinimui nerestartuojant programos; viešo
`StrategyFactory.register()` API atskleidimas, kad išoriniai moduliai galėtų pridėti
strategijas neredaguodami bibliotekos kodo.

---

## 4. Šaltiniai

- [Python `abc` modulis — Abstrakčios Bazinės Klasės](https://docs.python.org/3/library/abc.html)
- [PEP 8 — Python kodo stiliaus vadovas](https://peps.python.org/pep-0008/)
- [Python `unittest` karkasas](https://docs.python.org/3/library/unittest.html)
- [Refactoring Guru — Fabrikinis Metodas](https://refactoring.guru/design-patterns/factory-method)
- [Refactoring Guru — Strategijos Šablonas](https://refactoring.guru/design-patterns/strategy)
- [Python `json` modulis](https://docs.python.org/3/library/json.html)
- [Markdown sintaksės vadovas](https://www.markdownguide.org/basic-syntax/)
