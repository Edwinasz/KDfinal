"""
Matchmaking CLI — entry point.

Run from the project root (the folder that contains KDfinal/):
    python -m KDfinal

Available commands (type 'help' inside the shell):
    players              — list all players in the roster
    match <strategy>     — run matchmaking and print both teams
    strategies           — list valid strategy names
    history [n]          — show last n matches (default 5)
    quit                 — exit
"""

try:
    from .data_loader import load_players, save_match, load_matches
    from .matchmaking import StrategyFactory
except ImportError:
    from data_loader import load_players, save_match, load_matches
    from matchmaking import StrategyFactory

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

_LINE = "-" * 60
_HEAVY = "=" * 60


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
    print(f"\n  {label}  (total weight: {total_w:.1f})")
    print(_LINE)
    for i, p in enumerate(team, 1):
        _print_player_row(p, i)


def _tier_spread(team1: list, team2: list) -> int:
    all_tiers = [p.tank.tier for p in team1 + team2]
    return max(all_tiers) - min(all_tiers)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_help() -> None:
    print(f"""
{_HEAVY}
  MATCHMAKING CLI — commands
{_HEAVY}
  players              list every player in the roster
  match <strategy>     form two teams using the chosen strategy
  strategies           show all valid strategy names
  history [n]          show last n saved matches  (default: 5)
  quit                 exit the program
{_HEAVY}""")


def cmd_players(players: list) -> None:
    if not players:
        print("  No players loaded. Check data/players.json.")
        return
    print(f"\n  Roster — {len(players)} players")
    print(_LINE)
    for i, p in enumerate(players, 1):
        _print_player_row(p, i)
    print()


def cmd_match(players: list, args: list[str]) -> None:
    if not args:
        print("  Usage: match <strategy>")
        print(f"  Available: {', '.join(StrategyFactory.available())}")
        return

    strategy_name = args[0].lower()

    try:
        strategy = StrategyFactory.create(strategy_name)
    except ValueError as exc:
        print(f"  Error: {exc}")
        return

    result = strategy.match(players)

    if result is None:
        needed = 30
        print(
            f"  Not enough players for a match "
            f"(have {len(players)}, need {needed})."
        )
        return

    team1, team2 = result
    spread = _tier_spread(team1, team2)
    w1 = sum(p.matchmaking_weight() for p in team1)
    w2 = sum(p.matchmaking_weight() for p in team2)

    print(f"\n{_HEAVY}")
    print(f"  Strategy : {strategy_name}")
    print(f"  Tier spread : {spread}  (+/-{spread // 2 if spread % 2 == 0 else spread})")
    print(f"  Weight balance : {w1:.1f} vs {w2:.1f}  (diff {abs(w1 - w2):.1f})")
    print(_HEAVY)

    _print_team("TEAM 1", team1)
    _print_team("TEAM 2", team2)
    print()

    answer = input("  Save this match? [y/N] ").strip().lower()
    if answer == "y":
        match_id = save_match(team1, team2, strategy_name)
        print(f"  Saved — match id: {match_id}\n")
    else:
        print("  Match discarded.\n")


def cmd_strategies() -> None:
    print("\n  Available strategies:")
    descriptions = {
        "random":      "random shuffle, no balancing",
        "tier":        "equal tier distribution per team (+/-2 tier window)",
        "weight":      "greedy weight balancing",
        "tier_weight": "tier window first, then greedy weight balance (+/-2 tier window)",
    }
    for name in StrategyFactory.available():
        desc = descriptions.get(name, "")
        print(f"    {name:<14}  {desc}")
    print()


def cmd_history(args: list[str]) -> None:
    try:
        n = int(args[0]) if args else 5
    except ValueError:
        print("  Usage: history [number]")
        return

    matches = load_matches()
    if not matches:
        print("  No matches recorded yet.")
        return

    recent = matches[-n:]
    print(f"\n  Last {len(recent)} match(es)")
    print(_LINE)
    for m in reversed(recent):
        t1_names = ", ".join(p["username"] for p in m["Team1"])
        t2_names = ", ".join(p["username"] for p in m["Team2"])
        print(f"  [{m['match_id']}]  {m['timestamp'][:19]}  strategy={m['strategy']}")
        print(f"    Team1: {t1_names}")
        print(f"    Team2: {t2_names}")
        print()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    print(_HEAVY)
    print("  World of Tanks Matchmaking System")
    print("  Type 'help' for available commands.")
    print(_HEAVY)

    players = load_players()
    if players:
        print(f"  Loaded {len(players)} players from roster.\n")
    else:
        print("  Warning: no players loaded (data/players.json is empty).\n")

    while True:
        try:
            raw = input("mm> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye.")
            break

        if not raw:
            continue

        parts = raw.split()
        command, args = parts[0].lower(), parts[1:]

        if command in ("quit", "exit", "q"):
            print("  Goodbye.")
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
            print(f"  Unknown command '{command}'. Type 'help' for options.")


if __name__ == "__main__":
    main()
