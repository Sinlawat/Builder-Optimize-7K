"""Exact build optimizer via Integer Linear Programming (PuLP / CBC).

Decision variables per piece p (2 offense + 2 defense):
  m[p,t] in {0,1}   main option t is chosen (exactly one per piece, pool-restricted)
  x[p,t] in {0,1}   substat t is present (<= 4 per piece, distinct by construction)
  r[p,t] in Z>=0    extra rolls on substat t  (r <= cap*x, sum_t r <= 5)

A substat's value is base*(rolls+1) = base*(x + r), which is linear, so every stat
total is a linear expression. Targets become >= constraints; the lexicographic
objective (priority[0], then [1], ...) is handled by sequential re-optimization with
each solved stat locked at its optimum.

Why this matters: unlike greedy, ILP returns the GLOBAL optimum under the model.
The tests pin exact == greedy when there are no targets (a model-correctness net) and
exact's objective >= greedy's when targets conflict.
"""
from __future__ import annotations

import pulp

import constants as C
from data import get_hero
from stats import Build, Piece, compute_stats, validate_build, _raw_totals
from solver import SolveResult, _conv

_SLOT_OF = ["offense", "offense", "defense", "defense"]


def _pool(slot):
    return C.MAIN_VALUE_OFFENSE if slot == "offense" else C.MAIN_VALUE_DEFENSE


def _solve_model(hero, set_name, targets, priority, ctx, cap, h, base):
    """Solve the ILP for the given targets. Return SolveResult, or None if infeasible."""
    prob = pulp.LpProblem("skre_exact", pulp.LpMaximize)
    subs = list(C.SUBSTAT_BASE)

    m, x, r = {}, {}, {}
    for p in range(4):
        pool = _pool(_SLOT_OF[p])
        pool_types = list(pool)
        for i, t in enumerate(pool_types):
            m[(p, t)] = pulp.LpVariable(f"m_{p}_{i}", cat="Binary")
        prob += pulp.lpSum(m[(p, t)] for t in pool_types) == 1
        for j, t in enumerate(subs):
            x[(p, t)] = pulp.LpVariable(f"x_{p}_{j}", cat="Binary")
            r[(p, t)] = pulp.LpVariable(f"r_{p}_{j}", lowBound=0, upBound=cap, cat="Integer")
            prob += r[(p, t)] <= cap * x[(p, t)]
        prob += pulp.lpSum(x[(p, t)] for t in subs) <= C.SUBSTATS_PER_PIECE
        prob += pulp.lpSum(r[(p, t)] for t in subs) <= C.ROLLS_PER_PIECE

    def total(s):
        e = base[s]
        for p in range(4):
            for t, v in _pool(_SLOT_OF[p]).items():
                if C.OPTION_TARGET[t] == s:
                    e += m[(p, t)] * (v * _conv(t, h))
            for t, bv in C.SUBSTAT_BASE.items():
                if C.OPTION_TARGET[t] == s:
                    e += (x[(p, t)] + r[(p, t)]) * (bv * _conv(t, h))
        return e

    for s, tgt in targets.items():
        prob += total(s) >= tgt

    # lexicographic objective: maximize priority[0], lock it, then priority[1], ...
    for stat in priority:
        prob.setObjective(total(stat))
        status = prob.solve(pulp.PULP_CBC_CMD(msg=0))
        if pulp.LpStatus[status] != "Optimal":
            return None
        prob += total(stat) >= pulp.value(total(stat)) - 1e-6

    # extract the build
    pieces = []
    for p in range(4):
        pool = _pool(_SLOT_OF[p])
        main = next(t for t in pool if m[(p, t)].value() > 0.5)
        sub_list = [(t, int(round(r[(p, t)].value())))
                    for t in subs if x[(p, t)].value() > 0.5]
        pieces.append(Piece(_SLOT_OF[p], main, sub_list))
    build = Build(hero, set_name, pieces, **ctx)
    stats = compute_stats(build)
    met = all(stats[s] >= t for s, t in targets.items())
    return SolveResult(build, stats, [], met)


def solve_exact(hero, set_name, *, targets=None, priority=None, transcend=0,
                atk_lvl=0, def_lvl=0, hp_lvl=0, ring=6, cap=5) -> SolveResult:
    targets = dict(targets or {})
    priority = list(priority or ["ATK"])
    ctx = dict(transcend=transcend, atk_lvl=atk_lvl, def_lvl=def_lvl, hp_lvl=hp_lvl, ring=ring)
    h = get_hero(hero)
    base = _raw_totals(Build(hero, set_name, [], **ctx))   # unfloored fixed part

    reasoning = []
    # base check
    floored_base = compute_stats(Build(hero, set_name, [], **ctx))
    for s, t in targets.items():
        if floored_base[s] >= t:
            reasoning.append(f"\u2713 {s}: \u0e10\u0e32\u0e19 {floored_base[s]} \u2265 \u0e40\u0e1b\u0e49\u0e32 {t}")

    res = _solve_model(hero, set_name, targets, priority, ctx, cap, h, base)
    if res is None:                       # targets infeasible -> best effort, no targets
        res = _solve_model(hero, set_name, {}, priority, ctx, cap, h, base)
        res.targets_met = False
        reasoning.append("\u26a0 target \u0e02\u0e31\u0e14\u0e41\u0e22\u0e49\u0e07/\u0e40\u0e01\u0e34\u0e19\u0e40\u0e1e\u0e14\u0e32\u0e19 \u2014 \u0e41\u0e2a\u0e14\u0e07\u0e1a\u0e34\u0e25\u0e14\u0e4c\u0e17\u0e35\u0e48\u0e14\u0e35\u0e17\u0e35\u0e48\u0e2a\u0e38\u0e14\u0e42\u0e14\u0e22\u0e44\u0e21\u0e48\u0e1a\u0e31\u0e07\u0e04\u0e31\u0e1a target")

    errs = validate_build(res.build)
    if errs:
        reasoning.append("\u26a0 \u0e1c\u0e34\u0e14\u0e01\u0e0e: " + "; ".join(errs))
    for s, t in targets.items():
        reasoning.append(f"{'\u2713' if res.stats[s] >= t else '\u2717'} \u0e1c\u0e25 {s} = {res.stats[s]} (\u0e40\u0e1b\u0e49\u0e32 {t})")
    reasoning.append(f"\u2192 objective {' \u2192 '.join(priority)}: {priority[0]} = {res.stats[priority[0]]}  (global optimum / ILP)")
    res.reasoning = reasoning
    return res
