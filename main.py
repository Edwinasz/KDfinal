"""
Matchmaking CLI — paleidimo taškas.

Paleisti iš projekto šakninio katalogo (aplanko, kuriame yra KDfinal/):
    python -m KDfinal

Galimos komandos (rašyti 'help' viduje):
    players              — išvardinti visus žaidėjus
    match <strategija>   — paleisti matchmaking ir atspausdinti abi komandas
    strategies           — parodyti galimų strategijų pavadinimus
    history [n]          — rodyti paskutinius n mačus (numatyta 5)
    quit                 — išeiti
"""

try:
    from .data_loader import load_players, save_match, load_matches
    from .matchmaking import StrategyFactory
except ImportError:
    from data_loader import load_players, save_match, load_matches
    from matchmaking import StrategyFactory

# ---------------------------------------------------------------------------
# Rodymo pagalbinės funkcijos
# ---------------------------------------------------------------------------

_LINE = "-" * 80
_HEAVY = "=" * 80


def _print_player_row(player, index: int) -> None:
    wr = f"{player.win_rate:.1%}"
    print(
        f"  {index:>2}. {player.username:<16}"
        f"  {'T'+str(player.tank.tier):<3}  {player.tank.tank_class:<6}"
        f"  {player.tank.name:<22}"
        f"  WR {wr:>6}"
        f"  W {player.matchmaking_weight():.1f}"
    )


def _print_team(label: str, team: list) -> None:
    total_w = sum(p.matchmaking_weight() for p in team)
    print(f"\n  {label}  (bendras svoris: {total_w:.1f})")
    print(_LINE)
    for i, p in enumerate(team, 1):
        _print_player_row(p, i)


def _tier_spread(team1: list, team2: list) -> int:
    all_tiers = [p.tank.tier for p in team1 + team2]
    return max(all_tiers) - min(all_tiers)


# ---------------------------------------------------------------------------
# Komandų apdorojimas
# ---------------------------------------------------------------------------

def cmd_help() -> None:
    print(f"""
{_HEAVY}
  MATCHMAKING CLI — komandos
{_HEAVY}
  players              išvardinti visus žaidėjus
  match <strategija>   sudaryti dvi komandas pasirinkta strategija
  strategies           parodyti galimas strategijas
  history [n]          rodyti paskutinius n išsaugotų mačų  (numatyta: 5)
  quit                 išeiti
{_HEAVY}""")


def cmd_players(players: list) -> None:
    if not players:
        print("  Žaidėjai neįkelti. Patikrinkite data/players.json.")
        return
    print(f"\n  Sąrašas — {len(players)} žaidėjai")
    print(_LINE)
    for i, p in enumerate(players, 1):
        _print_player_row(p, i)
    print()


def cmd_match(players: list, args: list[str]) -> None:
    if not args:
        print("  Naudojimas: match <strategija>")
        print(f"  Galimos: {', '.join(StrategyFactory.available())}")
        return

    strategy_name = args[0].lower()

    try:
        strategy = StrategyFactory.create(strategy_name)
    except ValueError as exc:
        print(f"  Klaida: {exc}")
        return

    result = strategy.match(players)

    if result is None:
        needed = 30
        print(
            f"  Nepakanka žaidėjų mačui "
            f"(yra {len(players)}, reikia {needed})."
        )
        return

    team1, team2 = result
    spread = _tier_spread(team1, team2)
    w1 = sum(p.matchmaking_weight() for p in team1)
    w2 = sum(p.matchmaking_weight() for p in team2)

    print(f"\n{_HEAVY}")
    print(f"  Strategija : {strategy_name}")
    print(f"  Tier skirtumas : {spread}  (+/-{spread // 2 if spread % 2 == 0 else spread})")
    print(f"  Svorio balansas : {w1:.1f} vs {w2:.1f}  (skirtumas {abs(w1 - w2):.1f})")
    print(_HEAVY)

    _print_team("KOMANDA 1", team1)
    _print_team("KOMANDA 2", team2)
    print()

    answer = input("  Išsaugoti šį mačą? [y/N] ").strip().lower()
    if answer == "y":
        match_id = save_match(team1, team2, strategy_name)
        print(f"  Išsaugota — mačo id: {match_id}\n")
    else:
        print("  Mačas atmestas.\n")


def cmd_strategies() -> None:
    print("\n  Galimos strategijos:")
    descriptions = {
        "random":      "atsitiktinis maišymas, be balanso",
        "tier":        "lygus tier pasiskirstymas komandose (+/-2 tier langas)",
        "weight":      "godžioji svorio pusiausvyra",
        "tier_weight": "pirmiausia tier langas, tada godžioji svorio pusiausvyra (+/-2 tier langas)",
    }
    for name in StrategyFactory.available():
        desc = descriptions.get(name, "")
        print(f"    {name:<14}  {desc}")
    print()


def cmd_history(args: list[str]) -> None:
    try:
        n = int(args[0]) if args else 5
    except ValueError:
        print("  Naudojimas: history [skaičius]")
        return

    matches = load_matches()
    if not matches:
        print("  Mačų istorija tuščia.")
        return

    recent = matches[-n:]
    print(f"\n  Paskutiniai {len(recent)} mačai")
    print(_LINE)
    for m in reversed(recent):
        t1_names = ", ".join(p["username"] for p in m["Team1"])
        t2_names = ", ".join(p["username"] for p in m["Team2"])
        print(f"  [{m['match_id']}]  {m['timestamp'][:19]}  strategija={m['strategy']}")
        print(f"    Komanda 1: {t1_names}")
        print(f"    Komanda 2: {t2_names}")
        print()


# ---------------------------------------------------------------------------
# Pagrindinis ciklas
# ---------------------------------------------------------------------------

def main() -> None:
    print(_HEAVY)
    print("  World of Tanks Matchmaking Sistema")
    print("  Rašykite 'help' norėdami pamatyti komandas.")
    print(_HEAVY)

    players = load_players()
    if players:
        print(f"  Įkelti {len(players)} žaidėjai.\n")
    else:
        print("  Įspėjimas: žaidėjai neįkelti (data/players.json tuščias).\n")

    while True:
        try:
            raw = input("mm> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Viso gero.")
            break

        if not raw:
            continue

        parts = raw.split()
        command, args = parts[0].lower(), parts[1:]

        if command in ("quit", "exit", "q"):
            print("  Viso gero.")
            break
        elif command == "help":
            cmd_help()
        elif command == "players":
            cmd_players(players)
        elif command == "match":
            cmd_match(players, args)
        elif command == "strategies":
            cmd_strategies()
        elif command == "history":
            cmd_history(args)
        else:
            print(f"  Nežinoma komanda '{command}'. Rašykite 'help'.")


if __name__ == "__main__":
    main()
