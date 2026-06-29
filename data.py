"""Hero data model and loader."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "heroes.json"


@dataclass(frozen=True)
class Hero:
    name: str
    ele: str          # ATTACK / MAGIC / UNIVERSAL / DEFENSE / SUPPORT
    type: str         # ATTACK / MAGIC (damage type)
    atk: int          # base ATK  (X3)
    dfn: int          # base DEF  (X4)
    hp: int           # base HP   (X5)
    spd: int          # base SPD  (X2)
    star_main: str    # transcend main stat: ATK / DEF
    star4: str        # transcend tier-4 bonus: CR/CDM/WK/BLK/RED/EFF
    grade: str        # LEGEND / RARE


@lru_cache(maxsize=1)
def load_heroes() -> dict[str, Hero]:
    """Load all heroes keyed by name."""
    rows = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    heroes = {}
    for r in rows:
        heroes[r["name"]] = Hero(
            name=r["name"], ele=r["ele"], type=r["type"],
            atk=r["atk"], dfn=r["def"], hp=r["hp"], spd=r["spd"],
            star_main=r["star_main"], star4=r["star4"], grade=r["grade"],
        )
    return heroes


def get_hero(name: str) -> Hero:
    """Look up a hero by exact name. Raises KeyError if not found."""
    heroes = load_heroes()
    if name not in heroes:
        raise KeyError(f"Hero {name!r} not found. {len(heroes)} heroes available.")
    return heroes[name]
