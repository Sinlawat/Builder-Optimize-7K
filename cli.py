"""Command-line interface for the SKRE equipment optimizer.

Example:
    python cli.py Vanessa --set Assassin --target CR=71 SPD=29 WK=25 \
        --priority ATK CDM --transcend 6 --atk-lvl 30 --ring 6 --top 3
"""
from __future__ import annotations

import argparse
import sys

import constants as C
from solver import top_builds

LABELS = {
    "ATK": "Attack", "DEF": "Defense", "HP": "HP", "SPD": "Speed",
    "CR": "Crit Rate", "CDM": "Crit Damage", "WK": "Weakness Hit",
    "BLK": "Block Rate", "RED": "Dmg Taken Reduction",
    "EHR": "Effect Hit Rate", "ERes": "Effect Resistance",
}


def _parse_targets(items):
    targets = {}
    for item in items or []:
        if "=" not in item:
            sys.exit(f"bad --target {item!r}; use STAT=VALUE e.g. CR=71")
        key, val = item.split("=", 1)
        key = key.upper() if key.upper() in C.STATS else key
        if key not in C.STATS:
            sys.exit(f"unknown stat {key!r}. valid: {', '.join(C.STATS)}")
        targets[key] = int(val)
    return targets


def _print_build(rank, result, priority):
    stats = result.stats
    head = "  ".join(f"{LABELS.get(s, s)} {stats[s]}" for s in priority)
    flag = "" if result.targets_met else "  [targets NOT fully met]"
    print(f"\n#{rank}  {head}{flag}")
    print("  pieces:")
    for p in result.build.pieces:
        subs = ", ".join(f"{t}{'+' + str(r) if r else ''}" for t, r in p.substats)
        print(f"    [{p.slot:7}] main: {p.main:22} | sub: {subs}")
    if rank == 1:
        print("  reasoning:")
        for line in result.reasoning:
            print(f"    {line}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="SKRE equipment build optimizer")
    ap.add_argument("hero")
    ap.add_argument("--set", required=True, dest="set_name", choices=C.SET_NAMES)
    ap.add_argument("--target", nargs="+", default=[], help="STAT=VALUE, e.g. CR=71 SPD=29")
    ap.add_argument("--priority", nargs="+", default=["ATK"], help="ordered stat codes")
    ap.add_argument("--transcend", type=int, default=0, choices=range(13))
    ap.add_argument("--atk-lvl", type=int, default=0, choices=[0, 10, 20, 30])
    ap.add_argument("--def-lvl", type=int, default=0, choices=[0, 10, 20, 30])
    ap.add_argument("--hp-lvl", type=int, default=0, choices=[0, 10, 20, 30])
    ap.add_argument("--ring", type=int, default=6, choices=[4, 5, 6])
    ap.add_argument("--cap", type=int, default=5, choices=range(1, 6))
    ap.add_argument("--top", type=int, default=3)
    args = ap.parse_args(argv)

    targets = _parse_targets(args.target)
    priority = [p.upper() if p.upper() in C.STATS else p for p in args.priority]
    for p in priority:
        if p not in C.STATS:
            sys.exit(f"unknown priority stat {p!r}")

    builds = top_builds(
        args.hero, args.set_name, targets=targets, priority=priority, n=args.top,
        transcend=args.transcend, atk_lvl=args.atk_lvl, def_lvl=args.def_lvl,
        hp_lvl=args.hp_lvl, ring=args.ring, cap=args.cap,
    )

    print(f"Hero: {args.hero} | Set: {args.set_name} (4pc) | "
          f"T{args.transcend} | Ring {args.ring} | priority {' > '.join(priority)}")
    if targets:
        print("Targets: " + ", ".join(f"{LABELS.get(k, k)} >= {v}" for k, v in targets.items()))
    for i, r in enumerate(builds, 1):
        _print_build(i, r, priority)


if __name__ == "__main__":
    main()
