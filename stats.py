"""Stat engine: compute a build's final stats using the formulas reverse-engineered
from the SKRE Build Maker. Flat-layout imports (constants.py / data.py at repo root).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import floor

import constants as C
from data import get_hero


@dataclass
class Piece:
    """One equipment piece. slot decides which main-stat pool is legal."""
    slot: str                              # "offense" | "defense"
    main: str                              # main stat option name
    substats: list[tuple[str, int]] = field(default_factory=list)  # (type, rolls)


@dataclass
class Build:
    hero: str
    set_name: str
    pieces: list[Piece]
    transcend: int = 0                     # Q2, 0..12
    atk_lvl: int = 0                       # 0/10/20/30
    def_lvl: int = 0
    hp_lvl: int = 0
    ring: int = 6                          # 4/5/6


# ---------- helpers ----------

def _percent_base(stat: str, hero) -> float:
    return {"ATK": hero.atk, "DEF": hero.dfn, "HP": hero.hp}[stat]


def _contribution(opt_type: str, raw_value: float, hero) -> tuple[str, float]:
    """Map an option (main or substat) with its raw value to (stat_code, amount)."""
    stat = C.OPTION_TARGET[opt_type]
    if opt_type in C.PERCENT_TYPES:
        return stat, _percent_base(stat, hero) * raw_value / 100
    return stat, raw_value


def _main_value(main_type: str, slot: str) -> int:
    pool = C.MAIN_VALUE_OFFENSE if slot == "offense" else C.MAIN_VALUE_DEFENSE
    if main_type not in pool:
        raise ValueError(f"{main_type!r} is not a legal {slot} main stat")
    return pool[main_type]


def _transcend_pct(grade: str, star_main: str, target: str, q2: int) -> float:
    """Transcend % for an ATK/DEF/HP target, per grade and main-stat affinity."""
    if target == "HP":
        return C.TRANSCEND["legend_hp" if grade == "LEGEND" else "rare_hp"][q2]
    main_match = star_main == target          # star_main is "ATK" or "DEF"
    if grade == "LEGEND":
        return C.TRANSCEND["legend_main"][q2] if main_match else C.TRANSCEND["nonmain"][q2]
    return C.TRANSCEND["rare_main"][q2] if main_match else C.TRANSCEND["nonmain"][q2]


# ---------- public API ----------

def _raw_totals(build: Build) -> dict:
    """Unfloored stat totals (internal; compute_stats floors these)."""
    hero = get_hero(build.hero)
    q2 = build.transcend
    ring_pct = C.RING_PERCENT[build.ring]

    sb = C.SET_BONUS.get(build.set_name, {})
    four = lambda key: sb[key][0] if key in sb else 0   # 4-piece value or 0

    # transcend flat bonus to a single rate stat (Q2>=4 and star4 matches)
    flat = {s: 0 for s in C.STATS}
    if q2 >= C.TRANSCEND_FLAT_LEVEL and hero.star4 in C.STAR4_TO_STAT:
        flat[C.STAR4_TO_STAT[hero.star4]] = C.TRANSCEND_FLAT[hero.star4]

    tr_atk = floor(_transcend_pct(hero.grade, hero.star_main, "ATK", q2) * hero.atk / 100)
    tr_def = floor(_transcend_pct(hero.grade, hero.star_main, "DEF", q2) * hero.dfn / 100)
    tr_hp = floor(_transcend_pct(hero.grade, hero.star_main, "HP", q2) * hero.hp / 100)

    totals: dict[str, float] = {s: 0.0 for s in C.STATS}
    totals["ATK"] = (C.EQUIP_FLAT_BASE["ATK"] + hero.atk + tr_atk + C.LEVEL_BONUS["ATK"][build.atk_lvl]
                     + hero.atk * four("ATK_pct") / 100 + hero.atk * ring_pct / 100)
    totals["DEF"] = (C.EQUIP_FLAT_BASE["DEF"] + hero.dfn + tr_def + C.LEVEL_BONUS["DEF"][build.def_lvl]
                     + hero.dfn * four("DEF_pct") / 100 + hero.dfn * ring_pct / 100)
    totals["HP"] = (C.EQUIP_FLAT_BASE["HP"] + hero.hp + tr_hp + C.LEVEL_BONUS["HP"][build.hp_lvl]
                    + hero.hp * four("HP_pct") / 100 + hero.hp * ring_pct / 100)
    totals["SPD"] = hero.spd
    totals["CR"] = C.INNATE_BASE["CR"] + flat["CR"] + four("CR")
    totals["CDM"] = C.INNATE_BASE["CDM"] + flat["CDM"]
    totals["WK"] = flat["WK"] + four("WK")
    totals["BLK"] = flat["BLK"] + four("BLK")
    totals["RED"] = flat["RED"]
    totals["EHR"] = flat["EHR"] + four("EHR")
    totals["ERes"] = four("ERes")

    # add equipment main + substats
    for p in build.pieces:
        stat, amt = _contribution(p.main, _main_value(p.main, p.slot), hero)
        totals[stat] += amt
        for sub_type, rolls in p.substats:
            value = C.SUBSTAT_BASE[sub_type] * (rolls + 1)
            stat, amt = _contribution(sub_type, value, hero)
            totals[stat] += amt

    return totals


def compute_stats(build: Build) -> dict:
    """Return the final 11 stats for a build (locked set assumed 4-piece)."""
    return {s: int(floor(v)) for s, v in _raw_totals(build).items()}


def validate_build(build: Build) -> list[str]:
    """Return a list of rule violations (empty list = valid)."""
    errors: list[str] = []
    for i, p in enumerate(build.pieces):
        types = [t for t, _ in p.substats]
        if len(types) != len(set(types)):
            errors.append(f"piece {i}: duplicate substats {types}")
        if sum(r for _, r in p.substats) > C.ROLLS_PER_PIECE:
            errors.append(f"piece {i}: rolls exceed {C.ROLLS_PER_PIECE}")
        if len(p.substats) > C.SUBSTATS_PER_PIECE:
            errors.append(f"piece {i}: more than {C.SUBSTATS_PER_PIECE} substats")
        for t, r in p.substats:
            if t not in C.SUBSTAT_BASE:
                errors.append(f"piece {i}: {t!r} is not a valid substat")
            if not (0 <= r <= C.ROLLS_PER_PIECE):
                errors.append(f"piece {i}: roll count {r} out of range")
    return errors
