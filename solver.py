"""Constraint-based build solver (greedy v2).

Pipeline:
  1. base check     -- which targets the bare build already meets
  2. allocate       -- for each unmet target, spend the cheapest resources first
                       (mains -> sub slots -> rolls) until it is covered
  3. priority fill  -- pour every leftover main / sub slot / roll into the
                       lexicographic objective (priority[0], then priority[1], ...)
  4. verify         -- compute_stats + confirm targets, with line-by-line reasoning

Resources are explicit: 2 offense + 2 defense main slots, 4 pieces x 4 distinct
substats, 5 rolls per piece. The objective is linear so pouring leftovers into the
top priority stat is optimal; targets simply reserve capacity first.
"""
from __future__ import annotations

from dataclasses import dataclass

import constants as C
from data import get_hero
from stats import Build, Piece, compute_stats, validate_build


@dataclass
class SolveResult:
    build: Build
    stats: dict
    reasoning: list
    targets_met: bool


def _conv(opt_type, hero):
    if opt_type in C.PERCENT_TYPES:
        base = {"ATK": hero.atk, "DEF": hero.dfn, "HP": hero.hp}[C.OPTION_TARGET[opt_type]]
        return base / 100
    return 1.0


def _best_sub_for(stat, hero):
    best = None
    for t, base in C.SUBSTAT_BASE.items():
        if C.OPTION_TARGET[t] == stat:
            v = base * _conv(t, hero)
            if best is None or v > best[1]:
                best = (t, v)
    return best


def _best_main_for(stat, slot, hero):
    pool = C.MAIN_VALUE_OFFENSE if slot == "offense" else C.MAIN_VALUE_DEFENSE
    best = None
    for t, v in pool.items():
        if C.OPTION_TARGET[t] == stat:
            val = v * _conv(t, hero)
            if best is None or val > best[1]:
                best = (t, val)
    return best


def solve(hero, set_name, *, targets=None, priority=None, transcend=0,
          atk_lvl=0, def_lvl=0, hp_lvl=0, ring=6, cap=5, force_cover=None):
    targets = dict(targets or {})
    priority = list(priority or ["ATK"])
    ctx = dict(transcend=transcend, atk_lvl=atk_lvl, def_lvl=def_lvl, hp_lvl=hp_lvl, ring=ring)
    h = get_hero(hero)
    reasoning = []

    pieces = [Piece(s, "", []) for s in ("offense", "offense", "defense", "defense")]

    def rolls_used(p):
        return sum(r for _, r in p.substats)

    def add_main(stat):
        for p in pieces:
            if p.main == "":
                m = _best_main_for(stat, p.slot, h)
                if m:
                    p.main = m[0]
                    return m[1]
        return None

    def add_sub_slot(stat):
        sub = _best_sub_for(stat, h)
        if not sub:
            return None
        for p in pieces:
            types = [t for t, _ in p.substats]
            if len(p.substats) < C.SUBSTATS_PER_PIECE and sub[0] not in types:
                p.substats.append((sub[0], 0))
                return sub[1]
        return None

    def add_roll(stat):
        sub = _best_sub_for(stat, h)
        if not sub:
            return None
        for p in pieces:
            if rolls_used(p) < C.ROLLS_PER_PIECE:
                for i, (t, r) in enumerate(p.substats):
                    if t == sub[0] and r < cap:
                        p.substats[i] = (t, r + 1)
                        return sub[1]
        return None

    # 1. base check
    base = compute_stats(Build(hero, set_name, [], **ctx))
    deficits = {}
    for stat, tgt in sorted(targets.items(), key=lambda kv: kv[1] - base[kv[0]], reverse=True):
        if base[stat] >= tgt:
            reasoning.append(f"\u2713 {stat}: \u0e10\u0e32\u0e19 {base[stat]} \u2265 \u0e40\u0e1b\u0e49\u0e32 {tgt} \u2192 \u0e44\u0e21\u0e48\u0e15\u0e49\u0e2d\u0e07\u0e43\u0e0a\u0e49\u0e0a\u0e48\u0e2d\u0e07")
        else:
            deficits[stat] = tgt - base[stat]

    force_cover = dict(force_cover or {})
    # 2. allocate to cover targets (cheapest resources first)
    for stat, deficit in deficits.items():
        got, n_main, n_sub, n_roll = 0.0, 0, 0, 0
        if force_cover.get(stat) != "sub":          # "sub" = skip mains, leave them for objective
            while got < deficit:
                v = add_main(stat)
                if v is None:
                    break
                got += v; n_main += 1
        while got < deficit:
            v = add_sub_slot(stat)
            if v is None:
                break
            got += v; n_sub += 1
        while got < deficit:
            v = add_roll(stat)
            if v is None:
                break
            got += v; n_roll += 1
        parts = []
        if n_main: parts.append(f"Main x{n_main}")
        if n_sub: parts.append(f"Sub x{n_sub}")
        if n_roll: parts.append(f"+{n_roll} roll")
        used = ", ".join(parts) if parts else "\u0e44\u0e21\u0e48\u0e21\u0e35\u0e2d\u0e2d\u0e1b\u0e0a\u0e31\u0e19\u0e23\u0e2d\u0e07\u0e23\u0e31\u0e1a"
        ok = "" if got >= deficit else "  \u26a0 \u0e44\u0e21\u0e48\u0e1e\u0e2d (\u0e15\u0e31\u0e19\u0e40\u0e1e\u0e14\u0e32\u0e19\u0e2d\u0e38\u0e1b\u0e01\u0e23\u0e13\u0e4c)"
        reasoning.append(f"\u2022 {stat}: \u0e02\u0e32\u0e14 {deficit} \u2192 {used}{ok}")

    # 3. priority fill
    def fill_main(slot):
        for s in priority:
            m = _best_main_for(s, slot, h)
            if m:
                return m[0]
        pool = C.MAIN_VALUE_OFFENSE if slot == "offense" else C.MAIN_VALUE_DEFENSE
        return max(pool, key=pool.get)

    for p in pieces:
        if p.main == "":
            p.main = fill_main(p.slot)

    # ranked filler substat types: each priority stat's subs, highest value first
    filler_types = []
    for s in priority:
        subs = sorted([t for t in C.SUBSTAT_BASE if C.OPTION_TARGET[t] == s],
                      key=lambda t: C.SUBSTAT_BASE[t] * _conv(t, h), reverse=True)
        filler_types += subs

    if filler_types:
        changed = True
        while changed:
            changed = False
            for p in pieces:
                if len(p.substats) >= C.SUBSTATS_PER_PIECE:
                    continue
                present = {t for t, _ in p.substats}
                nxt = next((t for t in filler_types if t not in present), None)
                if nxt is not None:
                    p.substats.append((nxt, 0))
                    changed = True
        for p in pieces:
            while rolls_used(p) < C.ROLLS_PER_PIECE:
                order = sorted(range(len(p.substats)), key=lambda i: (
                    priority.index(C.OPTION_TARGET[p.substats[i][0]])
                    if C.OPTION_TARGET[p.substats[i][0]] in priority else 99,
                    -C.SUBSTAT_BASE[p.substats[i][0]] * _conv(p.substats[i][0], h)))
                idx = next((i for i in order if p.substats[i][1] < cap), None)
                if idx is None:
                    break
                t, r = p.substats[idx]
                p.substats[idx] = (t, r + 1)

    build = Build(hero, set_name, pieces, **ctx)

    # 4. verify
    errs = validate_build(build)
    if errs:
        reasoning.append("\u26a0 \u0e1c\u0e34\u0e14\u0e01\u0e0e: " + "; ".join(errs))
    stats = compute_stats(build)
    met = all(stats[s] >= t for s, t in targets.items())
    for s, t in targets.items():
        reasoning.append(f"{'\u2713' if stats[s] >= t else '\u2717'} \u0e1c\u0e25 {s} = {stats[s]} (\u0e40\u0e1b\u0e49\u0e32 {t})")
    reasoning.append(f"\u2192 objective {' \u2192 '.join(priority)}: {priority[0]} = {stats[priority[0]]}")
    return SolveResult(build, stats, reasoning, met)


# ---------- Top-N alternatives ----------

def _has_main(stat, hero):
    return (_best_main_for(stat, "offense", hero) is not None
            or _best_main_for(stat, "defense", hero) is not None)


def _build_sig(build):
    """Signature for dedupe: mains + sorted substats per piece."""
    return tuple((p.slot, p.main, tuple(sorted(p.substats))) for p in build.pieces)


def top_builds(hero, set_name, *, targets=None, priority=None, n=3, cap=5, **ctx):
    """Return up to `n` meaningfully-different builds, ranked by the objective.

    Diversity axis: each target that *could* be covered by a main may instead be
    covered by substats, freeing different resources -> different objective result.
    """
    targets = dict(targets or {})
    priority = list(priority or ["ATK"])
    h = get_hero(hero)
    base = compute_stats(Build(hero, set_name, [], **ctx))
    flexible = [s for s, t in targets.items() if base[s] < t and _has_main(s, h)]

    import itertools
    seen, ranked = set(), []
    for combo in itertools.product(("main", "sub"), repeat=len(flexible)):
        fc = dict(zip(flexible, combo))
        r = solve(hero, set_name, targets=targets, priority=priority,
                  force_cover=fc, cap=cap, **ctx)
        if targets and not r.targets_met:
            continue
        sig = _build_sig(r.build)
        if sig in seen:
            continue
        seen.add(sig)
        ranked.append(r)

    if not ranked:                       # nothing met targets -> show best effort
        ranked = [solve(hero, set_name, targets=targets, priority=priority, cap=cap, **ctx)]
    ranked.sort(key=lambda r: tuple(-r.stats[s] for s in priority))
    return ranked[:n]
